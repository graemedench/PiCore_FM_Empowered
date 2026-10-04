"""Known ABBA disc identity, cache, offline fallback and status decoration."""
from tempfile import TemporaryDirectory
from unittest.mock import patch
from sable.pcp.cd_metadata import Metadata, disc_id
starts = [150,17515,35788,54268,70278,90938,109965,131180,153280,167235,182308,206655,225740,249063,271020,285533,303335,325368,342593]
entries = [(i+1,n-150,False) for i,n in enumerate(starts)] + [(170,355200-150,False)]
assert disc_id(entries) == 'AB12Fy4NMHcV7o5ADcvL.gBANHs-'
with TemporaryDirectory() as root:
 m=Metadata(root);m.cache['disc']=dict(album='Gold',albumart='https://example.org/art.jpg',tracks={'3':dict(title='Take a Chance on Me',artist='ABBA')})
 state=dict(uri='http://127.0.0.1:9180/cd/disc/3.wav');m.decorate(state)
 assert state['title']=='Take a Chance on Me' and state['album']=='Gold'
 d=dict(id='unknown',entries=entries,tracks=[dict(number=1)])
 with patch('sable.pcp.cd_metadata.get_json',side_effect=OSError('offline')) as request:
  m.apply(d,True);m.apply(d,True);assert request.call_count==1
 assert 'title' not in d['tracks'][0]
print('PASS: disc identity, metadata decoration, offline fallback and retry cooldown')
