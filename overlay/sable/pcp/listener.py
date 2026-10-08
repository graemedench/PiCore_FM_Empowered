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
    title = song.get('title', '')
    for filename, label in (('clyde2.mp3', 'Greatest Hits Radio'),
                            ('absolute80s.mp3', 'Absolute 80s')):
        if filename in uri.lower() and (filename in title.lower() or
                title.startswith(('http:', 'https:')) or not title):
            title = label
    art = song.get('artwork_url', '')
    if not art and song.get('coverid'):
        art = '/music/%s/cover_128x128.jpg' % song['coverid']
    return dict(status=data.get('mode', 'stop'), title=title,
                artist=song.get('artist', ''), album=song.get('album', ''),
                uri=uri, albumart=art, volume=abs(volume), mute=volume < 0,
                seek=int(float(data.get('time', 0)) * 1000),
                duration=int(float(song.get('duration', data.get('duration', 0)))),
                service='tidal' if uri.startswith('tidal:') else
                        'webradio' if song.get('remote') else 'mpd',
                stream=bool(song.get('remote')), samplerate='', bitdepth='')


def native_player_id():
    import re
    try:
        text=Path('/usr/local/etc/pcp/pcp.cfg').read_text()
        match=re.search(r'^MAC_ADDRESS="([0-9a-f:]{17})"$',text,re.M)
        if match:
            return match[1]
        return Path('/sys/class/net/eth0/address').read_text().strip()
    except OSError:
        return '00:00:00:00:00:00'  # Desktop fixture fallback only.


