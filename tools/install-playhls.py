"""Install pinned native PlayHLS support for direct radio streams."""
import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

URL = 'https://bpa-code.github.io/bpaplugins/PlayHLS-v212.ZIP'
SHA1 = '3da446c52d2eecbc1d70834bfa822b6bf761d616'
base = Path('/mnt/sda2/tce/slimserver/Cache/InstalledPlugins/Plugins')
if (base / 'PlayHLS').exists():
    raise SystemExit('PlayHLS already installed; preserve existing version')
data = urllib.request.urlopen(URL, timeout=30).read()
if hashlib.sha1(data).hexdigest() != SHA1:
    raise SystemExit('Publisher checksum mismatch')
archive = zipfile.ZipFile(io.BytesIO(data))
if not all((base / name).resolve().is_relative_to(base.resolve())
           for name in archive.namelist()):
    raise SystemExit('Unexpected archive path')
archive.extractall(base)
print('Installed PlayHLS 2.12. Enable plugin.state:PlayHLS then restart Lyrion.')
