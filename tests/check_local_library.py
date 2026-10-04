"""Local groups/tracks are scoped; mixed playlists and queue remain intact."""
from unittest.mock import Mock
import os,sys
if os.name == 'nt':
    sys.modules.setdefault('fcntl', Mock())
from sable.pcp.listener import LyrionListener

listener = LyrionListener(None, None)
def rpc(command, player=None):
    if command[:2] == ['pref', 'plugin.onlinelibrary:enableLocalTracksOnly']:
        return {'_p2': '1'}
    if command == ['libraries']:
        return {'folder_loop': [{'id': '91b427f1'}]}
    if command[0] == 'status':
        return {'playlist_loop': [{'title': 'Online queued', 'url': 'tidal://123.mp4'}]}
    return {}
listener.rpc = Mock(side_effect=rpc)
def pages(command, loop, *filters):
    if command in ('albums', 'artists', 'genres'):
        assert 'library_id:localTracksOnly' in filters
        return [{'id': 1, {'albums':'album','artists':'artist','genres':'genre'}[command]: 'Local'}]
    if command == 'titles':
        assert 'library_id:localTracksOnly' in filters
        return [{'title': 'Local track', 'url': 'file:///mnt/sda2/Music/a.mp3'}]
    assert not any(str(x).startswith('library_id:') for x in filters)
    return [{'id': 33, 'playlist': 'FM4 Favorites'}] if command == 'playlists' else [{'title': 'Online favorite', 'url': 'tidal://123.mp4'}]
listener._pages = Mock(side_effect=pages)
for source in ('albums', 'artists', 'genres'):
    assert listener._items('pcp:' + source)[0]['_folder']
assert listener._items('pcp:tracks?album_id=1')[0]['uri'].startswith('file:')
assert listener._items('pcp:playlists')
assert listener._items('pcp:tracks?playlist_id=33')[0]['uri'].startswith('tidal:')
assert listener._items('pcp:queue')[0]['uri'].startswith('tidal:')
listener._local_library_ready = False
listener.rpc = Mock(return_value={})
try:
    listener._local_library_filter()
except RuntimeError:
    pass
else:
    raise AssertionError('Unavailable local library must not silently expose all music')
listener._commands.shutdown()
listener._browse.shutdown()
print('PASS: local-only groups/tracks; mixed playlist/queue preserved; no unfiltered fallback')
