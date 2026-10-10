"""Receiver track details, independent of the paused Lyrion queue."""
import base64
import os
import re
import threading
from pathlib import Path

_airplay = {}
_started = False

def _read_airplay():
    import time
    path = '/tmp/shairport-sync-metadata'
    buffer = b''
    while True:
        try:
            with open(path, 'rb', buffering=0) as stream:
                while True:
                    chunk = stream.read(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    while b'</item>' in buffer:
                        item, buffer = buffer.split(b'</item>', 1)
                        code = re.search(rb'<code>([0-9a-fA-F]+)</code>', item)
                        data = re.search(rb'<data[^>]*>(.*?)</data>', item, re.S)
                        if not code or not data:
                            continue
                        key = {'6d696e6d': 'title', '61736172': 'artist',
                               '6173616c': 'album'}.get(code[1].decode().lower())
                        if code[1].decode().lower() == '50494354' and data:
                            image = base64.b64decode(data[1])
                            if image.startswith(b'\xff\xd8') or image.startswith(b'\x89PNG'):
                                import hashlib
                                name = 'receiver-art-' + hashlib.sha256(image).hexdigest()[:16] + '.img'
                                target = Path('/var/www') / name
                                target.write_bytes(image)
                                _airplay['albumart'] = 'http://127.0.0.1/' + name
                        if key:
                            _airplay[key] = base64.b64decode(data[1]).decode('utf-8', 'replace')
                    if len(buffer) > 2000000:
                        buffer = b''
        except (OSError, ValueError):
            pass
        time.sleep(1)

def decorate(state):
    global _started
    if not _started:
        _started = True
        threading.Thread(target=_read_airplay, daemon=True, name='receiver-metadata').start()
    if state['service'] == 'airplay':
        state.update(dict(_airplay))
        # Session age is not the current track position.
        state['seek'] = 0
        return
    if state['service'] != 'bluetooth':
        return
    import dbus
    bus = dbus.SystemBus()
    objects = dbus.Interface(bus.get_object('org.bluez', '/'),
                             'org.freedesktop.DBus.ObjectManager').GetManagedObjects()
    for path, interfaces in objects.items():
        player = interfaces.get('org.bluez.MediaPlayer1')
        if not player:
            continue
        device = objects.get(player.get('Device'), {}).get('org.bluez.Device1', {})
        if not device.get('Connected', False):
            continue
        track = player.get('Track', {})
        state.update(title=str(track.get('Title') or 'Bluetooth'),
                     artist=str(track.get('Artist') or device.get('Alias') or 'Connected receiver'),
                     album=str(track.get('Album') or ''),
                     status='play' if player.get('Status') == 'playing' else 'pause',
                     seek=int(player.get('Position', 0)), duration=int(track.get('Duration', 0)) // 1000,
                     stream=not bool(track.get('Duration')))
        break
