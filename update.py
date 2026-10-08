"""Run the public installer noninteractively; preserve its diagnostic log."""
from pathlib import Path
import subprocess

URL = 'https://raw.githubusercontent.com/graemedench/PiCore_FM_Empowered/main/bootstrap.sh'
LOG = Path('/mnt/sda2/fm4-update.log')

def apply():
    script = Path('/tmp/fm4-panel-bootstrap.sh')
    with LOG.open('w') as log:
        log.write('FM4 Settings update started\n'); log.flush()
        try:
            subprocess.run(['wget', '-O', str(script), URL], stdout=log, stderr=log,
                           check=True, timeout=90)
            subprocess.run(['/bin/sh', str(script)], stdin=subprocess.DEVNULL,
                           stdout=log, stderr=log, check=True, timeout=1800)
        except (OSError, subprocess.SubprocessError):
            return False, 'See /mnt/sda2/fm4-update.log'
    return True, 'Patches applied; reboot to load'
