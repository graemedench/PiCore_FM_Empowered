"""Small OLED source symbols drawn as vectors and cached by the carousel."""
from PIL import Image, ImageDraw
from ..screens import home


def icon(name, size):
    image = Image.new('L', (192, 192))
    draw = ImageDraw.Draw(image)
    if name == 'fm4_queue':
        # Play marker and three tracks: distinct from the saved-playlist icon.
        draw.polygon([(24, 30), (24, 72), (58, 51)], fill=255)
        draw.line([(76, 51), (168, 51)], fill=255, width=12)
        for y in (96, 141):
            draw.ellipse((29, y-7, 43, y+7), fill=255)
            draw.line([(76, y), (168, y)], fill=255, width=12)
    elif name == 'fm4_bbc_sounds':
        # BBC block letters above a compact audio waveform, drawn without fonts.
        for x, letter in zip((18, 72, 126), ('B', 'B', 'C')):
            draw.rectangle((x, 24, x+46, 70), fill=255)
            if letter == 'B':
                draw.line([(x+12, 33), (x+12, 61)], fill=0, width=5)
                draw.line([(x+12, 34), (x+27, 34), (x+33, 40), (x+27, 47),
                           (x+12, 47), (x+27, 47), (x+33, 54), (x+27, 61), (x+12, 61)], fill=0, width=5)
            else:
                draw.line([(x+34, 34), (x+18, 34), (x+12, 40), (x+12, 55),
                           (x+18, 61), (x+34, 61)], fill=0, width=5)
        for x, height in zip((34, 58, 82, 106, 130, 154), (26, 48, 72, 54, 34, 18)):
            draw.rounded_rectangle((x-5, 124-height//2, x+5, 124+height//2), radius=5, fill=255)
    else:
        raise ValueError('Unknown source symbol')
    return image.resize((size, size), Image.Resampling.LANCZOS)


class PiCoreHome(home.HomeScreen):
    def _icon(self, name, size):
        if name in ('fm4_queue', 'fm4_bbc_sounds'):
            key = (name, size)
            if key not in self._cache:
                self._cache[key] = icon(name, size)
            return self._cache[key]
        return super()._icon(name, size)


home._NAME_ICONS.update({'queue': 'fm4_queue', 'bbc sounds': 'fm4_bbc_sounds'})
home._NAME_ICONS.update({'beta spotify': 'spotify', 'beta qobuz': 'qobuz'})
