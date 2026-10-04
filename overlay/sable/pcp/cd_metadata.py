"""MusicBrainz exact-disc lookup. Only explicit worker calls perform network IO."""
import base64
import hashlib
import json
from pathlib import Path
import threading
import time
import urllib.request

USER_AGENT = 'PiCore-FM-Empowered/0.1 (https://github.com/graemedench/PiCore_FM_Empowered)'


def disc_id(entries):
    if any(data for _, _, data in entries[:-1]):
        raise ValueError('Mixed-mode metadata lookup not supported')
    first, last = entries[0][0], entries[-2][0]
    offsets = {number: lba + 150 for number, lba, _ in entries}
    text = '%02X%02X%08X' % (first, last, offsets[0xAA])
    text += ''.join('%08X' % offsets.get(n, 0) for n in range(1, 100))
    return base64.b64encode(hashlib.sha1(text.encode('ascii')).digest()).decode().translate(str.maketrans('+/', '._')).replace('=', '-')


def artist(credits):
    return ''.join(c.get('name', c.get('artist', {}).get('name', '')) + c.get('joinphrase', '') for c in credits)


def get_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read(4 * 1024 * 1024))


class Metadata:
    def __init__(self, root='/mnt/sda2/tce/fm4-cd-metadata'):
        self.root = Path(root)
        self.cache = {}
        self.retry = {}
        self.loaded = set()
        self.lock = threading.Lock()
        self.last_request = 0

    def apply(self, disc, lookup=False):
        identity = disc['id']
        if not lookup:
            result = self.cache.get(identity, {})
            for key in ('album', 'artist', 'albumart'):
                if key in result:
                    disc[key] = result[key]
            for track in disc['tracks']:
                track.update(result.get('tracks', {}).get(str(track['number']), {}))
            return
        with self.lock:
            if identity not in self.cache:
                try:
                    self.cache[identity] = json.loads((self.root / (identity + '.json')).read_text())
                except (OSError, ValueError):
                    pass
            if lookup and identity not in self.cache and time.monotonic() > self.retry.get(identity, 0):
                try:
                    mbid = disc_id(disc['entries'])
                    time.sleep(max(0, 1.1 - (time.monotonic() - self.last_request)))
                    self.last_request = time.monotonic()
                    data = get_json('https://musicbrainz.org/ws/2/discid/' + mbid + '?fmt=json&inc=recordings%2Bartist-credits')
                    candidates = []
                    for release in data.get('releases', []):
                        for medium in release.get('media', []):
                            if any(d['id'] == mbid for d in medium.get('discs', [])) and len(medium.get('tracks', [])) == len(disc['tracks']):
                                candidates.append((release, medium))
                    candidates.sort(key=lambda pair: (len(pair[0].get('media', [])), pair[0].get('date', '9999'), pair[0]['id']))
                    if candidates:
                        release, medium = candidates[0]
                        result = dict(album=release['title'], artist=artist(release.get('artist-credit', [])), release=release['id'], tracks={})
                        for native, track in zip(disc['tracks'], medium['tracks']):
                            result['tracks'][str(native['number'])] = dict(title=track['title'], artist=artist(track.get('artist-credit', [])) or result['artist'])
                        # A missing cover must never discard a successful title lookup.
                        for cover_release, _ in candidates[:3]:
                            try:
                                covers = get_json('https://coverartarchive.org/release/' + cover_release['id'])
                                front = next(image for image in covers['images'] if image.get('front'))
                                result['albumart'] = front['thumbnails']['250'].replace('http://', 'https://', 1)
                                break
                            except Exception:
                                continue
                        self.cache[identity] = result
                        try:
                            self.root.mkdir(parents=True, exist_ok=True)
                            target = self.root / (identity + '.json')
                            temporary = target.with_suffix('.tmp')
                            temporary.write_text(json.dumps(result))
                            temporary.replace(target)
                        except OSError:
                            pass
                except Exception:
                    pass
                self.retry[identity] = time.monotonic() + 600
            result = self.cache.get(identity, {})
        for key in ('album', 'artist', 'albumart'):
            if key in result:
                disc[key] = result[key]
        for track in disc['tracks']:
            track.update(result.get('tracks', {}).get(str(track['number']), {}))

    def decorate(self, state):
        parts = state.get('uri', '').split('/')
        if len(parts) != 6 or parts[3] != 'cd':
            return
        if parts[4] not in self.cache and parts[4] not in self.loaded:
            self.loaded.add(parts[4])
            try:
                self.cache[parts[4]] = json.loads((self.root / (parts[4] + '.json')).read_text())
            except (OSError, ValueError):
                pass
        result = self.cache.get(parts[4], {})
        number = parts[5].removesuffix('.wav')
        state.update(result.get('tracks', {}).get(number, {}))
        for key in ('album', 'albumart'):
            if key in result:
                state[key] = result[key]
        state.update(service='cd_controller', stream=False)
