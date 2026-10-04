"""Original Sable Panel with an elapsed clock and compact stereo level bars."""
from ..screens.modern import ModernScreen
import time
import math
from .visual_layouts import Cycle, needles, spectrum


class FM4Modern(ModernScreen):
    def __init__(self, app):
        super().__init__(app)
        self.cycle = Cycle()
        self._bands = [0.] * 24
        self._next_fft = 0
        self._last_theme = None
        self._ppm = [0.,0.]
        self._ppm_time = time.monotonic()
        self._peak_hold_until = [0.,0.]

    def interact(self):
        self.cycle.interact(time.monotonic())

    def render(self, canvas, draw, w, h):
        theme = self.app.settings.get('display', 'theme', default='panel')
        if theme not in ('panel_vu', 'panel_spectrum', 'panel_ppm'):
            self._last_theme = theme
            return super().render(canvas, draw, w, h)
        now = time.monotonic()
        if theme != self._last_theme:
            self.cycle.interact(now)
            self._last_theme = theme
        st = self.app.store.get()
        playing = st.status == 'play' and not self.app.soft_stopped()
        visual, overlay = self.cycle.update(now, playing, (st.uri, st.title, st.artist), notice_seconds=4 if theme in ('panel_vu','panel_ppm') else 2)
        if not visual:
            return self._render_panel(canvas, draw, w, h, st, not playing)
        if theme in ('panel_vu', 'panel_ppm'):
            if theme == 'panel_ppm':
                elapsed = min(.25, max(0., now-self._ppm_time))
                self._ppm_time = now
                for channel, value in enumerate(self.app.levels.peaks()):
                    if value >= self._ppm[channel]:
                        self._ppm[channel] = value
                        self._peak_hold_until[channel] = now + 1.0
                    elif now > self._peak_hold_until[channel]:
                        fall_time = min(elapsed, now-self._peak_hold_until[channel])
                        self._ppm[channel] = max(value, self._ppm[channel]-fall_time/2.8)
                values = self._ppm
            else:
                values = self.app.levels.read()
            needles(draw, w, h, [max(0., min(1., (v*50-14)/42)) for v in self.app.levels.read()] if theme == 'panel_ppm' else values, peaks=values if theme == 'panel_ppm' else None)
            if theme == 'panel_ppm':
                for channel in range(2):
                    cx,cy,radius=w*(channel+.5)/2,h+3,h-28
                    for tick in range(7):
                        angle=math.radians(150-20*tick)
                        self.text(canvas,(int(cx+radius*math.cos(angle))-2,int(cy-radius*math.sin(angle))-4),str(tick+1),self.app.fonts.get('mono',8),fill=120)
                self.text(canvas,(2,2),'PEAK',self.app.fonts.get('mono',8),fill=100)
            for x, label in ((w//4-9,'L'), (3*w//4-9,'R')):
                self.text(canvas, (x, 4), label, self.app.fonts.get('mono', 10), fill=160)
        else:
            if now >= self._next_fft:
                values = self.app.levels.spectrum()
                self._bands = [max(value, old-.12) for value, old in zip(values, self._bands)]
                self._next_fft = now+.05
            spectrum(draw, w, h, self._bands)
            for x, label in ((2,'60'), (w//2-12,'1k'), (w-24,'18k')):
                self.text(canvas, (x, h-9), label, self.app.fonts.get('mono', 8), fill=100)
        if overlay:
            draw.rectangle((0, 0, w-1, 25), fill=0)
            self.text(canvas, (w//2, 7), st.title[:36], self.app.fonts.get('sans', 11), fill=255, anchor='mm')
            self.text(canvas, (w//2, 20), st.artist[:42], self.app.fonts.get('sans', 9), fill=150, anchor='mm')

    def _drain_floor(self):
        pass  # Shared-memory producer never waits for a consumer.

    def _render_panel(self, canvas, draw, w, h, st, paused):
        super()._render_panel(canvas, draw, w, h, st, paused)
        elapsed = max(0, int(self.app.store.live_position_ms() / 1000))
        if st.duration_s:
            elapsed = min(elapsed, st.duration_s)
        counter = '%d:%02d' % divmod(elapsed, 60)
        if st.duration_s > 0:
            counter += ' / %d:%02d' % divmod(st.duration_s, 60)
        font = self.app.fonts.get('mono', 9)
        if paused:
            width = self.text_width(draw, counter, font)
            self.text(canvas, (w - width - 3, 44), counter, font, fill=115)
        else:
            self.text(canvas, (128, 34), counter, font, fill=145)

    def _render_level_bars(self, canvas, draw, tx, w, h):
        left, right = self.app.levels.read()
        for channel, level in enumerate((left, right)):
            y = 47 + channel * 8
            self.text(canvas, (tx, y-2), 'L' if channel == 0 else 'R',
                      self.app.fonts.get('mono', 8), fill=100)
            x0, x1 = tx + 12, w - 3
            draw.rectangle((x0, y, x1, y + 3), fill=25)
            end = int((x1-x0) * level)
            if end > 0:
                draw.rectangle((x0, y, x0 + end, y + 3), fill=170)
                draw.line((x0, y, x0 + end, y), fill=235)
