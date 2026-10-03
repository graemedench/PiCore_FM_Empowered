"""Reuse the verified Linux GPIO/SPI transport with Sable's display contract."""
import threading
from luma.oled.device import ssd1322
from luma.core.framebuffer import diff_to_previous
from panel import Serial
from ..display.base import Display


class PiCoreDisplay(Display):
    def __init__(self):
        super().__init__(256, 64)
        self._lock = threading.RLock()
        self.serial = Serial()
        self.device = ssd1322(self.serial, width=256, height=64,
                              mode='RGB', framebuffer=diff_to_previous())
        self._previous = None

    def present(self, image):
        with self._lock:
            raw = image.tobytes()
            if raw != self._previous:
                self.device.display(image.convert('RGB'))
                self._previous = raw

    def set_contrast(self, value):
        with self._lock:
            self.device.contrast(value)

    def sleep(self):
        with self._lock:
            self.device.hide()

    def wake(self):
        with self._lock:
            self.device.show()
            self._previous = None

    def clear(self):
        self.present(self.blank_canvas())

    def force_full_redraw(self):
        self._previous = None

    def cleanup(self):
        with self._lock:
            self.device.cleanup()
