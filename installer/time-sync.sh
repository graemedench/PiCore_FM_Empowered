#!/bin/sh
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
