"""Bounded Lyrion JSON-RPC adapter; network work never blocks UI dispatch."""
import json
import threading
import time
from pathlib import Path
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def state_from_status(data):
    tracks = data.get('playlist_loop') or []
    song = tracks[0] if tracks else {}
    volume = int(float(data.get('mixer volume', 0)))
    uri = song.get('url', '')
    art = song.get('artwork_url', '')
    if not art and song.get('coverid'):
        art = '/music/%s/cover_128x128.jpg' % song['coverid']
    return dict(status=data.get('mode', 'stop'), title=song.get('title', ''),
                artist=song.get('artist', ''), album=song.get('album', ''),
                uri=uri, albumart=art, volume=abs(volume), mute=volume < 0,
                seek=int(float(data.get('time', 0)) * 1000),
                duration=int(float(song.get('duration', data.get('duration', 0)))),
                service='tidal' if uri.startswith('tidal:') else
                        'webradio' if song.get('remote') else 'mpd',
                stream=bool(song.get('remote')), samplerate='', bitdepth='')


class LyrionListener:
    def __init__(self, store, dispatch, host='http://127.0.0.1:9000',
                 player='d8:3a:dd:30:37:15', log=print):
        self.store, self.dispatch = store, dispatch
        self.host, self.player, self.log = host.rstrip('/'), player, log
        self.on_browse = self.on_sources = self.on_outputs = self.on_connect = None
        self.browse_sources = [dict(name=name, uri='pcp:' + root)
                               for name, root in [('Music Library', 'library'),
                                  ('Albums', 'albums'), ('Artists', 'artists'),
                                  ('Genres', 'genres'), ('Playlists', 'playlists'),
                                  ('Queue', 'queue'), ('TIDAL', 'tidal')]]
        self._stop = threading.Event()
        self._commands = ThreadPoolExecutor(1, thread_name_prefix='lms-command')
        self._browse = ThreadPoolExecutor(1, thread_name_prefix='lms-browse')
        self._generation = 0
        self._status_wake = threading.Event()

    def rpc(self, command, player=None):
        payload = dict(id=1, method='slim.request',
                       params=[self.player if player is None else player, command])
        request = urllib.request.Request(self.host + '/jsonrpc.js',
            json.dumps(payload).encode(), {'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=3) as response:
            data = json.load(response)
        if data.get('error'):
            raise RuntimeError(str(data['error']))
        return data.get('result', {})

    def start(self):
        self._thread = threading.Thread(target=self._poll, daemon=True, name='lms-status')
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._status_wake.set()
        self._thread.join(timeout=4)
        self._commands.shutdown(wait=False, cancel_futures=True)
        self._browse.shutdown(wait=False, cancel_futures=True)

    def _poll(self):
        connected = False
        while not self._stop.is_set():
            try:
                receiver = Path('/tmp/fm4-receiver.json')
                if receiver.exists():
                    active = json.loads(receiver.read_text())
                    source = active['source']
                    state = dict(status='play', title='AirPlay' if source == 'airplay' else 'Bluetooth', artist='Connected receiver',
                        album='', albumart='', uri='receiver:' + source, service=source,
                        seek=int((time.time() - active['started']) * 1000), duration=0,
                        stream=True)
                else:
                    state = state_from_status(self.rpc(['status', '-', '1', 'tags:aldKcu']))
                self.dispatch(lambda s=state: self.store.apply_pushstate(s))
                if not connected and self.on_connect:
                    self.dispatch(self.on_connect)
                connected = True
            except Exception as exc:
                if connected:
                    self.log('Lyrion disconnected:', exc)
                connected = False
            self._status_wake.wait(.5 if connected else 2)
            self._status_wake.clear()

    def _return_local(self):
        from .receiver_hook import return_local
        return_local()

    def _submit(self, command):
        def work():
            try:
                if command[0] in ('play', 'pause', 'stop') or (
                        command[0] == 'playlist' and command[1] in ('play', 'index')) or (
                        command[0] == 'tidal' and command[1] == 'playlist'):
                    self._return_local()
                result = self.rpc(command)
                self._status_wake.set()
                return result
            except Exception as exc:
                self.log('Lyrion command failed:', command[0], exc)
        return self._commands.submit(work)

    def transport(self, command):
        if command == 'toggle':
            def toggle():
                try:
                    self._return_local()
                    status = self.rpc(['status', '-', '1'])
                    self.rpc(['pause', '1'] if status.get('mode') == 'play' else ['play'])
                    self._status_wake.set()
                except Exception as exc:
                    self.log('Lyrion toggle failed:', exc)
            return self._commands.submit(toggle)
        if command in ('random', 'repeat'):
            self.set_playback_mode('random' if command == 'random' else 'playlist')
            return
        mapped = {'toggle': ['pause'], 'play': ['play'], 'pause': ['pause', '1'],
                  'stop': ['stop'], 'next': ['playlist', 'index', '+1'],
                  'previous': ['playlist', 'index', '-1']}
        if command in mapped:
            self._submit(mapped[command])

    def set_volume(self, value):
        if value in ('mute', 'unmute'):
            self._submit(['mixer', 'muting', 'toggle' if value == 'mute' else '0'])
        else:
            value = {'+': '+1', '-': '-1'}.get(value, value)
            self._submit(['mixer', 'volume', str(value)])

    def set_playback_mode(self, mode):
        self._submit(['playlist', 'shuffle', '1' if mode == 'random' else '0'])
        self._submit(['playlist', 'repeat', '1' if mode == 'track' else
                      '2' if mode == 'playlist' else '0'])

    def get_sources(self):
        if self.on_sources:
            self.dispatch(lambda: self.on_sources(self.browse_sources))

    @staticmethod
    def folder(title, uri):
        return dict(title=title, uri=uri, type='folder', _folder=True, service='mpd')

    def _pages(self, command, loop, *filters):
        items, start = [], 0
        while not self._stop.is_set():
            prefix = ['playlists', 'tracks'] if command == 'playlisttracks' else [command]
            result = self.rpc(prefix + [str(start), '100'] + list(filters), player='')
            page = result.get(loop, [])
            items.extend(page)
            start += len(page)
            if not page or start >= int(result.get('count', start)):
                break
        return items

    def _items(self, uri):
        path = uri.removeprefix('pcp:')
        if path == 'tidal' or path.startswith('tidal?'):
            query = urllib.parse.parse_qs(path.partition('?')[2])
            args = ['item_id:' + query['item'][0]] if query.get('item') else []
            result = self.rpc(['tidal', 'items', '0', '100'] + args)
            return [dict(title=row.get('name', 'Untitled'),
                    uri='pcp:tidal' + ('?' + urllib.parse.urlencode({'item': row['id']})),
                    _folder=bool(row.get('hasitems')), type='folder' if row.get('hasitems') else 'song',
                    service='tidal', _tidal_id=row['id'])
                    for row in result.get('loop_loop', []) if row.get('type') != 'search']
        if path in ('', 'library'):
            return [self.folder(x['name'], x['uri']) for x in self.browse_sources
                    if x['uri'] != 'pcp:library']
        if path in ('albums', 'artists', 'genres', 'playlists'):
            command, loop, label, filter_key = {
                'albums': ('albums', 'albums_loop', 'album', 'album_id'),
                'artists': ('artists', 'artists_loop', 'artist', 'artist_id'),
                'genres': ('genres', 'genres_loop', 'genre', 'genre_id'),
                'playlists': ('playlists', 'playlists_loop', 'playlist', 'playlist_id')
            }[path]
            return [self.folder(row.get(label, 'Untitled'),
                    'pcp:tracks?' + urllib.parse.urlencode({filter_key: row['id']}))
                    for row in self._pages(command, loop)]
        if path == 'queue':
            result = self.rpc(['status', '0', '10000', 'tags:adcu'])
            rows = result.get('playlist_loop', [])
        elif path.startswith('tracks?'):
            filters = ['%s:%s' % (key, values[0]) for key, values in
                       urllib.parse.parse_qs(path.split('?', 1)[1]).items()]
            if any(x.startswith('playlist_id:') for x in filters):
                rows = self._pages('playlisttracks', 'playlisttracks_loop',
                                   *filters, 'tags:adcu')
            else:
                rows = self._pages('titles', 'titles_loop', *filters, 'tags:adcu')
        else:
            raise ValueError('Unsupported browse source: ' + uri)
        return [dict(title=row.get('title', 'Untitled'), uri=row.get('url', ''),
                     type='song', service='mpd') for row in rows if row.get('url')]

    def browse(self, uri=''):
        self._generation += 1
        generation = self._generation
        def work():
            try:
                items = self._items(uri)
            except Exception as exc:
                self.log('Browse failed:', exc)
                items = [dict(title='Server unavailable — try again', _notice=True)]
            def deliver():
                if generation == self._generation and self.on_browse:
                    self.on_browse({'navigation': {'lists': [{'items': items}]}})
            self.dispatch(deliver)
        self._browse.submit(work)

    def play_item(self, item):
        if item.get('_tidal_id'):
            self._submit(['tidal', 'playlist', 'play', 'item_id:' + item['_tidal_id']])
            return
        self.play_uri(item.get('uri', ''))

    def play_uri(self, uri, **metadata):
        if uri.startswith('pcp:tidal?'):
            item_id = urllib.parse.parse_qs(uri.partition('?')[2])['item'][0]
            self._submit(['tidal', 'playlist', 'play', 'item_id:' + item_id])
            return
        if uri:
            self._submit(['playlist', 'play', uri])

    def play_all(self, items):
        if items and items[0].get('_tidal_id'):
            def tidal_work():
                self._return_local()
                for index, item in enumerate(items):
                    if item.get('_tidal_id'):
                        self.rpc(['tidal', 'playlist', 'play' if index == 0 else 'add',
                                  'item_id:' + item['_tidal_id']])
                self._status_wake.set()
            self._commands.submit(tidal_work)
            return
        urls = [item['uri'] for item in items if item.get('uri')]
        if not urls:
            return
        def work():
            try:
                self._return_local()
                self.rpc(['playlist', 'clear'])
                for url in urls:
                    self.rpc(['playlist', 'add', url])
                self.rpc(['play'])
            except Exception as exc:
                self.log('Queue update failed:', exc)
        self._commands.submit(work)

    def play_tidal_mix(self, position=0):
        def work():
            try:
                self._return_local()
                root = self.rpc(['tidal', 'items', '0', '100'])
                mix_root = next(row for row in root.get('loop_loop', [])
                                if row.get('name') == 'My Mix')
                mixes = self.rpc(['tidal', 'items', '0', '100', 'item_id:' + mix_root['id']])
                chosen = mixes.get('loop_loop', [])[position]
                self.rpc(['tidal', 'playlist', 'play', 'item_id:' + chosen['id']])
                self._status_wake.set()
            except Exception as exc:
                self.log('TIDAL mix unavailable:', type(exc).__name__)
        self._commands.submit(work)

    def refresh_library(self):
        self._submit(['rescan'])
        return 'requested'

    def play_bbc_station(self, station, callback):
        def work():
            try:
                self._return_local()
                from ..stations import PRESETS
                key = 'bbc_radio_2' if station == 'bbc_radio_two' else 'bbc_radio_4'
                title, uri, artwork = PRESETS[key]
                uri = 'hlsplay://' + uri.split('://', 1)[1]
                self.rpc(['playlist', 'play', uri, title])
                self._status_wake.set()
                message = title
            except Exception:
                message = 'Station unavailable'
            self.dispatch(lambda: callback(message))
        self._commands.submit(work)

    def save_current_track(self, callback, name='FM4 Favorites'):
        song = self.store.get()
        def work():
            try:
                if not song.uri:
                    raise ValueError('No track selected')
                rows = self._pages('playlists', 'playlists_loop')
                match = next((row for row in rows if row.get('playlist') == name), None)
                if match:
                    playlist_id = match['id']
                else:
                    result = self.rpc(['playlists', 'new', 'name:' + name], player='')
                    playlist_id = result.get('playlist_id', result.get('overwritten_playlist_id'))
                    if not playlist_id:
                        raise RuntimeError('Playlist directory is not configured')
                self.rpc(['playlists', 'edit', 'playlist_id:' + str(playlist_id),
                          'cmd:add', 'url:' + song.uri], player='')
                tracks = self._pages('playlisttracks', 'playlisttracks_loop',
                                     'playlist_id:' + str(playlist_id), 'tags:u')
                if not any(row.get('url') == song.uri for row in tracks):
                    raise RuntimeError('Playlist save could not be verified')
                self.dispatch(lambda: callback(True, name))
            except Exception as exc:
                self.log('Save track failed:', exc)
                message = str(exc)
                self.dispatch(lambda: callback(False, message))
        self._browse.submit(work)
