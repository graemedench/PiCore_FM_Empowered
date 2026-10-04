# Project log

## 2026-10-03 â€” working foundation and backup

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

## 2026-10-03 â€” first Sable/Lyrion prototype

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
- Verified FM4 Favorites contains Spell through Lyrion's playlist-tracks query
  and `/mnt/sda2/Playlists/FM4 Favorites.m3u`. Button events 1â€“5, 7â€“8 are visible
  in the runtime log; complete action mapping and LED positions remain pending.

## 2026-10-03 â€” button layout and responsiveness fix

- User reported sluggish buttons and button 2 reverting to Pause. Root causes:
  generic settings instead of the Empowered preset, 100ms scan sleeps without
  per-key debounce, and missing random/repeat transport mappings.
- Added FM4Buttons scan with 20ms stable debounce and about 15ms scan cadence,
  retaining deliberate holds. Deterministic quick-tap, bounce and hold checks pass.
- Migrated the entire button section from the pinned Empowered Graeme preset
  once. Future starts preserve settings. Button 1 toggles play/pause; button 2
  cycles modes; 3/4 previous/next; 5/6 radio presets and holds; 7 TIDAL mixes;
  8 Save Track. TIDAL's old Volumio mix URI shows an explicit pending message.
- Implemented random/repeat command mapping, wake status polling on command
  completion, and moved playlist saving off the transport worker.
- Live repeat/shuffle flag checks and play/pause/toggle checks pass. Measured
  transport commands about 21â€“22ms. Restored pre-test playback and flags.
- Deployed and restarted prototype. User tactile confirmation requested.

## 2026-10-03 â€” held Stop resume fix

- User confirmed buttons are much better, then reported that held Stop needed
  a track skip before restarting playback.
- Play/pause now clears the soft-stop latch and five-minute delayed stop timer,
  then explicitly resumes. Ordinary toggle consults live Lyrion state and sends
  Play when paused or stopped, avoiding ambiguous stop-state pause toggling.
- Actual app/Lyrion integration test passed: held Stop pauses, tap resumes the
  same queue index, latch/timer clear, and a hard-stopped player resumes on tap.
  Restored pre-test playback, deployed and restarted the prototype.

## Evening session â€” time, levels and saved stopping point

- User requested elapsed time and small VU bars on default Panel, with no bars
  in Performance, then asked to save and stop for tonight.
- Enabled native pCP VISUALISER setting and restarted Squeezelite, preserving
  playback state. Implemented real stereo RMS from its shared PCM export, using
  a nonblocking read lock for the copy and processing outside the lock.
- Added mm:ss elapsed counter. Pause freezes it. Performance omits levels.
- User confirmed lively, responsive screens and visible levels; requested
  elapsed / total format (for example 1:23 / 4:56). Applied for known-length
  tracks; streams without a duration retain elapsed time alone.
- Live stereo levels varied approximately 0.55â€“0.71 during the check. Tests pass
  for valid PCM access, all three layouts, absent Performance bars and frozen
  pause time. Inspected saved Panel, Performance and paused PNGs.
- Deployed current interface. Saved native automatic startup with initial-failure
  fallback to the original panel. Full reboot test remains for next session.
- Saved offline staged archive, dependency pins, build helpers, notes and previews.
  Remaining work includes IR/shutdown input, TIDAL mix mapping, shortcut saving,
  audio output/Wi-Fi settings, fullscreen meters and a complete fresh-SSD installer.

## 4 October — PPM and fresh SSD packaging

Added Panel / PPM with real PCM peak measurement and slow needle release.
VU/PPM track title and artist are centred across the meters for four seconds;
spectrum remains two seconds. Any interaction restores Panel for five seconds.
Deployed safely after checking no rip active; panel startup and native backup
passed. Local rendering and on-device four-second timing passed. User PPM
physical feedback pending. Native player identity now derives from pCP config
for replacement drives. Added fresh-install-only checksum-checked installer,
bundle builder, INSTALL.md and HARDWARE.md; existing FM4 installs are refused.
Fresh SSD install and Bluetooth audio acceptance remain pending. Read latest
FEATURE-MAP/INSTALL for current status; older log entries are historical.

## Complete project documentation and hardware pack

