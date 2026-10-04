"""Keep the normal idle clock, with a whole-disc extraction progress pie."""
from ..screens.clock import ClockScreen


def progress_pie(draw, w, h, fraction):
    x, y = w-19, h-19
    draw.rectangle((x-1, y-1, w-1, h-1), fill=0)
    box = (x, y, x+15, y+15)
    draw.ellipse(box, fill=25, outline=140)
    if fraction > 0:
        draw.pieslice(box, 270, 270+360*min(1, fraction), fill=220, outline=140)


class RipClock(ClockScreen):
    def render(self, canvas, draw, w, h):
        super().render(canvas, draw, w, h)
        listener = self.app.listener
        fraction = listener.get_rip_fraction() if listener else None
        if fraction is not None:
            progress_pie(draw, w, h, fraction)
