"""HS0038 GPIO27 edge decoding for the captured Apple aluminium remote."""
import threading

KEYS = {0xC0:'KEY_MENU', 0xFA:'KEY_PLAY', 0xA0:'KEY_PLAY', 0x3A:'KEY_ENTER',
        0x90:'KEY_LEFT', 0x60:'KEY_RIGHT', 0x30:'KEY_DOWN', 0x50:'KEY_UP'}


class Decoder:
    def __init__(self):
        self.fall = self.rise = None
        self.pulse = 0
        self.stage = 'idle'
        self.bits = []
        self.last = None
        self.last_time = 0

    def edge(self, high, now):
        if high:
            if self.fall is not None:
                self.pulse = now-self.fall
                if .007 < self.pulse < .011:
                    self.stage = 'header'
            self.rise = now
            return None
        self.fall = now
        if self.rise is None:
            return None
        space = now-self.rise
        if self.stage == 'header':
            if .0035 < space < .0055:
                self.bits, self.stage = [], 'bits'
            elif .0017 < space < .0028:
                self.stage = 'idle'
                if self.last and now-self.last_time < .25:
                    self.last_time = now
                    return self.last, True
            else:
                self.stage = 'idle'
        elif self.stage == 'bits':
            if not .00025 < self.pulse < .001:
                self.stage = 'idle'
                return None
            if .00025 < space < .001:
                self.bits.append(0)
            elif .0012 < space < .0022:
                self.bits.append(1)
            else:
                self.stage = 'idle'
                return None
            if len(self.bits) == 32:
                self.stage = 'idle'
                code = 0
                for bit in self.bits:
                    code = (code << 1) | bit
                # Preserve the captured remote's address and pairing ID.
                if code >> 16 == 0x77E1 and code & 255 == 0x5D:
                    key = KEYS.get((code >> 8) & 255)
                    if key:
                        self.last, self.last_time = key, now
                        return key, False
        return None


class Remote(threading.Thread):
    def __init__(self, callback, stop):
        super().__init__(daemon=True, name='fm4-ir')
        import gpiod
        from gpiod.line import Direction, Edge, Bias
        self.request = gpiod.request_lines('/dev/gpiochip0', consumer='fm4-ir',
            config={27:gpiod.LineSettings(direction=Direction.INPUT,
                    edge_detection=Edge.BOTH, bias=Bias.PULL_UP)}, event_buffer_size=256)
        self.callback, self.stop = callback, stop

    def run(self):
        import gpiod
        from datetime import timedelta
        decoder = Decoder()
        print('IR: Apple aluminium receiver listening on GPIO27')
        try:
            while not self.stop.is_set():
                if not self.request.wait_edge_events(timedelta(seconds=.2)):
                    continue
                for event in self.request.read_edge_events():
                    result = decoder.edge(event.event_type == gpiod.EdgeEvent.Type.RISING_EDGE,
                                          event.timestamp_ns / 1e9)
                    if result:
                        self.callback(*result)
        except Exception as exc:
            print('IR receiver stopped:', exc)
        finally:
            self.request.release()
