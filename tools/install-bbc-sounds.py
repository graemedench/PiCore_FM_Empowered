"""Install the pinned BBC Sounds plugin from the official Lyrion repository release.

Run on piCorePlayer, then enable plugin.state:BBCSounds through Lyrion's pref API,
restart Lyrion with its native stop/start commands, and sign in through its UI.
"""
import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

URL = 'https://github.com/expectingtofly/LMS_BBC_Sounds_Plugin/releases/download/2.54.8/BBCSoundsPlugin_2_54_8.zip'
SHA1 = 'f05b152747e76718a3d80a11e8f75bc137e39e38'
base = Path('/mnt/sda2/tce/slimserver/Cache/InstalledPlugins/Plugins')
if (base / 'BBCSounds').exists():
    raise SystemExit('BBC Sounds already exists; preserve the installed version')
data = urllib.request.urlopen(URL, timeout=30).read()
if hashlib.sha1(data).hexdigest() != SHA1:
    raise SystemExit('Official repository checksum mismatch')
archive = zipfile.ZipFile(io.BytesIO(data))
if not all((base / name).resolve().is_relative_to(base.resolve())
           for name in archive.namelist()):
    raise SystemExit('Unexpected archive path')
archive.extractall(base)
print('Installed verified BBC Sounds 2.54.8; enable, restart and sign in through Lyrion')
