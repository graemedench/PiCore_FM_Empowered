# PiCore FM Empowered

A piCorePlayer port of the Empowered Quadify/Sable interface for FM4 hardware.

## OLED screen rotation — 10 October 2026

Settings → Display → Screen Rotation now offers **Normal** and **Upside-down**. The OLED flips immediately, remembers the selection, and uses the same orientation for the startup screen. Tested on Graeme’s unit in both orientations. Included in fresh installs and updates through Settings → System → Check / Apply Updates. This setting affects the OLED only.

## HDMI console fix — 10 October 2026

HDMI now selects the graphics console opened by Jivelite at startup and when enabled from Settings, rather than assuming a fixed console number. This fixes the observed boot-console/black-screen mismatch. A full reboot was tested on Graeme’s unit and the HDMI picture was confirmed. Apply the update and reboot. HDMI receiver metadata remains unfinished.

## Receiver controls and Bluetooth update — 10 October 2026

Settings → Audio now includes AirPlay On/Off and Bluetooth pairing discovery for three minutes. AirPlay follows the device hostname after restarting the receiver or rebooting. Built-in Bluetooth is enabled at boot, and local playback releases the audio device before the Bluetooth helper starts. Audio was tested after disconnecting and reconnecting an iPhone. Apply the update and reboot.

Receiver title/artist metadata and Bluetooth track timing are included. **Receiver artwork is experimental:** actual AirPlay artwork is preferred; otherwise exact album or recording/artist matches are attempted through MusicBrainz and Cover Art Archive. Missing covers remain possible. These lookups send track metadata to those services. **HDMI receiver display remains unfinished**, and pairing-screen/countdown cleanup is still outstanding. No DSP integration is included.

## 10 October 2026 update

- **AirPlay release back to Sable:** fixes a failed handover where TIDAL skipped tracks or BBC appeared to play without sound after AirPlay stopped. The local player is checked rather than trusting its PID file; a stale file is cleared safely, startup is retried, and Lyrion must confirm reconnection before local playback continues. Tested on Graeme's unit with AirPlay followed by TIDAL and BBC Radio 2. Apply the update and reboot to load the fix.

- **Sable configuration page:** open `http://YOUR-IP/sable-config.html` for all account links, web player, Favorites and device settings. Its links follow your device address. Find the URL in Settings → Network & Services → Service URLs.
- **Streaming Services:** a new top-level Settings group controls which services appear in the carousel. Show/hide preserves accounts and playback. BBC Sounds and TIDAL remain shown by default.
- **Beta Spotify and Beta Qobuz:** publisher plugins are installed for new and existing users; both start hidden. Spotify uses SpotOn and requires Premium; Qobuz needs a streaming subscription. Plugins load and account pages work, but authenticated playback has not yet been verified. Spotify profile lookup currently encountered HTTP 429 rate limiting. Remote sign-in can be completed by pasting the full loopback URL into SpotOn's Manual authorisation field.

Apply through Settings → System → Check / Apply Updates, then reboot. Existing plugins/accounts are preserved. See [updated menu map](MENU.md). Fresh-install coverage is included but still needs a clean-device test.

## 9 October 2026 update

**Boot feedback:** the OLED now shows FM4 and startup messages while piCorePlayer loads, accompanied by the original soft LED crossfade through LEDs 1, 3, 5 and 7. The red LED stays out of the animation. Both hand over to the normal panel when ready. This provides earlier feedback; it does not promise a shorter overall boot. Existing users: apply the update and reboot.

The latest update has been tested on Graeme's FM4. It includes:

- **Persistence fixes:** learned remote codes, Apple pairing and Power-on Volume survive panel restarts and reboot. Codes already lost on an older build need to be learned again.
- **BBC radio metadata:** Radio 2/4 shortcuts use BBC Sounds for programme details and artwork, with a direct-stream fallback. The OLED shows the station heading and programme title below.
- **HDMI Now Playing (Beta):** Settings → Display. Optional Jivelite tools are downloaded when enabled; English and automatic Now Playing are selected. Connect HDMI before enabling and reboot when requested. HDMI restarts can leave a blank display; reboot to recover. This feature still needs broader testing.

- **Grouped Settings:** Display, Audio, Remote, Network & Services, Library & Shortcuts, and System. Now Playing and Back stay at the top level.
- **Power-on Volume:** Settings → Audio → Power-on Volume. Turn the knob to choose Off or 0–100% in 1% steps, click to save, or hold to cancel. The chosen level applies at startup and when playback resumes after an hour paused or stopped. AirPlay and Bluetooth keep the sending device's volume control.
- **Display Timeouts:** Settings → Display → Display Timeouts. Adjust pause-to-clock, clock dimming and display-off in 30-second steps, up to two hours. Zero means Off. Turn to adjust, click to save, hold to cancel.
- **Expanded remote learning:** Settings → Remote → Learn Remote. Alongside navigation, play/pause, volume and mute, learn dedicated next/previous track, Stop, Repeat/shuffle mode, Save track, Now Playing and navigation Back. Existing learned keys are preserved.
- **Popup sizing:** Message headings and details scale to fit the OLED.

