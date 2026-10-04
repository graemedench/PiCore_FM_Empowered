# Backups, updates and troubleshooting

## What is saved where

| Location | Purpose |
| --- | --- |
| `/home/tc/sable-pcp-stage` | Assembled Sable + Empowered patch + piCorePlayer adapter |
| `/home/tc/sable-pcp-stage/config/pcp-settings.json` | Panel settings, button assignments and IR pairing |
| `/home/tc/quadify-pcp` | Recovery panel and Python vendor dependencies |
| `/usr/local/etc/pcp/pcp.cfg` | Private native configuration; do not publish |
| `/mnt/sda2/tce/mydata.tgz` | Native piCorePlayer persistence backup |
| `/mnt/sda2/Music` and `/mnt/sda2/Playlists` | Music and saved playlists, backed up separately |
| `/home/tc/fm4-install-backup` | Fresh install's local native-setting snapshots |
| `/tmp/sable-pcp-stage.log` | Current panel log; temporary across reboot |

piCorePlayer runs many files in RAM. `pcp bu` saves configured persistent files
for the next boot. A successful save is different from a complete backup of
your music drive. Copy music, playlists and any private settings you need to
your own protected backup location separately.

Graeme's working project mirror is
`C:\Users\Graeme\OneDrive\3D Prints Etc\Quadify FM4\piCorePlayer_Empowered`.
The source repository contains public code, documentation, models and build
instructions. It excludes account passwords, private server backups, library
files and installed dependency folders. The local installer archive is a
build product; build scripts reproduce it from pinned sources over HTTPS.

## Updates

The supplied installer is **fresh-install-only** and refuses existing FM4
directories. Do not use it as an update command on the working unit. Build and
review a new archive, back up the current installation and apply only intended
changed files. Preserve `config/pcp-settings.json` and native configuration.
Do not restart the panel or modify CD tools while a rip is running. Check for
`Music/CD Rips/*/.track-*` and the on-screen rip state before deployment.

After a controlled update, check the panel log, test the changed feature and
save with `pcp bu`. Record the change, checks and remaining limitations in
[HANDOVER.md](../HANDOVER.md) and [CHANGELOG.md](../CHANGELOG.md). Source transfers
and repository sync use HTTPS. A full clean-drive installation test is still
required before calling the installer a stable release.

## Common checks

| Symptom | Check |
| --- | --- |
| Web player unreachable | Use current IP from Network; server uses port 9000, native pCP page uses port 80 |
| Copied music missing | Confirm Lyrion music path, then Refresh now and wait for scanning |
| Dark display | Check idle settings and panel log; confirm SPI, OLED power and wiring |
| Encoder/buttons unresponsive | Check GPIO wiring, I2C address 0x20 and exclusive panel process |
| Remote has no response | Use GPIO4, check battery/line of sight and pair identity; old GPIO27 notes do not apply here |
| Receiver visible but silent | Check actual audio output, native service state and receiver handover |
| VU/spectrum static | Enable native visualizer; check PCM/receiver feed and correct player identity |
| CD not listed | Confirm drive detection, CD kernel extension, power and USB connection |
| Rip stopped | Keep completed tracks; inspect error/progress, available space and drive connection before retrying |
| Changes vanished after reboot | Confirm native backup completed and persistent file list includes the changed files |
| Boot USB disturbed | Stop work and restore a stable boot/storage connection before continuing |

Use [INSTALL.md](../INSTALL.md) for fresh-drive acceptance/recovery and
[HARDWARE.md](../HARDWARE.md) for pin assignments. The original working drive
should remain intact until its replacement passes the complete checklist.
