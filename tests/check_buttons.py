"""Check quick taps, contact bounce and long holds without touching hardware."""
import threading
from unittest.mock import patch
from sable.pcp.buttons import FM4Buttons

def exercise(button, pressed, duration):
    scanner = FM4Buttons.__new__(FM4Buttons)
    scanner._running = True
    scanner._prev = [[1, 1] for _ in range(4)]
    scanner._hold_start, scanner._hold_fired = {}, set()
    scanner._lock = threading.Lock()
    scanner._ephemeral_led = 0
    scanner._write_leds_locked = lambda value: None
    scanner._desired_led = lambda: 0
    scanner._get_hold_action = lambda button: ('soft_stop', None)
    actions = []
    scanner._on_press = lambda button, override=None: actions.append((button, override))
    clock = [0.0]
    def read():
        matrix = [[1, 1] for _ in range(4)]
        matrix[(button-1)//2][(button-1)%2] = 0 if pressed(clock[0]) else 1
        return matrix
    scanner._read_matrix = read
    def sleep(_):
        clock[0] += .015  # two 5ms column settles plus 5ms scan sleep
        if clock[0] > duration:
            scanner._running = False
    with patch('sable.pcp.buttons.time.monotonic', lambda: clock[0]), \
         patch('sable.pcp.buttons.time.sleep', sleep):
        scanner._scan_loop()
    return actions

assert exercise(1, lambda t: .015 <= t < .075, .15) == [(1, None)]
assert exercise(2, lambda t: .015 <= t < .020 or .030 <= t < .10, .2) == [(2, None)]
assert exercise(1, lambda t: .015 <= t < 1.4, 1.5) == [(1, ('soft_stop', None))]
print('PASS: 60ms play tap, bouncing mode button, one long-hold action without tap')
