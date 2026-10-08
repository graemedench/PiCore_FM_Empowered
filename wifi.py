"""Native piCorePlayer Wi-Fi; credentials stay only on the player."""
import hashlib
import re
import shutil
import subprocess
import time
from pathlib import Path

CONFIG = Path('/usr/local/etc/pcp/wpa_supplicant.conf')


def run(args, timeout=12):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def scan():
    run(['ifconfig', 'wlan0', 'up'])
    result = run(['/usr/local/sbin/iwlist', 'wlan0', 'scan'])
    if result.returncode:
        raise RuntimeError('Scan failed')
    return list(dict.fromkeys(re.findall(r'ESSID:"([^"\n]+)"', result.stdout)))


def cli(*args):
    result = run(['/usr/local/sbin/wpa_cli', '-i', 'wlan0', *args], timeout=4)
    if result.returncode or 'FAIL' in result.stdout:
        raise RuntimeError('Wi-Fi command failed')
    return result.stdout.strip()


def status():
    try:
        return dict(line.split('=', 1) for line in cli('status').splitlines() if '=' in line)
    except Exception:
        return {}


def connect(ssid, password):
    if not 1 <= len(ssid.encode()) <= 32:
        return False, 'Invalid network name'
    if not 8 <= len(password) <= 63:
        return False, 'Password: 8-63 characters'
    if CONFIG.exists():
        backup = CONFIG.with_suffix('.conf.before-fm4')
        if not backup.exists():
            shutil.copy2(CONFIG, backup)
        text = CONFIG.read_text()
        text = re.sub(r'^update_config=.*$', 'update_config=1', text, flags=re.M)
        if 'update_config=' not in text:
            text += '\nupdate_config=1\n'
    else:
        text = '# Maintained by piCorePlayer\nctrl_interface=/var/run/wpa_supplicant\ncountry=GB\nupdate_config=1\n'
    CONFIG.write_text(text)
    CONFIG.chmod(0o600)
    try:
        run(['/usr/local/etc/init.d/wifi', 'wlan0', 'start'], timeout=15)
    except subprocess.TimeoutExpired:
        pass  # DHCP may still be waiting in the background for association.
    network = None
    try:
        network = cli('add_network').splitlines()[-1]
        if not network.isdigit():
            raise RuntimeError('No network id')
        cli('set_network', network, 'ssid', ssid.encode().hex())
        key = hashlib.pbkdf2_hmac('sha1', password.encode(), ssid.encode(), 4096, 32).hex()
        cli('set_network', network, 'psk', key)
        cli('set_network', network, 'key_mgmt', 'WPA-PSK')
        cli('set_network', network, 'priority', '1000')
        cli('select_network', network)
        for _ in range(60):
            info = status()
            if info.get('wpa_state') == 'COMPLETED' and info.get('ip_address'):
                cli('enable_network', 'all')
                cli('save_config')
                saved = CONFIG.read_text()
                if not saved.startswith('# Maintained by piCorePlayer'):
                    CONFIG.write_text('# Maintained by piCorePlayer\n' + saved)
                CONFIG.chmod(0o600)
                cfg = Path('/usr/local/etc/pcp/pcp.cfg')
                cfg.write_text(re.sub(r'^WIFI=.*$', 'WIFI="on"', cfg.read_text(), flags=re.M))
                files = Path('/opt/.filetool.lst')
                entries = files.read_text().splitlines()
                if 'usr/local/etc/pcp/wpa_supplicant.conf' not in entries:
                    entries.append('usr/local/etc/pcp/wpa_supplicant.conf')
                    files.write_text('\n'.join(entries) + '\n')
                return True, info['ip_address']
            time.sleep(1)
    except Exception:
        pass
    if network is not None:
        try:
            cli('remove_network', network)
            cli('enable_network', 'all')
        except Exception:
            pass
    return False, 'Could not join; check password'
