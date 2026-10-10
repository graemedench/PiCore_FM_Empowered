"""Sable piCore GPIO/SPI transport, using the shared validated wiring."""
import fcntl
import logging
import os
import struct
import threading
import time
import gpiod
from gpiod.line import Bias, Direction, Value
log = logging.getLogger('sable-hardware')

class Serial:
    """Luma transport using Linux SPI and gpiod instead of RPi.GPIO."""
    def __init__(self, hardware):
        oled = hardware["oled"]
        self.dc, self.rst = oled["dc"], oled["rst"]
        self.lines = gpiod.request_lines(hardware['gpiochip'], consumer='quadify-oled',
            config={(self.dc, self.rst): gpiod.LineSettings(direction=Direction.OUTPUT,
                                                  output_value=Value.INACTIVE)})
        self.fd = os.open('/dev/spidev%d.%d' % (oled['spi_port'], oled['spi_device']), os.O_RDWR)
        fcntl.ioctl(self.fd, 0x40016b01, struct.pack('B', 0))
        fcntl.ioctl(self.fd, 0x40016b03, struct.pack('B', 8))
        fcntl.ioctl(self.fd, 0x40046b04, struct.pack('I', 8000000))
        time.sleep(.3)
        self.lines.set_value(self.rst, Value.ACTIVE)
        time.sleep(.2)

    def command(self, *data):
        self.lines.set_value(self.dc, Value.INACTIVE)
        os.write(self.fd, bytes(data))

    def data(self, data):
        self.lines.set_value(self.dc, Value.ACTIVE)
        data = bytes(data)
        for pos in range(0, len(data), 4096):
            chunk = data[pos:pos + 4096]
            if os.write(self.fd, chunk) != len(chunk):
                raise OSError('Incomplete SPI write')

    def cleanup(self):
        if self.fd is not None:
            self.lines.set_value(self.rst, Value.INACTIVE)
            os.close(self.fd)
            self.fd = None
            self.lines.release()


class Decoder:
    TABLE = {1: 1, 7: 1, 14: 1, 8: 1, 2: -1, 4: -1, 13: -1, 11: -1}
    def __init__(self):
        self.previous = None
        self.acc = 0

    def feed(self, clk, dt):
        state = clk * 2 + dt
        if self.previous is not None:
            code = self.previous * 4 + state
            if self.previous != state and code not in self.TABLE:
                self.acc = 0
            else:
                self.acc += self.TABLE.get(code, 0)
        self.previous = state
        if state == 3:
            step = (self.acc >= 3) - (self.acc <= -3)
            self.acc = 0
            return step
        return 0


class Encoder(threading.Thread):
    def __init__(self, events, stop, hardware):
        super().__init__(daemon=True, name='encoder')
        self.events, self.stop, self.reverse = events, stop, hardware["rotary"]["reverse"]
        self.pins = [hardware["rotary"][key] for key in ("clk", "dt", "sw")]
        requested = tuple(pin for pin in self.pins if pin is not None)
        self.lines = gpiod.request_lines(hardware['gpiochip'], consumer='quadify-encoder',
            config={requested: gpiod.LineSettings(direction=Direction.INPUT,
                                                 bias=Bias.PULL_UP)})

    def run(self):
        decoder = Decoder()
        down = None
        raw = stable = False
        changed = time.monotonic()
        try:
            while not self.stop.is_set():
                clk, dt, sw = [v == Value.ACTIVE for v in [self.lines.get_value(pin) if pin is not None else Value.ACTIVE for pin in self.pins]]
                step = decoder.feed(int(clk), int(dt))
                if step:
                    self.events.put(('turn', -step if self.reverse else step))
                    log.info('Encoder detent %s', -step if self.reverse else step)
                now = time.monotonic()
                pressed = not sw
                if pressed != raw:
                    raw, changed = pressed, now
                if raw != stable and now - changed >= .025:
                    stable = raw
                    if stable:
                        down = now
                    elif down is not None:
                        kind = 'long' if now - down >= 1.5 else 'click'
                        self.events.put((kind, 0))
                        log.info('Encoder %s', kind)
                        down = None
                self.stop.wait(.001)
        except Exception:
            log.exception('Encoder input failed')
            self.events.put(('error', 'Encoder error'))
        finally:
            self.lines.release()


