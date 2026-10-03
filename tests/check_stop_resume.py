"""Check held-stop resume through the app and actual Lyrion player."""
from sable.pcp.runner import PiCoreApp
from sable.pcp.listener import LyrionListener, state_from_status
from sable.settings import Settings
from sable.display.sim import SimDisplay
import tempfile

app = PiCoreApp(SimDisplay(256, 64, frames_dir=None, ascii_preview=False),
                Settings(tempfile.mktemp()), dry_run=True)
l = LyrionListener(app.store, lambda cb: cb())
app.listener = l
before = l.rpc(['status', '-', '1', 'tags:adKcu'])
def flush():
    l._commands.submit(lambda: None).result(timeout=8)
def state():
    return l.rpc(['status', '-', '1', 'tags:adKcu'])
try:
    l.rpc(['play'])
    app.store.apply_pushstate(state_from_status(state()))
    app.go('modern')
    app.handle('soft_stop')
    flush()
    assert app.soft_stopped()
    assert state()['mode'] == 'pause'
    app.store.apply_pushstate(state_from_status(state()))
    app.handle('play_pause')
    flush()
    after = state()
    assert after['mode'] == 'play', 'Held Stop did not resume'
    assert not app.soft_stopped(), 'STOPPED display latch persisted'
    assert app._soft_stop_timer is None, 'Delayed stop timer still armed'
    assert after['playlist_cur_index'] == before['playlist_cur_index'], 'Track changed'
    # Also exercise the real stop reached after the soft-stop grace period.
    app.handle('soft_stop')
    flush()
    app._cancel_soft_stop()
    l.rpc(['stop'])
    app.handle('play_pause')
    flush()
    assert state()['mode'] == 'play', 'Tap did not resume a hard-stopped player'
    print('PASS: held Stop -> tap resumes same track; timer/latch cleared; hard Stop -> tap resumes')
finally:
    app._cancel_soft_stop()
    app._cancel_stop_timer()
    app._cancel_pause_timer()
    app._cancel_playback_settle()
    l.rpc(['pause', '1'] if before['mode'] == 'pause' else [before['mode']])
    l._commands.shutdown(wait=True)
    l._browse.shutdown(wait=True)
