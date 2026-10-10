"""Configurable active-low GPIO26 shutdown; require release before arming."""
import threading
import time


class HoldDetector:
    def __init__(self, seconds=2):
        self.seconds, self.since, self.armed, self.fired = seconds, None, False, False

    def update(self, pressed, now):
        if not pressed:
            self.armed, self.since, self.fired = True, None, False
        elif self.armed and not self.fired:
            if self.since is None:
                self.since = now
            elif now - self.since >= self.seconds:
                self.fired = True
                return True
        return False


class PowerButton(threading.Thread):
    def __init__(self, dispatch, stop, gpio=26, gpiochip='/dev/gpiochip0'):
        super().__init__(daemon=True, name='fm4-power')
        import gpiod
        from gpiod.line import Bias, Direction
        self.gpio = gpio
        self.request = gpiod.request_lines(gpiochip, consumer='fm4-power',
            config={gpio: gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP)})
        self.dispatch, self.stop = dispatch, stop

    def run(self):
        from gpiod.line import Value
        detector = HoldDetector()
        try:
            while not self.stop.is_set():
                if detector.update(self.request.get_value(self.gpio) == Value.INACTIVE,
                                   time.monotonic()):
                    self.dispatch()
                self.stop.wait(.025)
        finally:
            self.request.release()
