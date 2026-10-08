# Using PiCore FM Empowered

This is the piCorePlayer port of Graeme's modified Quadify/Sable interface. The
panel controls a local Lyrion server and Squeezelite player. Lyrion supplies
library browsing, queues, streaming plugins and artwork; the panel supplies the
FM4 controls, display, shortcuts, hardware integration and CD tools.

## Everyday controls

See [the complete short/long-press table](../CONTROLS.md). Button 1 toggles
play/pause; holding it enters soft stop. A tap resumes without needing a skip.
Buttons 3 and 4 move through the queue. Button 2 cycles **Play Single, Play All,
Repeat Single, Repeat All and Shuffle**. Playback mode applies to the loaded
queue; selecting a track from an album, CD or playlist loads its context and
starts at that track. Selecting an existing queue item changes its position.

Turn the encoder to adjust playback volume. Press to open the source carousel;
turn to a source, press to browse, then select your music. In menus, turning
moves the selection and pressing selects. Back returns one level; a long
encoder press returns to Now Playing. A dedicated shutdown switch or Settings
shutdown confirmation performs graceful shutdown. The physical shutdown and
wake sequence has been tested on Graeme's unit.

## Favorites and programmable shortcuts

Tap button 8 to add the current supported item to **FM4 Favorites**. Hold it to
open Save Shortcut, choose button 5, 6 or 7, and choose **Short press**, **Long
press** or **Cancel** with the encoder. This gives six programmable source
slots. CD stream addresses are temporary and are not reusable radio shortcuts.
Settings → Shortcuts can restore the default assignments. Defaults include BBC
Radio 2/4, Greatest Hits Radio and Absolute 80s; personal TIDAL mixes require
the owner's account and can be reassigned.

## Display choices

Settings → Display Mode selects the original Panel, Panel Performance or
Cinema presentation, or one of the new Panel/visualizer modes. Panel includes
elapsed time / track length and small left/right audio bars. Performance omits
these bars. Streams without a useful duration show elapsed time.

**Panel / Needle VU** displays separate left and right gauges. **Panel / Twin
Needle VU** gives each channel a bright, fast level needle and a dimmer peak
needle. The peak holds for one second and then falls at an eight-second
full-scale rate. **Panel / Spectrum** displays frequency bands with faster
updates. These are visual audio indicators, not calibrated measurement tools.

Each interaction returns the visualizer to Panel for five seconds. A track
change displays a centred title/artist popup for four seconds on the needle
views or two seconds on Spectrum. When idle, the clock can show a small rip
progress pie at the bottom right. Brightness and idle/clock settings are
available in Settings; saved options are persisted through native backup.

## Local music, queues and the web player

Albums, Artists and Genres show files stored locally, using Lyrion's local-only library. TIDAL remains available through its own source; playlists and the queue can contain both. In the web player, select **Local tracks only (no music service)** if its saved library selection still shows All Music.

Store music in `/mnt/sda2/Music` and saved playlists in `/mnt/sda2/Playlists` on
the supported USB-boot layout. Copy files through the native Samba Music share,
then run Settings → Music Library → Refresh now. Automatic refresh can be Off,
every 15 minutes or hourly; it waits while a rip is active. Storage displays
available capacity.

Settings → Service URLs → **Web player** displays `http://<current-IP>:9000/`.
Choose that entry to show the address; the submenu labels are not literal URLs.
The IP is resolved when opening the entry, so it follows the active network
route. If detection fails the hostname fallback is used. The same submenu links
to BBC Sounds/TIDAL sign-in and server settings. Use the device's current address on your own network.

Settings → Service URLs → **FM4 Favorites page** shows the artwork-enabled
saved-track page at `http://<current-IP>/fm4-favorites.html`. TIDAL entries link
to their public TIDAL track page; local entries show titles and available art.
It refreshes every minute and after a panel save. Playlist contents stay on your
FM4 and are not published to GitHub.

The native piCorePlayer configuration page is `http://<current-IP>/`, without
port 9000. Lyrion's web player and settings use port 9000.

## Streaming and receivers

TIDAL and BBC Sounds need their Lyrion plugins and your own sign-in. BBC account
features and available stations depend on the service. Native AirPlay 2 accepts
iPhone/iPad audio and integrates receiver handover and real stereo meter data.
Bluetooth is implemented through native BlueALSA; end-to-end Bluetooth audio
acceptance remains outstanding. Install/configure these services as described
in [INSTALL.md](../INSTALL.md). Use Settings → Audio Output to select
**Headphones** or the detected external DAC, with volume set appropriately.

## Wi-Fi and Apple remote

Settings → Network provides Wi-Fi scanning/joining and status/IP. Select your
network, use the encoder to enter the password and choose Join; Cancel leaves
the connection alone. Native piCorePlayer saves the network configuration.
Use the displayed new IP after changing networks.

The Apple aluminium IR receiver on this FM4 is wired to **BCM GPIO4 / physical
pin 7**. Settings → Pair Apple Remote opens a 30-second capture window. Send a
recognised Apple button to save its identity; timeout preserves the previous
pairing. The receiver and basic remote actions have been physically tested;
the pairing screen still needs a complete user acceptance check.

## CDs and ripping

Plug in a supported USB optical drive. CD appears in the carousel when the
drive is detected. Track selection queues the disc and starts at the selected
track. Disc titles and artwork are looked up using MusicBrainz and Cover Art
Archive when available; unknown discs retain generic names.

The CD menu offers playback, eject, FLAC rip and MP3 rip. Ripped albums go under
`Music/CD Rips` with artist/album folders and numbered track names. Existing
folders are preserved using a unique destination. The progress screen covers
reading and encoding; Cancel keeps completed tracks and Exit/continue leaves
the rip running. The library refreshes after completion. Ripping stops playback
of the actual CD to free the drive; TIDAL/radio/local-file playback can continue.
Do not eject or unplug the optical drive while ripping.

These are convenient local rips, without AccurateRip/secure-rip certification.
Completed ABBA MP3 and R.E.M. FLAC discs have been checked during development.
See [FEATURE-MAP.md](../FEATURE-MAP.md) for the latest verification status.
