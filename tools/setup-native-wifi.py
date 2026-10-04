"""Keep the installed native Wi-Fi firmware/tools in the correct boot order."""
import platform
from pathlib import Path

packages = ['firmware-rpi-wifi.tcz', 'wireless-' + platform.release() + '.tcz',
            'wireless_tools.tcz', 'wpa_supplicant.tcz']
base = Path('/mnt/sda2/tce')
for package in packages:
    if not (base / 'optional' / package).exists():
        raise SystemExit('Install the native package first: ' + package)
onboot = base / 'onboot.lst'
entries = [entry for entry in onboot.read_text().splitlines() if entry not in packages]
onboot.write_text('\n'.join(entries + packages) + '\n')
files = Path('/opt/.filetool.lst')
entries = files.read_text().splitlines()
if 'usr/local/etc/pcp/wpa_supplicant.conf' not in entries:
    # The file is created by join, so only add it once present.
    if Path('/usr/local/etc/pcp/wpa_supplicant.conf').exists():
        entries.append('usr/local/etc/pcp/wpa_supplicant.conf')
files.write_text('\n'.join(entries) + '\n')
print('Native Wi-Fi boot dependencies saved; Ethernet unchanged')
