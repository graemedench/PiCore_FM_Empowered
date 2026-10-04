# Feature and verification map

| Existing Quadify feature | piCorePlayer route | Status |
| --- | --- | --- |
| SSD1322 display, encoder | Linux SPI + GPIO character API | Test panel verified by user |
| Same fonts/layout/carousel | Reuse patched Sable screens and assets | User confirmed appearance and snappy navigation |
| Panel / Performance / Cinema | Sable rendering + Lyrion state and artwork | Panel/Performance render verified; elapsed counter added |
| Library albums/artists/genres/folders | Lyrion JSON-RPC | Adapter in progress |
| Queue and playlist browsing | Lyrion tracks/playlists queries | Adapter in progress |
| Track playback/volume/transport | Player-specific commands | Basic panel connected; full port pending |
| Single/all/repeat/shuffle | Lyrion queue, shuffle/repeat modes | Live repeat/shuffle flag checks pass; button feedback pending |
| Save Track to FM4 Favorites | Persistent Lyrion playlist append | Saved track verified in Lyrion and persistent M3U |
| Radio presets and favourites | Direct PlayHLS streams + existing commercial URLs | BBC Radio 2/4 playback verified without sign-in; commercial streams pending |
| Buttons and boot LEDs | Original MCP23017 controller + smbus2 | Controller initializes; events received; physical LED check pending |
| Apple IR | gpio-ir overlay + existing profile | Hardware node absent; pending |
| Shutdown GPIO and Settings confirmation | Original shutdown screen + `pcp sd` | GPIO21 installed; release/hold logic checked; physical poweroff pending |
| USB fixed/variable, headphones variable | pCP Squeezelite output settings | Pending; preserve safe volume |
| Network status and Wi-Fi picker | Native piCorePlayer wpa_supplicant and DHCP | User join confirmed at 192.168.1.19; default communications address; reboot pending |
| TIDAL browsing/mixes/saving | Lyrion TIDAL plugin interface | Authenticated browse and My Mix 1 playback verified; eight mixes available |
| AirPlay 2 receiver | Native Shairport Sync 5 + nqptp and DAC handover | Discovery/playback counter/real stereo meter feed verified; user says looking good |
| Bluetooth receiver | Native BlueALSA Player mode + DAC handover | Controller powered after reboot; phone pairing/audio verification pending |
| Small Panel VU bars | Native Squeezelite shared-memory PCM | Real stereo levels verified; absent in Performance |
| Full-screen spectrum/VU modes | Squeezelite visualizer shared memory | Pending implementation |
| Storage display/library refresh | Persistent /mnt/sda2 and Lyrion rescan | Paths verified; UI pending |
| Music SMB share | Samba4 authenticated share | Windows read/write test passed |
| Repeatable SSD build | Pinned sources, installer, safe export | Build manifest/log started |

Do not mark software initialization as physical hardware verification.
