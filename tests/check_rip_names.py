from pathlib import Path
from tempfile import TemporaryDirectory
from sable.pcp.rip_names import album_name,track_name,new_folder,safe_name
assert album_name({'artist':'ABBA','album':'Gold: Greatest Hits'})=='ABBA - Gold Greatest Hits'
for fmt in ('flac','mp3'):
 assert track_name({'number':1,'title':'Dancing Queen'},fmt)=='01 - Dancing Queen.'+fmt
assert safe_name('CON')=='_CON'
assert len(safe_name('É'*200).encode())<=180
assert '/' not in safe_name('a/b')
with TemporaryDirectory() as root:
 a=new_folder(Path(root),'Album');b=new_folder(Path(root),'Album')
 assert a.name=='Album' and b.name=='Album (2)'
print('PASS: FLAC/MP3 names, Windows compatibility and non-overwriting album folders')
