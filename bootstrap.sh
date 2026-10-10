#!/bin/sh
# Download the beta over HTTPS, verify it, and run/resume native setup.
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run with sudo sh'; exit 1; }
[ "$(uname -m)" = aarch64 ] || { echo 'This beta requires 64-bit piCorePlayer'; exit 1; }
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

[ -f /usr/local/etc/pcp/pcp.cfg ] || { echo 'piCorePlayer configuration not found'; exit 1; }
# Persistent native pCP NTP configuration and bounded recovery of an invalid clock.
fm4_time_check() {
    [ "$(id -u)" = 0 ] || { echo 'Time repair requires sudo'; return 1; }
    FM4_NTP_CHANGED=no
    if [ ! -s /etc/sysconfig/ntpserver ]; then
        mkdir -p /etc/sysconfig
        printf 'pool.ntp.org\n' > /etc/sysconfig/ntpserver
        FM4_NTP_CHANGED=yes
    fi
    if ! grep -qxF 'etc/sysconfig/ntpserver' /opt/.filetool.lst; then
        printf 'etc/sysconfig/ntpserver\n' >> /opt/.filetool.lst
        FM4_NTP_CHANGED=yes
    fi
    if ! grep -qx 'NTPD="yes"' /usr/local/etc/pcp/pcp.cfg; then
        grep -q '^NTPD=' /usr/local/etc/pcp/pcp.cfg || { echo 'Native NTPD setting missing'; return 1; }
        sed -i 's/^NTPD=.*/NTPD="yes"/' /usr/local/etc/pcp/pcp.cfg
        FM4_NTP_CHANGED=yes
    fi
    FM4_YEAR=$(date +%Y)
    if [ "$FM4_YEAR" -lt 2025 ] || [ "$FM4_YEAR" -gt 2036 ]; then
        echo 'Clock is invalid; synchronising before HTTPS downloads...'
        FM4_NTP_SERVER=$(awk 'NF && $1 !~ /^#/ {print $1; exit}' /etc/sysconfig/ntpserver)
        [ -n "$FM4_NTP_SERVER" ] || { echo 'NTP server setting is empty'; return 1; }
        busybox killall ntpd 2>/dev/null || true
        FM4_NTP_RESULT=0
        busybox timeout 45 busybox ntpd -n -q -p "$FM4_NTP_SERVER" || FM4_NTP_RESULT=$?
        /usr/sbin/ntpd || { echo 'Could not restart the NTP daemon'; return 1; }
        FM4_YEAR=$(date +%Y)
        if [ "$FM4_NTP_RESULT" != 0 ] || [ "$FM4_YEAR" -lt 2025 ] || [ "$FM4_YEAR" -gt 2036 ]; then
            echo 'Time sync failed. Check Ethernet, DNS and the configured NTP server, then retry.'
            return 1
        fi
    fi
    [ "$FM4_NTP_CHANGED" = no ] || pcp bu || return 1
    echo "Clock checked: $(date). NTP will remain enabled after reboot."
}

if grep -qxF 'usr/local/var/lib/samba' /opt/.filetool.lst; then
    mkdir -p /usr/local/var/lib/samba
fi
fm4_time_check
BASE=https://raw.githubusercontent.com/graemedench/PiCore_FM_Empowered/main
DEST="$FM4_STORAGE/fm4-beta-installer"
mkdir -p "$DEST"
if [ -f "$DEST/install.sh" ] && [ ! -f "$DEST/.fm4-beta-bundle" ]; then
    echo 'Existing unrelated installer directory preserved. Inspect it before proceeding.'
    exit 1
fi
if [ -f "$DEST/.fm4-beta-bundle" ] && [ -f "$DEST/install.sh" ]; then
    echo 'Resuming the original downloaded beta; your in-progress installation is preserved.'
    # Apply installer fixes without replacing the original runtime archive.
    for SCRIPT in install.py storage.py install.sh time-sync.sh DEJAVU-LICENSE.txt THIRD-PARTY-NOTICES.md EMPOWERED-NOTICE.md; do
        wget -O "$DEST/$SCRIPT.part" "$BASE/$SCRIPT"
        mv "$DEST/$SCRIPT.part" "$DEST/$SCRIPT"
    done
    mkdir -p "$DEST/updates"
    for SCRIPT in power.py runner.py wifi.py update.py ir-input.py settings.py listener.py hdmi.py hardware_web.py storage.py system_status.py sable-status.html sable-status.cgi hardware_config.py transport.py ir.py sable-hardware.html sable-hardware.cgi display.py boot_splash.py boot-indicator.py boot-oled.sh stage-start.sh source-icons.py sable-config.html streaming-plugins.py receiver_hook.py receiver_metadata.py receiver_art.py receiver-maintenance.py; do
        wget -O "$DEST/updates/$SCRIPT.part" "$BASE/$SCRIPT"
        mv "$DEST/updates/$SCRIPT.part" "$DEST/updates/$SCRIPT"
    done
    cd "$DEST"
    exec /bin/sh ./install.sh --setup
fi
echo 'Downloading FM4 beta installer over HTTPS...'
wget -O "$DEST/bundle.part" "$BASE/fm4-beta-installer.tar.gz"
wget -O "$DEST/checksum.part" "$BASE/fm4-beta-installer.tar.gz.sha256"
HASH=$(awk 'NR==1 {print $1}' "$DEST/checksum.part")
[ "${#HASH}" = 64 ] || { echo 'Invalid download checksum'; exit 1; }
case "$HASH" in *[!0-9a-f]*) echo 'Invalid download checksum'; exit 1;; esac
printf '%s  %s\n' "$HASH" "$DEST/bundle.part" | sha256sum -c -
if [ -f "$DEST/.fm4-beta-bundle" ] && [ "$(cat "$DEST/.fm4-beta-bundle")" != "$HASH" ]; then
    echo 'A different bundle was used previously. Resume with that original version; files preserved.'
    exit 1
fi
tar -xzf "$DEST/bundle.part" -C "$DEST"
printf '%s\n' "$HASH" > "$DEST/.fm4-beta-bundle"
cd "$DEST"
exec /bin/sh ./install.sh --setup
