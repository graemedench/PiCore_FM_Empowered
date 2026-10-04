"""Timing, pause/resume, tone response and actual small-screen rendering."""
import math
from types import SimpleNamespace
from unittest.mock import Mock,patch
from PIL import Image,ImageDraw,ImageFont
from sable.pcp.visual_layouts import Cycle
from sable.pcp.spectrum import analyse,N
from sable.pcp.modern import FM4Modern

c=Cycle(0)
assert c.update(0,True,('a',))[0] is False
assert c.update(4.99,True,('a',))[0] is False
assert c.update(5,True,('a',))[0] is True
c.interact(6);assert not c.update(10.99,True,('a',))[0]
assert c.update(11,True,('a',))[0]
assert c.update(12,True,('b',))==(True,True)
assert c.update(14,True,('b',))==(True,False)
assert not c.update(15,False,('b',))[0]
assert not c.update(16,True,('b',))[0]
assert analyse([0]*N,44100)==[0.]*24
low=analyse([16000*math.sin(2*math.pi*200*i/44100) for i in range(N)],44100)
high=analyse([16000*math.sin(2*math.pi*5000*i/44100) for i in range(N)],44100)
assert low.index(max(low)) < high.index(max(high))
for theme in ('panel_vu','panel_spectrum','panel_ppm'):
 st=SimpleNamespace(uri='a',title='Dancing Queen',artist='ABBA',status='play')
 app=SimpleNamespace(settings=SimpleNamespace(get=lambda *a,**k:theme),store=SimpleNamespace(get=lambda:st),soft_stopped=lambda:False,fonts=SimpleNamespace(get=lambda *a:ImageFont.load_default()),levels=SimpleNamespace(peaks=lambda:[.6,.8],read=lambda:[.6,.8],spectrum=lambda:high))
 with patch('time.monotonic',return_value=0):screen=FM4Modern(app)
 screen._render_panel=Mock()
 for now in (0,5,6,8):
  if now==6:st.title='Knowing Me, Knowing You'
  canvas=Image.new('L',(256,64))
  with patch('time.monotonic',return_value=now):screen.render(canvas,ImageDraw.Draw(canvas),256,64)
  if now:assert canvas.getbbox()
  if now==5:canvas.save('outputs/'+theme+'-preview.png')
 assert screen._render_panel.call_count==1
c=Cycle(0)
c.update(0,True,'a',4)
assert c.update(10,True,'b',4)==(True,True)
assert c.update(13.99,True,'b',4)==(True,True)
assert c.update(14,True,'b',4)==(True,False)
print('PASS: 5s interaction, 4s VU/PPM and 2s spectrum titles; all three layouts render')

from sable.pcp.clock import progress_pie
pixels=[]
for fraction in (0,.25,.5,1):
 canvas=Image.new('L',(256,64));progress_pie(ImageDraw.Draw(canvas),256,64,fraction)
 pixels.append(sum(v==220 for v in canvas.getdata()))
assert pixels==sorted(pixels) and len(set(pixels))==4
print('PASS: whole-disc clock pie fills monotonically')

# Peak needle holds while fast level input drops, then releases.
app.levels.peaks=lambda:[.8,.6]
with patch('time.monotonic',return_value=0):screen=FM4Modern(app)
screen._render_panel=Mock()
for now in (0,5):
 with patch('time.monotonic',return_value=now):screen.render(canvas,ImageDraw.Draw(canvas),256,64)
assert screen._ppm==[.8,.6]
app.levels.peaks=lambda:[.1,.1]
with patch('time.monotonic',return_value=5.9):screen.render(canvas,ImageDraw.Draw(canvas),256,64)
assert screen._ppm==[.8,.6]
with patch('time.monotonic',return_value=6.1):screen.render(canvas,ImageDraw.Draw(canvas),256,64)
assert .1 < screen._ppm[0] < .8
print('PASS: one-second peak hold then slow release')
