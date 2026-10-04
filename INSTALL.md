# Fresh SSD installation — release candidate

This bundle installs the FM4 interface over an official piCorePlayer image. It
does not flash or partition a disk. The running FM4 is tested; installation on a
blank replacement SSD has not yet been tested. Keep the working boot drive as
the recovery route until a complete fresh-drive test passes.

## Prepare the new drive

1. Write the official **aarch64 piCorePlayer 11.1.0** image to the new SSD using
   an image writer. Check the selected drive before writing. Boot the Pi from
   that SSD, with the original boot drive disconnected.
2. Resize the installation using piCorePlayer's web controls. This installer
   currently requires the boot SSD's TCE at `/mnt/sda2/tce`; SD-card or other
   mount layouts are not supported yet. Connect Ethernet for initial setup.
3. Enable SSH, SPI and I2C using native configuration and reboot. Verify the
   OLED wiring against HARDWARE.md. Select the intended audio device and test
   normal playback at a comfortable volume.
4. Install and start local Lyrion from the native LMS page. Set music to
   `/mnt/sda2/Music` and playlists to `/mnt/sda2/Playlists` once created. If
   Lyrion's address restrictions are enabled, allow `127.0.0.1` for the panel.
5. Install native `python3.11` using `tce-load -wi python3.11` as user `tc`.

Official references: [Getting started](https://docs.picoreplayer.org/getting-started/),
[Standalone pCP](https://docs.picoreplayer.org/projects/standalone-pcp/),
[Samba setup](https://docs.picoreplayer.org/how-to/add_usb_hdd/).

## Build and install

On Windows, from a fresh project checkout, run `./build-stage.ps1`, then
`./build-installer.ps1`. Both preserve existing build directories rather than
overwriting them. Source repositories use HTTPS and pinned revisions.

Copy `fm4-installer.tar.gz` to `/tmp` on the new Pi using SCP. As `tc`:

```sh
mkdir -p /tmp/fm4-install
tar -xzf /tmp/fm4-installer.tar.gz -C /tmp/fm4-install
cd /tmp/fm4-install
python3.11 install.py --check
sudo python3.11 install.py --install
```

The installer checks its archive hash, requires local Lyrion and SPI, refuses
an existing FM4 installation, installs pinned Python dependencies and native
CD/encoding/font packages, creates music/playlists directories, derives the
player identity from native configuration, enables the visualizer and saves
startup through native backup. It does not copy passwords, music, accounts or
the old drive's private settings. Reboot manually after successful completion.

## Complete services

AirPlay 2/Bluetooth and Samba remain native setup steps in this first installer.
Install/enable receivers using piCorePlayer first. With playback stopped, run
the staged `setup-native-receivers.py`, then `setup-receiver-levels.py` as root.
The initial receiver helper targets `hw:CARD=AUDIO`; choose your actual output
in the FM4 Audio Output menu afterwards before testing receiver audio. Save
with `pcp bu`. Configure Samba using piCorePlayer's native page; the development
unit's temporary guest access is not automatically reproduced.

Install the TIDAL/BBC Sounds plugins through Lyrion, then sign into your own
accounts. Wi-Fi credentials and remote pairing are configured afresh on the
panel. CD metadata comes from MusicBrainz/Cover Art Archive when available;
unidentified discs retain usable generic track names.

## Acceptance and recovery

Check boot persistence, OLED/encoder/buttons, play-pause/stop-resume, full queue
skipping, each audio output, Wi-Fi reconnection, IR pairing, radio shortcuts,
AirPlay, Bluetooth, CD playback and named FLAC/MP3 ripping. Confirm a rip leaves
non-CD audio playing. Test Panel/VU/Twin Needle/Spectrum, five-second interaction return,
four-second VU/Twin Needle title and two-second spectrum title. Confirm shutdown/wake.

Installer backups of native settings are at `/home/tc/fm4-install-backup/`.
If installation fails, do not retry over partially installed files blindly.
Read its error, restore the saved pcp.cfg/onboot.lst/filetool.lst to their
original paths if needed, and run `pcp bu`. For a startup-only failure, clear
USER_COMMAND_1 in native settings and save. The working original drive remains
the simplest complete recovery. No secure-rip/AccurateRip verification or
calibrated broadcast-meter certification is claimed.
