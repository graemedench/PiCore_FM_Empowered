"""A selected CD track loads the whole disc, preserves modes and rejects stale discs."""
from types import SimpleNamespace
from unittest.mock import Mock
from sable.pcp.listener import LyrionListener

listener = LyrionListener(None, lambda fn: fn())
listener._commands.shutdown()
class Immediate:
    def submit(self, fn):
        fn()
listener._commands = Immediate()
listener.cd = SimpleNamespace(inspect=lambda **kwargs: dict(id='disc', tracks=[
    dict(number=number) for number in (1, 2, 3)]))
listener.rpc = Mock()
listener._return_local = Mock()
url = 'http://127.0.0.1:9180/cd/disc/2.wav'
listener.play_item(dict(uri=url, title='Track 02', service='cd_controller'))
commands = [call.args[0] for call in listener.rpc.call_args_list]
assert commands[0] == ['playlist', 'clear']
assert [c[2] for c in commands[1:4]] == [url.replace('/2.wav', '/%d.wav' % n) for n in (1, 2, 3)]
assert commands[-1] == ['playlist', 'index', '1']
assert not any(c[1] in ('repeat', 'shuffle') for c in commands)
listener.rpc.reset_mock()
listener.play_uri(url.replace('/disc/', '/old-disc/'))
listener.rpc.assert_not_called()
listener.play_all([dict(uri=url.replace('/2.wav', '/1.wav'), service='cd_controller')])
assert listener.rpc.call_args.args[0] == ['playlist', 'index', '0']
listener.rpc.reset_mock()
listener.play_all([dict(uri='file:///a'), dict(uri='file:///b'), dict(uri='file:///c')], start=1)
assert listener.rpc.call_args.args[0] == ['playlist', 'index', '1']
assert len(listener.rpc.call_args_list) == 5
listener.rpc.reset_mock()
listener.play_item(dict(uri='file:///b', _queue_index=1))
assert listener.rpc.call_args.args[0] == ['playlist', 'index', '1']
assert len(listener.rpc.call_args_list) == 1
listener._browse.shutdown()
print('PASS: selected track queues full disc at correct index; modes preserved; stale disc rejected')
