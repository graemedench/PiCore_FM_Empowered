# Third-party credits and distribution audit

Audit date: 8 October 2026. This is a component inventory and recorded findings,
not a blanket declaration that every asset has cleared legal review.

We have made a good-faith effort to identify components, retain notices and
respect applicable terms. If an attribution, permission or licence requirement
has been missed, please [report it](https://github.com/graemedench/PiCore_FM_Empowered/issues)
with the affected file/component and relevant terms. We will investigate promptly
and correct any confirmed omission or breach, including removing affected
material where necessary. This statement does not replace licence obligations
or resolve the outstanding checks recorded below.

## Scope of our notices

Any FM4/Quadify Empowered personal-use restriction applies only to contributions
whose authors can grant those terms. It does **not** replace or restrict the
licences of independent third-party software, fonts or assets. Original notices
and third-party licence rights remain applicable. No endorsement by the projects
or service brands below is implied.

## Code and assets distributed in our beta archive

- [Sable](https://github.com/theshepherdmatt/sable), Matt and contributors:
  modified Python source and panel artwork. The retained upstream README is
  included. No general licence file was found in the source snapshot used for
  this port. Graeme reports permission from Matt for the port; the exact scope
  of redistribution of code and assets is confirmed by Graeme as the intended
  permission scope; the written permission record should be kept privately.
  Do not assume that a public GitHub repository grants unrestricted reuse.
- [Quadify Empowered](https://github.com/graemedench/quadify_empowered), Graeme
  and contributors: port behaviour and original contributions. The original
  personal-use notice is retained with the scope clarification above.
- Graeme/Alex's FM4 adapter, installer, wiring SVG and documentation accompany
  the modified panel source. The installer does not distribute dependency wheels,
  compiled native packages, commercial music, album-cover caches or credentials.
- Existing Sable menu PNGs, including service-brand icons and `vuscreen.png`,
  are retained upstream assets. Their individual creator/provenance is not
  established by a separate asset licence in the snapshot. Matt's permission
  must cover assets he owns; third-party logos are not claimed as ours.
- Setup screenshots were supplied by Graeme and depict piCorePlayer. The NTP
  annotated example was edited with OpenAI's image tool. piCorePlayer interface
  names and artwork remain attributable to that project.

## Python dependencies downloaded on the device

These are installed from publisher wheels by pip; we do not repackage the wheels
in the beta archive. Exact-version PyPI metadata and representative publisher
wheels were inspected. All six contained licence files under `.dist-info`;
the installer retains these directories. The inspected binary wheels were
aarch64 examples, not a claim of testing every platform/Python variant.

| Component | Version | Declared licence | Publisher |
| --- | --- | --- | --- |
| Pillow | 12.3.0 | MIT-CMU | [Pillow](https://pypi.org/project/Pillow/12.3.0/) |
| gpiod | 2.5.0 | LGPL-2.1-or-later | [gpiod](https://pypi.org/project/gpiod/2.5.0/) |
| cbor2 | 6.1.5 | MIT | [cbor2](https://pypi.org/project/cbor2/6.1.5/) |
| luma.core | 2.6.0 | MIT | [Richard Hull and contributors](https://pypi.org/project/luma.core/2.6.0/) |
| luma.oled | 3.16.0 | MIT | [Richard Hull and contributors](https://pypi.org/project/luma.oled/3.16.0/) |
| smbus2 | 0.6.0 | MIT | [smbus2](https://pypi.org/project/smbus2/0.6.0/) |

pip may also resolve transitive dependencies. Their installed metadata/notices
must be retained. This audit is not an exhaustive inventory of those packages.

## Lyrion plugins downloaded from their publishers

The installer downloads the original archives and verifies their pinned SHA-1
values. All seven exact archives were inspected; source headers and bundled
notices are preserved by extraction. We do not bundle these archives or modify
their plugin code. Per-file terms can differ from a project's main licence.

| Plugin / publisher | Version | Finding in downloaded archive |
| --- | --- | --- |
| [RadioNowPlaying / Paul Webster](http://radionowplaying.com/) | 0.0.56 | Main plugin GPL-3.0-or-later; embedded CBOR modules use Perl terms |
| [BBC Sounds / ExpectingToFly](https://github.com/expectingtofly/LMS_BBC_Sounds_Plugin) | 2.54.8 | Inspected source headers GPL-3.0-or-later |
| [RadioNet / bpa](https://bpa-code.github.io/bpaplugins/) | 3.4 | Main plugin header says GPLv2 |
| [Material Skin / Craig Drummond](https://github.com/CDrummond/lms-material) | 6.4.11 | Main plugin MIT; Search.pm has GPL header; bundled font LICENSES retained |
| [TIDAL / Michael Herger](https://github.com/michaelherger/lms-plugin-tidal) | 1.8.1 | No explicit licence file or licence header established in the inspected archive; unresolved |
| [MusicArtistInfo / Michael Herger](https://www.herger.net/) | 1.30.1 | No explicit licence file or licence header established in the inspected archive; unresolved |
| [PlayHLS / bpa](https://bpa-code.github.io/bpaplugins/) | 2.12 | GPLv2 / GPL-2.0-or-later headers in inspected main modules; other embedded modules have separate terms |

## Native packages and services

Installed by piCorePlayer/Tiny Core package tools rather than redistributed in
our archive: [piCorePlayer](https://www.picoreplayer.org/),
[Tiny Core Linux](http://tinycorelinux.net/),
[Lyrion Music Server](https://github.com/LMS-Community/slimserver),
[Squeezelite](https://github.com/ralph-irving/squeezelite),
[Shairport Sync](https://github.com/mikebrady/shairport-sync), Bluetooth support,
[Samba](https://www.samba.org/), [FFmpeg](https://ffmpeg.org/),
[LAME](https://lame.sourceforge.io/) and libarchive.
Those packages retain their own terms; build options can affect native licences.
The FM4 shared-memory reader uses Squeezelite's `output_vis.c` format as an
interface reference, with independently written Python implementation; the
Squeezelite C source/binary is not included in our beta archive.

The DejaVu font is downloaded from the native package, then copied unchanged
to the recovery panel under the legacy filename `arial.ttf` (it is **not**
Microsoft Arial). The full [DejaVu licence](https://dejavu-fonts.github.io/License.html)
is supplied in `DEJAVU-LICENSE.txt` and beside the installed recovery-panel copy.
It covers Bitstream and Arev notices and public-domain DejaVu changes.

[MusicBrainz](https://musicbrainz.org/) and
[Cover Art Archive](https://coverartarchive.org/) provide disc metadata and
artwork when available. Retrieved images retain their owners' rights; we do
not distribute a cover-art collection or grant reuse rights in those images.

## Outstanding release checks

1. Retain Matt's written permission covering distributed modified code/artwork,
   and resolve any third-party artwork he cannot license.
2. Confirm publisher terms for TIDAL/MusicArtistInfo and provenance of unlabelled
   upstream assets; absence of a licence file is not permission to relicense.
3. Before distributing a prebuilt disk image or vendored dependency binaries,
   audit the complete installed dependency tree and any source-offer obligations.
   This installer audit does not approve that different distribution format.

The concrete packaging fixes from this audit are the DejaVu notice and the
clarification that our personal-use terms do not override third-party licences.
