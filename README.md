# PiCore FM Empowered

A piCorePlayer port of the modified Quadify/Sable interface for Graeme's FM4:
the familiar Sable presentation with responsive controls, standalone Lyrion,
streaming, receivers, CD tools and printable hardware files in one project.

**Release candidate:** the working FM4 has been tested during development.
A complete fresh-SSD installation and Bluetooth audio still need acceptance
checks. See [the verification map](FEATURE-MAP.md) for exact status. This is an
interface/install overlay, not a bootable disk image.

## Start here

| Guide | What it covers |
| --- | --- |
| [Fresh SSD installation](INSTALL.md) | Base image, prerequisites, installer build, acceptance and recovery |
| [Short/long-press controls](CONTROLS.md) | Button table and feature overview |
| [User guide](docs/USER-GUIDE.md) | Browsing, favorites, shortcuts, displays, services, Wi-Fi, IR and CDs |
| [Hardware and pins](HARDWARE.md) | Tested OLED, encoder, buttons, IR and shutdown wiring |
| [Wiring diagram](docs/FM4-WIRING-DIAGRAM.svg) | Labelled GPIO/SPI/I2C map, corrected to GPIO4 IR |
| [Build notes](docs/FM4-BUILD-NOTES.md) | Reversible mounting and rear-panel conversion |
| [Maintenance](docs/MAINTENANCE.md) | Persistent files, backups, updates and troubleshooting |
| [Feature/test status](FEATURE-MAP.md) | Implemented features and outstanding physical checks |
| [Development log](HANDOVER.md) | Decisions and verification for future work |
| [Change log](CHANGELOG.md) | Development changes |

## Included features

- SSD1322 OLED, encoder, MCP23017 buttons/LEDs and Empowered short/long actions.
- Lyrion library, album, artist, genre, playlist and queue browsing; selected
  tracks retain their surrounding queue.
- Play/pause, soft stop/resume, previous/next and five playback modes.
- FM4 Favorites plus six programmable short/long source shortcuts on 5-7.
- TIDAL/BBC Sounds integration, radio presets and service URL display including
  the browser control UI.
- Native Wi-Fi join/status, library refresh and storage information.
- Headphones/external DAC selection, AirPlay 2 receiver integration and native
  Bluetooth support (Bluetooth audio acceptance remains outstanding).
- Apple aluminium IR capture/pairing, graceful shutdown and wake.
- USB CD detection, playback queues, metadata/artwork, named FLAC/MP3 ripping,
  cancellation and background progress.
- Panel/Performance/Cinema plus Needle VU, Twin Needle VU and Spectrum;
  elapsed/track length, live audio levels and centred track-change popups.
- Pinned HTTPS source build, captured preferences and two-phase fresh installer.
- Artwork-enabled FM4 Favorites web page with public TIDAL links.

See the user guide for behavior and limitations. Music, accounts, passwords and
private machine backups are not included. The captured profile restores the development unit's password-free Music
share; Wi-Fi, account credentials, music and playlist contents are excluded.

## Printable parts and editable designs

The [FM4 Button Print Pack](FM4%20Button%20Print%20Pack/READ%20ME.txt) includes
the all-variants 3MF plate, [preview](FM4%20Button%20Print%20Pack/All_Button_Variants_Preview.png),
two-colour FDM STL pairs, raised-icon resin STLs and editable blank-cap source.
Re-slice for your printer. Play/Pause and Play Mode caps match the Empowered
layout; alternate original icons are retained.

[FM4 Mounting Parts](FM4%20Mounting%20Parts/README.md) includes the screen holder,
rotary bracket, V6 knob extender and reversible Ethernet panel with photos.
[Hardware Design Sources](Hardware%20Design%20Sources/README.md) adds current
Inventor/STL designs, working USB rear-panel parts and a PCB test template.
Working designs have their fit/revision status identified. The
[file inventory](docs/HARDWARE-FILES.json) records sizes and SHA-256 hashes.

## Build from a blank SSD

Start with the [official 64-bit piCorePlayer image](https://docs.picoreplayer.org/downloads/)
and an image writer such as [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
Follow [INSTALL.md](INSTALL.md) to prepare USB boot and local Lyrion. Build the
overlay with [build-stage.ps1](build-stage.ps1), then package it with
[build-installer.ps1](build-installer.ps1). The
[installer source](installer/install.py) checks prerequisites and archive
integrity and refuses an existing FM4 install. Keep the working drive until its
replacement passes the acceptance checklist.

## Origins, credit and notices

- [Matt's original Sable project](https://github.com/theshepherdmatt/sable)
- [Quadify project and wiring](https://quadify.uk/wiring.html)
- [Quadify Empowered, our earlier Volumio enhancement](https://github.com/graemedench/quadify_empowered)
- [piCorePlayer](https://www.picoreplayer.org/)
- [Lyrion Music Server](https://lyrion.org/)

This port was **vibe coded by Graeme Dench with Alex (OpenAI Codex)**. Graeme
directed the features, supplied the hardware and tested it. Alex did the heavy
lifting on implementation, integration, debugging and documentation.

Matt's Sable design and development made this possible; original authorship and
notices are retained. Graeme reports that Matt has granted permission for the
port. Thanks also to piCorePlayer/Lyrion and MusicBrainz/Cover Art Archive.
Copied Quadify Empowered materials retain their
[personal-use notice](docs/QUADIFY-EMPOWERED-PERSONAL-USE-NOTICE.md); the port does
not broaden rights in original projects or designs.