See the [full Settings menu map](MENU.md) and [button and remote controls](CONTROLS.md). Apply the update below, then reboot to load it. This tested update does not replace the remaining clean-install beta checks.

## Existing beta users: please rerun the installer

Updates on **8 October 2026** fix missing onboard Wi-Fi tools/firmware, improve
Wi-Fi connection feedback and
correct guest write permissions on the Music share. Please rerun this command
over SSH to apply the fixes, then reboot when prompted:

```sh
wget -O /tmp/fm4-bootstrap.sh https://raw.githubusercontent.com/graemedench/PiCore_FM_Empowered/main/bootstrap.sh && sudo sh /tmp/fm4-bootstrap.sh
```

Your existing settings, account sign-ins, music and Favorites are preserved.
**Backup cleanup is withdrawn pending reboot investigation.** The installer no
longer moves Python dependencies or install tools out of `/home/tc`. If you
already applied that cleanup, this update does not automatically undo it;
retain your original recovery backup and report any boot problem.
Keep Ethernet connected until Wi-Fi shows a working IP address. See the
[installation guide](INSTALL.md) if the clock needs syncing before downloading.

**Updated after 22:40 BST on 8 October 2026?** Future patches can now be applied
from the FM4 panel: **Settings → System → Check / Apply Updates → Apply latest patches? →
Yes, apply patches**. On success, choose **Reboot now** or **Later** with the encoder.
On older builds, Check / Apply Updates is directly under Settings. Builds without that option need the SSH command above once. Keep power
and internet connected while patching. This reapplies the latest patches; it
does not compare release version numbers.

**First tester beta: full scripted clean-install hardware validation is still pending.** Keep your working boot drive intact and use a freshly flashed piCorePlayer 11.1.0 64-bit USB drive on the tested Pi 4 FM4 hardware.

See [the illustrated installation guide](INSTALL.md). Download the installer directly in SSH:

Check [hardware and wiring assumptions](HARDWARE.md) before installing. DAC HAT
support is not yet validated; shutdown now uses GPIO26 / pin 37, which must be
checked against the particular HAT's reserved pins.

```sh
wget -O /tmp/fm4-bootstrap.sh https://raw.githubusercontent.com/graemedench/PiCore_FM_Empowered/main/bootstrap.sh && sudo sh /tmp/fm4-bootstrap.sh
```

After a successful phase, answer y at the reboot prompt; reconnect and run the same command. Allow about one minute for network time after reboot. If date is still wrong, use the force-sync step in the guide before downloading. Select Settings → Audio → Audio Output after installation. Accounts, music and personal playlists are not imported. The beta archive includes its Python/shell source and original project notices. The private working project and development logs are kept privately for now.

## What is included

- [INSTALL.md](INSTALL.md): Raspberry Pi Imager, 64-bit selection, screenshot walkthrough, time sync, installer and first-use checks.
- [HARDWARE.md](HARDWARE.md): wiring picture, physical/BCM pin table, current shutdown wiring and DAC HAT limits.
- [CONTROLS.md](CONTROLS.md): features and short/long press controls.
- [MENU.md](MENU.md): complete Settings menu map, numeric editors and remote learning.
- One beta bundle and its checksum; bootstrap and installer/runtime repair source alongside them. Only screenshots use an images folder.

## Credits

See [third-party credits and licence audit](THIRD-PARTY-NOTICES.md) for dependencies,
retained notices and outstanding permission checks. Our personal-use notice does
not override third-party licence rights.

We have made a good-faith effort to identify third-party components, preserve
their notices and respect their licence terms. Some checks remain open and are
listed in the audit; this is not a guarantee of complete licence compliance.
If you believe we have missed an attribution, permission or licence requirement,
please [open an issue](https://github.com/graemedench/PiCore_FM_Empowered/issues)
with the affected file or component and relevant terms. We will investigate
promptly and correct any confirmed omission or breach, including removing
affected material where necessary.

Based on [Matt's original Sable project](https://github.com/theshepherdmatt/sable) and [Graeme's Quadify Empowered modifications](https://github.com/graemedench/quadify_empowered), using [piCorePlayer](https://www.picoreplayer.org/) and [Lyrion Music Server](https://lyrion.org/).

Vibe coded by Graeme Dench with Alex (OpenAI Codex). Graeme directed the features, supplied the hardware and performed hands-on testing; Alex did the heavy lifting on implementation, integration, debugging and documentation. Matt's original design and development made this port possible; Matt has granted permission for this port. Original project rights and notices remain applicable.
