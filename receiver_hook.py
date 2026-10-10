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

def ensure_local_player():
    """Retry an early ALSA-open failure without trusting the native PID file."""
    import fcntl
    with open('/tmp/fm4-local-player.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        pidfile = Path('/var/run/squeezelite.pid')
        def running():
            return subprocess.run(['pidof', 'squeezelite'], capture_output=True).returncode == 0
        for attempt in range(4):
            if state.exists():
                raise RuntimeError('Receiver still owns audio')
            if not running():
                if pidfile.exists():
                    pid = pidfile.read_text().strip()
                    # Never remove a PID file belonging to a live process.
                    if pid.isdigit() and Path('/proc', pid).exists():
                        raise RuntimeError('Squeezelite PID file belongs to a live process')
                    pidfile.unlink()
                with open('/tmp/fm4-local-player-start.log', 'ab') as log:
                    subprocess.run(['/usr/local/etc/init.d/squeezelite', 'start'],
                                   stdout=log, stderr=log, timeout=10, check=False)
                time.sleep(1)
            if running():
                listener = LyrionListener(None, None)
                for _ in range(8):
                    if not running(): break
                    try:
                        if listener.rpc(['status', '-', '1']).get('player_connected'):
                            return
                    except Exception:
                        pass
                    time.sleep(.25)
            time.sleep(.5)
        raise RuntimeError('Local audio player did not reconnect')


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
    ensure_local_player()


def return_local():
    """Explicit local playback ends receiver ownership even if a phone stays connected."""
    if not state.exists():
        ensure_local_player()
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
    ensure_local_player()
    if 'SHAIRPORT="no"' not in Path('/usr/local/etc/pcp/pcp.cfg').read_text():
        subprocess.run(['/usr/local/etc/init.d/shairport-sync', 'start'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    if sys.argv[1] == 'start':
        begin()
    elif sys.argv[1] == 'stop':
        end()
