"""Persist installed native CD driver and FLAC encoder packages."""
import platform
from pathlib import Path

base = Path('/mnt/sda2/tce')
packages = ['cdrom-' + platform.release() + '.tcz', 'pcp-ffmpeg.tcz']
for name in packages:
    if not (base / 'optional' / name).exists():
        raise SystemExit('Install native extension first: ' + name)
path = base / 'onboot.lst'
entries = path.read_text().splitlines()
for name in packages:
    if name not in entries:
        entries.append(name)
path.write_text('\n'.join(entries) + '\n')
print('Native CD driver and FLAC encoding dependencies saved')
