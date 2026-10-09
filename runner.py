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
from ..screens.browse import BrowseScreen, _play_all_tracks
from .listener import LyrionListener, native_player_id


def fitted_text(canvas, fonts, text, y, size=26, face='sans_bold', fill=255):
    """Fit a centred single line inside the actual OLED width."""
    from PIL import ImageDraw
    from ..screens.base import crisp_text
    text = str(text or '').replace('\n', ' ')
    draw = ImageDraw.Draw(canvas)
    available = canvas.width - 12
    while size > 8 and draw.textlength(text, font=fonts.get(face, size)) > available:
        size -= 1
    font = fonts.get(face, size)
    if draw.textlength(text, font=font) > available:
        while text and draw.textlength(text + '...', font=font) > available:
            text = text[:-1]
        text += '...'
    crisp_text(canvas, (canvas.width // 2, y), text, font, fill=fill, anchor='mm')


class PiCoreApp(App):
    def _draw_osd(self, img):
        if not self._osd or self._osd_volume or time.monotonic() >= self._osd[2]:
            return super()._draw_osd(img)
        from PIL import Image
        out = Image.blend(img, Image.new('L', img.size, 0), .8)
        big, small, _ = self._osd
        fitted_text(out, self.fonts, small, out.height // 2 - 15, 11, 'sans', 160)
        fitted_text(out, self.fonts, big, out.height // 2 + 8)
        return out

    def _on_state(self, old, new):
        now = time.monotonic()
        idle_since = getattr(self, '_volume_idle_since', None)
        first = not hasattr(self, '_volume_idle_since')
        if first:
            self._volume_idle_since = None if new.status == 'play' else now
        elif new.status != 'play' and idle_since is None:
            self._volume_idle_since = now
        resumed = (new.status == 'play' and idle_since is not None
                   and now - idle_since >= 3600)
        if new.status == 'play':
            self._volume_idle_since = None
        marker = Path('/tmp/fm4-power-volume-applied')
        startup = first and not marker.exists()
        if startup:
            marker.touch()
        value = self.settings.get('audio', 'power_on_volume', default=None)
        if (startup or resumed) and value is not None and new.service not in ('airplay', 'bluetooth'):
            self.listener.set_volume(max(0, min(100, int(value))))
        super()._on_state(old, new)

    def set_audio_output(self, output):
        self.show_osd('AUDIO OUTPUT', 'Switching...')
        def done(error):
            self.show_osd('AUDIO OUTPUT', str(error) if error else 'Output saved')
            self.fsm.screens['menu'].refresh_audio_outputs()
        self.listener.set_audio_output(output, done)

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
        modern = self.fsm.screens.get('modern')
        if hasattr(modern, 'interact'):
            modern.interact()
        if cmd == 'volume':
            self.note_activity()
            self.nudge_volume(1 if arg == '+' else -1)
            return
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
        songs = _play_all_tracks(frame['items'])
        if item in songs and not item.get('_play_all'):
            if item.get('_queue_index') is not None:
                self.app.listener.play_item(item)
            else:
                self.app.listener.play_all(songs, start=next(i for i, song in enumerate(songs) if song is item))
            self.app.go(self.app.nowplaying_screen())
            return
        super().handle_select()

    def on_browse_data(self, data):
        super().on_browse_data(data)
        for frame in self.stack:
            for item in frame['items']:
                if item.get('_rip_format') == 'mp3':
                    item['title'] = 'Rip MP3 (320 kbps)'
        self.app.render()


class PiCoreMenu(MenuScreen):
    def _edit_number(self, label, section, key, default, minimum, maximum, step, unit):
        value = self.app.settings.get(section, key, default=default)
        self._number_entry = dict(label=label, section=section, key=key,
            value=minimum if value is None else int(value), minimum=minimum,
            maximum=maximum, step=step, unit=unit)
        self.app.fsm.reset_menu_timer()

    def _save_number(self):
        entry = self._number_entry
        value = entry['value']
        if entry['key'] == 'power_on_volume' and value < 0:
            value = None
        self.app.settings.set(entry['section'], entry['key'], value)
        self._number_entry = None
        if entry['key'] == 'clock_after_s' and self.app.store.get().status == 'pause':
            self.app._arm_pause_timer()
        self.app.note_activity()
        self.app.fsm.reset_menu_timer()
        self.app.show_osd('SAVED', entry['label'])
        self._wifi_jobs.submit(subprocess.run, ['pcp', 'bu'], capture_output=True, timeout=90)

    def on_exit(self):
        self._number_entry = None
        super().on_exit()

    def _power_volume_label(self):
        value = self.app.settings.get('audio', 'power_on_volume', default=None)
        return 'Off' if value is None else str(value) + '%'

    def _set_power_volume(self, value):
        self.app.settings.set('audio', 'power_on_volume', value)
        self.app.show_osd('POWER-ON VOLUME', 'Off' if value is None else str(value) + '%')
        self._wifi_jobs.submit(subprocess.run, ['pcp', 'bu'], capture_output=True, timeout=90)

    def _audio_output_items(self):
        items = [(d['name'], lambda value=d['id']: self._set_audio_output(value))
                 for d in getattr(self.app.listener, 'audio_outputs', [])]
        # Reuse Sable's navigation marker without platform-specific device assumptions.
        from ..screens.menu import _BACK
        return items + [('Back', _BACK)]

    def _audio_output_label(self):
        from .outputs import selected
        listener = self.app.listener
        device = selected(getattr(listener, 'audio_outputs', []), getattr(listener, 'audio_output', ''))
        return device['name'] if device else 'Select Output'

    def _pair_ir(self):
        remote = getattr(self.app, 'ir_remote', None)
        if not remote or not remote.is_alive():
            self.app.show_osd('IR REMOTE', 'Receiver unavailable')
            return
        self.app.show_osd('PAIR APPLE REMOTE', 'Press Menu within 30 seconds')
        def finish(identity):
            def apply():
                if identity is None:
                    self.app.show_osd('IR REMOTE', 'Pairing timed out')
                else:
                    self.app.settings.set('ir', 'pair_id', identity)
                    self.app.show_osd('IR REMOTE', 'Paired successfully')
                    self._wifi_jobs.submit(subprocess.run, ['pcp', 'bu'], capture_output=True, timeout=90)
            self.app.listener.dispatch(apply)
        remote.begin_pair(finish)

    def _cancel_ir_learn(self):
        remote = getattr(self.app, 'ir_remote', None)
        if remote:
            remote.cancel_learn()
        self.app.show_osd('REMOTE LEARNING', 'Cancelled')

    def _learn_ir(self, label, key):
        remote = getattr(self.app, 'ir_remote', None)
        if not remote or not remote.is_alive():
            self.app.show_osd('IR REMOTE', 'Receiver unavailable')
            return
        self.app.show_osd('LEARN: ' + label.upper(), 'Press remote key (30 sec)', duration=30)
        def finish(code):
            def apply():
                if code is None:
                    self.app.show_osd('REMOTE LEARNING', 'No supported signal received')
                    return
                mappings = dict(self.app.settings.get('ir', 'learned', default={}))
                mappings = {c: k for c, k in mappings.items() if k != key}
                mappings[code] = key
                self.app.settings.set('ir', 'learned', mappings)
                remote.set_mappings(mappings)
                self.app.show_osd('REMOTE SAVED', label, duration=5)
                self._wifi_jobs.submit(subprocess.run, ['pcp', 'bu'], capture_output=True, timeout=90)
            self.app.listener.dispatch(apply)
        remote.begin_learn(finish)

    def _reset_ir_learn(self):
        self._cancel_ir_learn()
        self.app.settings.set('ir', 'learned', {})
        remote = getattr(self.app, 'ir_remote', None)
        if remote:
            remote.set_mappings({})
        self.app.show_osd('IR REMOTE', 'Apple mappings restored')
        self._wifi_jobs.submit(subprocess.run, ['pcp', 'bu'], capture_output=True, timeout=90)

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
            self.app.show_osd('WI-FI', 'Joining; allow up to 1 minute', duration=90)
            def work():
                from .wifi import connect
                try:
                    ok, message = connect(ssid, password)
                except Exception:
                    ok, message = False, 'Connection failed'
                def done():
                    self._wifi_busy = False
                    self.app.show_osd('WI-FI CONNECTED' if ok else 'WI-FI', message, duration=15)
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

    def _add_mini_playlist(self):
        self.app.show_osd('MINI PLAYLIST', 'Adding tracks...')
        self.app.listener.add_mini_playlist(lambda ok, message:
            self.app.show_osd('PLAYLIST ADDED' if ok else 'ADD FAILED', message, duration=5))

    def _show_signin(self, title, path, port=9000):
        address = 'FM4-Reborn.local'
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
                connection.connect(('192.0.2.1', 80))
                address = connection.getsockname()[0]
        except OSError:
            pass
        self._signin_url = (title, 'http://' + address + (':' + str(port) if port != 80 else '') + '/' + path)
        self.app.render()

    def handle_select(self):
        if getattr(self, '_number_entry', None):
            self._save_number()
            return
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
        if getattr(self, '_number_entry', None):
            self._number_entry = None
            self.app.fsm.reset_menu_timer()
            return
        remote = getattr(self.app, 'ir_remote', None)
        if remote and remote.learn_until:
            self._cancel_ir_learn()
        if self._signin_url:
            self._signin_url = None
            self.app.fsm.reset_menu_timer()
            return
        super().handle_back()

    def handle_scroll(self, delta):
        entry = getattr(self, '_number_entry', None)
        if entry:
            entry['value'] = max(entry['minimum'], min(entry['maximum'],
                entry['value'] + int(delta) * entry['step']))
            self.app.fsm.reset_menu_timer()
            return
        entry = self._shortcut_entry
        if entry and entry['stage'] == 'press':
            entry['index'] = (entry['index'] + delta) % 3
            self.app.fsm.reset_menu_timer()
            return
        if not self._signin_url:
            super().handle_scroll(delta)

    def render(self, canvas, draw, w, h):
        entry = getattr(self, '_number_entry', None)
        if entry:
            self.app.fsm.reset_menu_timer()
            value = entry['value']
            off = value < 0 or (entry['unit'] == 'seconds' and value == 0)
            display = 'Off' if off else (str(value) + '%' if entry['unit'] == '%' else
                (str(value // 60) + 'm ' + str(value % 60) + 's'))
            fitted_text(canvas, self.app.fonts, entry['label'], 8, 11)
            fitted_text(canvas, self.app.fonts, display, h // 2, 26)
            fitted_text(canvas, self.app.fonts, 'Turn: adjust | Click: save | Hold: cancel', h-8, 9, 'sans', 130)
            return
        if self.stack and self._cur['label'] == 'PATCHED - REBOOT?':
            self.app.fsm.reset_menu_timer()
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
        fitted_text(canvas, self.app.fonts, title.upper(), 6, 9, 'mono', 230)
        for index, line in enumerate(textwrap.wrap(url, width=40,
                                                  break_on_hyphens=False)):
            self.text(canvas, (3, 15 + index*11), line, font, fill=190)
        fitted_text(canvas, self.app.fonts, 'Open in browser | Press to return', h-5, 9, 'mono', 105)

    def _reboot_after_update(self):
        self.app.show_osd('REBOOTING', 'Please wait', duration=60)
        self._wifi_jobs.submit(subprocess.run, ['pcp', 'rb'], capture_output=True)

    def _update_later(self):
        self.app.go(self.app.base_screen())
        self.app.show_osd('PATCHED', 'Reboot later to load', duration=5)

    def _show_update_reboot(self):
        self.app._osd = None
        self.app.go('menu')
        self.stack.append(self._frame('PATCHED - REBOOT?', [
            ('Later', self._update_later), ('Reboot now', self._reboot_after_update)]))
        self.app.render()

    def _apply_updates(self):
        if getattr(self, '_update_busy', False):
            self.app.show_osd('UPDATE', 'Already running', duration=5)
            return
        self._update_busy = True
        self.app.show_osd('UPDATING', 'Keep power on; please wait', duration=1800)
        def work():
            from .update import apply
            try:
                ok, message = apply()
            except Exception:
                ok, message = False, 'Update failed; see update log'
            def done():
                self._update_busy = False
                if ok:
                    self._show_update_reboot()
                else:
                    self.app.show_osd('PATCH FAILED', 'See fm4-update.log', duration=15)
            self.app.listener.dispatch(done)
        self._wifi_jobs.submit(work)

    def _build_tree(self):
        tree = super()._build_tree()
        # Expose only functioning settings during the staged port.
        tree = [row for row in tree if row[0] not in
                ('Screen Rotation',)]
        for index, row in enumerate(tree):
            if row[0] == 'Display Mode':
                choices = [item for item in row[1] if item[0].startswith('Modern:')]
                choices += [('Panel / Needle VU', lambda: self._set_modern('panel_vu')),
                            ('Panel / Spectrum', lambda: self._set_modern('panel_spectrum')),
                            ('Panel / Twin Needle VU', lambda: self._set_modern('panel_ppm')),
                            ('Back', row[1][-1][1])]
                tree[index] = (row[0], choices, *row[2:])
            elif row[0] == 'Network':
                tree[index] = (row[0], row[1][:-1] + [
                    ('Wi-Fi status / IP', self._show_wifi_status), row[1][-1]], *row[2:])
        tree.insert(3, ('Power-on Volume', lambda: self._edit_number(
            'Power-on Volume', 'audio', 'power_on_volume', None, -1, 100, 1, '%'),
            self._power_volume_label))
        tree.insert(4, ('Display Timeouts', [
            (label, lambda label=label, key=key, default=default: self._edit_number(
                label, 'screensaver', key, default, 0, 7200, 30, 'seconds'))
            for label, key, default in [('Pause to clock', 'clock_after_s', 300),
                ('Clock dim after', 'dim_s', 120), ('Display off after', 'idle_s', 3600)]
            ] + [('Back', '__back__')]))
        tree.insert(-1, ('Check / Apply Updates', [
            ('Apply latest patches?', [
                ('Cancel', '__back__'), ('Yes, apply patches', self._apply_updates)]),
            ('Back', '__back__')]))
        tree.insert(-1, ("Add G's Mini Tidal List", self._add_mini_playlist))
        tree.insert(-1, ('Pair Apple Remote', self._pair_ir))
        learn_keys = [('Up', 'KEY_UP'), ('Down', 'KEY_DOWN'),
                      ('Left', 'KEY_LEFT'), ('Right', 'KEY_RIGHT'),
                      ('Select', 'KEY_ENTER'), ('Menu', 'KEY_HOME'),
                      ('Back / previous', 'KEY_BACK'), ('Play / pause', 'KEY_PLAY'),
                      ('Volume up', 'KEY_VOLUMEUP'), ('Volume down', 'KEY_VOLUMEDOWN'),
                      ('Mute', 'KEY_MUTE'),
                      ('Next track', 'KEY_NEXTSONG'), ('Previous track', 'KEY_PREVIOUSSONG'),
                      ('Stop', 'KEY_STOP'), ('Repeat / shuffle mode', 'KEY_REPEAT'),
                      ('Save track', 'KEY_RECORD'), ('Now Playing', 'KEY_INFO'),
                      ('Back (navigation)', 'KEY_EXIT')]
        tree.insert(-1, ('Beta Learn remote', [
            ('Learn ' + label, lambda label=label, key=key: self._learn_ir(label, key))
            for label, key in learn_keys] + [
                ('Cancel learning', self._cancel_ir_learn),
                ('Restore Apple defaults', self._reset_ir_learn), ('Back', '__back__')]))
        tree.insert(-1, ('Service URLs', [
            ('Web player', lambda: self._show_signin('FM4 web player', '')),
            ('FM4 Favorites page', lambda: self._show_signin('FM4 Favorites', 'fm4-favorites.html', 80)), 
            ('BBC Sounds', lambda: self._show_signin('BBC Sounds sign-in',
                'plugins/BBCSounds/settings/basic.html')),
            ('TIDAL', lambda: self._show_signin('TIDAL sign-in',
                'plugins/TIDAL/settings.html')),
            ('Server settings', lambda: self._show_signin('Server settings',
                'settings/server/basic.html')),
            ('Back', '__back__'),
        ]))
        by_name = {row[0]: row for row in tree}
        groups = [
            ('Display', ('Display Mode', 'Brightness', 'Display Timeouts')),
            ('Audio', ('Audio Output', 'Power-on Volume', 'Playback')),
            ('Remote', ('Pair Apple Remote', 'Beta Learn remote')),
            ('Network & Services', ('Network', 'Service URLs')),
            ('Library & Shortcuts', ('Music Library', 'Shortcuts', "Add G's Mini Tidal List")),
            ('System', ('Storage', 'Check / Apply Updates', 'Shutdown')),
        ]
        used = {'Now Playing', 'Back'}
        grouped = [by_name['Now Playing']]
        for title, names in groups:
            rows = [by_name[name] for name in names if name in by_name]
            used.update(names)
            grouped.append((title, rows + [('Back', '__back__')]))
        # Keep future settings reachable if a new row has not yet been grouped.
        grouped[-1][1][-1:-1] = [row for row in tree if row[0] not in used]
        grouped.append(by_name['Back'])
        return grouped



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', default='http://127.0.0.1:9000')
    parser.add_argument('--player', default=None)
    parser.add_argument('--settings', default='config/pcp-settings.json')
    parser.add_argument('--sim', action='store_true')
    parser.add_argument('--seconds', type=float, default=0)
    args = parser.parse_args()
    args.player = args.player or native_player_id()
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
    from .source_icons import PiCoreHome
    app.fsm.screens['home'] = PiCoreHome(app)
    from .clock import RipClock
    app.fsm.screens['clock'] = RipClock(app)
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
    listener.on_outputs = app.fsm.screens['menu'].refresh_audio_outputs
    listener.get_audio_outputs()
    buttons = None
    power_button = None
    remote = None
    if not args.sim:
        from .buttons import FM4Buttons
        from ..hardware import MCP
        buttons = FM4Buttons(MCP, lambda cmd, arg=None:
            events.put(('callback', lambda: app.handle(cmd, arg))), app.store, app=app)
        buttons.start()
        listener.on_connect = buttons.signal_ready
        from .power import PowerButton
        shutdown_gpio = app.settings.get('power', 'shutdown_gpio', default=26)
        if shutdown_gpio is not None:
            try:
                power_button = PowerButton(lambda: events.put(('callback',
                    lambda: app.handle('shutdown'))), stop, gpio=shutdown_gpio)
                power_button.start()
            except Exception as exc:
                print('Shutdown GPIO unavailable:', exc)
        if app.settings.get('ir', 'enabled', default=True):
            from .ir import Remote
            from ..inputs.ir import IrListener
            app.settings.set('ir', 'profile', 'Apple Aluminium Remote (this unit)')
            bridge = IrListener(lambda cmd, arg=None: events.put(('callback',
                lambda: app.handle(cmd, arg))), app=app)
            try:
                remote = Remote(lambda key, repeat: bridge._on_line(
                    '0 %02x %s Apple_Aluminium_Sable' % (int(repeat), key)), stop,
                    pair_id=app.settings.get('ir', 'pair_id', default=0x15),
                    mappings=app.settings.get('ir', 'learned', default={}))
                app.ir_remote = remote
                remote.start()
            except Exception as exc:
                print('IR unavailable:', exc)
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
        if remote:
            remote.join(timeout=1)
        app.levels.close()
        display.cleanup()


if __name__ == '__main__':
    main()
