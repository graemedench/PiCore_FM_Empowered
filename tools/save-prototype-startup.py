"""Save the tested prototype as native pCP startup, with local recovery backup."""
import re
import shutil
from pathlib import Path

cfg = Path('/usr/local/etc/pcp/pcp.cfg')
backup = Path('/home/tc/sable-pcp-stage/pcp.cfg.before-prototype-startup')
if not backup.exists():
    shutil.copy2(cfg, backup)
text, count = re.subn(r'^USER_COMMAND_1=.*$',
    'USER_COMMAND_1="/bin/sh /home/tc/sable-pcp-stage/stage-start.sh"',
    cfg.read_text(), flags=re.M)
if count != 1:
    raise RuntimeError('Expected exactly one native user startup setting')
cfg.write_text(text)
print('Native prototype startup saved; run pcp bu to persist configuration')