Copied the released Quadify Empowered button/mounting packs and current local
CAD/USB-panel/PCB-template files. Included 86 hardware-pack files with a SHA-256
inventory; working parts explicitly labelled. Updated the copied wiring diagram
and build notes to verified GPIO4 IR. Added detailed user/maintenance guides,
full controls table, source credits and links to Matt, Quadify Empowered, the
official piCorePlayer base image and FM4 installer build/source. Installer
bundle now includes referenced documents and hardware packs. Fresh SSD and
Bluetooth audio acceptance remain outstanding; no live-device changes here.

## Expanded fresh install and Favorites web page

Captured allowlisted panel preferences/shortcuts, remote identity and reusable
native/server settings without Wi-Fi, passwords, tokens, music or machine ID.
Added bootstrap/prepare for Python, native Lyrion/Samba/AirPlay/Bluetooth and
SPI/I2C; restore configures paths, localhost player, outputs, receivers, guest
Music sharing and pinned public plugins. Preparation and restore pass isolated
filesystem tests; a real clean SSD install is still outstanding. Official
plugin ZIP checksums and flat/enclosing layouts verified; RadioNowPlaying uses
publisher HTTP. Added native-httpd FM4 Favorites page, real art, public TIDAL
links, startup/minute/save refresh and OLED URL entry. Live page and remote
artwork returned HTTP 200; current saved TIDAL URI is tidal://218740662.mp4,
covered by link parser. Existing Favorites data remains on device, outside Git.

## 2026-10-04 — local library excludes cloud albums

- Diagnosed 37 combined albums: 32 were TIDAL cloud entries. Local-only view contains five albums and 68 tracks; every local indexed file exists. No files or cloud library entries deleted.
- Scoped panel Albums, Artists, Genres and their track lists to native localTracksOnly library. Mixed playlists and queue remain intact; live FM4 Favorites verified with a local track and TIDAL track.
- Enabled native local-only virtual library and saved default library preference; restored by installer. Browser may retain its own All Music selection; documented local-only selector.
- Deployed and restarted panel with no active rip, saved piCore backup. Regression checks cover local scope, mixed playlists/queue and missing virtual library. Clean SSD hardware installation remains untested.

## 2026-10-04 — scheduled Favorites backups

- Favorites watcher now backs up on startup and checks hourly; writes only changed versions, keeps latest plus three rotating versions outside the music scan at /mnt/sda2/FM4 Backups/Playlists. Empty/missing source does not overwrite backup. Same-disk protection against accidental edits, not drive failure. Initial backup verified live; regression checks passed.
- Old Quadify playlist import pending location of network backup; local OneDrive/project searches found no saved playlist. Current Favorites preserved.

- Imported GATEWAY Quadify-latest.playlist: 14 entries reduce to 11 distinct entries (9 TIDAL + BBC Radio 2/4); duplicates were removed by Lyrion. Preserved pre-import playlist separately. Playlisttracks queries now include player context to support HTTP streams; verified indexed URLs and web export. Old BBC direct stream links preserved, playback not tested.
- User requested three rotating copies and one HTML: changed retention to numbered slots 1–3 plus latest and HTML. Network upload pending private share credentials (guest rejected); local hourly backup active.

- Added optional SMB upload with private device-only configuration and credentials; share rejects supplied login including GATEWAY domain. Network schedule left unconfigured pending valid login. Native libarchive dependency installed for smbclient. No account/share access settings changed.

- Imported GATEWAY Quadify-latest.playlist: 14 entries reduce to 11 distinct entries (9 TIDAL + BBC Radio 2/4); duplicates were removed by Lyrion. Preserved pre-import playlist separately. Playlisttracks queries now include player context to support HTTP streams; verified indexed URLs and web export. Old BBC direct stream links preserved, playback not tested.
- User requested three rotating copies and one HTML: changed retention to numbered slots 1–3 plus latest and HTML. Network upload pending private share credentials (guest rejected); local hourly backup active.

- Network backup enabled and tested successfully to GATEWAY / Gateway Share (192.168.1.200). Verified latest M3U, rotating slot 1 and HTML on share; remaining slots fill on subsequent playlist changes. Private device credentials/config saved with native backup, excluded from project and installer. Hourly/startup watcher reads config dynamically.
