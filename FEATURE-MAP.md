# Feature and verification map

| Existing Quadify feature | piCorePlayer route | Status |
| --- | --- | --- |
| SSD1322 display, encoder | Linux SPI + GPIO character API | Test panel verified by user |
| Same fonts/layout/carousel | Reuse patched Sable screens and assets | User confirmed appearance and snappy navigation |
| Panel / Performance / Cinema | Sable rendering + Lyrion state and artwork | Panel/Performance render verified; elapsed counter added |
| Library albums/artists/genres/folders | Lyrion JSON-RPC | Browse integration checks pass; filesystem folder browser still pending |
| Queue and playlist browsing | Lyrion tracks/playlists queries | Browse integration checks pass; filesystem folder browser still pending |
| Track playback/volume/transport | Player-specific commands | User confirmed improved buttons; local play/pause/stop-resume verified |
| Single/all/repeat/shuffle | Lyrion queue, shuffle/repeat modes | Live repeat/shuffle flag checks pass; button feedback pending |
| Save Track to FM4 Favorites | Persistent Lyrion playlist append | Saved track verified in Lyrion and persistent M3U |
| Radio presets and favourites | Direct PlayHLS streams + existing commercial URLs | BBC Radio 2/4 playback verified without sign-in; Greatest Hits and Absolute 80s playback verified |
| Buttons and boot LEDs | Original MCP23017 controller + smbus2 | Controller initializes; events received; physical LED check pending |
| Apple IR | gpio-ir overlay + existing profile | Hardware node absent; pending |
| Shutdown GPIO and Settings confirmation | Original shutdown screen + `pcp sd` | GPIO21 release/hold checks pass; user confirmed physical shutdown and wake-up work |
| USB fixed/variable, headphones variable | pCP Squeezelite output settings | Pending; preserve safe volume |
| Network status and Wi-Fi picker | Native piCorePlayer wpa_supplicant and DHCP | User join confirmed at 192.168.1.19; default communications address; reboot reconnection verified |
| TIDAL browsing/mixes/saving | Lyrion TIDAL plugin interface | Authenticated browse and My Mix 1 playback verified; eight mixes available |
| AirPlay 2 receiver | Native Shairport Sync 5 + nqptp and DAC handover | Discovery/playback counter/real stereo meter feed verified; user says looking good |
| Bluetooth receiver | Native BlueALSA Player mode + DAC handover | Controller powered after reboot; phone pairing/audio verification pending |
| Small Panel VU bars | Native Squeezelite shared-memory PCM | Real stereo levels verified; absent in Performance |
| Full-screen spectrum/VU modes | Squeezelite visualizer shared memory | Pending implementation |
| Storage display/library refresh | Persistent /mnt/sda2 and Lyrion rescan | Storage UI restored; manual and timed rescan connected |
| Music SMB share | Samba4 authenticated share | Windows read/write test passed |
| Repeatable SSD build | Pinned sources, installer, safe export | Pinned rebuild archive and helpers saved; complete installer pending |

Do not mark software initialization as physical hardware verification.

- Hold button 8: restored Save Shortcut picker for short/long assignments on 5–7; persistence check passed, user confirmed picker; Cancel regression passed. Tap 8 remains FM4 Favorites.


- CD playback/ripping: deferred hardware integration; no live optical drive detected, extraction tools absent.
- Named playlist recall: command-path check passes; live audio check pending.
- Shortcuts reset: restored with native backup.


