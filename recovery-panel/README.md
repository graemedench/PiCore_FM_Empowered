# Quadify on piCorePlayer: first display and encoder port

Tested on FM4-Reborn, Raspberry Pi 4, piCorePlayer 11.1.0 (64-bit).

The user confirmed the OLED image, encoder direction/position and click handling.
The final boot hook was verified after a clean reboot: the panel and local server
started automatically, and the panel selected the connected FM4-Reborn player.

The SSD1322 display is 256 × 64, SPI0/CE0, DC GPIO24, reset GPIO25.
The rotary encoder uses CLK GPIO13, DT GPIO5, switch GPIO6, with pull-ups.
This port uses Linux GPIO character devices rather than the older RPi.GPIO library.

## Controls

- Turn on Now Playing to change volume by 2 percentage points per detent.
- Press for the menu; turn to move; press to choose.
- Hold for 1.5 seconds, then release, to return to Now Playing.
- Encoder Test shows turn position and click count.
- Brightness allows adjustment with the knob.
- Clock shows time and date.
- Menu returns to Now Playing after 15 seconds without input.

The playback menu provides Play/Pause, Next Track and Previous Track.
Library, TIDAL and playlist browsing are not part of this first hardware port.

## Installed layout

`/home/tc/quadify-pcp` contains the panel, startup script, vendor libraries and font.
Python 3.11 is installed as a piCorePlayer extension. The private vendor directory
contains Pillow 12.3.0, gpiod 2.5.0, cbor2 6.1.5, luma.core 2.6.0 and luma.oled 3.16.0.
The installed font is a copy of this user's Windows Arial font; it is not included
in this source package. Supply a licensed `arial.ttf`, or change the font path.

piCorePlayer's `USER_COMMAND_1` startup setting runs `start.sh`. The panel connects
to the local Lyrion server at http://127.0.0.1:9000. Lyrion 9.1.1 stores its cache
and settings persistently under `/mnt/sda2/tce/slimserver`.

The original piCorePlayer configuration, bootlocal and extension list are saved
on the Pi as `*.before`. They may contain private settings and are not copied here.
piCorePlayer's backup preserves the panel and startup changes across reboot.

Logs: `/tmp/quadify-panel.log`; PID file: `/tmp/quadify-panel.pid`.
Only one panel process can claim its lock and hardware at a time.

For a manual start on the Pi: `sudo sh /home/tc/quadify-pcp/start.sh`.
For rotated installation, add `--rotate 180` to the startup command. If encoder
direction is reversed, add `--normal-encoder`.

Use piCorePlayer's normal shutdown action to stop the local music server cleanly.
