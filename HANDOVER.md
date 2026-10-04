# piCorePlayer Empowered — living handover

Updated: end of the 3 October evening session (Europe/London).

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
The initial saved boot command started the recovery panel. At the end-of-session
milestone it was switched to the tested Sable prototype (see final log entry).
User confirmed the
Sable appearance and snappy navigation. MCP23017 now initializes at 0x20 after
loading i2c-dev and i2c-bcm2835; smbus2 0.6.0 installed. Buttons/LEDs are connected
but physical checks are pending. Save Track targets **FM4 Favorites**, the name
chosen by the user, with asynchronous read-back verification.
Button feedback exposed generic defaults and slow scans. The runner now migrates
the complete Empowered button preset once, and FM4Buttons uses per-key debounce
with faster scans. Repeat/shuffle and play/pause live checks pass; see the latest
CHANGELOG entry. TIDAL mix conversion and held Save shortcut remain unfinished.
User confirmed improved button responsiveness. Held Stop resume now explicitly
clears its latch/timer and plays the same track; app/Lyrion live checks passed.
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

## Saved stopping point for tonight

Elapsed counter and real left/right RMS level bars are implemented in
`pcp/modern.py` and `pcp/levels.py`. Panel shows both; Performance omits the bars.
Counter displays elapsed / total for known-length tracks and freezes on pause.
User confirmed the lively screens and levels. Live PCM and layout checks passed; rendered previews
are in `previews/`. Native pCP VISUALISER="yes" enables Squeezelite -v.
PCM levels represent the source signal before final software volume adjustment.
Native startup now points to `/home/tc/sable-pcp-stage/stage-start.sh`, which falls
back to the recovery panel if initial startup fails. No reboot was required or
tested for this final change. Recovery instructions are in STAGING.md.
The offline staged source archive is saved locally/OneDrive; dependency pins and
upstream revisions are recorded. A complete clean-SSD installer is still pending.
User asked to stop for tonight after this milestone and revisit another day.

## Rebuild and backup principles

## 2026-10-04 — receiver and TIDAL work in progress

Native pcp-shairportsync and pcp-bt packages installed and added to onboot.lst.
AirPlay 2 uses shairport-sync-ap2 5.0.0 and nqptp, output hw:CARD=AUDIO,
advertised as FM4-Reborn AirPlay. Avahi needed an explicit start; stage-start.sh
now starts it when available. Receiver hooks pause Lyrion and release Squeezelite
before AirPlay uses the DAC, then restore the paused local player afterward.
AirPlay discovery and a running ALSA receiver session verified, but user reports
phone playback counter stalls: audio playback is NOT yet confirmed. Temporary
foreground diagnostics in /tmp/fm4-airplay-debug.log; inspect bounded error lines,
never export full protocol logs or credentials. Restore native daemon after repair.

TIDAL authenticated browsing returns eight My Mix playlists. My Mix 1 CLI playback
loaded 40 tracks, mode play and elapsed time advanced. Button 7 now maps old
Volumio mix shortcuts to Lyrion My Mix 1 (tap) / My Mix 2 (hold), with TIDAL browse
in source carousel. Native plugin identifiers are used rather than Volumio URLs.
Dedicated active-low GPIO21 shutdown installed; release-to-arm and two-second
single-event hold logic passed. Physical shutdown has not been tested.

Bluetooth controller still unavailable in the running device tree (/dev/serial1
absent); boot config no longer has disable-bt, so reboot is pending. Native
Bluetooth output is configured to the USB DAC. Phone must be paired and configured
as type 2 Player using native pcp-bt-config, NOT type 1 Speaker. BluetoothHandover
watches native bluealsa-aplay to release local playback; requires live testing.
The phone counter started advancing after receiver restart. Sound confirmation
remains pending. AirPlay/Bluetooth meters now have a real ALSA PCM-copy feed,
receiver-levels.sh and setup-receiver-levels.py. Receiver PCM is drained to RAM-only
stereo RMS snapshots, with no audio files recorded. 16/32-bit silence and stereo
level checks passed; live receiver bars still await confirmation. Run native setup
first, meter setup second (the latter sets SHAIRPORT_OUT/BT_OUT_DEVICE=fm4_receiver).
Root ALSA includes tc's .asoundrc; persistence includes root/.asoundrc explicitly.
Live AirPlay ALSA meter snapshots subsequently showed nonzero stereo levels, and
AudioLevels.read() returned the receiver feed successfully. OLED appearance and
audible sound still need user confirmation. Native daemon is running with
-d fm4_receiver; ALSA hardware status RUNNING verified. Native AirPlay daemon restored after diagnostics. Full receiver metadata remains
pending. Radio shortcut URLs returned HTTP 200 HLS playlists but actual playback
still requires verification; no HLS plugin was found in the inspected directories.
CD playback/ripping deferred at user's request. No completed installer claimed.

Later checkpoint: reboot completed successfully. Sable runner, native AirPlay 2,
nqptp and BlueALSA returned automatically. Bluetooth controller is powered and
pairable; discoverable enabled for the native 180-second window. No phone was
paired at this checkpoint, so native type 2 configuration/audio test remains.
User said AirPlay was "looking good" after the real receiver meter feed was added.

