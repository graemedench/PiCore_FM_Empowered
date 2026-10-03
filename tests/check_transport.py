"""Exercise actual Lyrion controls, then restore playback and repeat/shuffle."""
import time
from sable.pcp.listener import LyrionListener

l = LyrionListener(None, lambda cb: None)
def status():
    return l.rpc(['status', '-', '1'])
def flush():
    l._commands.submit(lambda: None).result(timeout=8)

before = status()
try:
    for mode, repeat, shuffle in [('all', 0, 0), ('track', 1, 0),
                                  ('playlist', 2, 0), ('random', 0, 1),
                                  ('single', 0, 0)]:
        l.set_playback_mode(mode)
        flush()
        result = status()
        assert int(result['playlist repeat']) == repeat, (mode, result)
        assert int(result['playlist shuffle']) == shuffle, (mode, result)
        print('PASS mode:', mode, flush=True)
    for command, expected in [('play', 'play'), ('toggle', 'pause'),
                              ('toggle', 'play'), ('pause', 'pause')]:
        started = time.monotonic()
        l.transport(command)
        flush()
        deadline = time.monotonic() + 3
        while status()['mode'] != expected and time.monotonic() < deadline:
            time.sleep(.05)
        assert status()['mode'] == expected, command
        print('PASS transport:', command, round((time.monotonic()-started)*1000), 'ms', flush=True)
finally:
    l.rpc(['playlist', 'repeat', str(before['playlist repeat'])])
    l.rpc(['playlist', 'shuffle', str(before['playlist shuffle'])])
    l.rpc(['pause', '1'] if before['mode'] == 'pause' else [before['mode']])
    l._commands.shutdown(wait=True)
    l._browse.shutdown(wait=True)
print('Playback and mode settings restored', flush=True)
