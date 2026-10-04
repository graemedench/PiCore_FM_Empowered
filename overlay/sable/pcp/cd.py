"""Linux CD audio IOCTL reader and loopback WAV service for local Lyrion.

ABI: linux/uapi/cdrom.h. Direct extraction retries failed reads; this is not
cdparanoia secure ripping or an AccurateRip verification implementation.
"""
import ctypes
import fcntl
import hashlib
import os
from pathlib import Path
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 9180
SECTOR = 2352
_io_lock = threading.Lock()


def devices():
    return ['/dev/' + p.name for p in sorted(Path('/sys/class/block').glob('sr*'))]


def toc(device):
    fd = os.open(device, os.O_RDONLY | os.O_NONBLOCK)
    try:
        header = bytearray(2)
        fcntl.ioctl(fd, 0x5305, header)
        first, last = header
        if not 1 <= first <= last <= 99:
            raise ValueError('Invalid CD table')
        entries = []
        for number in list(range(first, last + 1)) + [0xAA]:
            entry = bytearray(12)
            entry[0], entry[2] = number, 1  # CDROM_LBA
            fcntl.ioctl(fd, 0x5306, entry)
            entries.append((number, struct.unpack_from('=i', entry, 4)[0], bool(entry[1] & 0x40)))
        tracks = [dict(number=n, start=start, end=entries[i+1][1],
                       duration=(entries[i+1][1]-start)/75)
                  for i, (n, start, data) in enumerate(entries[:-1]) if not data]
        if not tracks:
            raise ValueError('No audio tracks')
        identity = hashlib.sha256(repr(entries).encode()).hexdigest()[:20]
        return dict(device=device, id=identity, tracks=tracks, entries=entries)
    finally:
        os.close(fd)


class ReadAudio(ctypes.Structure):
    _fields_ = [('lba', ctypes.c_int), ('format', ctypes.c_ubyte),
                ('frames', ctypes.c_int), ('buffer', ctypes.c_void_p)]


def pcm(fd, start, frames):
    buffer = ctypes.create_string_buffer(frames * SECTOR)
    request = ReadAudio(start, 1, frames, ctypes.addressof(buffer))
    argument = bytearray(bytes(request))
    for attempt in range(3):
        try:
            with _io_lock:
                fcntl.ioctl(fd, 0x530e, argument)
            return buffer.raw
        except OSError:
            if attempt == 2:
                raise
            time.sleep(.05)


def wav_header(size):
    return struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', size+36, b'WAVE', b'fmt ',
                       16, 1, 2, 44100, 176400, 4, 16, b'data', size)


def chunks(disc, track, offset=0, length=None):
    size = (track['end'] - track['start']) * SECTOR
    remaining = size-offset if length is None else length
    fd = os.open(disc['device'], os.O_RDONLY | os.O_NONBLOCK)
    try:
        sector, skip = divmod(offset, SECTOR)
        while remaining > 0:
            if sector % 240 == 0 and toc(disc['device'])['id'] != disc['id']:
                raise ValueError('CD changed')
            count = min(16, track['end']-track['start']-sector)
            if count <= 0:
                return
            data = pcm(fd, track['start']+sector, count)[skip:]
            data = data[:remaining]
            yield data
            remaining -= len(data)
            sector += count
            skip = 0
    finally:
        os.close(fd)


