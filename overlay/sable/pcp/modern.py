"""Original Sable Panel with an elapsed clock and compact stereo level bars."""
from ..screens.modern import ModernScreen


class FM4Modern(ModernScreen):
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
