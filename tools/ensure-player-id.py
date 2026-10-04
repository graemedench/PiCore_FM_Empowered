"""Keep the player identity stable across Ethernet/Wi-Fi on this FM4.

Run as root, then restart Squeezelite and the panel, and perform pcp bu.
"""
import re
from pathlib import Path

config = Path('/usr/local/etc/pcp/pcp.cfg')
text = config.read_text()
match = re.search(r'^MAC_ADDRESS="([^"]*)"$', text, re.M)
if not match:
    raise SystemExit('Native MAC_ADDRESS setting missing')
identity = match[1] or Path('/sys/class/net/eth0/address').read_text().strip()
if not re.fullmatch(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}', identity):
    raise SystemExit('Invalid player identity')
text = text[:match.start()] + 'MAC_ADDRESS="' + identity + '"' + text[match.end():]
config.write_text(text)
print('Stable player ID:', identity)
