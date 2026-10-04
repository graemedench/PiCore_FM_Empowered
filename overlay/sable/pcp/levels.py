"""Read real stereo PCM levels from Squeezelite's Linux visualizer shared memory.

Format reference: ralph-irving/squeezelite output_vis.c. Linux 64-bit time_t,
16,384 signed 16-bit samples. A nonblocking shared read lock only covers copying;
level calculations run after releasing it so audio output is never held up.
"""
import ctypes
import json
import math
import mmap
import struct
import time
from pathlib import Path


class AudioLevels:
    def __init__(self, player):
        self.path = Path('/dev/shm/squeezelite-' + player)
        self.mapping = None
        self.levels = [0.0, 0.0]
        self.retry_at = 0

    @property
    def available(self):
        if self.mapping is None and time.monotonic() >= self.retry_at:
            self.retry_at = time.monotonic() + 2
            try:
                with self.path.open('r+b') as handle:
                    self.mapping = mmap.mmap(handle.fileno(), 0)
                self.offset = len(self.mapping) - 32768 - 24
                if self.offset < 32:
                    raise ValueError('Unsupported visualizer layout')
                size = struct.unpack_from('<I', self.mapping, self.offset)[0]
                if size != 16384:
                    raise ValueError('Unsupported visualizer buffer size')
                self.lib = ctypes.CDLL('libpthread.so.0')
                self.lib.pthread_rwlock_tryrdlock.argtypes = [ctypes.c_void_p]
                self.lib.pthread_rwlock_unlock.argtypes = [ctypes.c_void_p]
                self.address = ctypes.addressof(ctypes.c_char.from_buffer(self.mapping))
            except (OSError, ValueError):
                self.close()
        return self.mapping is not None

    def read(self):
        target = [0.0, 0.0]
        if Path('/tmp/fm4-receiver.json').exists():
            try:
                frame = json.loads(Path('/tmp/fm4-receiver-levels.json').read_text())
                if time.time() - frame['updated'] < .3:
                    target = frame['levels']
            except (OSError, ValueError, KeyError):
                pass
            self.levels = [max(value, old - .12) for value, old in zip(target, self.levels)]
            return self.levels
        if self.available and self.lib.pthread_rwlock_tryrdlock(self.address) == 0:
            try:
                size, index, running, rate, updated = struct.unpack_from(
                    '<IIB3xIq', self.mapping, self.offset)
                raw = self.mapping[self.offset + 24:]
            finally:
                self.lib.pthread_rwlock_unlock(self.address)
            if running and time.time() - updated < 2 and index < size and index % 2 == 0:
                samples = struct.unpack('<16384h', raw)
                count = 1024
                for channel in range(2):
                    power = sum(samples[(index - 2 * frame + channel) % size] ** 2
                                for frame in range(1, count + 1)) / count
                    rms = math.sqrt(power) / 32768
                    db = 20 * math.log10(max(rms, 1e-6))
                    target[channel] = max(0.0, min(1.0, (db + 50) / 50))
        self.levels = [max(value, old - .12) for value, old in zip(target, self.levels)]
        return self.levels

    def close(self):
        if self.mapping is not None:
            self.mapping.close()
            self.mapping = None
