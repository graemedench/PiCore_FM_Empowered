# piCorePlayer Empowered — living handover

Updated: 3 October 2026 (Europe/London).

## Purpose and user instructions

Port the modified Quadify/Sable FM4 interface to piCorePlayer with the same look
and better responsiveness. Keep playback and the existing test panel recoverable.
Save a repeatable build for migration to a larger SSD. Keep this folder copied to
`C:\Users\Graeme\OneDrive\3D Prints Etc\Quadify FM4\piCorePlayer_Empowered` after changes.
Read this file before continuing and update it after each meaningful milestone.
Do not record passwords, tokens or private credentials in the backup.
Use HTTPS by default for all Git transfers and synchronization. Project repository:
https://github.com/graemedench/PiCore_FM_Empowered.

## Live test unit

- Raspberry Pi 4 Model B Rev 1.5, hostname `FM4-Reborn` / `fm4-reborn.local`.
- Ethernet IP `192.168.1.18`; SSH account `tc`. Credentials supplied separately.
- piCorePlayer 11.1.0, piCore 16.1, kernel 6.12.67-pcpCore-v8, aarch64.
- USB system media: `/dev/sda2` mounted at `/mnt/sda2`, about 13 GB available
  before music uploads. Persistent extensions: `/mnt/sda2/tce`.
- Lyrion 9.1.1 installed and autostarts. Web UI: http://192.168.1.18:9000/.
- Squeezelite player `FM4-Reborn`, ID `d8:3a:dd:30:37:15`, explicitly connects
  to the local server (`SERVER_IP="127.0.0.1"`). USB audio is `hw:CARD=AUDIO`.
- SMSL USB DAC and Pi headphone output detected; playback confirmed by user.

## Work completed and tested

1. Connected by SSH; confirmed architecture, audio devices, SPI and GPIO API.
2. Installed Python 3.11 and the small display/encoder test panel.
3. User verified OLED, encoder rotation and click handling.
4. Installed Lyrion, enabled local server and connected Squeezelite.
5. Tested reboot. Corrected startup: commands after the standard bootlocal
   pipeline can be delayed; use piCorePlayer `USER_COMMAND_1` instead.
6. Second reboot verified automatic panel and server startup. User confirmed
   the screen returned. No extra manual Sable restart was required.
7. Created persistent `/mnt/sda2/Music` and `/mnt/sda2/Playlists`, owned by tc:staff.
8. Installed Samba4. Authenticated writable `Music` share points only at
   `/mnt/sda2/Music`. Windows login, file creation and cleanup verified.
   UNC: `\\192.168.1.18\Music`. Account `tc`; password is not stored here.
9. Saved extensions, Samba configuration/account database and boot settings
   through piCorePlayer backup. Music is outside `/home/tc`, so uploads are
   not packed into the system configuration backup.
10. User copied two folders. Verified Lyrion mediadirs is `/mnt/sda2/Music`;
    requested incremental rescan and confirmed completion: 32 tracks, 2 albums.

## Source baseline for the full port

- Sable: https://github.com/theshepherdmatt/sable
  revision `3670e503db8124de5890a6df1dc1b68b95d392a6`.
- Empowered enhancement pack: https://github.com/graemedench/quadify_empowered
  revision `ed3d9417b1b18fdd13a83a3dd5b65505c7bef0c7`.
- The Empowered patch applies cleanly to that pinned Sable baseline.
- Working enhanced source: `work/sable-port` in this Codex workspace.
- Reuse the enhanced Sable screens, assets, menus and settings. Add a separate
  piCorePlayer backend and Linux GPIO transport; do not run the Volumio installer.

## Hardware map (latest published FM4 map)

| Function | BCM GPIO / interface |
| --- | --- |
| SSD1322 256 × 64 | SPI0 CE0, MOSI10, SCLK11, DC24, RST25 |
| Encoder | CLK13, DT5, SW6; pull-ups; reverse direction enabled |
| MCP23017 | I²C1, address 0x20; SDA2/SCL3 |
| LEDs | MCP GPIOA0–7; reverse ribbon mapping per hardware preset |
| Buttons | MCP GPIOB0–1 columns, GPIOB2–5 rows |
| HS0038 IR | GPIO27, physical pin13 |
| Shutdown switch | GPIO21, physical pin40; active low, two-second hold |

Earlier chat notes said IR GPIO4 and shutdown GPIO17. The newer published FM4
wiring diagram and current Sable defaults say GPIO27 and GPIO21. Use the newer
map for the port, then physically verify IR and shutdown before marking tested.
SPI already works. I²C and IR device nodes were absent at initial full-port check.

## Current first-panel installation

`/home/tc/quadify-pcp/panel.py`, `start.sh`, vendor libraries and font.
Startup: `USER_COMMAND_1="/bin/sh /home/tc/quadify-pcp/start.sh"`.
Log `/tmp/quadify-panel.log`; PID `/tmp/quadify-panel.pid`.
Dependencies: Python3.11, Pillow12.3.0, gpiod2.5.0, cbor2 6.1.5,
luma.core2.6.0, luma.oled3.16.0. The test panel uses a personally licensed
Windows Arial font; the full port should use Sable's DejaVu fonts instead.
Its menu offers basic transport, encoder test, brightness and clock.
Original pCP settings are saved as `*.before` on the Pi, not in this backup.

## Full port — work in progress

Pinned Sable source has been copied to an isolated working directory and the
Empowered modifications applied. Inspected state model, rendering, menus,
browser, album-art cache, input handling and moOde backend as an adapter example.
Implemented an initial independent Lyrion backend and piCorePlayer runner in
`overlay/sable/pcp/`. See STAGING.md and CHANGELOG.md for the current deployment.
Read-only live integration checks and original-screen simulation passed. The
OLED prototype runs at `/home/tc/sable-pcp-stage`; physical confirmation pending.
The saved boot command still starts the recovery panel.
The full port is not yet installed or feature-complete.

Architecture: input sampling separate from dispatch, independent command,
browse and status workers, cached browse results, stale-result protection,
single serialized UI dispatch, and image changes only sent to SPI.
Preserve actual Sable artwork/layout and font hierarchy.

## Features that need implementation or verification

See FEATURE-MAP.md. In particular: local album/artist/folder browsing and queue,
artwork; playback modes and Save Track; buttons/LEDs; IR; output switching;
network settings; shutdown; spectrum and TIDAL plugin-specific functionality.
Unknown API calls must have bounded timeouts. The server `apps` request timed
out during initial inspection, so plugin browsing needs protocol verification.

## Rebuild and backup principles

Keep installable source overlays, pinned revisions, exact dependencies, installer,
hardware settings, feature/test map and this log together. Preserve media files
separately through the Music share. Export safe user settings separately from
private credentials. Back up Lyrion playlists and preferences on the source SSD
before replacing it. A whole-drive image remains a separate useful recovery copy.
Do not claim OneDrive cloud upload is verified merely because the local copy
was written; the OneDrive application handles that synchronization.
