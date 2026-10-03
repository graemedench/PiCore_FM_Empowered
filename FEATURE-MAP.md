# Feature and verification map

| Existing Quadify feature | piCorePlayer route | Status |
| --- | --- | --- |
| SSD1322 display, encoder | Linux SPI + GPIO character API | Test panel verified by user |
| Same fonts/layout/carousel | Reuse patched Sable screens and assets | Port in progress |
| Panel / Performance / Cinema | Sable rendering + Lyrion state and artwork | Port in progress |
| Library albums/artists/genres/folders | Lyrion JSON-RPC | Adapter in progress |
| Queue and playlist browsing | Lyrion tracks/playlists queries | Adapter in progress |
| Track playback/volume/transport | Player-specific commands | Basic panel connected; full port pending |
| Single/all/repeat/shuffle | Lyrion queue, shuffle/repeat modes | Pending full-port verification |
| Save Track to FM4 Favorites | Persistent Lyrion playlist append | Implemented; live save verification pending |
| Radio presets and favourites | Sable URLs + Lyrion favourites | Pending verification |
| Buttons and boot LEDs | Original MCP23017 controller + smbus2 | I²C enablement pending |
| Apple IR | gpio-ir overlay + existing profile | Hardware node absent; pending |
| Shutdown GPIO and Settings confirmation | Original shutdown screen + `pcp sd` | Pending; use latest GPIO21 map |
| USB fixed/variable, headphones variable | pCP Squeezelite output settings | Pending; preserve safe volume |
| Network status and Wi-Fi picker | Native piCorePlayer configuration | Wired status available; Wi-Fi port pending |
| TIDAL browsing/mixes/saving | Lyrion TIDAL plugin interface | Plugin state/API not yet verified |
| Spectrum/VU modes | Squeezelite visualizer shared memory | Pending feasibility check |
| Storage display/library refresh | Persistent /mnt/sda2 and Lyrion rescan | Paths verified; UI pending |
| Music SMB share | Samba4 authenticated share | Windows read/write test passed |
| Repeatable SSD build | Pinned sources, installer, safe export | Build manifest/log started |

Do not mark software initialization as physical hardware verification.
