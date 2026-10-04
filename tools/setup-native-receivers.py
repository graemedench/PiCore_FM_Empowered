"""Configure installed native receiver packages; no passwords are exported."""
import re
import shutil
from pathlib import Path

base = Path('/home/tc/sable-pcp-stage')
cfg = Path('/usr/local/etc/pcp/pcp.cfg')
backup = base / 'pcp.cfg.before-receivers'
if not backup.exists():
    shutil.copy2(cfg, backup)
text = cfg.read_text()
for key, value in dict(SHAIRPORT='ap2', SHAIRPORT_OUT='hw:CARD=AUDIO',
                       BT_OUT_DEVICE='hw:CARD=AUDIO', RPIBLUETOOTH='on').items():
    text, count = re.subn(r'^' + key + '=.*$', key + '="' + value + '"', text, flags=re.M)
    if count != 1:
        raise RuntimeError('Missing native setting: ' + key)
cfg.write_text(text)
airplay = Path('/usr/local/etc/pcp/shairport-sync-ap2.conf')
if airplay.is_symlink():
    original = airplay.read_text()
    airplay.unlink()
    airplay.write_text(original)
shutil.copy2(airplay, base / 'shairport-sync-ap2.conf.before-receivers')
airplay.write_text('''general = { name = "FM4-Reborn AirPlay"; };
alsa = { disable_standby_mode = "auto"; };
metadata = { enabled = "yes"; include_cover_art = "yes";
  pipe_name = "/tmp/shairport-sync-metadata"; };
sessioncontrol = {
  run_this_before_play_begins = "/bin/sh /home/tc/sable-pcp-stage/receiver-hook.sh start";
  run_this_after_play_ends = "/bin/sh /home/tc/sable-pcp-stage/receiver-hook.sh stop";
  wait_for_completion = "yes";
};
diagnostics = { log_output_to = "/var/log/pcp_shairport-sync.log";
  statistics = "no"; log_verbosity = 1; };
''')
Path('/usr/local/etc/pcp/shairportextra.cfg').write_text(
    '-c /usr/local/etc/pcp/shairport-sync-ap2.conf\n')
onboot = Path('/mnt/sda2/tce/onboot.lst')
packages = onboot.read_text().splitlines()
for package in ('pcp-shairportsync.tcz', 'pcp-bt.tcz'):
    if package not in packages:
        packages.append(package)
onboot.write_text('\n'.join(packages) + '\n')
files = Path('/opt/.filetool.lst')
entries = files.read_text().splitlines()
for entry in ('var/lib/bluetooth', 'usr/local/var/lib/bluealsa',
              'usr/local/etc/bluetooth', 'usr/local/etc/pcp/shairport-sync-ap2.conf'):
    if entry not in entries:
        entries.append(entry)
files.write_text('\n'.join(entries) + '\n')
for directory in ('/var/lib/bluetooth', '/usr/local/var/lib/bluealsa'):
    Path(directory).mkdir(parents=True, exist_ok=True)
print('Native AirPlay 2 and Bluetooth settings configured; run pcp bu')
