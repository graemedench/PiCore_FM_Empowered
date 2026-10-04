"""HS0038 GPIO4 edge decoding for the captured Apple aluminium remote."""
import threading

KEYS = {0xC0:'KEY_MENU', 0xFA:'KEY_PLAY', 0xA0:'KEY_PLAY', 0x3A:'KEY_ENTER',
        0x90:'KEY_LEFT', 0x60:'KEY_RIGHT', 0x30:'KEY_DOWN', 0x50:'KEY_UP'}


class Decoder:
    def __init__(self, pair_id=0x15):
        self.pair_id = pair_id
        self.fall = self.rise = None
        self.pulse = 0
        self.stage = 'idle'
        self.bits = []
        self.last = None
        self.last_time = 0
        self.last_code = None

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
                self.last_code = code
                # Preserve the captured remote's address and pairing ID.
                if code >> 16 == 0x77E1 and code & 255 == self.pair_id:
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
            config={4:gpiod.LineSettings(direction=Direction.INPUT,
                    edge_detection=Edge.BOTH, bias=Bias.PULL_UP)}, event_buffer_size=256)
        self.callback, self.stop = callback, stop

    def run(self):
        import gpiod
        from datetime import timedelta
        decoder = Decoder()
        from pathlib import Path
        import json, time
        recent = []
        edge_count = 0
        published = 0
        print('IR: Apple aluminium receiver listening on GPIO4')
        try:
            while not self.stop.is_set():
                if not self.request.wait_edge_events(timedelta(seconds=.2)):
                    continue
                for event in self.request.read_edge_events():
                    edge_count += 1
                    if Path('/tmp/fm4-ir-capture').exists():
                        recent.append((event.event_type.name, event.timestamp_ns))
                        recent = recent[-160:]
                    result = decoder.edge(event.event_type == gpiod.EdgeEvent.Type.RISING_EDGE,
                                          event.timestamp_ns / 1e9)
                    if result:
                        print('IR key:', result[0], 'repeat' if result[1] else 'press')
                        self.callback(*result)
                if recent and time.monotonic()-published > .2:
                    published = time.monotonic()
                    Path('/tmp/fm4-ir-capture.json').write_text(json.dumps(dict(edges=edge_count, code=decoder.last_code, samples=recent)))
        except Exception as exc:
            print('IR receiver stopped:', exc)
        finally:
            self.request.release()
