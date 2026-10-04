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

from sable.pcp.favorites_page import backup_playlist
with TemporaryDirectory() as folder:
    root = Path(folder); source = root / 'favorites.m3u'; backups = root / 'backups'
    assert not backup_playlist(source, backups)
    source.write_text('#EXTM3U\ntidal://123.mp4\n')
    assert backup_playlist(source, backups)
    assert not backup_playlist(source, backups)
    for i in range(35):
        source.write_text('#EXTM3U\ntidal://%d.mp4\n' % i)
        assert backup_playlist(source, backups)
    assert len(list(backups.glob('FM4 Favorites-*-*.m3u'))) == 30
    assert (backups / 'FM4 Favorites-latest.m3u').read_bytes() == source.read_bytes()
print('PASS: missing playlist, change detection, latest copy and 30-version retention')
