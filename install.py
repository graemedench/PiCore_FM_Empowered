"""Fresh USB-SSD overlay installer. --check is read-only; never formats disks."""
import argparse
import hashlib
import json
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
STATE = Path('/mnt/sda2/fm4-installer-state.json')

def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}

def save_state(values):
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(values, indent=2) + '\n')
    temporary.replace(STATE)

def run(*args):
    progress = state()
    key = json.dumps([str(arg) for arg in args])
    cacheable = any(token in args for token in ('pcp-load', 'tce-load', 'pip', 'ensurepip'))
    if cacheable and key in progress.get('commands', []):
        print('Already completed:', ' '.join(map(str, args)), flush=True)
        return
    print('Running:', ' '.join(map(str, args)), flush=True)
    subprocess.run(args, check=True)
    if cacheable:
        progress = state()
        progress.setdefault('commands', []).append(key)
        save_state(progress)

def check(require_ready=True):
    problems = []
    if platform.machine() != 'aarch64':
        problems.append('Requires the tested aarch64 piCorePlayer image')
    paths = [CFG, Path('/mnt/sda2/tce/onboot.lst'), HERE / 'fm4-profile.json', HERE / 'fm4-plugins.json']
    if require_ready:
        paths.append(Path('/dev/spidev0.0'))
    for path in paths:
        if not path.exists():
            problems.append('Missing prerequisite: ' + str(path))
    mounts = Path('/proc/mounts').read_text() if Path('/proc/mounts').exists() else ''
    if not any(line.split()[:2] == ['/dev/sda2', '/mnt/sda2'] for line in mounts.splitlines()):
        problems.append('Requires /dev/sda2 mounted at /mnt/sda2; no disk layout will be changed')
    elif shutil.disk_usage(Path('/mnt/sda2')).free < 2 * 1024**3:
        problems.append('At least 2 GB free on the expanded system partition is required')
    if require_ready:
        try:
            with urllib.request.urlopen('http://127.0.0.1:9000', timeout=5) as response:
                if response.status != 200:
                    problems.append('Local Lyrion server is not ready')
        except Exception:
            problems.append('Run --prepare and reboot to enable local Lyrion and SPI')
    if (STAGE.exists() or RECOVERY.exists()) and not state().get('install_started'):
        problems.append('Existing FM4 installation found: fresh-install mode will not overwrite it')
    archive = HERE / 'sable-pcp-stage.tar.gz'
    checksum = HERE / 'sable-pcp-stage.tar.gz.sha256'
    if not archive.exists() or not checksum.exists():
        problems.append('Build bundle first: archive/checksum missing')
    elif hashlib.sha256(archive.read_bytes()).hexdigest() != checksum.read_text().split()[0].lower():
        problems.append('Archive checksum mismatch')
    print('\n'.join(problems) if problems else 'Fresh-install prerequisites passed')
    return problems

def config_values(values):
    text = CFG.read_text()
    for key, value in values.items():
        if not re.fullmatch(r'[A-Z0-9_]+', key) or any(c in str(value) for c in '\n\r"'):
            raise RuntimeError('Invalid native setting')
        text, count = re.subn(r'^' + key + '=.*$', key + '="' + str(value) + '"', text, flags=re.M)
        if count != 1:
            raise RuntimeError('Native setting missing: ' + key)
    CFG.write_text(text)

def native_package(name):
    # Follow the same download/load route used by the native LMS install page.
    run('sudo', '-u', 'tc', 'pcp-load', '-w', name + '.tcz')
    run('sudo', '-u', 'tc', 'pcp-load', '-i', name + '.tcz')
    path = Path('/mnt/sda2/tce/onboot.lst')
    lines = path.read_text().splitlines()
    if name + '.tcz' not in lines:
        path.write_text('\n'.join(lines + [name + '.tcz']) + '\n')

def prepare_wifi():
    """Add tools/firmware to fresh and completed installs; do not join a network."""
    for name in ('wireless_tools', 'wpa_supplicant', 'firmware-rpi-wifi'):
        native_package(name)

