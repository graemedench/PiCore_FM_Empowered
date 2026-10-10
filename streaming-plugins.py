"""Install missing beta streaming plugins; preserve existing installations/accounts."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import urllib.request
import zipfile

PLUGINS = (
 ('SpotOn', 'https://github.com/stiefenm/spoton/releases/download/v3.5.8/SpotOn-v3.5.8.zip',
  'a1f73ceeb9310cb5fc3cfc72fbc7ed51dec9a10c'),
 ('Qobuz', 'https://github.com/LMS-Community/plugin-Qobuz/releases/download/3.7.2/Qobuz.zip',
  '1048fb5daaf5396c30440cd0af92a076db5a3501'))

def install(base=Path('/mnt/sda2/tce/slimserver/Cache/InstalledPlugins/Plugins')):
    added = []
    for name, url, checksum in PLUGINS:
        if (base / name).exists():
            print('Preserving existing', name)
            continue
        data = urllib.request.urlopen(url, timeout=90).read()
        if hashlib.sha1(data).hexdigest() != checksum:
            raise RuntimeError('Publisher checksum mismatch: ' + name)
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as folder, zipfile.ZipFile(io.BytesIO(data)) as archive:
            root = Path(folder)
            for member in archive.infolist():
                if not (root/member.filename).resolve().is_relative_to(root.resolve()) or stat.S_ISLNK(member.external_attr >> 16):
                    raise RuntimeError('Unsafe plugin archive')
            archive.extractall(root)
            candidate = root/'Plugins'/name if (root/'Plugins'/name).is_dir() else root/name if (root/name).is_dir() else root
            if not (candidate/'install.xml').is_file():
                raise RuntimeError('Plugin install descriptor missing')
            for helper in candidate.glob('Bin/*/*'):
                if helper.is_file(): helper.chmod(0o755)
            shutil.copytree(candidate, base/name)
        subprocess.run(['chown','-R','tc:staff',str(base/name)],check=True)
        payload=json.dumps({'id':1,'method':'slim.request','params':['',['pref','plugin.state:'+name,'enabled']]}).encode()
        request=urllib.request.Request('http://127.0.0.1:9000/jsonrpc.js',payload,{'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=15) as response:
            if json.load(response).get('error'): raise RuntimeError('Cannot enable '+name)
        added.append(name)
    if added:
        subprocess.run(['/usr/local/etc/init.d/slimserver','stop'],check=True)
        subprocess.run(['/usr/local/etc/init.d/slimserver','start'],check=True)
    print('Beta streaming plugins ready; playback requires subscriptions')

if __name__ == '__main__': install()
