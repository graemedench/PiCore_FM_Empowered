"""Drain an ALSA PCM copy and publish stereo RMS levels; no audio is stored."""
import json
import math
import struct
import sys
import time
from pathlib import Path


def levels(raw, bits):
    samples = struct.unpack('<' + ('h' if bits == 16 else 'i') * (len(raw) // (bits // 8)), raw)
    result = []
    for channel in range(2):
        values = samples[channel::2]
        rms = math.sqrt(sum(x*x for x in values) / max(1, len(values))) / (2 ** (bits-1))
        result.append(max(0., min(1., (20*math.log10(max(rms, 1e-6)) + 50)/50)))
    return result


def main():
    bits = int(sys.argv[1])
    if bits not in (16, 32):
        # Unsupported formats still drain rather than blocking sound.
        while sys.stdin.buffer.read(8192):
            pass
        return
    rate = int(sys.argv[2]) if len(sys.argv) > 2 else 44100
    from .spectrum import analyse
    output = Path('/tmp/fm4-receiver-levels.json')
    last = 0
    last_fft = 0
    bands = [0.] * 24
    while True:
        raw = sys.stdin.buffer.read(1024 * 2 * (bits // 8))
        if not raw:
            break
        now = time.monotonic()
        if now-last < .05:
            continue
        last = now
        try:
            samples = struct.unpack('<' + ('h' if bits == 16 else 'i') * (len(raw) // (bits // 8)), raw)
            mono = [(a+b)/2 for a,b in zip(samples[::2], samples[1::2])]
            if now-last_fft >= .05:
                bands = analyse(mono, rate, scale=2**(bits-1))
                last_fft = now
            frame = dict(updated=time.time(), levels=levels(raw, bits), spectrum=bands,
                         peaks=[max((abs(v) for v in samples[c::2]), default=0)/2**(bits-1) for c in range(2)])
            temporary = output.with_suffix('.new')
            temporary.write_text(json.dumps(frame))
            temporary.replace(output)
        except Exception:
            pass  # Keep draining even if publishing a meter frame fails.


if __name__ == '__main__':
    main()
