"""Reuse the verified Linux GPIO/SPI transport with Sable's display contract."""
import threading
from luma.oled.device import ssd1322
from luma.core.framebuffer import diff_to_previous
from .transport import Serial
from ..display.base import Display


class PiCoreDisplay(Display):
    def __init__(self, hardware=None, settings=None):
        super().__init__(256, 64)
        self._lock = threading.RLock()
        from .hardware_config import load
        self.serial = Serial(hardware or load())
        self.device = ssd1322(self.serial, width=256, height=64,
                              mode='RGB', framebuffer=diff_to_previous())
        self._previous = None
        from ..settings import Settings
        settings = settings or Settings('/home/tc/sable-pcp-stage/config/pcp-settings.json')
        self._rotation = int(settings.get('display', 'rotate', default=0) or 0)

    def present(self, image):
        with self._lock:
            raw = image.tobytes()
            if raw != self._previous:
                frame = image.rotate(180) if self._rotation == 180 else image
                self.device.display(frame.convert('RGB'))
                self._previous = raw

    def set_rotate(self, degrees):
        if degrees not in (0, 180):
            raise ValueError('Screen rotation must be 0 or 180 degrees')
        with self._lock:
            self._rotation = degrees
            self._previous = None

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
