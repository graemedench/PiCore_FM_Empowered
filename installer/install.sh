#!/bin/sh
# Run from the unpacked bundle on a fresh USB-boot piCorePlayer installation.
set -eu
cd "$(dirname "$0")"
MODE=${1:---setup}
case "$MODE" in --check|--prepare|--install|--setup) ;; *) echo 'Use --check, --prepare, --install or --setup'; exit 1;; esac
if [ "$MODE" != '--check' ]; then
  . ./time-sync.sh
  fm4_time_check
fi
if ! command -v python3.11 >/dev/null 2>&1; then
  [ "$MODE" != '--check' ] || { echo 'Python is not installed yet. Run sudo sh install.sh --prepare'; exit 1; }
  [ "$(id -u)" = 0 ] || { echo 'Run preparation with sudo'; exit 1; }
  [ -f /mnt/sda2/tce/onboot.lst ] || { echo 'Supported USB boot layout required'; exit 1; }
  [ ! -d /home/tc/sable-pcp-stage ] || { echo 'Existing FM4 install preserved'; exit 1; }
  sudo -u tc pcp-load -w python3.11.tcz
  sudo -u tc pcp-load -i python3.11.tcz
  grep -qx 'python3.11.tcz' /mnt/sda2/tce/onboot.lst || echo 'python3.11.tcz' >> /mnt/sda2/tce/onboot.lst
fi
exec python3.11 install.py "$MODE"
