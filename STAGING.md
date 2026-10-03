# Staged Sable prototype

This is an initial display/library prototype, not the complete port or a clean
SSD installer. Run `build-stage.ps1` from a fresh checkout to recreate the archive
from the pinned upstream sources. All Git transfers use HTTPS.

The current Pi already has Python 3.11, the recovery panel and its vendor
dependencies installed. The prototype reuses its verified `Serial` and `Encoder`
classes. DejaVu fonts are provided by the native `dejavu-fonts-ttf.tcz` extension.
Do not run upstream Volumio installation scripts on piCorePlayer.

## Current deployment

- Prototype files: `/home/tc/sable-pcp-stage`.
- Settings: `config/pcp-settings.json` relative to that directory.
- Start as root: `sudo /bin/sh /home/tc/sable-pcp-stage/stage-start.sh`.
- PID: `/tmp/sable-pcp-stage.pid`; log: `/tmp/sable-pcp-stage.log`.
- Read-only checks from the prototype directory:
  `PYTHONPATH=src:/home/tc/quadify-pcp/vendor python3.11 check_live.py`.
- Simulation leaves the OLED alone:
  `PYTHONPATH=src:/home/tc/quadify-pcp:/home/tc/quadify-pcp/vendor python3.11 -m sable.pcp.runner --sim --seconds 3`.

Only one display process may run. Both use `/tmp/quadify-panel.lock`.
Stop the current panel before starting the prototype. Do not remove the lock
file while a process owns it.

## Recovery

Stop the prototype using its PID, then run
`sudo /bin/sh /home/tc/quadify-pcp/start.sh`. A reboot also returns to the saved
recovery panel: the persistent boot command has not been switched to Sable yet.

## Verified so far

Live Lyrion checks passed for player metadata and time units, albums, artists,
genres, empty playlists, queue, album tracks, asynchronous browse stale-response
protection and status delivery. Simulation renders using the original screens
and DejaVu fonts. Hardware process started without errors; user visual and
navigation confirmation is pending.

Album/artist/genre lists are paginated. Queue currently has a 10,000-item limit.
Playlist contents, transport changes and mode changes still need live tests.
Settings that require unfinished adapters are temporarily hidden. Spectrum,
audio output switching, Wi-Fi setup, button/IR input and playlist saving remain
unfinished. Single/all selection follows Sable's existing browse behavior;
repeat track/all and shuffle are mapped to Lyrion.
