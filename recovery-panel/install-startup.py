#!/usr/bin/env python3
"""Register the already-installed panel with piCorePlayer's persistent startup."""
from pathlib import Path
import os
import shutil

app = Path('/home/tc/quadify-pcp')
boot = Path('/opt/bootlocal.sh')
config = Path('/usr/local/etc/pcp/pcp.cfg')
onboot = Path('/etc/sysconfig/tcedir/onboot.lst')
for path, backup in [(boot, 'bootlocal.sh.before'), (config, 'pcp.cfg.before'),
                     (onboot, 'onboot.lst.before')]:
    destination = app / backup
    if not destination.exists():
        shutil.copyfile(path, destination)
        os.chmod(destination, 0o600)

text = boot.read_text()
entry = '/bin/sh /home/tc/quadify-pcp/start.sh'
text = text.replace('\n# Quadify OLED and encoder\n' + entry + '\n', '\n')
boot.write_text(text)
text = config.read_text()
for key, value in [('LMSERVER', 'yes'), ('NTPD', 'yes'), ('SERVER_IP', '127.0.0.1'),
                   ('USER_COMMAND_1', entry)]:
    lines = text.splitlines()
    replacement = '%s="%s"' % (key, value)
    if any(line.startswith(key + '=') for line in lines):
        lines = [replacement if line.startswith(key + '=') else line for line in lines]
    else:
        lines.append(replacement)
    text = '\n'.join(lines) + '\n'
config.write_text(text)
text = onboot.read_text()
for package in ['python3.11.tcz', 'slimserver.tcz']:
    if package not in text.splitlines():
        text = text.rstrip() + '\n' + package + '\n'
onboot.write_text(text)
os.chmod(app / 'start.sh', 0o755)
print('Panel boot startup registered; local Lyrion autostart enabled.')
