"""Idempotent receiver setup corrections; reboot after applying."""
from pathlib import Path
import shutil, subprocess, re
backup=Path('/mnt/sda2/FM4 Backups/Receivers')
backup.mkdir(parents=True,exist_ok=True)
def save(path):
    target=backup/path.name
    if not target.exists(): shutil.copy2(path,target)
boot=Path('/mnt/sda1')
mounted=any(x.split()[1]==str(boot) for x in Path('/proc/mounts').read_text().splitlines())
if not mounted: subprocess.run(['mount','/dev/sda1',str(boot)],check=True)
try:
    p=boot/'config.txt';s=p.read_text()
    updated=re.sub(r'^dtoverlay=disable-bt\s*$', '# Built-in Bluetooth enabled for Sable receivers',s,flags=re.M)
    if updated!=s: save(p);p.write_text(updated);subprocess.run(['sync'],check=True)
finally:
    if not mounted: subprocess.run(['umount',str(boot)],check=True)
p=Path('/usr/local/etc/pcp/shairport-sync-ap2.conf')
if p.exists():
    s=p.read_text();updated=s.replace('name = "FM4-Reborn AirPlay"','name = "%h"')
    if updated!=s: save(p);p.write_text(updated)
p=Path('/usr/local/bin/pcp-btspeaker-daemon.py')
if p.exists():
    s=p.read_text()
    needle='    proc = Popen(args, stdout=DEVNULL, stderr=DEVNULL, shell=False)'
    patch="""    # Sable: release local audio before the Bluetooth helper opens ALSA.
    if output == 'fm4_receiver':
        import subprocess
        subprocess.run(['/usr/local/bin/python3.11', '-c',
            "import sys; sys.path.insert(0, '/home/tc/sable-pcp-stage/src'); from sable.pcp.receiver_hook import begin; begin('bluetooth')"],
            check=True, timeout=15)
"""
    if patch not in s:
        if s.count(needle)!=1: raise RuntimeError('Unrecognised Bluetooth daemon; refusing patch')
        save(p);s=s.replace(needle,patch+needle);compile(s,str(p),'exec')
        if p.is_symlink(): p.unlink()
        p.write_text(s);p.chmod(0o755)
    p=Path('/opt/.filetool.lst');rows=p.read_text().splitlines()
    entry='usr/local/bin/pcp-btspeaker-daemon.py'
    if entry not in rows: p.write_text('\n'.join(rows+[entry])+'\n')
print('Receiver fixes applied; reboot to load Bluetooth changes')