Raw BBC HLS shortcut playback failed to advance and Lyrion logged missing protocol
handler. Installed BBC Sounds 2.54.8 from the official Lyrion plugin repository's
HTTPS release, verified SHA1 f05b152747e76718a3d80a11e8f75bc137e39e38, enabled via
pref plugin.state:BBCSounds and native Lyrion stop/start. Plugin requires BBC account
sign-in; user asked to do that privately through Settings. Buttons 5/6 now use
sounds://_LIVE_bbc_radio_two and sounds://_LIVE_bbc_radio_fourfm, with an asynchronous
"Sign in on web player" message while unsigned. Actual BBC playback remains untested.
Installer helper saved as tools/install-bbc-sounds.py. Commercial hold shortcuts
still retain their previous RadioFeeds URLs and have not been playback-tested.

## Receiver ownership correction after user reported stuck AirPlay

Local transport and source commands now explicitly release receiver ownership on
the command worker, leaving UI dispatch responsive. return_local disconnects native
Bluetooth audio helpers, terminates stale helpers, ends AirPlay, clears its state,
restores Squeezelite and reopens AirPlay discovery. Bluetooth monitoring now checks
live executable command lines rather than pidof, which also matched zombie helpers.
Late Avahi startup now preserves an existing DBus daemon; native Avahi init's first
start restarts DBus and detached the already-running Bluetooth services. Native
Bluetooth service restart was attempted for recovery; phone reconnection remains
to be checked. Receiver marker absent and Squeezelite connected verified afterward.

An actual local MP3 played with elapsed 4.8 seconds; toggle paused, second toggle
resumed. Queue restored afterward. Transport checks against the current TIDAL queue
did not pass toggle because streamed playback stopped; do not claim all streaming
transport tests passed. The earlier generic songs-query test selected a streaming
entry; a filesystem MP3 was used for the meaningful local regression check.
BBC sign-in is still required and credentials should remain in Lyrion's own UI.

## Direct BBC radio restored without sign-in

User preferred the same no-account streams used by Volumio. Installed publisher
PlayHLS 2.12 from https://bpa-code.github.io/bpaplugins/PlayHLS-v212.ZIP, verified
SHA1 3da446c52d2eecbc1d70834bfa822b6bf761d616 against repo-playhls-v2.xml. Enabled
plugin.state:PlayHLS and restarted Lyrion. Actual Radio 2 playback reached 7.06s;
Radio 4 reached 7.61s, correct queue index and Radio 4 title. Original HTTP URLs
were mapped by the plugin to hlsplay; shortcuts now use hlsplay:// explicitly and
pass station title, avoiding initial HTTP scan latency. Buttons 5/6 are deployed
on the direct route and do NOT require BBC Sounds sign-in. BBC Sounds remains
optional for its own browsing/catch-up; sign-in page is
http://192.168.1.18:9000/plugins/BBCSounds/settings/basic.html.
Rebuild helper tools/install-playhls.py saved. pcp-ffmpeg package was downloaded
while evaluating fallback, but not loaded or added to boot; native PlayHLS 2 needs
no additional executable. Live tests restored the original 40-track queue afterward.

## Long-press radio and service sign-in menu

Button 5 hold still uses the RadioFeeds clyde2-mp3 endpoint for Greatest Hits Radio
(Glasgow & the West); button 6 hold uses absolute80s-mp3. Both played in live checks,
elapsed 3.01s / 2.55s. Native playlist play now passes the supplied station title.
The OLED adapter replaces generic clyde2.mp3/absolute80s.mp3 labels with station names,
while preserving actual song metadata. No signed stream URLs are saved in source.

Settings menu now has Service sign-in: BBC Sounds, TIDAL and Server settings. Each
shows its complete browser URL wrapped across the OLED, using the current routed
IP; hostname fallback FM4-Reborn.local. Page remains visible until encoder press or
back. Render/return and station-label preservation checks passed on the Pi.
User signed in to BBC Sounds privately. Authenticated root menu and its 27 Listen
Live entries verified. BBC Sounds added to source carousel using the native OPML
plugin browse/play interface, alongside TIDAL. Search entry omitted until text entry
is implemented; browse results currently limited to 100 per level. Catch-up playback
has not been tested. Direct BBC button streams remain independent of sign-in.


Keep installable source overlays, pinned revisions, exact dependencies, installer,
hardware settings, feature/test map and this log together. Preserve media files
separately through the Music share. Export safe user settings separately from
private credentials. Back up Lyrion playlists and preferences on the source SSD
before replacing it. A whole-drive image remains a separate useful recovery copy.
Do not claim OneDrive cloud upload is verified merely because the local copy
was written; the OneDrive application handles that synchronization.

## Wi-Fi encoder controls — installed, real join pending

