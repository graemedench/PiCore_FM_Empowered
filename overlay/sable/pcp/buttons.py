"""FM4 matrix scan with per-key debounce and prompt short-tap detection."""
import time
from ..inputs.buttons import ButtonsLeds, _BUTTON_MAP, _HOLD_BUTTONS


class FM4Buttons(ButtonsLeds):
    def _scan_loop(self):
        raw = [[1, 1] for _ in range(4)]
        changed = [[0.0, 0.0] for _ in range(4)]
        while self._running:
            matrix = self._read_matrix()
            now = time.monotonic()
            for row in range(4):
                for col in range(2):
                    value = matrix[row][col]
                    if value != raw[row][col]:
                        raw[row][col], changed[row][col] = value, now
                    previous = self._prev[row][col]
                    if now - changed[row][col] < .020:
                        value = previous
                    button = _BUTTON_MAP[row][col]
                    if button in _HOLD_BUTTONS:
                        self._scan_hold_button(button, value == 0, previous == 0, now)
                    elif value == 0 and previous == 1:
                        self._on_press(button)
                    self._prev[row][col] = value
            time.sleep(.005)