def prepare():
    if os.geteuid() != 0 or check(require_ready=False):
        raise SystemExit('Run sudo --prepare on a fresh supported USB-boot installation')
    backup = Path('/home/tc/fm4-install-backup') / ('prepare-' + time.strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True, mode=0o700)
    for name, source in [('pcp.cfg', CFG), ('onboot.lst', Path('/mnt/sda2/tce/onboot.lst'))]:
        shutil.copy2(source, backup / name)
    for name in ('slimserver', 'samba4', 'pcp-shairportsync', 'pcp-bt'):
        native_package(name)
    prepare_wifi()
    boot = Path('/mnt/sda1')
    boot.mkdir(exist_ok=True)
    boot_mounts = [line.split() for line in Path('/proc/mounts').read_text().splitlines() if line.split()[1] == str(boot)]
    mounted = bool(boot_mounts)
    if mounted and boot_mounts[0][0] != '/dev/sda1':
        raise RuntimeError('Boot mount is not /dev/sda1; refusing configuration changes')
    if not mounted:
        run('mount', '-t', 'vfat', '/dev/sda1', str(boot))
    try:
        config = boot / 'config.txt'
        if not config.is_file():
            raise RuntimeError('Boot config.txt missing; preserve drive and inspect manually')
        shutil.copy2(config, backup / 'config.txt')
        text = config.read_text()
        if '# FM4 hardware' not in text:
            config.write_text(text + '\n[all]\n# FM4 hardware\ndtparam=spi=on\ndtparam=i2c_arm=on\n')
        run('sync')
    finally:
        if not mounted:
            run('umount', str(boot))
    config_values({'LMSERVER': 'yes', 'MODE': '30'})
    run('pcp', 'bu')
    progress = state()
    progress['prepared_boot'] = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    save_state(progress)
    print('Native server/receiver/sharing packages and SPI/I2C prepared. Reboot, then run --install.')

