"""Check release-to-arm, short taps and a single shutdown event per hold."""
from sable.pcp.power import HoldDetector

d = HoldDetector()
assert not d.update(True, 0)
assert not d.update(True, 10)  # A held input during startup must not shut down.
assert not d.update(False, 11)
assert not d.update(True, 12)
assert not d.update(False, 12.1)  # Short tap.
assert not d.update(True, 13)
assert not d.update(True, 14.9)
assert d.update(True, 15)
assert not d.update(True, 20)  # No repeated shutdown events.
assert not d.update(False, 21)
assert not d.update(True, 22)
assert d.update(True, 24)
print('Shutdown hold checks passed')
