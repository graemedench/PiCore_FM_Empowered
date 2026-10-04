"""Native piCorePlayer output routing, shared by music and receivers."""
from pathlib import Path
import re
import subprocess

CONFIG = Path('/usr/local/etc/pcp/pcp.cfg')


def devices():
    result = subprocess.run(['aplay', '-l'], capture_output=True, text=True, timeout=5, check=True)
    return [dict(id='hw:CARD=%s,DEV=%s' % (card, device), name=name.strip())
            for card, name, device in re.findall(r'^card \d+: ([A-Za-z0-9_]+) \[([^\]]+)\], device (\d+):', result.stdout, re.M)]


def current():
    match = re.search(r'^OUTPUT="([^"]*)"', CONFIG.read_text(), re.M)
    return match[1] if match else ''


def selected(outputs, value):
    return next((d for d in outputs if d['id'] == value or d['id'].removesuffix(',DEV=0') == value), None)


def change(value):
    if not selected(devices(), value):
        raise ValueError('Output disconnected - reopen Audio Output')
    config = CONFIG.read_text()
    alsa = Path('/home/tc/.asoundrc')
    old_alsa = alsa.read_text()
    if not re.search(r'pcm\.fm4_receiver\s*\{', old_alsa):
        raise ValueError('Receiver routing unavailable')
    updated = re.sub(r'(pcm\.fm4_receiver\s*\{.*?slave\.pcm\s*)"[^"]*"',
                     lambda m: m[1] + '"' + value + '"', old_alsa, count=1, flags=re.S)
    new_config = re.sub(r'^OUTPUT=.*$', 'OUTPUT="' + value + '"', config, flags=re.M)
    services = ['/usr/local/etc/init.d/' + name for name in ('squeezelite', 'shairport-sync')]
    try:
        for service in services:
            subprocess.run([service, 'stop'], capture_output=True, timeout=15, check=True)
        CONFIG.write_text(new_config)
        alsa.write_text(updated)
        import time
        time.sleep(1)
        for service in services:
            subprocess.run([service, 'start'], capture_output=True, timeout=20, check=True)
    except Exception:
        CONFIG.write_text(config)
        alsa.write_text(old_alsa)
        for service in services:
            subprocess.run([service, 'restart'], capture_output=True, timeout=25)
        raise
    backup = subprocess.run(['pcp', 'bu'], capture_output=True, text=True, timeout=90)
    if backup.returncode or 'Backup successful' not in backup.stdout:
        raise RuntimeError('Output changed, but backup failed')
