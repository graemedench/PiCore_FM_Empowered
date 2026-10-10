"""Alpha, same-origin CGI editor for Sable hardware wiring."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit

from .hardware_config import PATH, DEFAULTS, load, merge

STAGE = PATH.parent.parent
BACKUP = PATH.with_name('hardware.previous.json')
STATUS = Path('/tmp/sable-hardware-status.json')
TOKEN = Path('/tmp/sable-hardware-token')
LOCK = Path('/tmp/sable-hardware-web.lock')
PID = Path('/tmp/sable-pcp-stage.pid')
PYTHON = '/usr/local/bin/python3.11'


def atomic(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(name, mode)
        if path.exists():
            stat = path.stat()
            os.chown(name, stat.st_uid, stat.st_gid)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def encoded(config):
    return (json.dumps(config, indent=2) + '\n').encode()


def revision():
    return hashlib.sha256(PATH.read_bytes() if PATH.exists() else b'').hexdigest()


def token():
    # Called under LOCK, shared by independent CGI requests.
    if not TOKEN.exists():
        atomic(TOKEN, secrets.token_urlsafe(32).encode(), 0o600)
    return TOKEN.read_text()


def status(phase, message):
    atomic(STATUS, encoded({'phase': phase, 'message': message}))


def current_status():
    try:
        return json.loads(STATUS.read_text())
    except (FileNotFoundError, ValueError):
        return {'phase': 'idle', 'message': ''}


def state():
    error = ''
    try:
        config = load(PATH)
    except (ValueError, TypeError, KeyError):
        config, error = DEFAULTS, 'Saved mapping is invalid. Review it or restore the previous mapping.'
    return {'config': config, 'error': error, 'revision': revision(), 'token': token(),
            'has_backup': BACKUP.exists(), 'status': current_status()}


def authenticate(env, body, expected):
    if env.get('CONTENT_TYPE', '').split(';')[0] != 'application/json':
        raise ValueError('Use a JSON request')
    origin = urlsplit(env.get('HTTP_ORIGIN', ''))
    if origin.scheme not in ('http', 'https') or origin.netloc != env.get('HTTP_HOST'):
        raise ValueError('Open Hardware Setup on this device before making changes')
    supplied = body.get('token')
    if not isinstance(supplied, str) or not secrets.compare_digest(supplied, expected):
        raise ValueError('Page expired. Reload Hardware Setup')


def stop_panel():
    if not PID.exists():
        return
    pid = int(PID.read_text().strip())
    proc = Path('/proc') / str(pid)
    if not proc.exists():
        return
    cmd = (proc / 'cmdline').read_bytes().split(b'\0')
    if b'sable.pcp.runner' not in cmd:
        raise RuntimeError('Panel PID does not identify Sable; refusing to stop it')
    identity = (proc / 'stat').read_text().split()[21]
    def alive():
        try:
            fields = (proc / 'stat').read_text().split()
            return fields[21] == identity and fields[2] != 'Z'
        except FileNotFoundError:
            return False
    os.kill(pid, signal.SIGTERM)
    for _ in range(100):
        if not alive():
            return
        time.sleep(.1)
    # Network worker threads can keep Python alive after GPIO cleanup. Only
    # terminate the same verified panel process, never another reused PID.
    if alive():
        os.kill(pid, signal.SIGKILL)
    for _ in range(30):
        if not alive():
            return
        time.sleep(.1)
    raise RuntimeError('Panel did not release hardware; no second panel was started')


def start_panel():
    env = dict(os.environ, PYTHONPATH=str(STAGE / 'src') + ':/home/tc/quadify-pcp:/home/tc/quadify-pcp/vendor')
    with Path('/tmp/sable-pcp-stage.log').open('w') as log:
        process = subprocess.Popen([PYTHON, '-u', '-m', 'sable.pcp.runner'], cwd=STAGE,
            env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    PID.write_text(str(process.pid))
    time.sleep(4)
    if process.poll() is not None:
        raise RuntimeError('Panel failed to start with the proposed wiring')


def backup_system():
    subprocess.run(['pcp', 'bu'], check=True, timeout=180,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def apply(config, old):
    stopped = False
    try:
        status('working', 'Saving mapping and backing up piCorePlayer…')
        atomic(PATH, encoded(config))
        backup_system()
        status('working', 'Restarting the panel…')
        stop_panel()
        stopped = True
        start_panel()
        status('done', 'Mapping saved. Check the OLED and controls. Restore previous mapping if needed.')
    except Exception as exc:
        atomic(PATH, old)
        recovery = ''
        try:
            backup_system()
            if stopped:
                stop_panel()
                start_panel()
            recovery = ' Previous mapping restored.'
        except Exception:
            recovery = ' Previous file restored; panel recovery needs checking over SSH.'
        status('error', str(exc) + recovery)


def worker():
    with LOCK.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            task = json.loads(Path('/tmp/sable-hardware-task.json').read_text())
            apply(merge(task['config']), bytes.fromhex(task['old']))
        except Exception as exc:
            status('error', 'Hardware setup failed: ' + str(exc))


def request(env, body):
    authenticate(env, body, token())
    action = body.get('action')
    if action not in ('validate', 'save', 'restore', 'preview_restore'):
        raise ValueError('Unknown action')
    if body.get('revision') != revision():
        raise ValueError('Mapping changed since this page loaded. Reload before applying')
    candidate = (merge(json.loads(BACKUP.read_text())) if action in ('restore', 'preview_restore')
                 else merge(body.get('config')))
    if action in ('validate', 'preview_restore'):
        return {'config': candidate, 'valid': True}
    if body.get('acknowledge_alpha') is not True:
        raise ValueError('Acknowledge Alpha — Not Supported — Use at own risk before applying')
    old = PATH.read_bytes() if PATH.exists() else encoded(load(PATH))
    # Keep a known-valid recovery file; never replace it with a broken mapping.
    try:
        merge(json.loads(old))
        atomic(BACKUP, old)
    except (ValueError, TypeError):
        old = (encoded(merge(json.loads(BACKUP.read_text()))) if BACKUP.exists()
               else encoded(DEFAULTS))
    atomic(Path('/tmp/sable-hardware-task.json'), encoded({'config': candidate, 'old': old.hex()}), 0o600)
    status('queued', 'Applying mapping… Keep this page open.')
    with Path('/tmp/sable-hardware-web.log').open('a') as log:
        try:
            subprocess.Popen([PYTHON, '-m', 'sable.pcp.hardware_web', '--worker'], cwd=STAGE,
                env=dict(os.environ, PYTHONPATH=str(STAGE / 'src')), stdin=subprocess.DEVNULL,
                stdout=log, stderr=log, start_new_session=True)
        except Exception:
            status('error', 'Could not start the hardware setup worker. No mapping was changed.')
            raise
    return {'accepted': True}


def main():
    if '--worker' in sys.argv:
        worker()
        return
    code = '200 OK'
    try:
        with LOCK.open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                result = {'status': current_status(), 'busy': True}
            else:
                if os.environ.get('REQUEST_METHOD') == 'GET':
                    result = state()
                elif os.environ.get('REQUEST_METHOD') == 'POST':
                    size = int(os.environ.get('CONTENT_LENGTH', '0'))
                    if not 0 < size <= 16384:
                        raise ValueError('Invalid request size')
                    body = json.loads(sys.stdin.read(size))
                    if not isinstance(body, dict):
                        raise ValueError('Request must be an object')
                    if current_status()['phase'] == 'queued':
                        raise ValueError('A mapping update is already queued')
                    result = request(os.environ, body)
                else:
                    raise ValueError('Use GET or POST')
    except (ValueError, TypeError, KeyError, FileNotFoundError) as exc:
        code, result = '400 Bad Request', {'error': str(exc)}
    except Exception:
        code, result = '500 Internal Server Error', {'error': 'Hardware setup failed. Check the device over SSH.'}
    print('Status: ' + code)
    print('Content-Type: application/json; charset=utf-8')
    print('Cache-Control: no-store\n')
    print(json.dumps(result))


def install_web():
    """Recreate web assets from the persistent stage on panel startup."""
    for source, target in [('sable-hardware.html', '/var/www/sable-hardware.html'),
                           ('sable-hardware.cgi', '/var/www/cgi-bin/sable-hardware.cgi')]:
        destination = Path(target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((STAGE / 'assets' / source).read_bytes())
        if source.endswith('.cgi'):
            destination.chmod(0o755)
    filelist = Path('/opt/.filetool.lst')
    if filelist.exists():
        entries = filelist.read_text().splitlines()
        for entry in ('var/www/sable-hardware.html', 'var/www/cgi-bin/sable-hardware.cgi'):
            if entry not in entries:
                with filelist.open('a') as out:
                    out.write('\n' + entry + '\n')
                entries.append(entry)


if __name__ == '__main__':
    main()
