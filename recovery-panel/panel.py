#!/usr/bin/env python3
"""Quadify SSD1322 and encoder bridge for piCorePlayer (GPIO character API)."""
import argparse
import fcntl
import json
import logging
import os
import queue
import signal
import socket
import struct
import sys
import threading
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'vendor'))
import gpiod
from gpiod.line import Bias, Direction, Value
from PIL import Image, ImageDraw, ImageFont
from luma.oled.device import ssd1322
from luma.core.framebuffer import diff_to_previous

log = logging.getLogger('quadify')


class Serial:
    """Luma transport using Linux SPI and gpiod instead of RPi.GPIO."""
    def __init__(self):
        self.lines = gpiod.request_lines('/dev/gpiochip0', consumer='quadify-oled',
            config={(24, 25): gpiod.LineSettings(direction=Direction.OUTPUT,
                                                  output_value=Value.INACTIVE)})
        self.fd = os.open('/dev/spidev0.0', os.O_RDWR)
        fcntl.ioctl(self.fd, 0x40016b01, struct.pack('B', 0))
        fcntl.ioctl(self.fd, 0x40016b03, struct.pack('B', 8))
        fcntl.ioctl(self.fd, 0x40046b04, struct.pack('I', 8000000))
        time.sleep(.3)
        self.lines.set_value(25, Value.ACTIVE)
        time.sleep(.2)

    def command(self, *data):
        self.lines.set_value(24, Value.INACTIVE)
        os.write(self.fd, bytes(data))

    def data(self, data):
        self.lines.set_value(24, Value.ACTIVE)
        data = bytes(data)
        for pos in range(0, len(data), 4096):
            chunk = data[pos:pos + 4096]
            if os.write(self.fd, chunk) != len(chunk):
                raise OSError('Incomplete SPI write')

    def cleanup(self):
        if self.fd is not None:
            self.lines.set_value(25, Value.INACTIVE)
            os.close(self.fd)
            self.fd = None
            self.lines.release()


class Decoder:
    TABLE = {1: 1, 7: 1, 14: 1, 8: 1, 2: -1, 4: -1, 13: -1, 11: -1}
    def __init__(self):
        self.previous = None
        self.acc = 0

    def feed(self, clk, dt):
        state = clk * 2 + dt
        if self.previous is not None:
            code = self.previous * 4 + state
            if self.previous != state and code not in self.TABLE:
                self.acc = 0
            else:
                self.acc += self.TABLE.get(code, 0)
        self.previous = state
        if state == 3:
            step = (self.acc >= 3) - (self.acc <= -3)
            self.acc = 0
            return step
        return 0


class Encoder(threading.Thread):
    def __init__(self, events, stop, reverse=True):
        super().__init__(daemon=True, name='encoder')
        self.events, self.stop, self.reverse = events, stop, reverse
        self.lines = gpiod.request_lines('/dev/gpiochip0', consumer='quadify-encoder',
            config={(13, 5, 6): gpiod.LineSettings(direction=Direction.INPUT,
                                                 bias=Bias.PULL_UP)})

    def run(self):
        decoder = Decoder()
        down = None
        raw = stable = False
        changed = time.monotonic()
        try:
            while not self.stop.is_set():
                clk, dt, sw = [v == Value.ACTIVE for v in self.lines.get_values([13, 5, 6])]
                step = decoder.feed(int(clk), int(dt))
                if step:
                    self.events.put(('turn', -step if self.reverse else step))
                    log.info('Encoder detent %s', -step if self.reverse else step)
                now = time.monotonic()
                pressed = not sw
                if pressed != raw:
                    raw, changed = pressed, now
                if raw != stable and now - changed >= .025:
                    stable = raw
                    if stable:
                        down = now
                    elif down is not None:
                        kind = 'long' if now - down >= 1.5 else 'click'
                        self.events.put((kind, 0))
                        log.info('Encoder %s', kind)
                        down = None
                self.stop.wait(.001)
        except Exception:
            log.exception('Encoder input failed')
            self.events.put(('error', 'Encoder error'))
        finally:
            self.lines.release()