def rpc(command):
    data = json.dumps({'id': 1, 'method': 'slim.request', 'params': ['', command]}).encode()
    request = urllib.request.Request('http://127.0.0.1:9000/jsonrpc.js', data, {'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=10) as response:
        result = json.load(response)
    if result.get('error'):
        raise RuntimeError(str(result['error']))
    return result.get('result', {})

def extract(archive, target):
    with tarfile.open(archive) as source:
        for item in source.getmembers():
            destination = (target / item.name).resolve()
            if not destination.is_relative_to(target.resolve()) or item.issym() or item.islnk() or not (item.isfile() or item.isdir()):
                raise RuntimeError('Unsafe archive member: ' + item.name)
        source.extractall(target, filter='data')

def ensure_favorites():
    """Create the empty native playlist once; never replace a user's saved tracks."""
    playlist = Path('/mnt/sda2/Playlists/FM4 Favorites.m3u')
    if playlist.exists():
        print('FM4 Favorites preserved')
        return
    rpc(['playlists', 'new', 'name:FM4 Favorites'])
    if not playlist.exists():
        raise RuntimeError('Lyrion did not create FM4 Favorites; check its playlist directory')
    run('chown', 'tc:staff', str(playlist))
    print('Empty FM4 Favorites created')

def install_notices():
    """Retain notices alongside installed copies, including older bundle repairs."""
    changed = False
    for target, name in ((RECOVERY, 'DEJAVU-LICENSE.txt'),
                         (STAGE, 'DEJAVU-LICENSE.txt'),
                         (STAGE, 'THIRD-PARTY-NOTICES.md'),
                         (STAGE, 'EMPOWERED-NOTICE.md')):
        source = HERE / name
        if source.is_file() and target.is_dir():
            destination = target / name
            if not destination.exists() or destination.read_bytes() != source.read_bytes():
                shutil.copy2(source, destination)
                run('chown', 'tc:staff', str(destination))
                changed = True
    if changed:
        run('pcp', 'bu')

def enable_boot_oled():
    if not (STAGE / 'boot-oled.sh').exists():
        return False
    boot = Path('/opt/bootlocal.sh')
    text = boot.read_text()
    marker = '# FM4 early OLED status'
    if marker in text:
        return False
    if '#pCPstart------' not in text:
        raise RuntimeError('Native boot startup marker missing; boot file preserved')
    backup = Path('/mnt/sda2/bootlocal-before-fm4-oled.sh')
    if not backup.exists():
        shutil.copy2(boot, backup)
    text = text.replace('#pCPstart------', marker + '\n/bin/sh ' + str(STAGE / 'boot-oled.sh') + '\n#pCPstart------', 1)
    boot.write_text(text)
    return True


def update_shutdown_runtime():
    prepare_wifi()
    music = Path('/mnt/sda2/Music')
    if music.is_dir():
        run('chown', 'tc:staff', str(music))
        music.chmod(0o775)
    install_notices()
    changed = False
    for name in ('power.py', 'runner.py', 'wifi.py', 'update.py', 'ir-input.py', 'settings.py', 'listener.py', 'hdmi.py', 'boot_splash.py', 'boot-indicator.py', 'boot-oled.sh', 'stage-start.sh', 'source-icons.py', 'sable-config.html', 'streaming-plugins.py'):
        source = HERE / 'updates' / name
        if source.exists():
            destination = (STAGE / 'src/sable/inputs/ir.py' if name == 'ir-input.py'
                           else STAGE / 'assets/sable-config.html' if name == 'sable-config.html'
                           else STAGE / 'src/sable/pcp/source_icons.py' if name == 'source-icons.py'
                           else STAGE / name if name in ('boot-oled.sh', 'stage-start.sh', 'streaming-plugins.py')
                           else STAGE / 'src/sable/boot_indicator.py' if name == 'boot-indicator.py'
                           else STAGE / 'src/sable/settings.py' if name == 'settings.py'
                           else STAGE / 'src/sable/pcp' / name)
            if not destination.exists() or source.read_bytes() != destination.read_bytes():
                shutil.copy2(source, destination)
                run('chown', 'tc:staff', str(destination))
                changed = True
    if (STAGE / 'streaming-plugins.py').exists():
        run('python3.11', str(STAGE / 'streaming-plugins.py'))
    if enable_boot_oled():
        changed = True
    if changed:
        run('pcp', 'bu')
    print('Shutdown default is GPIO26, physical pin 37. Move the wire with power disconnected; reboot to load updated code.')

def install():
    if os.geteuid() != 0:
        raise SystemExit('Run installation with sudo; --check needs no sudo')
    if state().get('complete'):
        ensure_favorites()
        update_shutdown_runtime()
        print('Installation already completed. Existing settings preserved.')
        return
    if check():
        raise SystemExit('Resolve the prerequisites in INSTALL.md first')
    backup = Path('/home/tc/fm4-install-backup') / time.strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True, mode=0o700)
    for name, source in [('pcp.cfg', CFG), ('onboot.lst', Path('/mnt/sda2/tce/onboot.lst')), ('filetool.lst', Path('/opt/.filetool.lst'))]:
        shutil.copy2(source, backup / name)
    (backup / 'install.log').write_text('Fresh FM4 overlay install started\n')
    profile = json.loads((HERE / 'fm4-profile.json').read_text())
    progress = state()
    if progress.get('complete'):
        print('Installation already completed. Existing settings preserved.')
        return
    digest = hashlib.sha256((HERE / 'sable-pcp-stage.tar.gz').read_bytes()).hexdigest()
    if progress.get('archive') and progress['archive'] != digest:
        raise RuntimeError('Resume with the original installer bundle; archive has changed')
    progress.update(install_started=True, archive=digest)
    save_state(progress)
    packages = ['dejavu-fonts-ttf', 'pcp-ffmpeg', 'pcp-lame', 'libarchive', 'cdrom-' + platform.release()]
    for package in packages:
        run('sudo', '-u', 'tc', 'tce-load', '-wi', package)
    if not state().get('extracted'):
        extract(HERE / 'sable-pcp-stage.tar.gz', STAGE)
        shutil.copytree(HERE / 'recovery-panel', RECOVERY, dirs_exist_ok=True)
        progress = state(); progress['extracted'] = True; save_state(progress)
    run('chown', '-R', 'tc:staff', str(STAGE), str(RECOVERY))
    run('sudo', '-u', 'tc', 'python3.11', '-m', 'ensurepip', '--user')
    run('sudo', '-u', 'tc', 'python3.11', '-m', 'pip', 'install', '--only-binary=:all:', '--target', str(RECOVERY / 'vendor'), '-r', str(HERE / 'requirements-lock.txt'))
    font = next(Path('/usr/local/share/fonts').rglob('DejaVuSans.ttf'))
    shutil.copy2(font, RECOVERY / 'arial.ttf')
    font_notice = HERE / 'recovery-panel/DEJAVU-LICENSE.txt'
    if font_notice.exists():
        shutil.copy2(font_notice, RECOVERY / 'DEJAVU-LICENSE.txt')
    panel = profile['panel']
    panel.setdefault('ir', {}).setdefault('pair_id', 0x15)
    # Preserve the captured assignments instead of applying upstream defaults.
    panel['_meta'] = {'pcp_button_layout': 1}
    panel_path = STAGE / 'config/pcp-settings.json'
    if not state().get('panel_saved'):
        panel_path.write_text(json.dumps(panel, indent=2) + '\n')
        progress = state(); progress['panel_saved'] = True; save_state(progress)
    for name in ('Music', 'Playlists'):
        path = Path('/mnt/sda2') / name
        path.mkdir(exist_ok=True)
        run('chown', 'tc:staff', str(path))
        path.chmod(0o775)
    for helper in ('ensure-player-id.py', 'setup-native-cd.py'):
        run('python3.11', str(STAGE / helper))
    text = CFG.read_text()
    text, count = re.subn(r'^VISUALISER=.*$', 'VISUALISER="yes"', text, flags=re.M)
    if count != 1:
        raise RuntimeError('Native VISUALISER setting missing')
    CFG.write_text(text)
    configured_output = re.search(r'^OUTPUT="([^"]*)"', CFG.read_text(), re.M)
    output = configured_output[1] if configured_output and configured_output[1] else profile['native']['output']
    if not output or output == 'detect':
        listing = subprocess.check_output(['aplay', '-l'], text=True)
        cards = re.findall(r'^card \d+: ([A-Za-z0-9_]+).*?device (\d+):', listing, re.M)
        if not cards:
            raise RuntimeError('No audio output detected; connect a DAC and rerun')
        card, device = next((item for item in cards if item[0] == 'Headphones'), cards[0])
        output = 'hw:CARD=%s,DEV=%s' % (card, device)
    config_values({'OUTPUT': output, 'SAMBA': 'yes', 'SERVER_IP': '127.0.0.1'})
    for helper in ('setup-native-receivers.py', 'setup-receiver-levels.py'):
        run('python3.11', str(STAGE / helper))
    alsa = Path('/home/tc/.asoundrc')
    alsa.write_text(alsa.read_text().replace('slave.pcm "hw:CARD=AUDIO"', 'slave.pcm "' + output + '"'))
    guest = profile['native'].get('guest_music_share', False)
    if not guest:
        raise RuntimeError('This profile requires a separate authenticated Samba setup')
    samba = Path('/usr/local/etc/samba/smb.conf')
    samba.parent.mkdir(parents=True, exist_ok=True)
    if samba.exists():
        shutil.copy2(samba, backup / 'smb.conf')
    if samba.is_symlink():
        samba.unlink()
    samba.write_text('''[global]
workgroup = WORKGROUP
security = user
map to guest = Bad User
guest account = tc
server min protocol = SMB2
load printers = no
disable spoolss = yes
[Music]
path = /mnt/sda2/Music
browseable = yes
read only = no
guest ok = yes
guest only = yes
force user = tc
force group = staff
create mask = 0664
directory mask = 0775
''')
    run('python3.11', str(STAGE / 'install-profile-plugins.py'), str(HERE / 'fm4-plugins.json'))
    run('chown', '-R', 'tc:staff', '/mnt/sda2/tce/slimserver/Cache/InstalledPlugins')
    for key, value in [('mediadirs', ['/mnt/sda2/Music']), ('playlistdir', '/mnt/sda2/Playlists'),
                       ('language', profile['server']['language']), ('skin', profile['server']['skin']), ('wizardDone', 1),
                       ('plugin.onlinelibrary:enableLocalTracksOnly', 1),
                       ('libraryId', hashlib.md5(b'localTracksOnly').hexdigest()[:8])]:
        rpc(['pref', key, value])
    for plugin in json.loads((HERE / 'fm4-plugins.json').read_text()):
        rpc(['pref', 'plugin.state:' + plugin['name'], 'enabled'])
    ensure_favorites()
    update_shutdown_runtime()
    run('/usr/local/etc/init.d/slimserver', 'stop')
    run('/usr/local/etc/init.d/slimserver', 'start')
    entries = Path('/opt/.filetool.lst').read_text().splitlines()
    # Samba creates its state directory lazily; filetool requires it to exist.
    Path('/usr/local/var/lib/samba').mkdir(parents=True, exist_ok=True)
    for entry in ('home/tc', 'usr/local/etc/pcp', 'usr/local/etc/samba/smb.conf', 'usr/local/var/lib/samba'):
        if entry not in entries and not (entry == 'home/tc' and 'home' in entries):
            entries.append(entry)
    Path('/opt/.filetool.lst').write_text('\n'.join(entries) + '\n')
    # Startup is enabled last, after dependencies and files are in place.
    run('python3.11', str(STAGE / 'save-prototype-startup.py'))
    run('pcp', 'bu')
    progress = state(); progress['complete'] = True; save_state(progress)
    (backup / 'install.log').write_text('Fresh FM4 overlay installed; native backup completed. Reboot and validate hardware.\n')
    print('Installed. Reboot, then follow the acceptance checklist in INSTALL.md.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--setup', action='store_true')
    args = parser.parse_args()
    if sum((args.check, args.install, args.prepare, args.setup)) != 1:
        parser.error('Choose --check, --prepare or --install')
    if args.setup:
        progress = state()
        if progress.get('complete'):
            ensure_favorites()
            update_shutdown_runtime()
            print('Already installed. Reboot if you have not done so, then test the panel.')
        elif not progress.get('prepared_boot'):
            prepare()
        elif progress['prepared_boot'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip():
            print('Reboot first, then run the same --setup command again.')
        else:
            install()
        raise SystemExit(0)
    if args.prepare:
        prepare()
        raise SystemExit(0)
    if args.check:
        raise SystemExit(bool(check()))
    install()
