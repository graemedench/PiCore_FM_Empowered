"""Exercise the hold-8 picker and persisted short/long assignments without GPIO."""
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from sable.pcp.runner import PiCoreApp, PiCoreMenu
from sable.settings import Settings

with tempfile.TemporaryDirectory() as directory:
    path = str(Path(directory) / 'settings.json')
    app = PiCoreApp.__new__(PiCoreApp)
    app.settings = Settings(path)
    app.listener = SimpleNamespace(_commands=Mock())
    app.store = SimpleNamespace(get=lambda: SimpleNamespace(
        service='mpd', title='A track', uri='file:///mnt/sda2/Music/test.mp3'))
    app.go = Mock()
    app.render = Mock()
    app.note_activity = Mock()
    app.show_osd = Mock()
    app.base_screen = lambda: 'modern'
    app.fsm = SimpleNamespace(screens={}, current=None, reset_menu_timer=Mock())
    menu = PiCoreMenu(app)
    app.fsm.screens['menu'] = menu
    for long_press in (False, True):
        app.handle('save_shortcut')
        assert menu._shortcut_entry['stage'] == 'button'
        assert not menu.accept_shortcut_button(4)
        assert app.capture_shortcut_button(7)
        menu._shortcut_entry['index'] = int(long_press)
        menu._shortcut_select()
        saved = Settings(path).get('buttons', 'btn_7')
        prefix = 'hold_' if long_press else ''
        assert saved[prefix + 'action'] == 'play_uri'
        assert saved[prefix + 'arg'].startswith('file:///mnt/sda2/Music/test.mp3')
        assert menu._shortcut_entry is None
    assert app.listener._commands.submit.call_count == 2
    menu._wifi_jobs.shutdown()
print('PASS: hold-8 picker, button capture, short/long settings reload, backup requested')
