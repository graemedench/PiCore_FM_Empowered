"""Sable screens with Lyrion and piCorePlayer inputs; staged hardware runner."""
import argparse
import json
import queue
import signal
import subprocess
import threading
import time
from pathlib import Path

from ..app import App
from ..settings import Settings
from ..screens.menu import MenuScreen
from .listener import LyrionListener


class PiCoreApp(App):
    def volume_available(self):
        return True

    def nowplaying_screen(self):
        return 'modern'

    def spectrum_available(self):
        return False

    def _transport(self, command):
        self.listener.transport(command)

    def _poweroff(self):
        if not self.dry_run:
            subprocess.Popen(['pcp', 'sd'])

    def nudge_volume(self, delta):
        self.listener.set_volume('%+d' % int(delta))
        self.show_osd('VOLUME', str(max(0, min(100, self.store.get().volume + int(delta)))))

    def handle(self, cmd, arg=None):
        if cmd == 'play_uri' and str(arg or '').startswith('tidal://'):
            self.show_osd('TIDAL', 'Mix connection pending')
            return
        if cmd in ('random', 'repeat'):
            self._set_playback_mode('random' if cmd == 'random' else 'playlist')
            return
        if cmd == 'save_track':
            self.show_osd('SAVING', 'Current track')
            self.listener.save_current_track(lambda ok, message:
                self.show_osd('SAVED' if ok else 'SAVE FAILED', message))
            return
        if cmd in ('save_shortcut', 'play_playlist'):
            self.show_osd('COMING NEXT', 'Playlist saving')
            return
        return super().handle(cmd, arg)


class PiCoreMenu(MenuScreen):
    def _build_tree(self):
        tree = super()._build_tree()
        # Expose only functioning settings during the staged port.
        tree = [row for row in tree if row[0] not in
                ('Audio Output', 'Storage', 'Screen Rotation', 'Shortcuts')]
        for index, row in enumerate(tree):
            if row[0] == 'Display Mode':
                tree[index] = (row[0], [item for item in row[1]
                    if item[0].startswith('Modern:') or item[0] == 'Back'], *row[2:])
            elif row[0] == 'Network':
                tree[index] = (row[0], [item for item in row[1]
                    if item[0] != 'Wi-Fi Networks'], *row[2:])
        return tree


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', default='http://127.0.0.1:9000')
    parser.add_argument('--player', default='d8:3a:dd:30:37:15')
    parser.add_argument('--settings', default='config/pcp-settings.json')
    parser.add_argument('--sim', action='store_true')
    parser.add_argument('--seconds', type=float, default=0)
    args = parser.parse_args()
    events, stop = queue.Queue(), threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    if args.sim:
        from ..display.sim import SimDisplay
        display = SimDisplay(256, 64, frames_dir='var/pcp-frames', ascii_preview=False)
        encoder = None
    else:
        import fcntl
        lock_file = open('/tmp/quadify-panel.lock', 'w')
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        from .display import PiCoreDisplay
        from panel import Encoder
        display = PiCoreDisplay()
        encoder = Encoder(events, stop)
        encoder.start()
    from ..display import fonts
    for font_dir in ('/usr/local/share/fonts/truetype/dejavu',
                     '/usr/local/share/fonts/dejavu', '/usr/share/fonts/truetype/dejavu'):
        if (Path(font_dir) / 'DejaVuSans.ttf').exists():
            fonts._DIR = font_dir
            break
    app = PiCoreApp(display, Settings(args.settings), dry_run=args.sim)
    # One-time migration restores the user's complete Empowered layout.
    # Later startup preserves edits instead of resetting button preferences.
    if not app.settings.get('_meta', 'pcp_button_layout', default=0):
        preset = json.loads(Path('config/settings.graeme.json').read_text())
        for button, cfg in preset['buttons'].items():
            app.settings.set('buttons', button, cfg)
        app.settings.set('_meta', 'pcp_button_layout', 1)
    app.fsm.screens['menu'] = PiCoreMenu(app)
    app._playback_settle_s = .15
    app.albumart.host = app.albumart_cinema.host = args.server.rstrip('/')
    listener = LyrionListener(app.store, lambda cb: events.put(('callback', cb)),
                              host=args.server, player=args.player)
    app.listener = listener
    listener.on_browse = app.fsm.screens['browse'].on_browse_data
    listener.on_sources = app.fsm.screens['home'].refresh_sources
    buttons = None
    if not args.sim:
        from .buttons import FM4Buttons
        from ..hardware import MCP
        buttons = FM4Buttons(MCP, lambda cmd, arg=None:
            events.put(('callback', lambda: app.handle(cmd, arg))), app.store, app=app)
        buttons.start()
        listener.on_connect = buttons.signal_ready
    app.fsm.go('clock')
    listener.start()
    started = time.monotonic()
    try:
        while not stop.is_set():
            if args.seconds and time.monotonic() - started > args.seconds:
                break
            # Limit each batch so a burst of input cannot starve rendering.
            for _ in range(64):
                try:
                    kind, arg = events.get_nowait()
                except queue.Empty:
                    break
                if kind == 'callback':
                    arg()
                elif kind == 'turn':
                    app.handle('scroll', arg)
                elif kind == 'click':
                    app.handle('select')
                elif kind == 'long':
                    app.handle('home')
            app.tick_idle(time.monotonic())
            app.reconcile_screen()
            app.render()
            stop.wait(.05)
    finally:
        stop.set()
        listener.stop()
        if encoder:
            encoder.join(timeout=2)
        if buttons:
            buttons.stop()
        display.cleanup()


if __name__ == '__main__':
    main()
