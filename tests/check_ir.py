from sable.pcp.ir import Decoder,KEYS
from sable.inputs.ir import command_for

def frame(decoder,key,start=1,address=0x77E1):
 now=start;decoder.edge(False,now);now+=.009;decoder.edge(True,now);now+=.0045;decoder.edge(False,now)
 result=None
 for bit in format((address<<16)|(key<<8)|0x5D,'032b'):
  now+=.000574;decoder.edge(True,now);now+=.001668 if bit=='1' else .000547
  result=decoder.edge(False,now)
 return result,now
for code,key in KEYS.items():
 d=Decoder(pair_id=0x5D);result,now=frame(d,code);assert result==(key,False)
 now+=.04;d.edge(False,now);now+=.009;d.edge(True,now);now+=.002242
 assert d.edge(False,now)==(key,True)
assert frame(Decoder(pair_id=0x5D),0xC0,address=0x1234)[0] is None
assert command_for('KEY_ENTER','browse',True)==('select',None)
assert command_for('KEY_PLAY','browse',True)==('toggle',None)
assert command_for('KEY_LEFT','home',True)==('scroll',-1)
assert command_for('KEY_UP','modern',True)==('volume','+')
print('PASS: captured Apple codes, repeats, unknown remote rejection and context mapping')
from unittest.mock import Mock
from types import SimpleNamespace
from sable.pcp.runner import PiCoreMenu
m=object.__new__(PiCoreMenu)
remote=Mock();remote.is_alive.return_value=True
m.app=SimpleNamespace(ir_remote=remote,show_osd=Mock(),settings=Mock(),listener=SimpleNamespace(dispatch=lambda f:f()))
m._wifi_jobs=Mock()
m._pair_ir();remote.begin_pair.call_args.args[0](0x5D)
m.app.settings.set.assert_called_once_with('ir','pair_id',0x5D)
m._wifi_jobs.submit.assert_called_once()
m.app.settings.reset_mock();m._wifi_jobs.reset_mock()
m._pair_ir();remote.begin_pair.call_args.args[0](None)
m.app.settings.set.assert_not_called();m._wifi_jobs.submit.assert_not_called()
print('PASS: Settings pairing persists new ID and backup; timeout keeps original ID')
