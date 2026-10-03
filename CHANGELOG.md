# Project log

## 2026-10-03 — working foundation and backup

- Verified the OLED and encoder with the user; saved the first-panel recovery code.
- Enabled standalone Lyrion playback, persistent Music and Playlists folders,
  and an authenticated writable Music share. Library scan and playback confirmed.
- Confirmed panel and server startup after reboot.
- Prepared pinned Sable source with the existing Empowered patch for the full port.
  The full interface remains in development; it is not installed yet.
- Established this handover, feature map and build manifest. Keep these and the
  source synchronized to the user's local OneDrive backup after each milestone.
- User created https://github.com/graemedench/PiCore_FM_Empowered as the project
  repository. Save source and a repeatable installer here as development proceeds.

Future entries should record changed files, deployment steps, checks and results,
remaining problems, and rollback/rebuild implications. Never include credentials.

## 2026-10-03 — first Sable/Lyrion prototype

- Added `overlay/sable/pcp/`: bounded JSON-RPC listener, independent status,
  browse and command workers, stale browse-response guard, original Sable runner,
  and Linux SPI/GPIO display adapter using the tested recovery transport.
- Added read-only live integration checks; all passed against the device.
- Installed native DejaVu fonts; simulation renders successfully.
- Found Lyrion main process stopped on reconnect. Restarted native service;
  API responds. Log shows preceding TIDAL authentication errors; cause of exit
  is not established. Do not attribute the stop to those errors without evidence.
- Staged runtime at `/home/tc/sable-pcp-stage`; started OLED prototype as root
  without logged errors. Physical confirmation requested from user.
- Persistent boot remains the recovery panel. Added reproducible staged build
  script and recovery/deployment notes; a complete fresh-SSD installer is pending.
- User confirmed the original interface looks good and navigation feels snappy.
- Loaded I2C drivers (boot config already enables I2C), detected MCP23017 at
  0x20, installed smbus2 0.6.0 and started original Sable buttons/LED controller.
  Button actions and physical LED positions await user confirmation.
- Implemented asynchronous Save Track with read-back verification. User chose
  **FM4 Favorites** as the persistent playlist name.
