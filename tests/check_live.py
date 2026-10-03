"""Read-only integration check on the Pi; never changes playback or settings."""
import queue
import time
from sable.state import StateStore
from sable.pcp.listener import LyrionListener, state_from_status

events = queue.Queue()
store = StateStore()
listener = LyrionListener(store, events.put)
status = listener.rpc(['status', '-', '1', 'tags:adKcu'])
assert status['player_connected'] == 1, 'Player is disconnected'
mapped = state_from_status(status)
assert mapped['seek'] == int(float(status['time']) * 1000)
print('Player state:', mapped['status'], mapped['title'], mapped['volume'])
for source in ('albums', 'artists', 'genres', 'playlists', 'queue'):
    items = listener._items('pcp:' + source)
    print(source, len(items))
    if source == 'albums' and items:
        tracks = listener._items(items[0]['uri'])
        assert tracks, 'First album returned no playable tracks'
        print('First album tracks:', len(tracks))
responses = []
listener.on_browse = responses.append
listener.browse('pcp:albums')
listener.browse('pcp:artists')
deadline = time.monotonic() + 10
while time.monotonic() < deadline and not responses:
    try:
        events.get(timeout=.2)()
    except queue.Empty:
        pass
assert len(responses) == 1, 'Missing or stale asynchronous browse response'
listener.start()
deadline = time.monotonic() + 5
while time.monotonic() < deadline:
    try:
        events.get(timeout=.2)()
        if store.get().title == mapped['title']:
            break
    except queue.Empty:
        pass
listener.stop()
assert store.get().title == mapped['title'], 'Status polling did not reach UI dispatch'
print('PASS: player mapping, library browse, stale-response guard and status polling')
