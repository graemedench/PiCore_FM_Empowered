# PiCore FM Empowered

Port of the modified Quadify/Sable FM4 interface to piCorePlayer, preserving its
look while improving input and playback responsiveness.

**Status:** the FM4 prototype now includes standalone Lyrion, responsive OLED and
controls, TIDAL/BBC Sounds/radio, Wi-Fi, AirPlay 2, audio output selection, IR
pairing, shutdown, CD playback and named FLAC/MP3 ripping. Panel/VU, Panel/Twin Needle VU
and Panel/Spectrum provide alternate live audio views. Bluetooth audio and a
complete fresh-SSD install still need physical acceptance tests.

Start with [INSTALL.md](INSTALL.md) for the new SSD release candidate,
[HARDWARE.md](HARDWARE.md) for wiring, [FEATURE-MAP.md](FEATURE-MAP.md) for test
status and [HANDOVER.md](HANDOVER.md) for the development log.
[STAGING.md](STAGING.md) retains the original prototype deployment history.
Build the source archive with `build-stage.ps1`, then package it with
`build-installer.ps1`. Sources are pinned and fetched over HTTPS.

Music, passwords, machine backups and private server settings are excluded.
Upstream Sable assets and notices remain with their original project.

## Credits

This port was vibe coded by Graeme Dench with Alex (OpenAI Codex). Graeme directed
its features, supplied the FM4 hardware and tested it in use. Alex did the heavy
lifting on the software implementation, piCorePlayer integration, debugging and
rebuild documentation.

The interface is based on [Sable by Matt](https://github.com/theshepherdmatt/sable)
and the original Quadify/Sable work. Matt's design and development made this port
possible; upstream authorship and notices are retained. Graeme reports that Matt
has granted permission for this port. Thanks also to the piCorePlayer and Lyrion
contributors, and the MusicBrainz/Cover Art Archive communities.

See [CONTROLS.md](CONTROLS.md) for features and short/long press controls.