class LMS(threading.Thread):
    def __init__(self, events, stop, server=None):
        super().__init__(daemon=True, name='music-server')
        self.events, self.stop, self.server = events, stop, server
        self.commands = queue.Queue()
        self.player = None

    def discover(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(2)
            sock.sendto(b'eNAME\0JSON\0', ('255.255.255.255', 3483))
            packet, address = sock.recvfrom(2048)
        port, pos = 9000, 1
        while pos + 5 <= len(packet):
            tag, size = packet[pos:pos+4], packet[pos+4]
            value = packet[pos+5:pos+5+size]
            if tag == b'JSON':
                port = int(value)
            pos += 5 + size
        return 'http://%s:%d' % (address[0], port)

    def rpc(self, player, command):
        data = json.dumps({'id': 1, 'method': 'slim.request',
                           'params': [player, command]}).encode()
        request = urllib.request.Request(self.server.rstrip('/') + '/jsonrpc.js',
            data, {'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=3) as reply:
            body = json.load(reply)
        if body.get('error'):
            raise RuntimeError(str(body['error']))
        return body.get('result', {})

    def run(self):
        retry = 0
        while not self.stop.is_set():
            try:
                if not self.server:
                    self.server = self.discover()
                    log.info('Found music server %s', self.server)
                if not self.player:
                    players = self.rpc('', ['players', '0', '100']).get('players_loop', [])
                    match = [p for p in players if p.get('ip', '').split(':')[0] == '192.168.1.18'
                             or p.get('name') == 'FM4-Reborn']
                    if len(match) != 1:
                        raise RuntimeError('FM4-Reborn player not uniquely identified')
                    self.player = match[0]['playerid']
                    log.info('Using player %s', self.player)
                while True:
                    try:
                        command = self.commands.get_nowait()
                    except queue.Empty:
                        break
                    self.rpc(self.player, command)
                status = self.rpc(self.player, ['status', '-', '1', 'tags:ad'])
                self.events.put(('status', status))
                retry = 0
                self.stop.wait(.5)
            except Exception as exc:
                if retry == 0:
                    log.warning('Music server unavailable: %s', exc)
                retry += 1
                # Never replay stale control commands after reconnection.
                while not self.commands.empty():
                    try:
                        self.commands.get_nowait()
                    except queue.Empty:
                        break
                self.events.put(('offline', str(exc)))
                self.player = None
                self.stop.wait(5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', help='Lyrion URL, e.g. http://192.168.1.10:9000')
    parser.add_argument('--rotate', type=int, choices=[0, 180], default=0)
    parser.add_argument('--normal-encoder', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    lock = open('/tmp/quadify-panel.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    stop, events = threading.Event(), queue.Queue()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    serial = Serial()
    display = ssd1322(serial_interface=serial, width=256, height=64, mode='RGB',
                      rotate=args.rotate // 90, framebuffer=diff_to_previous())
    display.clear()
    display.contrast(160)
    fontfile = BASE / 'arial.ttf'
    font = ImageFont.truetype(str(fontfile), 12)
    titlefont = ImageFont.truetype(str(fontfile), 16)
    encoder = Encoder(events, stop, not args.normal_encoder)
    music = LMS(events, stop, args.server)
    encoder.start()
    music.start()
    log.info('Panel ready: SPI0 CE0, DC24 RST25; encoder CLK13 DT5 SW6')
    mode, selected, detents, clicks, last_input = 'home', 0, 0, 0, time.monotonic()
    status, online, brightness = {}, False, 160
    items = ['Now Playing', 'Play / Pause', 'Next Track', 'Previous Track',
             'Encoder Test', 'Brightness', 'Clock']
    frame_due = 0
    previous_frame = None

    def text(draw, pos, value, face=font, fill=220):
        value = str(value)
        while value and draw.textbbox((0, 0), value, font=face)[2] > 250:
            value = value[:-1]
        draw.text(pos, value, font=face, fill=(fill, fill, fill))

    try:
        while not stop.is_set():
            now = time.monotonic()
            while not events.empty():
                kind, value = events.get_nowait()
                if kind == 'status':
                    status, online = value, True
                elif kind == 'offline':
                    online = False
                elif kind == 'error':
                    log.error(value)
                else:
                    last_input = now
                    if kind == 'turn':
                        detents += value
                        if mode == 'menu':
                            selected = (selected + value) % len(items)
                        elif mode == 'brightness':
                            brightness = max(16, min(255, brightness + value * 8))
                            display.contrast(brightness)
                        elif mode == 'home' and online:
                            music.commands.put(['mixer', 'volume', '%+d' % (value * 2)])
                    elif kind == 'long':
                        mode = 'home'
                    elif kind == 'click':
                        clicks += 1
                        if mode == 'menu':
                            choice = items[selected]
                            if choice == 'Now Playing':
                                mode = 'home'
                            elif choice in ['Play / Pause', 'Next Track', 'Previous Track']:
                                if online:
                                    command = {'Play / Pause': ['pause'],
                                               'Next Track': ['playlist', 'index', '+1'],
                                               'Previous Track': ['playlist', 'index', '-1']}[choice]
                                    music.commands.put(command)
                                    mode = 'home'
                            elif choice == 'Encoder Test':
                                mode = 'test'
                            elif choice == 'Brightness':
                                mode = 'brightness'
                            elif choice == 'Clock':
                                mode = 'clock'
                        else:
                            mode = 'menu'
            if mode not in ['home', 'clock', 'test'] and now - last_input > 15:
                mode = 'home'
            if now < frame_due:
                stop.wait(.01)
                continue
            frame_due = now + .1
            image = Image.new('RGB', (256, 64))
            draw = ImageDraw.Draw(image)
            if mode == 'menu':
                text(draw, (2, 0), 'QUADIFY  /  MENU', titlefont)
                for row in range(3):
                    idx = (selected + row - 1) % len(items)
                    text(draw, (3, 20 + row * 14), ('> ' if idx == selected else '  ') + items[idx],
                         fill=255 if idx == selected else 130)
            elif mode == 'test':
                text(draw, (2, 0), 'ENCODER TEST', titlefont)
                text(draw, (2, 23), 'Position: %d   Clicks: %d' % (detents, clicks))
                text(draw, (2, 46), 'Turn to test; hold to return')
            elif mode == 'brightness':
                text(draw, (2, 0), 'BRIGHTNESS', titlefont)
                text(draw, (2, 25), '%d / 255' % brightness)
                text(draw, (2, 46), 'Turn to adjust; press for menu')
            elif mode == 'clock' or not online:
                text(draw, (2, 0), 'QUADIFY  /  piCorePlayer', titlefont)
                text(draw, (2, 24), time.strftime('%H:%M:%S   %a %d %b'))
                text(draw, (2, 47), 'Press knob for menu' if mode == 'clock' else 'Server offline - press for menu')
            else:
                track = (status.get('playlist_loop') or [{}])[0]
                text(draw, (2, 0), track.get('title') or 'FM4-Reborn', titlefont)
                text(draw, (2, 23), track.get('artist') or track.get('album') or 'piCorePlayer')
                volume = status.get('mixer volume', '?')
                text(draw, (2, 45), '%s   Volume %s%%   Press: menu' % (status.get('mode', '').upper(), volume))
                duration = float(status.get('duration') or 0)
                if duration:
                    width = max(0, min(255, int(255 * float(status.get('time') or 0) / duration)))
                    draw.line((0, 63, width, 63), fill=(180, 180, 180))
            pixels = image.tobytes()
            if pixels != previous_frame:
                display.display(image)
                previous_frame = pixels
    finally:
        stop.set()
        encoder.join(2)
        display.cleanup()
        lock.close()
        log.info('Panel stopped')


if __name__ == '__main__':
    main()
