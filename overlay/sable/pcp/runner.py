"""Sable screens with Lyrion and piCorePlayer inputs; staged hardware runner."""
import argparse
import json
import queue
import signal
import subprocess
import threading
import time
import socket
import textwrap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..app import App
from ..settings import Settings
from ..screens.menu import MenuScreen
from ..screens.browse import BrowseScreen
from .listener import LyrionListener


class PiCoreApp(App):
    def volume_available(self):
        return self.store.get().service not in ('airplay', 'bluetooth')

    def nowplaying_screen(self):
        return 'modern'

    def spectrum_available(self):
        levels = getattr(self, 'levels', None)
        return bool(levels and levels.available)

    def _transport(self, command):
        self.listener.transport(command)

    def _poweroff(self):
        if not self.dry_run:
            subprocess.Popen(['pcp', 'sd'])

    def nudge_volume(self, delta):
        if not self.volume_available():
            self.show_osd('RECEIVER', 'Volume on your phone')
            return
        self.listener.set_volume('%+d' % int(delta))
        self.show_osd('VOLUME', str(max(0, min(100, self.store.get().volume + int(delta)))))

    def handle(self, cmd, arg=None):
        if cmd in ('bbc_radio_2', 'bbc_radio_4'):
            station = 'bbc_radio_two' if cmd == 'bbc_radio_2' else 'bbc_radio_fourfm'
            self.note_activity()
            self._begin_source_change()
            self.show_osd('RADIO', 'Loading station')
            self.listener.play_bbc_station(station, lambda message:
                self.show_osd('RADIO', message))
            return
        if cmd == 'play_pause' and self.soft_stopped():
            self.note_activity()
            self._cancel_soft_stop()
            self._transport('play')
            self.render()
            return
        if cmd == 'play_uri' and str(arg or '').startswith('tidal://mymusic/mixes/'):
            self.note_activity()
            self._begin_source_change()
            self.listener.play_tidal_mix(0 if 'My Mix 1' in str(arg) else 1)
            self.show_osd('TIDAL', 'Loading mix')
            return
        if cmd in ('random', 'repeat'):
            self._set_playback_mode('random' if cmd == 'random' else 'playlist')
            return
        if cmd == 'save_track':
            self.show_osd('SAVING', 'Current track')
            self.listener.save_current_track(lambda ok, message:
                self.show_osd('SAVED' if ok else 'SAVE FAILED', message))
            return
        if cmd == 'play_playlist':
            self.note_activity()
            self._begin_source_change()
            self.show_osd('PLAYLIST', str(arg or ''))
            self.listener.play_playlist(str(arg or ''), lambda ok, message:
                self.show_osd('PLAYLIST' if ok else 'UNAVAILABLE', message))
            return
        return super().handle(cmd, arg)

    def current_shortcut_source(self):
        st = self.store.get()
        if st.uri.startswith('http://127.0.0.1:9180/cd/'):
            return None  # Disc URLs are temporary, not reusable shortcuts.
        if st.service in ('airplay', 'bluetooth'):
            return None
        if st.title in ('BBC Radio 2', 'BBC Radio 4'):
            return ('bbc_radio_2' if st.title.endswith('2') else 'bbc_radio_4', '', st.title)
        if st.title in ('Greatest Hits Radio', 'Greatest Hits Radio (Glasgow & the West)', 'Absolute 80s'):
            station = 'absolute80s-mp3' if st.title == 'Absolute 80s' else 'clyde2-mp3'
            return ('play_uri', 'http://www.radiofeeds.net/playlists/bauerflash.pls?station=' + station + ' | ' + st.title, st.title)
        return super().current_shortcut_source()

    def save_shortcut(self, button, long_press, action, arg):
        super().save_shortcut(button, long_press, action, arg)
        # Tiny Core keeps settings in RAM until its native backup completes.
        def backup():
            result = subprocess.run(['pcp', 'bu'], capture_output=True, timeout=90)
            if result.returncode:
                self.listener.dispatch(lambda: self.show_osd('BACKUP FAILED', 'Shortcut saved in RAM'))
        self.listener._commands.submit(backup)


class PiCoreBrowse(BrowseScreen):
    def handle_select(self):
        frame = self._cur
        item = frame['items'][frame['index']] if frame['items'] else {}
        if item.get('_cd_eject'):
            if self.app.listener.get_rip_progress():
                self.app.show_osd('CD RIPPING', 'Cancel rip before eject')
            else:
                self.app.show_osd('CD', 'Ejecting disc')
                self.app.listener.eject_cd()
            return
        super().handle_select()

    def on_browse_data(self, data):
        super().on_browse_data(data)
        for frame in self.stack:
            frame['items'] = [item for item in frame['items'] if item.get('_rip_format') != 'mp3']
        self.app.render()


