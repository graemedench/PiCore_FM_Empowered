"""Artwork-enabled local Favorites page, refreshed off the UI thread."""
import html
from pathlib import Path
import re
import socket
import time
import threading

_export_lock = threading.Lock()
from urllib.parse import urlsplit, urlunsplit


def local_address():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(('192.0.2.1', 80))
            return sock.getsockname()[0]
    except OSError:
        return 'FM4-Reborn.local'


def public_track_url(uri):
    match = re.fullmatch(r'tidal://(?:(?:song|track)/)?(\d+)(?:\.(?:mp4|flac|aac))?(?:\?.*)?', uri)
    return 'https://tidal.com/browse/track/' + match[1] if match else ''


def safe_art(uri, address):
    if uri.startswith('/'):
        uri = 'http://' + address + ':9000' + uri
    parts = urlsplit(uri)
    if parts.scheme not in ('http', 'https') or parts.username or parts.password:
        return ''
    if parts.hostname in ('127.0.0.1', 'localhost'):
        uri = urlunsplit((parts.scheme, address + ':9000', parts.path, parts.query, parts.fragment))
    return uri


def render(tracks, address, generated=None):
    rows = []
    for item in tracks:
        title = html.escape(str(item.get('title') or 'Unknown track'))
        artist = html.escape(str(item.get('artist') or ''))
        album = html.escape(str(item.get('album') or ''))
        uri = str(item.get('url') or '')
        link = public_track_url(uri)
        title = f'<a href="{link}" target="_blank" rel="noopener">{title}</a>' if link else title
        art = item.get('artwork_url') or ('/music/%s/cover_128x128.jpg' % item['coverid'] if item.get('coverid') else '')
        art = safe_art(str(art), address)
        image = '<img src="%s" alt="" loading="lazy">' % html.escape(art, quote=True) if art else '<div class="blank" aria-hidden="true">♪</div>'
        rows.append(f'<li>{image}<div><strong>{title}</strong><p>{artist}</p><small>{album}</small></div></li>')
    stamp = html.escape(generated or time.strftime('%Y-%m-%d %H:%M'))
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="60"><title>FM4 Favorites</title><style>
body{font-family:system-ui,sans-serif;background:#111820;color:#edf3fa;max-width:850px;margin:2rem auto;padding:0 1rem}a{color:#85c7ff}header p,small{color:#acbdce}ol{padding-left:1.5rem}li{display:flex;gap:1rem;align-items:center;margin:1.2rem 0}img,.blank{width:80px;height:80px;object-fit:cover;background:#263442;border-radius:8px;flex-shrink:0}.blank{display:grid;place-items:center;font-size:2rem}li p{margin:.35rem 0}nav{display:flex;gap:1rem;flex-wrap:wrap}
</style></head><body><header><h1>FM4 Favorites</h1><p>Your saved tracks. Open a TIDAL track to save it to your TIDAL collection.</p><nav><a href="http://''' + html.escape(address, quote=True) + ''':9000/">FM4 web player</a></nav></header><ol>''' + (''.join(rows) or '<p>No saved tracks yet. Tap button 8 while a track is playing.</p>') + f'</ol><footer><small>{len(tracks)} tracks · Updated {stamp} · Refreshes automatically</small></footer></body></html>'


def _export(listener, destination=Path('/var/www/fm4-favorites.html')):
    rows = listener._pages('playlists', 'playlists_loop')
    match = next((r for r in rows if r.get('playlist') == 'FM4 Favorites'), None)
    tracks = listener._pages('playlisttracks', 'playlisttracks_loop',
        'playlist_id:' + str(match['id']), 'tags:alucK') if match else []
    # Native httpd serves the page. Atomic replacement keeps reads consistent.
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.tmp')
    temporary.write_text(render(tracks, local_address()), encoding='utf-8')
    temporary.chmod(0o644)
    temporary.replace(destination)


def watch(listener):
    while not listener._stop.is_set():
        try:
            export(listener)
        except Exception as exc:
            listener.log('Favorites page refresh:', str(exc))
        listener._stop.wait(60)


def export(listener, destination=Path('/var/www/fm4-favorites.html')):
    with _export_lock:
        return _export(listener, destination)
