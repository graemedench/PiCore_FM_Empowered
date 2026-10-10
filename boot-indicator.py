"""Very-early front-panel LED boot indicator.

The MCP23017 LEDs are digital rather than PWM-capable.  A short, rapid
old/new alternation gives a soft-looking crossfade to the eye while Sable is
booting, then systemd stops this service before Sable owns the LEDs.
"""
import signal
import time

from .hardware import led_byte
from .pcp.hardware_config import load, mcp_pins
MCP = None

_STOP = False
# Human-facing LED positions 1, 3, 5 and 7.  Position 8 (the red LED) is
# deliberately excluded from the startup animation.
_BOOT_LEDS = (0, 2, 4, 6)
_FRAME_S = 0.012
_BLEND_STEPS = 8
_BLEND_REPEATS = 8
_HOLD_S = 0.28


def _stop(_signum, _frame):
    global _STOP
    _STOP = True


def _write(bus, mask):
    bus.write_byte_data(MCP.addr, MCP.GPIOA, led_byte(mask, MCP))


def _crossfade(bus, old_mask, new_mask):
    """Fake a PWM crossfade by proportionally alternating two LED masks."""
    for step in range(_BLEND_STEPS + 1):
        if _STOP:
            return
        new_frames = step
        old_frames = _BLEND_STEPS - step
        for _ in range(_BLEND_REPEATS):
            if old_frames:
                _write(bus, old_mask)
                time.sleep(_FRAME_S * old_frames / _BLEND_STEPS)
            if new_frames:
                _write(bus, new_mask)
                time.sleep(_FRAME_S * new_frames / _BLEND_STEPS)


def main():
    global _STOP, MCP
    hardware = load()
    if not hardware['mcp']['enabled']:
        return 0
    MCP = mcp_pins(hardware)
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    try:
        import smbus2
        bus = smbus2.SMBus(MCP.bus)
        bus.write_byte_data(MCP.addr, MCP.IODIRA, 0x00)
    except Exception as exc:
        print("boot-indicator: MCP unavailable:", exc)
        return 0
    try:
        old = 0
        while not _STOP:
            for bit in _BOOT_LEDS:
                if _STOP:
                    break
                new = 1 << bit
                _crossfade(bus, old, new)
                old = new
                time.sleep(_HOLD_S)
    except Exception as exc:
        print("boot-indicator: LED write failed:", exc)
    finally:
        try:
            _write(bus, 0)
            bus.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())