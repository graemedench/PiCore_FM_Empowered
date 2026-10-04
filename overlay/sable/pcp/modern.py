"""Original Sable Panel with an elapsed clock and compact stereo level bars."""
from ..screens.modern import ModernScreen
import time
from .visual_layouts import Cycle, needles, spectrum


class FM4Modern(ModernScreen):
    def __init__(self, app):
        super().__init__(app)
        self.cycle = Cycle()
        self._bands = [0.] * 24
        self._next_fft = 0
        self._last_theme = None

    def interact(self):
        self.cycle.interact(time.monotonic())

    def render(self, canvas, draw, w, h):
        theme = self.app.settings.get('display', 'theme', default='panel')
        if theme not in ('panel_vu', 'panel_spectrum'):
            self._last_theme = theme
            return super().render(canvas, draw, w, h)
        now = time.monotonic()
        if theme != self._last_theme:
            self.cycle.interact(now)
            self._last_theme = theme
        st = self.app.store.get()
        playing = st.status == 'play' and not self.app.soft_stopped()
        visual, overlay = self.cycle.update(now, playing, (st.uri, st.title, st.artist))
        if not visual:
            return self._render_panel(canvas, draw, w, h, st, not playing)
        if theme == 'panel_vu':
            needles(draw, w, h, self.app.levels.read())
            for x, label in ((w//4-3,'L'), (3*w//4-3,'R')):
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
            self.text(canvas, (3, 0), st.title[:40], self.app.fonts.get('regular', 11), fill=255)
            self.text(canvas, (3, 14), st.artist[:45], self.app.fonts.get('regular', 9), fill=150)

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
