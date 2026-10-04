"""Add an ALSA audio copy for meters while retaining direct USB DAC playback."""
from pathlib import Path
import re

path = Path('/home/tc/.asoundrc')
text = path.read_text() if path.exists() else ''
if 'pcm.fm4_receiver' not in text:
    text += '''
pcm.fm4_receiver {
    type file
    slave.pcm "hw:CARD=AUDIO"
    file "|/bin/sh /home/tc/sable-pcp-stage/receiver-levels.sh %b %r"
    format "raw"
}
'''
    path.write_text(text)
text = text.replace('receiver-levels.sh %b\"', 'receiver-levels.sh %b %r\"')
path.write_text(text)
# Root runs the receivers. Include tc's configuration without changing native ALSA.
root = Path('/root/.asoundrc')
root_text = root.read_text() if root.exists() else ''
include = '</home/tc/.asoundrc>'
if include not in root_text:
    root.write_text(root_text + '\n' + include + '\n')
cfg = Path('/usr/local/etc/pcp/pcp.cfg')
text = cfg.read_text()
for key in ('SHAIRPORT_OUT', 'BT_OUT_DEVICE'):
    text = re.sub(r'^'+key+r'=.*$', key+'="fm4_receiver"', text, flags=re.M)
cfg.write_text(text)
files = Path('/opt/.filetool.lst')
entries = files.read_text().splitlines()
if 'root/.asoundrc' not in entries:
    entries.append('root/.asoundrc')
files.write_text('\n'.join(entries)+'\n')
print('Receiver meter audio copy configured')
