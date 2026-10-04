"""Exercise installer phases against an isolated filesystem, never a real Pi."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
from unittest.mock import patch

project = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fm4_installer', project / 'installer/install.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

with TemporaryDirectory() as folder:
    root = Path(folder)
    def fake_path(path):
        text = str(path)
        return root / text.lstrip('/') if text.startswith('/') else Path(path)
    m.CFG = fake_path('/usr/local/etc/pcp/pcp.cfg')
    m.STAGE = fake_path('/home/tc/sable-pcp-stage')
    m.RECOVERY = fake_path('/home/tc/quadify-pcp')
    m.HERE = root / 'bundle'
    m.HERE.mkdir()
    for path, text in {
        '/usr/local/etc/pcp/pcp.cfg': '\n'.join(k+'=""' for k in ('LMSERVER','MODE','OUTPUT','SAMBA','SERVER_IP','NAME','VISUALISER'))+'\n',
        '/mnt/sda2/tce/onboot.lst': 'pcp.tcz\n',
        '/proc/mounts': '/dev/sda2 /mnt/sda2 ext4 rw 0 0\n',
        '/mnt/sda1/config.txt': '[all]\n',
        '/dev/spidev0.0': '',
        '/opt/.filetool.lst': 'home/tc\n',
        '/usr/local/share/fonts/dejavu/DejaVuSans.ttf': 'fixture',
    }.items():
        target = fake_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    profile = json.loads((project / 'fm4-profile.json').read_text())
    (m.HERE / 'fm4-profile.json').write_text(json.dumps(profile))
    (m.HERE / 'fm4-plugins.json').write_text((project / 'fm4-plugins.json').read_text())
    (m.HERE / 'requirements-lock.txt').write_text('fixture')
    (m.HERE / 'recovery-panel').mkdir()
    (m.HERE / 'recovery-panel/panel.py').write_text('fixture')
    archive = m.HERE / 'sable-pcp-stage.tar.gz'
    with tarfile.open(archive, 'w:gz') as target:
        item = tarfile.TarInfo('config')
        item.type = tarfile.DIRTYPE
        target.addfile(item)
    (m.HERE / 'sable-pcp-stage.tar.gz.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest())
    calls, preferences = [], []
    def fake_run(*args):
        calls.append(args)
        if any(str(a).endswith('setup-receiver-levels.py') for a in args):
            target = fake_path('/home/tc/.asoundrc')
            target.write_text('slave.pcm "hw:CARD=AUDIO"\n')
    class Response(io.BytesIO):
        status = 200
    with patch.object(m, 'Path', side_effect=fake_path), patch.object(m.platform, 'machine', return_value='aarch64'), \
         patch.object(m.os, 'geteuid', return_value=0, create=True), patch.object(m.os, 'chown', create=True), patch.object(m, 'run', side_effect=fake_run), \
         patch.object(m.urllib.request, 'urlopen', return_value=Response(b'')), patch.object(m, 'rpc', side_effect=lambda command: preferences.append(command)):
        assert not m.check(require_ready=False)
        m.prepare()
        assert 'dtparam=spi=on' in fake_path('/mnt/sda1/config.txt').read_text()
        assert 'LMSERVER="yes"' in m.CFG.read_text()
        assert any('slimserver.tcz' in args for args in calls)
        m.install()
        saved = json.loads((m.STAGE / 'config/pcp-settings.json').read_text())
        assert saved['buttons'] == profile['panel']['buttons']
        assert saved['_meta']['pcp_button_layout'] == 1
        assert 'SERVER_IP="127.0.0.1"' in m.CFG.read_text()
        assert 'Headphones' in fake_path('/home/tc/.asoundrc').read_text()
        assert 'guest only = yes' in fake_path('/usr/local/etc/samba/smb.conf').read_text()
        assert ['pref', 'mediadirs', ['/mnt/sda2/Music']] in preferences
        assert not any('wifi' in str(args).lower() or 'wpa' in str(args).lower() for args in calls)
        assert m.check(require_ready=False), 'Existing installation must be refused'
print('PASS: fresh prepare/install, settings restore, native packages, local server, sharing and existing-install guard')
