"""Fresh USB-SSD overlay installer. --check is read-only; never formats disks."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile
import time
import urllib.request

HERE = Path(__file__).resolve().parent
STAGE = Path('/home/tc/sable-pcp-stage')
RECOVERY = Path('/home/tc/quadify-pcp')
CFG = Path('/usr/local/etc/pcp/pcp.cfg')

def run(*args):
    subprocess.run(args, check=True)

def check():
    problems = []
    if platform.machine() != 'aarch64':
        problems.append('Requires the tested aarch64 piCorePlayer image')
    for path in (CFG, Path('/mnt/sda2/tce/onboot.lst'), Path('/dev/spidev0.0')):
        if not path.exists():
            problems.append('Missing prerequisite: ' + str(path))
    try:
        with urllib.request.urlopen('http://127.0.0.1:9000', timeout=5) as response:
            if response.status != 200:
                problems.append('Local Lyrion server is not ready')
    except Exception:
        problems.append('Install/start local Lyrion and allow localhost before installing')
    if STAGE.exists() or RECOVERY.exists():
        problems.append('Existing FM4 installation found: fresh-install mode will not overwrite it')
    archive = HERE / 'sable-pcp-stage.tar.gz'
    checksum = HERE / 'sable-pcp-stage.tar.gz.sha256'
    if not archive.exists() or not checksum.exists():
        problems.append('Build bundle first: archive/checksum missing')
    elif hashlib.sha256(archive.read_bytes()).hexdigest() != checksum.read_text().split()[0].lower():
        problems.append('Archive checksum mismatch')
    print('\n'.join(problems) if problems else 'Fresh-install prerequisites passed')
    return problems

def extract(archive, target):
    with tarfile.open(archive) as source:
        for item in source.getmembers():
            destination = (target / item.name).resolve()
            if not destination.is_relative_to(target.resolve()) or item.issym() or item.islnk() or not (item.isfile() or item.isdir()):
                raise RuntimeError('Unsafe archive member: ' + item.name)
        source.extractall(target, filter='data')

def install():
    if os.geteuid() != 0:
        raise SystemExit('Run installation with sudo; --check needs no sudo')
    if check():
        raise SystemExit('Resolve the prerequisites in INSTALL.md first')
    backup = Path('/home/tc/fm4-install-backup') / time.strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True, mode=0o700)
    for name, source in [('pcp.cfg', CFG), ('onboot.lst', Path('/mnt/sda2/tce/onboot.lst')), ('filetool.lst', Path('/opt/.filetool.lst'))]:
        shutil.copy2(source, backup / name)
    (backup / 'install.log').write_text('Fresh FM4 overlay install started\n')
    packages = ['python3.11', 'dejavu-fonts-ttf', 'pcp-ffmpeg', 'pcp-lame', 'cdrom-' + platform.release()]
    for package in packages:
        run('sudo', '-u', 'tc', 'tce-load', '-wi', package)
    extract(HERE / 'sable-pcp-stage.tar.gz', STAGE)
    shutil.copytree(HERE / 'recovery-panel', RECOVERY)
    run('chown', '-R', 'tc:staff', str(STAGE), str(RECOVERY))
    run('sudo', '-u', 'tc', 'python3.11', '-m', 'ensurepip', '--user')
    run('sudo', '-u', 'tc', 'python3.11', '-m', 'pip', 'install', '--only-binary=:all:', '--target', str(RECOVERY / 'vendor'), '-r', str(HERE / 'requirements-lock.txt'))
    font = next(Path('/usr/local/share/fonts').rglob('DejaVuSans.ttf'))
    shutil.copy2(font, RECOVERY / 'arial.ttf')
    for name in ('Music', 'Playlists'):
        path = Path('/mnt/sda2') / name
        path.mkdir(exist_ok=True)
        run('chown', 'tc:staff', str(path))
    for helper in ('ensure-player-id.py', 'setup-native-cd.py'):
        run('python3.11', str(STAGE / helper))
    text = CFG.read_text()
    text, count = re.subn(r'^VISUALISER=.*$', 'VISUALISER="yes"', text, flags=re.M)
    if count != 1:
        raise RuntimeError('Native VISUALISER setting missing')
    CFG.write_text(text)
    entries = Path('/opt/.filetool.lst').read_text().splitlines()
    for entry in ('home/tc', 'usr/local/etc/pcp'):
        if entry not in entries:
            entries.append(entry)
    Path('/opt/.filetool.lst').write_text('\n'.join(entries) + '\n')
    # Startup is enabled last, after dependencies and files are in place.
    run('python3.11', str(STAGE / 'save-prototype-startup.py'))
    run('pcp', 'bu')
    (backup / 'install.log').write_text('Fresh FM4 overlay installed; native backup completed. Reboot and validate hardware.\n')
    print('Installed. Reboot, then follow the acceptance checklist in INSTALL.md.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    if args.check == args.install:
        parser.error('Choose --check or --install')
    if args.check:
        raise SystemExit(bool(check()))
    install()
