#!/bin/sh
# Run from the unpacked bundle on a fresh USB-boot piCorePlayer installation.
set -eu
cd "$(dirname "$0")"
# Follow piCorePlayer's active extension directory, not USB enumeration order.
if [ -L /etc/sysconfig/tcedir ]; then
    FM4_TCE=$(readlink -f /etc/sysconfig/tcedir)
else
    FM4_TCE=$(cat /etc/sysconfig/tcedir)
fi
case "$FM4_TCE" in /*) ;; *) echo 'Active extension directory unavailable'; exit 1;; esac
FM4_TCE=$(readlink -f "$FM4_TCE")
[ -f "$FM4_TCE/onboot.lst" ] || { echo 'Active extension directory missing onboot.lst'; exit 1; }
FM4_STORAGE=$FM4_TCE
while ! awk -v target="$FM4_STORAGE" '$2 == target && $1 ~ /^\/dev\// && $4 ~ /(^|,)rw(,|$)/ {found=1} END {exit !found}' /proc/mounts; do
    [ "$FM4_STORAGE" != / ] || { echo 'System storage not mounted read/write; refusing to guess'; exit 1; }
    FM4_STORAGE=$(dirname "$FM4_STORAGE")
done
export FM4_TCE FM4_STORAGE
echo "System storage: $FM4_STORAGE (extensions: $FM4_TCE)"

MODE=${1:---setup}
case "$MODE" in --check|--prepare|--install|--setup) ;; *) echo 'Use --check, --prepare, --install or --setup'; exit 1;; esac
if [ "$MODE" != '--check' ]; then
  . ./time-sync.sh
  fm4_time_check
fi
if ! command -v python3.11 >/dev/null 2>&1; then
  [ "$MODE" != '--check' ] || { echo 'Python is not installed yet. Run sudo sh install.sh --prepare'; exit 1; }
  [ "$(id -u)" = 0 ] || { echo 'Run preparation with sudo'; exit 1; }
  [ -f "$FM4_TCE/onboot.lst" ] || { echo 'Supported USB boot layout required'; exit 1; }
  [ ! -d /home/tc/sable-pcp-stage ] || { echo 'Existing FM4 install preserved'; exit 1; }
  sudo -u tc pcp-load -w python3.11.tcz
  sudo -u tc pcp-load -i python3.11.tcz
  grep -qx 'python3.11.tcz' "$FM4_TCE/onboot.lst" || echo 'python3.11.tcz' >> "$FM4_TCE/onboot.lst"
fi
python3.11 install.py "$MODE"
if [ "$MODE" != '--check' ]; then
  if [ -t 0 ]; then
    printf '\nPhase completed successfully. Reboot now? [y/N]: '
    IFS= read -r FM4_REBOOT_REPLY || FM4_REBOOT_REPLY=n
    case "$FM4_REBOOT_REPLY" in
      y|Y|yes|YES) echo 'Rebooting piCorePlayer...'; pcp rb ;;
      *) echo 'Reboot when ready with: pcp rb. After preparation, reconnect and run the same installer command.' ;;
    esac
  else
    echo 'Phase completed. Reboot when ready with: pcp rb'
  fi
fi
