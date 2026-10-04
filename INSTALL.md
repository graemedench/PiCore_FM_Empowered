# Fresh SSD installation - release candidate

This installs the FM4 interface over an official piCorePlayer image. It never
flashes or partitions a disk. The working FM4 is tested; the expanded installer
has passed isolated prepare/restore tests, but still needs a complete clean-SSD
hardware acceptance test. Keep the original boot drive until that passes.

## Downloads and sources

- [Official piCorePlayer image downloads](https://docs.picoreplayer.org/downloads/): use 11.1.0 **64-bit/aarch64** for this tested Pi 4 build.
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
- [PiCore FM Empowered](https://github.com/graemedench/PiCore_FM_Empowered)
- [Matt's original Sable](https://github.com/theshepherdmatt/sable)
- [Quadify Empowered, the earlier Volumio enhancement](https://github.com/graemedench/quadify_empowered)
- [FM4 installer source](installer/install.py), [bootstrap](installer/install.sh) and [bundle builder](build-installer.ps1)

The base image provides the operating system; this project's installer adds
FM4 functionality. Generated archives are build products, excluded from Git.
Graeme's local backup includes `fm4-installer.tar.gz`. Do not run the old
Volumio installer on piCorePlayer.

## Prepare the SSD and build the bundle

1. Write the official 64-bit image to the replacement SSD. Check the selected
   disk before writing; leave the working drive disconnected and intact.
2. Boot the Pi from the new SSD over **Ethernet**. Set a fresh system password,
   enable SSH and resize the installation using the native guided setup. The
   supported layout is `/dev/sda2` mounted at `/mnt/sda2`, with its TCE directory
   at `/mnt/sda2/tce`. Other disk layouts are refused. No Wi-Fi setup is imported.
3. Check the wiring against [HARDWARE.md](HARDWARE.md). The installer will enable
   SPI/I2C and reboot preparation; IR uses GPIO4 on this unit.
4. On Windows, with Git, PowerShell and tar available, use a fresh checkout:

```powershell
git clone https://github.com/graemedench/PiCore_FM_Empowered.git
cd PiCore_FM_Empowered
./build-stage.ps1
./build-installer.ps1
scp fm4-installer.tar.gz tc@YOUR-NEW-PI-IP:/tmp/
```

Sources are pinned and fetched over HTTPS. Existing build/bundle directories
are preserved; use a fresh checkout for a new build.

## Install in two phases

SSH to the new Pi. Extract to the persistent SSD because `/tmp` disappears on
reboot:

```sh
sudo mkdir -p /mnt/sda2/fm4-installer
sudo tar -xzf /tmp/fm4-installer.tar.gz -C /mnt/sda2/fm4-installer
cd /mnt/sda2/fm4-installer
sudo sh install.sh --prepare
```

Preparation installs Python if needed, installs native Lyrion/Samba/AirPlay/
Bluetooth packages through piCorePlayer's package loader, saves the local-server
setting, backs up boot configuration and enables SPI/I2C. It does not change
Wi-Fi or format storage. **Reboot using the native piCorePlayer web page**, then
return to the persistent bundle:

```sh
cd /mnt/sda2/fm4-installer
sh install.sh --check
sudo sh install.sh --install
```

Restore validates the archive and prerequisites, installs runtime/fonts/CD
encoders, imports [the reusable profile](fm4-profile.json), creates empty Music
and Playlists directories, sets Lyrion paths and plugin preferences, configures
receivers/real meter routing and the Music share, enables startup and performs
native backup. It refuses existing FM4 directories. Reboot once more using the
native web page, then run the acceptance checklist.

## What comes back automatically

- Captured front-panel buttons, short/long shortcuts, clock/idle/brightness and
  display preferences, playback mode, refresh interval and Apple remote identity.
- Local Lyrion and a stable player identity derived from the new Pi, with
  Squeezelite directed to localhost rather than another network server.
- Headphones output matching the captured build, AirPlay 2/Bluetooth configuration,
  real audio-meter routing and native startup/persistence.
- Music and Playlists paths; an empty FM4 Favorites playlist is created by the
  first Save action. The Favorites web page is regenerated at startup.
- Pinned TIDAL, BBC Sounds, Material Skin, PlayHLS and the supplementary radio/
  artwork plugins listed in [fm4-plugins.json](fm4-plugins.json).
- The captured **password-free Music share**. Anyone on the reachable local
  network can read/write it, matching the current development unit. Change
  `guest_music_share`/the share setup before installation if you need another
  policy; authenticated sharing is not automated in this candidate.

Wi-Fi, system/account passwords, streaming tokens, music, existing playlist
contents, Bluetooth pairings and old machine MAC/IP addresses are excluded.
Sign into TIDAL and BBC Sounds yourself. Captured TIDAL mix shortcuts belong to
Graeme's account; another account should reassign button 7. Music and existing
playlists can be restored separately; this installer does not copy them.

The MusicArtistInfo/Material versions follow the pinned manifest, which can be
slightly newer than the live development unit. Plugins are downloaded from their
publishers and checked against the official repository checksums. RadioNowPlaying
uses its publisher's HTTP download; all Git/source transfers remain HTTPS.

## Acceptance and recovery

Check reboot persistence, OLED/encoder/buttons, play/pause/stop/resume and queue
skipping; audio outputs; radio/TIDAL/BBC after sign-in; AirPlay; Bluetooth pairing
and sound; IR; shutdown/wake; CD playback and named FLAC/MP3 ripping. Confirm
non-CD audio can keep playing during ripping. Test the display modes and the
Favorites page from another browser. Wi-Fi can be configured later if required.

The native pCP page is `http://NEW-IP/`; Lyrion is `http://NEW-IP:9000/`;
Favorites is `http://NEW-IP/fm4-favorites.html`. Panel Service URLs displays the
current address when opened.

Backups are under `/home/tc/fm4-install-backup/`. On failure, preserve the error
and inspect the saved settings before retrying. The installer intentionally
refuses a partially installed FM4 tree; use a fresh image or an inspected manual
recovery rather than deleting directories blindly. Restore saved native config,
onboot/filetool lists and boot config to their original locations if needed,
then save with `pcp bu`. For a startup-only failure, clear USER_COMMAND_1 in
native settings and save. The original working drive is the complete fallback.

Official references: [Getting started](https://docs.picoreplayer.org/getting-started/),
[Standalone pCP](https://docs.picoreplayer.org/projects/standalone-pcp/),
[Samba setup](https://docs.picoreplayer.org/how-to/add_usb_hdd/).
No secure-rip/AccurateRip or calibrated meter certification is claimed.
