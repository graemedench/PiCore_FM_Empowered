"""Hand USB audio to AirPlay, then return to the paused local player."""
import json
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


if __name__ == '__main__':
    if sys.argv[1] == 'start':
        begin()
    elif sys.argv[1] == 'stop':
        end()
