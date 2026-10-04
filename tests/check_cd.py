"""Read-only live CD/WAV range check; never starts playback or ripping."""
import struct
import urllib.request
from sable.pcp.cd import CDService, ReadAudio, pcm, toc
import ctypes

assert ctypes.sizeof(ReadAudio) == 24
assert ReadAudio.buffer.offset == 16
service = CDService()
disc = service.inspect()
assert disc and disc['tracks']
assert all(t['end'] > t['start'] for t in disc['tracks'])
url = service.url(disc['tracks'][0]['number'])
request = urllib.request.Request(url, headers={'Range': 'bytes=0-4095'})
with urllib.request.urlopen(request, timeout=15) as response:
    data = response.read()
    assert response.status == 206 and len(data) == 4096
    assert data[:4] == b'RIFF' and data[8:12] == b'WAVE'
    assert struct.unpack_from('<I', data, 24)[0] == 44100
print('PASS: CD TOC, aarch64 ABI, WAV stream and byte range; tracks:', len(disc['tracks']))
