"""Optional native HDMI preparation; leave it disabled until explicitly chosen."""
from pathlib import Path
import shutil
import subprocess
import re


def prepare():
    if not Path('/opt/jivelite/bin/jivelite.sh').exists():
        for mode in ('-w', '-i'):
            subprocess.run(['sudo', '-u', 'tc', 'pcp-load', mode,
                            'pcp-jivelite-vis.tcz'], check=True, timeout=600)
    onboot = Path('/mnt/sda2/tce/onboot.lst')
    rows = onboot.read_text().splitlines()
    if 'pcp-jivelite-vis.tcz' not in rows:
        onboot.write_text('\n'.join(rows + ['pcp-jivelite-vis.tcz']) + '\n')
    boot = Path('/mnt/sda1')
    boot.mkdir(exist_ok=True)
    mounts = [line.split() for line in Path('/proc/mounts').read_text().splitlines()
              if line.split()[1] == str(boot)]
    if mounts and mounts[0][0] != '/dev/sda1':
        raise RuntimeError('Unexpected boot mount; inspect manually')
    if not mounts:
        subprocess.run(['mount', '-t', 'vfat', '/dev/sda1', str(boot)], check=True)
    try:
        config = boot / 'config.txt'
        text = config.read_text()
        if not re.search(r'^dtoverlay=vc4-kms-v3d(?:,.*)?\s*$', text, re.M):
            backup = boot / 'config.txt.before-fm4-hdmi'
            if not backup.exists():
                shutil.copy2(config, backup)
            config.write_text(text + '\n[all]\n# FM4 optional HDMI\ndtoverlay=vc4-kms-v3d\n')
        subprocess.run(['sync'], check=True)
    finally:
        if not mounts:
            subprocess.run(['umount', str(boot)], check=True)
    exclusions = Path('/opt/.xfiletool.lst')
    rows = exclusions.read_text().splitlines() if exclusions.exists() else []
    if 'opt/jivelite' not in rows:
        exclusions.write_text('\n'.join(rows + ['opt/jivelite']) + '\n')
    config = Path('/usr/local/etc/pcp/pcp.cfg')
    text = config.read_text()
    text = re.sub(r'^SCREENVC4=.*$', 'SCREENVC4="yes"', text, flags=re.M)
    config.write_text(text)