Installed native wireless_tools, wpa_supplicant, matching wireless kernel module
and firmware-rpi-wifi extensions. Initial brcmfmac probe ran before firmware was
loaded; reloading that Wi-Fi module brought wlan0 up without touching Ethernet.
Actual scan returned one unique nearby network. setup-native-wifi.py records
firmware before module/tools in onboot.lst. Stage startup loads brcmfmac if available.

Settings -> Network -> Wi-Fi Networks now scans on a background worker, then uses
the encoder to enter a password, select DELETE/CANCEL/JOIN. Full printable ASCII
entry and masked password rendering were tested, along with menu presence and
short-password rejection before any configuration changes. Wi-Fi status / IP is
also present. Ethernet remains connected and unchanged.

pcp/wifi.py uses native wlan0 startup, wpa_cli association and DHCP status. New
profile SSID is supplied as hex (no shell interpolation), PSK derived using PBKDF2;
credentials stay on the Pi. Existing configuration is privately backed up on the
Pi once and profiles retained. Only successful association with an IP saves the
profile, WIFI=on and persistence entry; native pcp backup follows asynchronously.
Failed new associations remove their pending profile and re-enable prior networks.
Current entry supports WPA personal passphrases of 8-63 characters; open networks,
raw 64-character PSKs and enterprise authentication are not implemented.

User asked to enter the real password privately on the FM4 and report its connected
IP. Real join, saved-profile reboot and operation with Ethernet unplugged have NOT
yet been verified. Do not advise unplugging Ethernet until an actual Wi-Fi IP is
confirmed. No Wi-Fi passwords/configuration are exported to GitHub or OneDrive.

## Wi-Fi join confirmed — default communications address

User confirmed encoder join succeeded at 192.168.1.19. Existing trusted SSH session
independently confirms wlan0 has 192.168.1.19. Use this Wi-Fi address as the default
for future device communication and web links; Ethernet 192.168.1.18 is secondary.
Saved-profile reboot remains untested. User intends to leave Ethernet unplugged.

Windows has an old SSH identity recorded for .19. Verified FM4 ECDSA fingerprint
through the existing trusted SSH session: SHA256:3wjzghdCT4LAkz9D+67hSAq2lfXGkUjS2WIXM0KNFHw,
exactly matching the key presented by .19. Until known_hosts is deliberately updated,
ssh/scp -o HostKeyAlias=192.168.1.18 to 192.168.1.19 verifies against the existing FM4
identity; do not disable strict host-key verification or blindly delete old keys.

### 2026-10-04 — Hold 8 shortcut learning restored
Tap 8 still adds the current track to FM4 Favorites. Hold 8 opens Save Shortcut; press 5, 6 or 7, choose Short/Long with the encoder and click to save. Assignments use atomic settings writes followed by native pcp backup. Receiver inputs are not learnable. TIDAL/BBC collection identifiers and known radio preset entry URLs are preserved for recall. Deployed over Wi-Fi .19; runner healthy, native backup succeeded. check_shortcut_save.py passed picker capture, short/long settings reload and backup scheduling without changing real button assignments. Physical user confirmation pending. Legacy named playlist action remains unfinished.

### 2026-10-04 — Explicit shortcut Cancel
The destination picker now shows Short press, Long press and Cancel as three encoder choices. Cancel returns to the playback view without changing assignments or scheduling backup. Regression check covers unchanged settings after Cancel.

### 2026-10-04 — Revision-one gap closure
Restored Storage using mounted /mnt/sda2 capacity/free space, Shortcuts / Reset 5-7 Defaults with native backup, named playlist recall via Lyrion playlistcontrol and a real timer for Music Library auto-refresh (15 minutes/hour/off). Added check_revision_one.py: schedule/disable, named and missing playlist handling, mounted storage. Checks passed on FM4; shortcut/cancel and shutdown hold regression checks run too. Playlist recall is command-path tested, not live audio verified in this session. Native shutdown route confirmed pcp sd -> exitcheck.sh -> /opt/shutdown.sh (stops LMS) -> poweroff; actual hardware poweroff remains pending. No live optical drive in sysfs; /dev/sr0 and sr1 nodes exist but no drive/device present. cdparanoia and cd-discid absent; pcp ffmpeg package cached but executable not loaded. CD implementation requires a connected drive and native package/kernel support; do not treat stale nodes as detected hardware. User asked for more progress toward revision one, not a completed release.

Device backup attempt after deployment FAILED: tar /mnt/sda2/tce/mydata.tgz Input/output error. Runner remains healthy in RAM. Investigating USB storage; do not reboot or claim latest device persistence. Local source/archive backup remains available.

Storage diagnosis: kernel logged usb 2-1 disconnect at uptime 5078s, ext4 shutdown and journal abort/device offline on sda2. Reconnected Verbatim STORE N GO at scsi 1:0:0:0. Slimtype eBAU108 6 L CD-ROM appeared at scsi 2:0:0:0 after USB hub connection, but sr_mod is absent from current kernel extensions. Do not reboot, remount or run filesystem repairs while backing extensions/LMS remain active. Asked user to confirm boot USB stable; storage recovery first, then optical kernel extension/tools. Earlier no-drive observation was before this hardware arrival.
