#!/bin/sh
# Download the beta over HTTPS, verify it, and run/resume native setup.
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run with sudo sh'; exit 1; }
[ "$(uname -m)" = aarch64 ] || { echo 'This beta requires 64-bit piCorePlayer'; exit 1; }
grep -q '^/dev/sda2 /mnt/sda2 ' /proc/mounts || { echo 'USB piCorePlayer layout required'; exit 1; }
[ -f /usr/local/etc/pcp/pcp.cfg ] || { echo 'piCorePlayer configuration not found'; exit 1; }
BASE=https://raw.githubusercontent.com/graemedench/PiCore_FM_Empowered/main
DEST=/mnt/sda2/fm4-beta-installer
mkdir -p "$DEST"
if [ -f "$DEST/install.sh" ] && [ ! -f "$DEST/.fm4-beta-bundle" ]; then
    echo 'Existing unrelated installer directory preserved. Inspect it before proceeding.'
    exit 1
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
