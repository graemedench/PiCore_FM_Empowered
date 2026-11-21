"""Run the public installer; preserve diagnostics on the active system drive."""
from pathlib import Path
import subprocess
import hashlib
import json
import os
from .storage import storage_location

URL = 'https://raw.githubusercontent.com/graemedench/PiCore_FM_Empowered/main/bootstrap.sh'

CONFIG = Path(__file__).resolve().parents[3] / 'config'

def alpha_target():
    root, _ = storage_location()
    script = root / 'fm4-private-alpha/install.py'
    manifest = CONFIG / 'alpha-update.json'
    if not manifest.exists() or not script.is_file():
        return None
    expected = json.loads(manifest.read_text())['sha256']
    if hashlib.sha256(script.read_bytes()).hexdigest() != expected:
        raise ValueError('Alpha package check failed')
    return script

def channel():
    path = CONFIG / 'update-channel.json'
    value = json.loads(path.read_text()).get('channel') if path.exists() else 'public'
    if value not in ('public', 'alpha'):
        raise ValueError('Invalid update channel')
    return value

def set_channel(value):
    if value not in ('public', 'alpha'):
        raise ValueError('Invalid update channel')
    if value == 'alpha' and alpha_target() is None:
        raise ValueError('No local Alpha package')
    CONFIG.mkdir(parents=True, exist_ok=True)
    temporary = CONFIG / 'update-channel.json.tmp'
    with temporary.open('w') as output:
        json.dump({'channel': value}, output)
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(CONFIG / 'update-channel.json')

def apply():
    selected = channel()
    if selected == 'alpha':
        script = alpha_target()
        if script is None:
            return False, 'No local Alpha package'
        root, _ = storage_location()
        with (root / 'fm4-update.log').open('w') as log:
            try:
                subprocess.run(['python3.11', str(script)], stdin=subprocess.DEVNULL,
                               stdout=log, stderr=log, check=True, timeout=1800)
            except (OSError, subprocess.SubprocessError):
                return False, 'Alpha failed; see update log'
        return True, 'Alpha applied; reboot to load'
    script = Path('/tmp/fm4-panel-bootstrap.sh')
    fallback = Path('/tmp/fm4-update.log')
    try:
        root, tce = storage_location()
        destination = root / 'fm4-update.log'
        log = destination.open('w')
    except (OSError, RuntimeError) as error:
        fallback.write_text('Update did not start: ' + str(error) + '\n')
        return False, 'See ' + str(fallback)
    with log:
        log.write('FM4 Settings update started\nSystem storage: ' + str(root) + '\nExtension directory: ' + str(tce) + '\n')
        log.flush()
        try:
            subprocess.run(['wget', '-O', str(script), URL], stdout=log, stderr=log,
                           check=True, timeout=90)
            subprocess.run(['/bin/sh', str(script)], stdin=subprocess.DEVNULL,
                           stdout=log, stderr=log, check=True, timeout=1800)
        except (OSError, subprocess.SubprocessError) as error:
            log.write('Update failed: ' + str(error) + '\n')
            return False, 'See ' + str(destination)
    return True, 'Patches applied; reboot to load'
