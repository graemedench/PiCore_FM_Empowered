"""Interaction-driven Panel/visualiser layouts with short track notifications."""
import math
import time


class Cycle:
    def __init__(self, now=None):
        self.panel_until = (time.monotonic() if now is None else now) + 5
        self.track = None
        self.overlay_until = 0
        self.playing = False

    def interact(self, now):
        self.panel_until = now + 5

    def update(self, now, playing, track):
        if playing and not self.playing:
            self.interact(now)
        if self.track is not None and track != self.track:
            self.overlay_until = now + 2
        self.track, self.playing = track, playing
        return playing and now >= self.panel_until, now < self.overlay_until


def needles(draw, w, h, levels):
    for channel, level in enumerate(levels):
        cx, cy, radius = w * (channel+.5)/2, h+3, h-15
        draw.arc((cx-radius, cy-radius, cx+radius, cy+radius), 210, 330, fill=95, width=1)
        for tick in range(11):
            angle = math.radians(150-12*tick)
            outer = (cx+radius*math.cos(angle), cy-radius*math.sin(angle))
            inner = (cx+(radius-5)*math.cos(angle), cy-(radius-5)*math.sin(angle))
            draw.line((inner, outer), fill=230 if tick >= 8 else 130)
        angle = math.radians(150-120*max(0, min(1, level)))
        draw.line((cx, cy, cx+(radius-8)*math.cos(angle), cy-(radius-8)*math.sin(angle)), fill=255, width=2)
        draw.line((cx-6, h-2, cx+6, h-2), fill=120)


def spectrum(draw, w, h, bands):
    width = w/len(bands)
    for index, value in enumerate(bands):
        x = int(index*width)+2
        height = int(max(0, min(1, value))*(h-15))
        if height:
            draw.rectangle((x, h-10-height, int((index+1)*width)-2, h-10), fill=160)
            draw.line((x, h-10-height, int((index+1)*width)-2, h-10-height), fill=255)
