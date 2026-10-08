# FM4 beta installer — first clean-install test

This beta adds the FM4 interface to piCorePlayer. The installer has passed isolated
checks; the complete scripted hardware installation still needs Graeme's test.
Keep the working boot drive disconnected and intact.

Use the tested Raspberry Pi 4 with FM4 wiring and **piCorePlayer 11.1.0 64-bit**,
booted from USB. Other Pi models and SD-card layouts are not supported by this beta.
Download the base image from https://docs.picoreplayer.org/downloads/.

## Before installation

1. Flash the USB drive and boot over Ethernet.
2. Open the piCorePlayer web interface, set your own password and enable SSH.
3. Enter `pool.ntp.org` in the guided NTP step and choose **Set and Enable**.
   The installer also enables persistent NTP, preserves an explicit server setting
   and attempts a bounded time sync if the clock has reset. If the first HTTPS
   download cannot run because the date is wrong, first run
   `sudo busybox ntpd -n -q -p pool.ntp.org`, then retry the install command.
4. Enable Lyrion server mode, select your audio output and resize the partition.
   Use the largest size in the dropdown, then reboot. At least 2 GB free is required.
5. Check the date after reboot with `date` in SSH. Correct time is required for HTTPS.

## Download and install from GitHub

SSH into the fresh Pi as `tc`, then paste this command:

```sh
wget -O /tmp/fm4-bootstrap.sh https://raw.githubusercontent.com/graemedench/PiCore_FM_Empowered/main/bootstrap.sh && sudo sh /tmp/fm4-bootstrap.sh
```

The bootstrap downloads the beta over HTTPS, verifies its SHA-256 checksum and
keeps the bundle on the SSD at `/mnt/sda2/fm4-beta-installer`.

After preparation completes, reboot through the piCorePlayer web interface.
SSH back in and paste the **same command** again, or resume the downloaded copy:

```sh
cd /mnt/sda2/fm4-beta-installer
sudo sh install.sh --setup
```

After installation completes, reboot again. These explicit reboot steps let you
read the log and catch a failure during the first beta test. This is a test build,
not yet a verified end-to-end clean installation.

If a download fails, keep the same bundle and rerun the command. Completed package
steps are recorded on the SSD. The installer refuses an unrelated existing FM4
installation and preserves settings when rerun after completion. It does not format
storage or import any music, playlists, account tokens, Wi-Fi or network-backup passwords.

## First use

- On the FM4 OLED, open **Settings → Audio Output** and select your connected
  USB DAC, **Headphones**, or HDMI device. The list is detected from the devices
  attached to your Pi. Start a track and confirm you hear sound. If your DAC is
  missing, connect it and reopen the menu. This also sets the receiver audio route.
- Sign into TIDAL and BBC Sounds through Settings → Service URLs. The web player
  is `http://YOUR-PI-IP:9000/`; Favorites is `http://YOUR-PI-IP/fm4-favorites.html`.
- Button 7 resolves My Mix 1 / My Mix 2 against the signed-in TIDAL account.
- Favorites begins empty. Button 8 saves a track. **Add G's Mini Tidal List** is optional.
- The writable Music share is `\\YOUR-PI-IP\Music`. This beta uses guest access;
  some Windows 11 systems require client settings changes. It does not enable SMB1.
- No CD drive is needed. CD controls appear when a supported drive is attached.
- Beta remote learning supports the current 32-bit decoder, not every IR protocol.

## Browser addresses

Replace `YOUR-PI-IP` with the address shown in **Settings → Service URLs**
or on your piCorePlayer page. The OLED shows addresses using the current IP.
These are address templates; `YOUR-PI-IP` is not typed literally into the browser.

| Page | Address |
| --- | --- |
| piCorePlayer setup | `http://YOUR-PI-IP/` |
| FM4 web player | `http://YOUR-PI-IP:9000/` |
| TIDAL sign-in settings | `http://YOUR-PI-IP:9000/plugins/TIDAL/settings.html` |
| BBC Sounds sign-in settings | `http://YOUR-PI-IP:9000/plugins/BBCSounds/settings/basic.html` |
| FM4 Favorites | `http://YOUR-PI-IP/fm4-favorites.html` |
| Lyrion server settings | `http://YOUR-PI-IP:9000/settings/server/basic.html` |
| Windows Music share | `\\YOUR-PI-IP\Music` |

TIDAL settings provides the device-link sign-in instructions for your own account.
Use the local plugin addresses above; the current beta does not provide `/tidal`
or `/bbc` aliases.

## Acceptance checklist

- [ ] Both installer phases complete without manual repairs; retain terminal output.
- [ ] Clock remains correct after reboot; OLED, encoder and buttons work.
- [ ] Selected output plays music; play/pause, stop/resume, next/previous and repeat work.
- [ ] TIDAL/BBC authenticate using the tester's accounts; button 7 uses their mixes.
- [ ] Save a track, open Favorites, reboot and confirm it remains saved.
- [ ] Copy music through SMB and scan it; streaming albums do not appear as local files.
- [ ] AirPlay 2 and Bluetooth play, meters move and normal playback resumes afterwards.
- [ ] Start without a CD drive; if available test playback, FLAC/MP3 rip and named files.
- [ ] Check display modes, remote learning and shutdown/wake.
- [ ] Rerun the installer after completion: it must preserve settings and playlists.

Report which step failed and the terminal output. Do not overwrite the old working disk.

Based on Matt's original [Sable](https://github.com/theshepherdmatt/sable) and
[Quadify Empowered](https://github.com/graemedench/quadify_empowered). Graeme and
Alex (OpenAI Codex) vibe-coded this port, with Alex doing the implementation work
and Graeme guiding the design and testing the hardware.
