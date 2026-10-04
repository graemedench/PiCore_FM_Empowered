"""Favorites page: safe markup, public TIDAL links and atomic refresh."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from sable.pcp.favorites_page import render, export, safe_art, public_track_url

tracks = [dict(title='<script>oops</script>', artist='A & B', album='Example',
    url='tidal://track/12345?token=secret', artwork_url='/music/123/cover.jpg'),
    dict(title='Local song', artist='Artist', url='file:///mnt/sda2/Music/song.flac')]
assert public_track_url('tidal://218740662.mp4') == 'https://tidal.com/browse/track/218740662'
page = render(tracks, '192.168.1.19', 'test')
assert '<script>' not in page and '&lt;script&gt;' in page
assert 'https://tidal.com/browse/track/12345' in page
assert 'token=secret' not in page and 'file:///' not in page
assert 'http://192.168.1.19:9000/music/123/cover.jpg' in page
assert safe_art('javascript:alert(1)', '192.168.1.19') == ''
assert 'No saved tracks yet' in render([], '192.168.1.19')
def pages(command, loop, *filters):
    return [dict(id=33, playlist='FM4 Favorites')] if command == 'playlists' else tracks
with TemporaryDirectory() as folder, patch('sable.pcp.favorites_page.local_address', return_value='192.168.1.19'):
    target = Path(folder) / 'fm4-favorites.html'
    export(SimpleNamespace(_pages=pages), target)
    assert target.exists() and not target.with_suffix('.tmp').exists()
    assert 'FM4 Favorites' in target.read_text(encoding='utf-8')
print('PASS: safe artwork page, public TIDAL links, empty state and atomic export')
