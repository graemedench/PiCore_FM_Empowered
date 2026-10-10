"""Discover piCorePlayer storage from its active extension directory."""
from pathlib import Path

def storage_location(config=Path('/etc/sysconfig/tcedir'), mounts=Path('/proc/mounts')):
    if config.is_symlink():
        tce = config.resolve(strict=True)
    else:
        value = config.read_text().strip()
        if not value or not Path(value).is_absolute() or '\n' in value:
            raise RuntimeError('Active piCorePlayer extension directory is invalid')
        tce = Path(value).resolve(strict=True)
    if not tce.is_dir() or not (tce / 'onboot.lst').is_file():
        raise RuntimeError('Active extension directory or onboot.lst is missing')
    candidates = []
    for line in mounts.read_text().splitlines():
        fields = line.split()
        if len(fields) < 4:
            continue
        device, target, _, options = fields[:4]
        target = Path(target.replace(r'\040', ' ').replace(r'\134', chr(92)))
        if device.startswith('/dev/') and 'rw' in options.split(',') and (target == tce or target in tce.parents):
            candidates.append(target)
    if not candidates:
        raise RuntimeError('Active piCorePlayer storage is not mounted read/write; refusing to guess')
    return max(candidates, key=lambda p: len(p.parts)), tce
