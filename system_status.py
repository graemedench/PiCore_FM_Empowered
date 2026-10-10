"""Read-only, on-demand Linux system status. No monitoring daemon or disk writes."""
import json
import os
from pathlib import Path
import shutil
import time

def read(path):
    return Path(path).read_text()

def counters():
    cpu = [int(x) for x in read('/proc/stat').splitlines()[0].split()[1:9]]
    disks = {}
    for line in read('/proc/diskstats').splitlines():
        fields = line.split()
        name = fields[2]
        if name.startswith(('sd', 'nvme', 'mmcblk')) and Path('/sys/block', name).exists():
            disks[name] = [int(x) for x in fields[3:]]
    return cpu, disks

def snapshot(interval=0.25):
    before, old_disks = counters()
    start = time.monotonic()
    time.sleep(interval)
    after, disks = counters()
    elapsed = time.monotonic() - start
    delta = [b-a for a,b in zip(before, after)]
    total = sum(delta)
    memory = {}
    for line in read('/proc/meminfo').splitlines():
        key, value = line.split(':', 1)
        memory[key] = int(value.split()[0]) * 1024
    drives = []
    for name, values in disks.items():
        previous = old_disks.get(name, values)
        drives.append({'name': name, 'read_bps': max(0, values[2]-previous[2])*512/elapsed,
                       'write_bps': max(0, values[6]-previous[6])*512/elapsed,
                       'busy_percent': min(100, max(0, values[9]-previous[9])/elapsed/10)})
    volumes = []
    seen = set()
    for line in read('/proc/mounts').splitlines():
        device, mount = line.split()[:2]
        if not device.startswith(('/dev/sd', '/dev/mmcblk', '/dev/nvme')) or device in seen:
            continue
        seen.add(device)
        mount = mount.replace(r'\040', ' ')
        try:
            usage = shutil.disk_usage(mount)
            volumes.append({'device': device, 'mount': mount, 'total': usage.total,
                            'used': usage.used, 'free': usage.free})
        except OSError:
            pass
    try:
        temperature = int(read('/sys/class/thermal/thermal_zone0/temp'))/1000
    except (OSError, ValueError):
        temperature = None
    return {'cpu_percent': round(100*(total-delta[3]-delta[4])/total, 1) if total else 0,
            'iowait_percent': round(100*delta[4]/total, 1) if total else 0,
            'cores': os.cpu_count(), 'load': os.getloadavg(),
            'uptime': float(read('/proc/uptime').split()[0]), 'temperature': temperature,
            'memory_total': memory['MemTotal'], 'memory_available': memory.get('MemAvailable', memory['MemFree']),
            'swap_used': memory['SwapTotal']-memory['SwapFree'], 'drives': drives, 'volumes': volumes}

def main():
    print('Content-Type: application/json\r\nCache-Control: no-store\r\n')
    if os.environ.get('REQUEST_METHOD', 'GET') != 'GET':
        print(json.dumps({'error': 'Read-only endpoint'}))
        return
    try:
        print(json.dumps(snapshot()))
    except Exception:
        print(json.dumps({'error': 'System status is temporarily unavailable'}))

if __name__ == '__main__':
    main()
