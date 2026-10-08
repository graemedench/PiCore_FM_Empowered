# PiCore FM Empowered

A piCorePlayer port of the Empowered Quadify/Sable interface for FM4 hardware.

**First tester beta: full scripted clean-install hardware validation is still pending.** Keep your working boot drive intact and use a freshly flashed piCorePlayer 11.1.0 64-bit USB drive on the tested Pi 4 FM4 hardware.

See [the beta installation guide](BETA-INSTALL.md). Download the installer directly in SSH:

```sh
wget -O /tmp/fm4-bootstrap.sh https://raw.githubusercontent.com/graemedench/PiCore_FM_Empowered/main/bootstrap.sh && sudo sh /tmp/fm4-bootstrap.sh
```

Preparation requires a reboot; rerun the same command after reconnecting. Select Settings → Audio Output after installation. Accounts, music and personal playlists are not imported. The beta archive includes its Python/shell source and original project notices. The private working project and development logs remain in OneDrive.

## Credits

Based on [Matt's original Sable project](https://github.com/theshepherdmatt/sable) and [Quadify Empowered](https://github.com/graemedench/quadify_empowered), using [piCorePlayer](https://www.picoreplayer.org/) and [Lyrion Music Server](https://lyrion.org/).

Vibe coded by Graeme Dench with Alex (OpenAI Codex). Graeme directed the features, supplied the hardware and performed hands-on testing; Alex did the heavy lifting on implementation, integration, debugging and documentation. Matt's original design and development made this port possible; Graeme has received Matt's permission for the port. Original project rights and notices remain applicable.
