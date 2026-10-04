"""Hand USB audio to AirPlay, then return to the paused local player."""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from .listener import LyrionListener

state = Path('/tmp/fm4-receiver.json')


def begin(source='airplay'):
    try:
        LyrionListener(None, None).rpc(['pause', '1'])
    except Exception:
        pass
    subprocess.run(['/usr/local/etc/init.d/squeezelite', 'stop'], check=False)
    temporary = state.with_suffix('.new')
    temporary.write_text(json.dumps(dict(source=source, started=time.time())))
    temporary.replace(state)


def end(source='airplay'):
    if state.exists() and json.loads(state.read_text()).get('source') != source:
        return
    state.unlink(missing_ok=True)
    subprocess.run(['/usr/local/etc/init.d/squeezelite', 'start'], check=False)


def return_local():
    """Explicit local playback ends receiver ownership even if a phone stays connected."""
    if not state.exists():
        return
    # Disconnect only native Bluetooth audio players, not unrelated peripherals.
    for entry in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            args = entry.read_bytes().decode().strip('\0').split('\0')
            if args and Path(args[0]).name == 'bluealsa-aplay':
                address = args[-1]
                if len(address) == 17 and address.count(':') == 5:
                    try:
                        subprocess.run(['bluetoothctl', 'disconnect', address],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                    except subprocess.TimeoutExpired:
                        pass
                    # Native BlueALSA can leave its audio helper running after disconnect.
                    # A stale helper must not reclaim ownership from local playback.
                    os.kill(int(entry.parent.name), signal.SIGTERM)
        except (OSError, UnicodeError, subprocess.TimeoutExpired):
            pass
    subprocess.run(['/usr/local/etc/init.d/shairport-sync', 'stop'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        if subprocess.run(['pidof', 'shairport-sync-ap2'],
                          stdout=subprocess.DEVNULL).returncode != 0:
            break
        time.sleep(.1)
    state.unlink(missing_ok=True)
    subprocess.run(['/usr/local/etc/init.d/squeezelite', 'start'], check=False)
    subprocess.run(['/usr/local/etc/init.d/shairport-sync', 'start'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    if sys.argv[1] == 'start':
        begin()
    elif sys.argv[1] == 'stop':
        end()
