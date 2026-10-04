# PiCore FM Empowered

Port of the modified Quadify/Sable FM4 interface to piCorePlayer, preserving its
look while improving input and playback responsiveness.

**Status:** standalone Lyrion, music sharing, OLED and encoder work on the test
unit. The complete Sable interface and repeatable installer are in development.

Start with [HANDOVER.md](HANDOVER.md), [FEATURE-MAP.md](FEATURE-MAP.md) and
[CHANGELOG.md](CHANGELOG.md). `build-manifest.json` records the pinned baseline.
`recovery-panel/` contains the initial tested panel and its startup instructions.

Repository: https://github.com/graemedench/PiCore_FM_Empowered

The recovery panel is a saved working foundation, not yet a complete SSD rebuild
installer. Music, passwords, machine backups and private server settings are
excluded. Upstream Sable assets and licensing remain with their original project.

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
