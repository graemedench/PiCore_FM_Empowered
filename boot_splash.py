"""Early OLED status, with explicit release before the full panel starts."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from PIL import Image, ImageDraw, ImageFont
from panel import Serial
from luma.oled.device import ssd1322

STOP = Path('/tmp/fm4-boot-oled.stop')
PID = Path('/tmp/fm4-boot-oled.pid')


def status(text):
    stages = [('Waiting for valid date', 'Synchronising time'),
              ('Starting LMS', 'Starting music server'),
              ('Waiting for LMS to initiate', 'Waiting for music server'),
              ('Starting Squeezelite', 'Starting audio player'),
              ('Starting Samba', 'Starting file sharing'),
              ('Starting user commands', 'Opening your panel')]
    found = [(text.rfind(token), label) for token, label in stages if token in text]
    return max(found)[1] if found else 'Starting piCorePlayer'


def main():
    STOP.unlink(missing_ok=True)
    PID.write_text(str(os.getpid()))
    running = True
    def stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGTERM, stop)
    serial = Serial()
    device = ssd1322(serial, width=256, height=64)
    font = ImageFont.truetype('/home/tc/quadify-pcp/arial.ttf', 12)
    title = ImageFont.truetype('/home/tc/quadify-pcp/arial.ttf', 19)
    start = time.monotonic()
    log = Path('/var/log/pcp_boot.log')
    leds = subprocess.Popen([sys.executable, '-u', '-m', 'sable.boot_indicator'])
    try:
        while running and not STOP.exists() and time.monotonic() - start < 180:
            text = log.read_text(errors='replace')[-16000:] if log.exists() else ''
            image = Image.new('RGB', (256, 64))
            draw = ImageDraw.Draw(image)
            draw.text((8, 3), 'FM4', font=title, fill='white')
            draw.text((8, 29), status(text), font=font, fill='white')
            draw.text((8, 48), 'Booting', font=font, fill='white')
            # Activity indicator, not an invented completion percentage.
            x = 235 if int(time.monotonic() * 2) % 2 else 243
            draw.ellipse((x, 51, x+4, 55), fill='white')
            device.display(image)
            time.sleep(.5)
    finally:
        leds.terminate()
        try:
            leds.wait(timeout=3)
        except subprocess.TimeoutExpired:
            leds.kill()
            leds.wait()
        device.cleanup()
        PID.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
