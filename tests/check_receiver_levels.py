"""Verify silence, separate stereo channels and equivalent 16/32-bit levels."""
import struct
from sable.pcp.receiver_levels import levels

assert levels(bytes(4096), 16) == [0, 0]
left16 = levels(struct.pack('<2048h', *([16384, 0]*1024)), 16)
left32 = levels(struct.pack('<2048i', *([1073741824, 0]*1024)), 32)
assert left16[0] > .85 and left16[1] == 0
assert left16 == left32
right = levels(struct.pack('<2048h', *([0, 16384]*1024)), 16)
assert right == left16[::-1]
print('Receiver stereo RMS checks passed')
