"""Routing, persisted selection, and rollback without changing real hardware."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace
from sable.pcp import outputs

with TemporaryDirectory() as root:
 config=Path(root)/'pcp.cfg';alsa=Path(root)/'asoundrc'
 config.write_text('OUTPUT="hw:CARD=Headphones"\n');alsa.write_text('pcm.fm4_receiver {\n slave.pcm "hw:CARD=AUDIO"\n}\n')
 original=(config.read_text(),alsa.read_text())
 target='hw:CARD=AUDIO,DEV=0'
 real_path=Path
 def paths(value):
  return alsa if str(value)=='/home/tc/.asoundrc' else real_path(value)
 with patch.object(outputs,'CONFIG',config),patch.object(outputs,'Path',side_effect=paths),patch.object(outputs,'devices',return_value=[dict(id=target,name='USB DAC')]),patch('subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='Backup successful')) as run,patch('time.sleep'):
  outputs.change(target)
  assert outputs.current()==target and target in alsa.read_text()
  assert run.call_args.args[0]==['pcp','bu']
  config.write_text(original[0]);alsa.write_text(original[1])
  calls=[]
  def fail(command,**kwargs):
   calls.append(command)
   if command[-1]=='start':raise RuntimeError('device failed')
   return SimpleNamespace(returncode=0,stdout='Backup successful')
  run.side_effect=fail
  try:outputs.change(target)
  except RuntimeError:pass
  else:raise AssertionError('Expected rollback')
  assert (config.read_text(),alsa.read_text())==original
print('PASS: music/receiver route, backup and failed-switch rollback')
