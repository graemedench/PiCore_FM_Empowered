"""Run the public installer; preserve diagnostics on the active system drive."""
from pathlib import Path
import subprocess
from .storage import storage_location

URL = 'https://raw.githubusercontent.com/graemedench/PiCore_FM_Empowered/main/bootstrap.sh'

def apply():
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
