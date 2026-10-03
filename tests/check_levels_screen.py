"""Read actual PCM levels and render all Panel states without touching OLED."""
import time
from pathlib import Path
from PIL import ImageDraw
from sable.pcp.levels import AudioLevels
from sable.pcp.modern import FM4Modern
from sable.pcp.runner import PiCoreApp
from sable.pcp.listener import LyrionListener, state_from_status
from sable.settings import Settings
from sable.display.sim import SimDisplay
from sable.display import fonts

fonts._DIR = '/usr/local/share/fonts/dejavu'
app = PiCoreApp(SimDisplay(256, 64, frames_dir=None, ascii_preview=False),
                Settings('/tmp/fm4-preview-settings.json'), dry_run=True)
app.levels = AudioLevels('d8:3a:dd:30:37:15')
assert app.levels.available, 'Visualizer mapping unavailable'
samples = []
for _ in range(10):
    samples.append(app.levels.read())
    time.sleep(.05)
print('Stereo levels min/max:', min(min(v) for v in samples), max(max(v) for v in samples))
listener = LyrionListener(app.store, lambda cb: cb())
status = listener.rpc(['status', '-', '1', 'tags:adKcu'])
app.albumart.host = 'http://127.0.0.1:9000'
app.store.apply_pushstate(state_from_status(status))
screen = FM4Modern(app)
app.albumart.get(app.store.get().albumart)
time.sleep(.5)
output = Path('/tmp/fm4-previews')
output.mkdir(exist_ok=True)
for theme in ('panel', 'performance'):
    app.settings.set('display', 'theme', theme)
    canvas = app.display.blank_canvas()
    screen.render(canvas, ImageDraw.Draw(canvas), 256, 64)
    canvas.save(output / (theme + '.png'))
    if theme == 'performance':
        assert not any(canvas.getpixel((x, y)) for x in range(88, 254)
                       for y in range(47, 59)), 'Performance has level bars'
app.settings.set('display', 'theme', 'panel')
app.store.apply_pushstate({'status': 'pause'})
position = app.store.live_position_ms()
time.sleep(.1)
assert app.store.live_position_ms() == position, 'Paused counter advances'
canvas = app.display.blank_canvas()
screen.render(canvas, ImageDraw.Draw(canvas), 256, 64)
canvas.save(output / 'paused.png')
app.levels.close()
app._cancel_stop_timer()
app._cancel_pause_timer()
app._cancel_playback_settle()
print('PASS: PCM reader, Panel/Performance rendering, no Performance bars, frozen pause time')
