# PiCore FM Empowered

A piCorePlayer port of the Empowered Quadify/Sable interface for FM4 hardware.

**First tester beta: full scripted clean-install hardware validation is still pending.** Keep your working boot drive intact and use a freshly flashed piCorePlayer 11.1.0 64-bit USB drive on the tested Pi 4 FM4 hardware.

See [the illustrated installation guide](INSTALL.md). Download the installer directly in SSH:

Check [hardware and wiring assumptions](HARDWARE.md) before installing. DAC HAT
support is not yet validated; shutdown now uses GPIO26 / pin 37, which must be
checked against the particular HAT's reserved pins.

```sh
wget -O /tmp/fm4-bootstrap.sh https://raw.githubusercontent.com/graemedench/PiCore_FM_Empowered/main/bootstrap.sh && sudo sh /tmp/fm4-bootstrap.sh
```

After a successful phase, answer y at the reboot prompt; reconnect and run the same command. Allow about one minute for network time after reboot. If date is still wrong, use the force-sync step in the guide before downloading. Select Settings → Audio Output after installation. Accounts, music and personal playlists are not imported. The beta archive includes its Python/shell source and original project notices. The private working project and development logs are kept privately for now.

## What is included

- [INSTALL.md](INSTALL.md): Raspberry Pi Imager, 64-bit selection, screenshot walkthrough, time sync, installer and first-use checks.
- [HARDWARE.md](HARDWARE.md): wiring picture, physical/BCM pin table, current shutdown wiring and DAC HAT limits.
- [CONTROLS.md](CONTROLS.md): features and short/long press controls.
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
