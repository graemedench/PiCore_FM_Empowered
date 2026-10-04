"""Install pinned public plugins; account credentials are never imported."""
import hashlib
import io
import json
from pathlib import Path
import stat
import urllib.request
import zipfile


def install(manifest, base):
    for item in manifest:
        name = item['name']
        if (base / name).exists():
            raise RuntimeError('Existing plugin must be preserved: ' + name)
        if not item['url'].startswith(('https://', 'http://')):
            raise RuntimeError('Public web plugin source required')
        data = urllib.request.urlopen(item['url'], timeout=60).read()
        if hashlib.sha1(data).hexdigest() != item['sha1']:
            raise RuntimeError('Publisher checksum mismatch: ' + name)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            # Official plugins use both enclosing-name and flat ZIP layouts.
            enclosed = all(m.filename.startswith(name + '/') or m.filename == name
                           for m in archive.infolist())
            target = base if enclosed else base / name
            for member in archive.infolist():
                path = (target / member.filename).resolve()
                if not path.is_relative_to((base / name).resolve()) or stat.S_ISLNK(member.external_attr >> 16):
                    raise RuntimeError('Unexpected plugin archive path: ' + member.filename)
            archive.extractall(target)
        print('Installed', name, item['version'])


if __name__ == '__main__':
    import sys
    install(json.loads(Path(sys.argv[1]).read_text()),
        Path('/mnt/sda2/tce/slimserver/Cache/InstalledPlugins/Plugins'))