class PiCoreMenu(MenuScreen):
    _signin_url = None

    def _network_status(self):
        address = self._ip_address()
        if not address or address.startswith('127.'):
            return 'NOT CONNECTED', None
        for interface, label in (('eth0', 'WIRED'), ('wlan0', 'WI-FI')):
            try:
                if Path('/sys/class/net/' + interface + '/operstate').read_text().strip() == 'up':
                    return label, address
            except OSError:
                pass
        return 'NETWORK', address

    def __init__(self, app):
        super().__init__(app)
        self._wifi_jobs = ThreadPoolExecutor(1, thread_name_prefix='fm4-wifi')
        self._wifi_busy = False

    @staticmethod
    def _storage_rows():
        import shutil
        rows = []
        path = Path('/mnt/sda2')
        if path.is_mount():
            usage = shutil.disk_usage(path)
            rows.append(('Music storage', usage.free, usage.total))
        return rows

    def _reset_shortcuts(self):
        super()._reset_shortcuts()
        self._wifi_jobs.submit(subprocess.run, ['pcp', 'bu'], capture_output=True, timeout=90)

    def _set_library_refresh(self, minutes):
        super()._set_library_refresh(minutes)
        self._wifi_jobs.submit(subprocess.run, ['pcp', 'bu'], capture_output=True, timeout=90)

    def _scan_wifi(self):
        if self._wifi_busy:
            return
        self._wifi_busy = True
        self.app.show_osd('WI-FI', 'Scanning networks')
        def work():
            from .wifi import scan
            try:
                networks = scan()
            except Exception:
                networks = []
            def done():
                self._wifi_busy = False
                if networks:
                    items = [(ssid, lambda ssid=ssid: self._start_wifi_entry(ssid))
                             for ssid in networks[:30]]
                    items.append(('Back', '__back__'))
                    self.stack.append(self._frame('WI-FI NETWORKS', items))
                    self.app.render()
                else:
                    self.app.show_osd('WI-FI', 'No networks / scan failed')
            self.app.listener.dispatch(done)
        self._wifi_jobs.submit(work)

    def _wifi_char(self):
        return ['JOIN', 'CANCEL', 'DELETE'] + list(
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') + [
            chr(code) for code in range(32, 127) if not chr(code).isalnum()]

    def _wifi_select(self):
        entry = self._wifi_entry
        char = self._wifi_char()[entry['index']]
        if char == 'DELETE':
            entry['password'] = entry['password'][:-1]
        elif char == 'CANCEL':
            self._wifi_entry = None
        elif char == 'JOIN':
            if self._wifi_busy:
                return
            self._wifi_busy = True
            ssid, password = entry['ssid'], entry['password']
            self._wifi_entry = None
            self.app.show_osd('WI-FI', 'Joining network')
            def work():
                from .wifi import connect
                try:
                    ok, message = connect(ssid, password)
                except Exception:
                    ok, message = False, 'Connection failed'
                def done():
                    self._wifi_busy = False
                    self.app.show_osd('WI-FI CONNECTED' if ok else 'WI-FI', message, duration=6)
                self.app.listener.dispatch(done)
                if ok:
                    result = subprocess.run(['pcp', 'bu'], capture_output=True, timeout=90)
                    if result.returncode:
                        self.app.listener.dispatch(lambda:
                            self.app.show_osd('WI-FI', 'Connected; backup failed'))
            self._wifi_jobs.submit(work)
        elif len(entry['password']) < 63:
            entry['password'] += char

    def _show_wifi_status(self):
        def work():
            from .wifi import status
            info = status()
            self.app.listener.dispatch(lambda: self.app.show_osd('WI-FI',
                info.get('ip_address', 'Not connected'), duration=6))
        self._wifi_jobs.submit(work)

    def _show_signin(self, title, path):
        address = 'FM4-Reborn.local'
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
                connection.connect(('192.0.2.1', 80))
                address = connection.getsockname()[0]
        except OSError:
            pass
        self._signin_url = (title, 'http://' + address + ':9000/' + path)
        self.app.render()

    def handle_select(self):
        entry = self._shortcut_entry
        if entry and entry['stage'] == 'press' and entry['index'] == 2:
            self._shortcut_entry = None
            self.app.go(self.app.base_screen())
            return
        if self._signin_url:
            self._signin_url = None
            self.app.fsm.reset_menu_timer()
            return
        super().handle_select()

    def handle_back(self):
        if self._signin_url:
            self._signin_url = None
            self.app.fsm.reset_menu_timer()
            return
        super().handle_back()

    def handle_scroll(self, delta):
        entry = self._shortcut_entry
        if entry and entry['stage'] == 'press':
            entry['index'] = (entry['index'] + delta) % 3
            self.app.fsm.reset_menu_timer()
            return
        if not self._signin_url:
            super().handle_scroll(delta)

    def render(self, canvas, draw, w, h):
        entry = self._shortcut_entry
        if entry and entry['stage'] == 'press':
            rows = [('Short press', ''), ('Long press', ''), ('Cancel', '')]
            self.draw_menu_surface(canvas, draw, w, h,
                'SAVE BUTTON %d' % entry['button'], rows, entry['index'],
                key_prefix='shortcut', top=self.TOP, row_h=self.ROW_H, nrows=self.ROWS)
            return
        if self._wifi_entry is not None:
            self.app.fsm.reset_menu_timer()
            entry = self._wifi_entry
            char = self._wifi_char()[entry['index']]
            rows = [('Password', '*' * min(16, len(entry['password'])) or '-'),
                    ('Choose', 'SPACE' if char == ' ' else char), ('Press', 'ADD / SELECT')]
            self.draw_menu_surface(canvas, draw, w, h, ('WI-FI: ' + entry['ssid'])[:25],
                rows, 1, key_prefix='wifi', top=self.TOP, row_h=self.ROW_H, nrows=self.ROWS)
            return
        if not self._signin_url:
            return super().render(canvas, draw, w, h)
        self.app.fsm.reset_menu_timer()
        title, url = self._signin_url
        font = self.app.fonts.get('mono', 9)
        self.text(canvas, (3, 1), title.upper(), font, fill=230)
        for index, line in enumerate(textwrap.wrap(url, width=40,
                                                  break_on_hyphens=False)):
            self.text(canvas, (3, 15 + index*11), line, font, fill=190)
        self.text(canvas, (3, 54), 'Open in browser | Press to return', font, fill=105)

    def _build_tree(self):
        tree = super()._build_tree()
        # Expose only functioning settings during the staged port.
        tree = [row for row in tree if row[0] not in
                ('Audio Output', 'Screen Rotation')]
        for index, row in enumerate(tree):
            if row[0] == 'Display Mode':
                tree[index] = (row[0], [item for item in row[1]
                    if item[0].startswith('Modern:') or item[0] == 'Back'], *row[2:])
            elif row[0] == 'Network':
                tree[index] = (row[0], row[1][:-1] + [
                    ('Wi-Fi status / IP', self._show_wifi_status), row[1][-1]], *row[2:])
        tree.insert(-1, ('Service sign-in', [
            ('BBC Sounds', lambda: self._show_signin('BBC Sounds sign-in',
                'plugins/BBCSounds/settings/basic.html')),
            ('TIDAL', lambda: self._show_signin('TIDAL sign-in',
                'plugins/TIDAL/settings.html')),
            ('Server settings', lambda: self._show_signin('Server settings',
                'settings/server/basic.html')),
            ('Back', '__back__'),
        ]))
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
    app.fsm.screens['browse'] = PiCoreBrowse(app)
    from .levels import AudioLevels
    from .modern import FM4Modern
    app.levels = AudioLevels(args.player)
    app.fsm.screens['modern'] = FM4Modern(app)
    app._playback_settle_s = .15
    app.albumart.host = app.albumart_cinema.host = args.server.rstrip('/')
    listener = LyrionListener(app.store, lambda cb: events.put(('callback', cb)),
                              host=args.server, player=args.player)
    app.listener = listener
    listener.cd.start()
    listener.refresh_minutes = lambda: app.settings.get('library', 'refresh_minutes', default=0)
    listener.on_browse = app.fsm.screens['browse'].on_browse_data
    listener.on_rip_info = app.fsm.screens['browse'].on_rip_info
    listener.on_rip_status = app.fsm.screens['browse'].on_rip_status
    listener.on_sources = app.fsm.screens['home'].refresh_sources
    buttons = None
    power_button = None
    if not args.sim:
        from .buttons import FM4Buttons
        from ..hardware import MCP
        buttons = FM4Buttons(MCP, lambda cmd, arg=None:
            events.put(('callback', lambda: app.handle(cmd, arg))), app.store, app=app)
        buttons.start()
        listener.on_connect = buttons.signal_ready
        from .power import PowerButton
        power_button = PowerButton(lambda: events.put(('callback',
                                    lambda: app.handle('shutdown'))), stop)
        power_button.start()
        from .bluetooth import BluetoothHandover
        BluetoothHandover(stop).start()
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
        if power_button:
            power_button.join(timeout=1)
        app.levels.close()
        display.cleanup()


if __name__ == '__main__':
    main()