class LyrionListener:
    def __init__(self, store, dispatch, host='http://127.0.0.1:9000',
                 player=None, log=print):
        self.store, self.dispatch = store, dispatch
        self.host, self.player, self.log = host.rstrip('/'), player or native_player_id(), log
        self.on_browse = self.on_sources = self.on_outputs = self.on_connect = None
        self.browse_sources = [dict(name=name, uri='pcp:' + root)
                               for name, root in [('Music Library', 'library'),
                                  ('Albums', 'albums'), ('Artists', 'artists'),
                                  ('Genres', 'genres'), ('Playlists', 'playlists'),
                                  ('Queue', 'queue'), ('TIDAL', 'tidal'),
                                  ('BBC Sounds', 'bbcsounds')]]
        self.audio_outputs = []
        self.audio_output = ''
        self._stop = threading.Event()
        self._commands = ThreadPoolExecutor(1, thread_name_prefix='lms-command')
        self._browse = ThreadPoolExecutor(1, thread_name_prefix='lms-browse')
        self._generation = 0
        self._local_library_ready = False
        self._status_wake = threading.Event()
        self.refresh_minutes = lambda: 0
        self._refresh_due = None
        self._refresh_interval = 0
        from .cd import CDService
        self.cd = CDService()
        self._cd_present = False
        self.on_rip_info = self.on_rip_status = None
        self._rip_cancel = threading.Event()
        self._rip_lock = threading.Lock()
        self._rip_message = ''
        self._rip_fraction = 0.

    def get_audio_outputs(self):
        def work():
            try:
                from .outputs import devices, current
                self.audio_outputs, self.audio_output = devices(), current()
                if self.on_outputs:
                    self.dispatch(lambda: self.on_outputs(self.audio_outputs))
            except Exception as exc:
                self.log('Audio output discovery failed:', exc)
        self._browse.submit(work)

    def set_audio_output(self, output, callback):
        def work():
            error = None
            try:
                from .outputs import change, current
                self._return_local()
                change(output)
                self.audio_output = current()
            except Exception as exc:
                error = str(exc)
                self.log('Output change:', exc)
            self.dispatch(lambda e=error: callback(e))
            self.get_audio_outputs()
        self._commands.submit(work)

    def _check_cd(self):
        from .cd import devices
        present = bool(devices())
        if present != self._cd_present:
            self._cd_present = present
            self.browse_sources = [s for s in self.browse_sources if s['uri'] != 'pcp:cd']
            if present:
                self.browse_sources.append(dict(name='Audio CD', uri='pcp:cd'))
            if self.on_sources:
                sources = list(self.browse_sources)
                self.dispatch(lambda: self.on_sources(sources))

    def _check_refresh(self, now):
        minutes = int(self.refresh_minutes() or 0)
        if minutes != self._refresh_interval:
            self._refresh_interval = minutes
            self._refresh_due = now + minutes * 60 if minutes > 0 else None
        if self._refresh_due is not None and now >= self._refresh_due:
            self.refresh_library()
            self._refresh_due = now + minutes * 60

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
        from .favorites_page import watch
        self._favorites_thread = threading.Thread(target=watch, args=(self,), daemon=True, name='favorites-page')
        self._favorites_thread.start()

    def stop(self):
        self._rip_cancel.set()
        if self.cd:
            self.cd.close()
        self._stop.set()
        self._status_wake.set()
        self._thread.join(timeout=4)
        self._commands.shutdown(wait=False, cancel_futures=True)
        self._browse.shutdown(wait=False, cancel_futures=True)

    def _poll(self):
        connected = False
        while not self._stop.is_set():
            try:
                self._check_refresh(time.monotonic())
                self._check_cd()
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
                    self.cd.metadata.decorate(state)
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
                        command[0] in ('tidal', 'bbcsounds') and command[1] == 'playlist'):
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
            result = self.rpc(prefix + [str(start), '100'] + list(filters),
                              player=None if command == 'playlisttracks' else '')
            page = result.get(loop, [])
            items.extend(page)
            start += len(page)
            if not page or start >= int(result.get('count', start)):
                break
        return items

    def _local_library_filter(self):
        if not self._local_library_ready:
            import hashlib
            key = 'plugin.onlinelibrary:enableLocalTracksOnly'
            if str(self.rpc(['pref', key, '?'], player='').get('_p2')) != '1':
                self.rpc(['pref', key, 1], player='')
            expected = hashlib.md5(b'localTracksOnly').hexdigest()[:8]
            libraries = self.rpc(['libraries'], player='').get('folder_loop', [])
            if not any(row.get('id') == expected for row in libraries):
                raise RuntimeError('Local-only library is not ready')
            self._local_library_ready = True
        return 'library_id:localTracksOnly'

    def _items(self, uri):
        if uri == 'pcp:cd':
            try:
                disc = self.cd.inspect(lookup=True)
            except OSError:
                disc = None
            tracks = [dict(title=t.get('title', 'Track %02d' % t['number']), uri=self.cd.url(t['number']),
                         type='song', service='cd_controller', duration=t['duration'])
                    for t in disc['tracks']] if disc else [dict(title='Insert an audio CD', _notice=True)]
            return tracks + [dict(title='Eject CD', _cd_eject=True)]
        path = uri.removeprefix('pcp:')
        tag = path.partition('?')[0]
        if tag in ('tidal', 'bbcsounds'):
            query = urllib.parse.parse_qs(path.partition('?')[2])
            args = ['item_id:' + query['item'][0]] if query.get('item') else []
            result = self.rpc([tag, 'items', '0', '100'] + args)
            return [dict(title=row.get('name', 'Untitled'),
                    uri='pcp:' + tag + ('?' + urllib.parse.urlencode({'item': row['id']})),
                    _folder=bool(row.get('hasitems')), type='folder' if row.get('hasitems') else 'song',
                    service=tag, _tidal_id=row['id'], _opml_tag=tag)
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
                    for row in self._pages(command, loop, *([self._local_library_filter()] if path != 'playlists' else []))]
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
                rows = self._pages('titles', 'titles_loop', *filters, self._local_library_filter(), 'tags:adcu')
        else:
            raise ValueError('Unsupported browse source: ' + uri)
        return [dict(title=row.get('title', 'Untitled'), uri=row.get('url', ''),
                     type='song', service='mpd', **({'_queue_index': row.get('playlist index', index)}
                        if path == 'queue' else {})) for index, row in enumerate(rows) if row.get('url')]

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
                    navigation = {'lists': [{'items': items}]}
                    if uri == 'pcp:cd' and items and not items[0].get('_notice'):
                        navigation['rip'] = dict(enabled=True, data=dict(
                            endpoint='music_service/cd_controller', method='getRipInfo'))
                    self.on_browse({'navigation': navigation})
            self.dispatch(deliver)
        self._browse.submit(work)

    def play_item(self, item):
        self.active_collection_uri = ''
        if item.get('_queue_index') is not None:
            self._submit(['playlist', 'index', str(item['_queue_index'])])
            return
        if item.get('_tidal_id'):
            self.active_collection_uri = item.get('uri', '')
            self._submit([item.get('_opml_tag', 'tidal'), 'playlist', 'play', 'item_id:' + item['_tidal_id']])
            return
        self.play_uri(item.get('uri', ''), title=item.get('title', ''))

    def play_uri(self, uri, **metadata):
        self.active_collection_uri = uri if uri.startswith(('pcp:tidal?', 'pcp:bbcsounds?')) else ''
        if uri.startswith('http://127.0.0.1:9180/cd/'):
            self.play_cd(uri)
            return
        if uri.startswith(('pcp:tidal?', 'pcp:bbcsounds?')):
            item_id = urllib.parse.parse_qs(uri.partition('?')[2])['item'][0]
            self._submit([uri[4:].partition('?')[0], 'playlist', 'play', 'item_id:' + item_id])
            return
        if uri:
            self._submit(['playlist', 'play', uri, metadata.get('title', '')])

    def play_cd(self, selected_uri):
        """Queue the complete disc, then start at the selected track."""
        def work():
            try:
                if self._rip_lock.locked():
                    raise ValueError('Cancel CD rip before playing')
                disc = self.cd.inspect(lookup=True)
                if not disc:
                    raise ValueError('No audio CD')
                parts = urllib.parse.urlparse(selected_uri).path.split('/')
                number = int(parts[-1].removesuffix('.wav'))
                if parts[-2] != disc['id']:
                    raise ValueError('CD changed - reopen Audio CD')
                index = next(i for i, track in enumerate(disc['tracks']) if track['number'] == number)
                self._return_local()
                self.rpc(['playlist', 'clear'])
                for track in disc['tracks']:
                    url = 'http://127.0.0.1:9180/cd/%s/%d.wav' % (disc['id'], track['number'])
                    self.rpc(['playlist', 'add', url, track.get('title', 'Track %02d' % track['number'])])
                self.rpc(['playlist', 'index', str(index)])
                self._status_wake.set()
            except Exception as exc:
                self.log('CD queue unavailable:', str(exc))
        self._commands.submit(work)

    def play_all(self, items, start=0):
        self.active_collection_uri = ''
        if not items or not 0 <= start < len(items):
            return
        if items and items[0].get('service') == 'cd_controller':
            self.play_cd(items[start]['uri'])
            return
        if items and items[0].get('_tidal_id'):
            def tidal_work():
                self._return_local()
                for index, item in enumerate(items):
                    if item.get('_tidal_id'):
                        self.rpc([item.get('_opml_tag', 'tidal'), 'playlist', 'play' if index == 0 else 'add',
                                  'item_id:' + item['_tidal_id']])
                self.rpc(['playlist', 'index', str(start)])
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
                self.rpc(['playlist', 'index', str(start)])
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
                self.active_collection_uri = 'pcp:tidal?' + urllib.parse.urlencode({'item': chosen['id']})
                self._status_wake.set()
            except Exception as exc:
                self.log('TIDAL mix unavailable:', type(exc).__name__)
        self._commands.submit(work)

    def refresh_library(self):
        self._submit(['rescan'])
        return 'requested'

    def request_cd_rip_info(self):
        def work():
            try:
                disc = self.cd.inspect(lookup=True)
                if not disc:
                    raise ValueError('No audio CD')
                root = Path('/mnt/sda2/Music')
                if not Path('/mnt/sda2').is_mount() or not root.is_dir():
                    raise ValueError('Music storage unavailable')
                info = dict(rippingAvailable=True, cdid=disc['id'], disc=disc,
                    album=disc.get('album', 'Audio CD'), tracks=disc['tracks'], availableDrives=[dict(
                        name='Music storage', path=str(root), available=True)])
            except Exception as exc:
                info = dict(rippingAvailable=False, error=str(exc))
            if self.on_rip_info:
                self.dispatch(lambda: self.on_rip_info(info))
        self._browse.submit(work)
        return True

    def get_rip_fraction(self):
        return self._rip_fraction if self._rip_lock.locked() else None

    def get_rip_progress(self):
        return self._rip_message if self._rip_lock.locked() else None

    def cancel_cd_rip(self):
        self._rip_cancel.set()
        return self._rip_lock.locked()

    def eject_cd(self):
        def work():
            if self._rip_lock.locked():
                return
            import os, fcntl
            from .cd import devices
            try:
                self.rpc(['stop'])
                found = devices()
                if found:
                    fd = os.open(found[0], os.O_RDONLY | os.O_NONBLOCK)
                    try:
                        fcntl.ioctl(fd, 0x5309)
                    finally:
                        os.close(fd)
                self.browse('pcp:cd')
            except Exception as exc:
                self.log('CD eject failed:', type(exc).__name__)
        self._commands.submit(work)

    def rip_cd(self, info, drive, fmt='flac'):
        if fmt not in ('flac', 'mp3') or drive not in info.get('availableDrives', []) or not self._rip_lock.acquire(False):
            return False
        self._rip_cancel.clear()
        self._rip_fraction = 0.
        def work():
            from .cd import rip_flac
            def report(message, progress=None):
                self._rip_message = message
                import re
                track = re.search(r'track (\d+)/(\d+)', message)
                if track and progress is not None:
                    number, total = map(int, track.groups())
                    self._rip_fraction = min(1., max(0., (number-1+progress)/total))
                if self.on_rip_status:
                    self.dispatch(lambda: self.on_rip_status(dict(message=message, progress=progress)))
            try:
                # Only physical CD playback competes with extraction for the drive.
                status = self.rpc(['status', '-', '1', 'tags:u'])
                song = (status.get('playlist_loop') or [{}])[0]
                uri = song.get('url', '')
                if uri.startswith('http://127.0.0.1:9180/cd/'):
                    self.rpc(['stop'])
                rip_flac(info['disc'], drive['path'], self._rip_cancel, report, fmt=fmt)
                self.refresh_library()
            except Exception as exc:
                report('Rip failed: ' + str(exc))
            finally:
                self._rip_lock.release()
        threading.Thread(target=work, daemon=True, name='fm4-cd-rip').start()
        return True

    def play_playlist(self, name, callback):
        def work():
            try:
                rows = self._pages('playlists', 'playlists_loop')
                match = next((row for row in rows if row.get('playlist') == name), None)
                if match is None:
                    raise ValueError('Playlist not found')
                self._return_local()
                self.rpc(['playlistcontrol', 'cmd:load', 'playlist_id:' + str(match['id'])])
                self.active_collection_uri = ''
                self._status_wake.set()
                try:
                    from .favorites_page import export
                    export(self)
                except Exception as exc:
                    self.log('Favorites page refresh:', str(exc))
                self.dispatch(lambda: callback(True, name))
            except Exception:
                self.dispatch(lambda: callback(False, 'Playlist not found / unavailable'))
        self._commands.submit(work)

    def play_bbc_station(self, station, callback):
        self.active_collection_uri = ''
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
        if song.uri.startswith('http://127.0.0.1:9180/cd/'):
            self.dispatch(lambda: callback(False, 'Rip the CD before saving'))
            return
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
