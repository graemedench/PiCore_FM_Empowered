"""Check storage, refresh scheduling and playlist lookup without altering playback."""
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch
from sable.pcp.listener import LyrionListener
from sable.pcp.runner import PiCoreMenu

listener = LyrionListener(None, lambda fn: fn())
listener.refresh_minutes = lambda: 15
listener.refresh_library = Mock()
listener._check_refresh(100)
listener._check_refresh(999)
listener.refresh_library.assert_not_called()
listener._check_refresh(1000)
listener.refresh_library.assert_called_once()
listener.refresh_minutes = lambda: 0
listener._check_refresh(1001)
listener._check_refresh(10000)
listener.refresh_library.assert_called_once()

class Immediate:
    def submit(self, fn):
        fn()

listener._commands.shutdown()
listener._commands = Immediate()
listener._pages = Mock(return_value=[{'id': 33, 'playlist': 'FM4 Favorites'}])
listener._return_local = Mock()
listener.rpc = Mock(return_value={})
result = []
listener.play_playlist('FM4 Favorites', lambda *args: result.append(args))
listener.rpc.assert_called_once_with(['playlistcontrol', 'cmd:load', 'playlist_id:33'])
assert result == [(True, 'FM4 Favorites')]
listener.rpc.reset_mock()
listener.play_playlist('Missing', lambda *args: result.append(args))
listener.rpc.assert_not_called()
assert result[-1][0] is False
listener._browse.shutdown()

with patch('sable.pcp.runner.Path') as path, patch('shutil.disk_usage') as usage:
    path.return_value.is_mount.return_value = False
    assert PiCoreMenu._storage_rows() == []
    path.return_value.is_mount.return_value = True
    usage.return_value = SimpleNamespace(free=5_000_000_000, total=13_000_000_000)
    assert PiCoreMenu._storage_rows() == [('Music storage', 5_000_000_000, 13_000_000_000)]
print('PASS: timed refresh/disable, named playlist lookup, missing playlist, mounted storage')
