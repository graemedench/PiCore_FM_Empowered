"""Exact album/artist artwork lookup; never block the UI."""
import json, urllib.request, urllib.parse, time
from concurrent.futures import ThreadPoolExecutor
jobs=ThreadPoolExecutor(1)
cache={}
retry_at={}
def decorate(state):
    if state.get('albumart'): return
    key=(state.get('artist','').strip(),state.get('album','').strip(),state.get('title','').strip())
    if not all(key): return
    if key not in cache or (not cache[key] and time.monotonic() >= retry_at.get(key, float('inf'))):
        cache[key]=''
        retry_at[key]=float('inf')
        jobs.submit(lookup,key)
    state['albumart']=cache[key]
def lookup(key):
    try:
        time.sleep(1.1)
        artist,album,title=key
        query='release:"%s" AND artist:"%s"' % (album.replace('"',' '),artist.replace('"',' '))
        url='https://musicbrainz.org/ws/2/release/?'+urllib.parse.urlencode(dict(query=query,fmt='json',limit=20))
        request=urllib.request.Request(url,headers={'User-Agent':'Sable-piCorePlayer/0.1 (https://github.com/graemedench/PiCore_FM_Empowered)'})
        with urllib.request.urlopen(request,timeout=8) as response: rows=json.load(response).get('releases',[])
        time.sleep(1.1)
        recording_query='recording:"%s" AND artist:"%s"' % (title.replace('"',' '),artist.replace('"',' '))
        recording_url='https://musicbrainz.org/ws/2/recording/?'+urllib.parse.urlencode(dict(query=recording_query,fmt='json',limit=5))
        request=urllib.request.Request(recording_url,headers={'User-Agent':'Sable-piCorePlayer/0.1 (https://github.com/graemedench/PiCore_FM_Empowered)'})
        with urllib.request.urlopen(request,timeout=8) as response: recordings=json.load(response).get('recordings',[])
        for recording in recordings:
            credits=[x.get('name','').casefold() for x in recording.get('artist-credit',[]) if isinstance(x,dict)]
            if recording.get('title','').casefold()==title.casefold() and artist.casefold() in credits:
                for release in recording.get('releases',[]):
                    release=dict(release)
                    release['_recording_match']=True
                    rows.append(release)
        for row in rows:
            artists=[x.get('name','').casefold() for x in row.get('artist-credit',[]) if isinstance(x,dict)]
            if row.get('_recording_match') or (row.get('title','').casefold()==album.casefold() and artist.casefold() in artists):
                art='https://coverartarchive.org/release/'+row['id']+'/front-250'
                try:
                    with urllib.request.urlopen(art,timeout=8) as response:
                        data=response.read(2000000)
                    import io,hashlib
                    from pathlib import Path
                    from PIL import Image
                    Image.open(io.BytesIO(data)).verify()
                    name='receiver-cover-'+hashlib.sha256(data).hexdigest()[:16]+'.img'
                    (Path('/var/www')/name).write_bytes(data)
                    cache[key]='http://127.0.0.1/'+name
                    return
                except Exception:
                    continue
    except Exception as exc: print('Receiver art:',type(exc).__name__)
    finally: retry_at[key]=time.monotonic()+300
