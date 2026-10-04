"""Background extraction preserves other playback and receiver ownership."""
from unittest.mock import Mock, patch
from sable.pcp.listener import LyrionListener

class Immediate:
 def __init__(self,target,**kwargs):self.target=target
 def start(self):self.target()

for fmt in ('flac','mp3'):
 for uri in ('tidal://track/123','file:///music/song.flac','https://radio.example/live','http://127.0.0.1:9180/cd/disc/1.wav'):
  l=LyrionListener(None,lambda f:f())
  l.rpc=Mock(return_value={'playlist_loop':[{'url':uri}]})
  l._return_local=Mock();l.refresh_library=Mock()
  drive=dict(path='/mnt/sda2/Music');info=dict(disc={'id':'disc'},availableDrives=[drive])
  with patch('sable.pcp.listener.threading.Thread',Immediate),patch('sable.pcp.cd.rip_flac') as rip:
   assert l.rip_cd(info,drive,fmt)
   rip.assert_called_once()
   assert rip.call_args.kwargs['fmt']==fmt
   assert (['stop'] in [c.args[0] for c in l.rpc.call_args_list])==('/cd/' in uri)
   l._return_local.assert_not_called()
   assert not l._rip_lock.locked()
  l._commands.shutdown();l._browse.shutdown()
print('PASS: FLAC/MP3 preserve TIDAL/library/radio; only CD playback stops; receivers untouched')