def rip_flac(disc, destination, cancel, report):
    import shutil
    import subprocess
    import tempfile
    import wave
    root = Path(destination).resolve()
    if root != Path('/mnt/sda2/Music') or not Path('/mnt/sda2').is_mount():
        raise ValueError('Music storage unavailable')
    if shutil.disk_usage(root).free < 1024**3:
        raise ValueError('At least 1 GB free required')
    if toc(disc['device'])['id'] != disc['id']:
        raise ValueError('CD changed')
    parent = root / 'CD Rips'
    parent.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='Audio CD ' + disc['id'] + ' ', dir=str(parent)))
    folder.chmod(0o755)
    for index, track in enumerate(disc['tracks'], 1):
        if cancel.is_set():
            report('Rip cancelled - saved tracks kept')
            return
        frames = track['end'] - track['start']
        report('Reading track %d/%d' % (index, len(disc['tracks'])), 0)
        with tempfile.TemporaryDirectory(prefix='.track-', dir=str(folder)) as temporary:
            wav = Path(temporary) / 'audio.wav'
            count = 0
            with wave.open(str(wav), 'wb') as output:
                output.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
                for data in chunks(disc, track):
                    if cancel.is_set():
                        report('Rip cancelled - saved tracks kept')
                        return
                    output.writeframesraw(data)
                    count += len(data)
                    if count % (240*SECTOR) == 0:
                        report('Reading track %d/%d' % (index, len(disc['tracks'])), .5*count/(frames*SECTOR))
            if count != frames*SECTOR or toc(disc['device'])['id'] != disc['id']:
                raise ValueError('Incomplete read / CD changed')
            report('Encoding track %d/%d' % (index, len(disc['tracks'])), .5)
            partial = Path(temporary) / 'audio.flac'
            process = subprocess.Popen(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error',
                '-n', '-i', str(wav), '-threads', '1', '-c:a', 'flac', '-metadata',
                'title=' + track.get('title', 'Track %02d' % track['number']), '-metadata',
                'album=' + disc.get('album', 'Audio CD'), '-metadata',
                'artist=' + track.get('artist', disc.get('artist', '')), 
                '-metadata', 'track=%d' % track['number'], str(partial)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline = time.monotonic()+900
            while process.poll() is None:
                if cancel.wait(.2) or time.monotonic() > deadline:
                    process.terminate()
                    try:
                        process.wait(3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    report('Rip cancelled - saved tracks kept')
                    return
            if process.returncode:
                raise ValueError('FLAC encoding failed')
            partial.chmod(0o644)
            partial.rename(folder / ('%02d - Track %02d.flac' % (track['number'], track['number'])))
        report('Saved track %d/%d' % (index, len(disc['tracks'])), 1)
    report('Rip complete: %d tracks (FLAC)' % len(disc['tracks']), 1)


class CDService:
    def __init__(self):
        self.disc = None
        self.server = None
        from .cd_metadata import Metadata
        self.metadata = Metadata()

    def inspect(self, lookup=False):
        found = devices()
        self.disc = toc(found[0]) if found else None
        if self.disc:
            self.metadata.apply(self.disc, lookup)
        return self.disc

    def url(self, number):
        return 'http://127.0.0.1:%d/cd/%s/%d.wav' % (PORT, self.disc['id'], number)

    def start(self):
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_HEAD(self):
                self.serve(False)

            def do_GET(self):
                self.serve(True)

            def serve(self, body):
                try:
                    parts = self.path.split('/')
                    if len(parts) != 4 or parts[1] != 'cd':
                        self.send_error(404)
                        return
                    disc = owner.inspect()
                    if not disc or disc['id'] != parts[2]:
                        self.send_error(410, 'CD changed or removed')
                        return
                    number = int(parts[3].removesuffix('.wav'))
                    track = next(t for t in disc['tracks'] if t['number'] == number)
                    data_size = (track['end']-track['start'])*SECTOR
                    size = data_size + 44
                    start, end = 0, size-1
                    range_header = self.headers.get('Range')
                    if range_header:
                        import re
                        match = re.fullmatch(r'bytes=(\d+)-(\d*)', range_header)
                        if not match:
                            self.send_error(416)
                            return
                        start = int(match[1])
                        end = min(size-1, int(match[2])) if match[2] else size-1
                        if start > end:
                            self.send_error(416)
                            return
                    self.send_response(206 if range_header else 200)
                    self.send_header('Content-Type', 'audio/wav')
                    self.send_header('Content-Length', str(end-start+1))
                    self.send_header('Accept-Ranges', 'bytes')
                    if range_header:
                        self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
                    self.end_headers()
                    if body:
                        if start < 44:
                            self.wfile.write(wav_header(data_size)[start:min(44, end+1)])
                        if end >= 44:
                            for data in chunks(disc, track, max(0, start-44), end-max(44, start)+1):
                                self.wfile.write(data)
                except (OSError, ValueError, StopIteration):
                    self.close_connection = True
        self.server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True, name='fm4-cd-http').start()

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
