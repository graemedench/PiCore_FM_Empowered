"""Enable native pCP Squeezelite visualizer, preserving playback state."""
import re
import shutil
import subprocess
import time
from pathlib import Path
from sable.pcp.listener import LyrionListener

listener = LyrionListener(None, None)
before = listener.rpc(['status', '-', '1'])
cfg = Path('/usr/local/etc/pcp/pcp.cfg')
text = cfg.read_text()
backup = Path('/home/tc/sable-pcp-stage/pcp.cfg.before-visualizer')
if not backup.exists():
    shutil.copy2(cfg, backup)
changed, count = re.subn(r'^VISUALISER=.*$', 'VISUALISER="yes"', text, flags=re.M)
if count != 1:
    raise RuntimeError('Expected exactly one VISUALISER setting')
cfg.write_text(changed)
subprocess.run(['/usr/local/etc/init.d/squeezelite', 'restart'], check=True)
deadline = time.monotonic() + 15
while time.monotonic() < deadline:
    time.sleep(.5)
    status = listener.rpc(['status', '-', '1'])
    if status.get('player_connected') and list(Path('/dev/shm').glob('squeezelite-*')):
        break
else:
    raise RuntimeError('Player visualizer did not become ready')
listener.rpc(['pause', '1'] if before['mode'] == 'pause' else [before['mode']])
if before.get('can_seek') and before.get('time'):
    listener.rpc(['time', str(before['time'])])
print('Native visualizer enabled; previous playback state restored')
