"""Bounded 1024-point FFT for real PCM; no optional numerical dependency."""
import cmath
import math

N = 1024
WINDOW = [0.5 - 0.5 * math.cos(2 * math.pi * i / (N - 1)) for i in range(N)]
REVERSE = [int(format(i, '010b')[::-1], 2) for i in range(N)]
TWIDDLES = {size: [cmath.exp(-2j * math.pi * k / size) for k in range(size // 2)]
            for size in (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)}


def analyse(samples, rate, scale=32768, bands=24):
    if len(samples) < N or rate <= 0:
        return [0.] * bands
    values = [samples[i] * WINDOW[i] / scale for i in range(N)]
    values = [complex(values[i]) for i in REVERSE]
    for size, factors in TWIDDLES.items():
        half = size // 2
        for start in range(0, N, size):
            for k, factor in enumerate(factors):
                even, odd = values[start+k], factor * values[start+k+half]
                values[start+k], values[start+k+half] = even + odd, even - odd
    # At low frequencies one FFT bin can cover several display bands.
    high = min(18000, rate / 2)
    edges = [60 * (high / 60) ** (i / bands) for i in range(bands+1)]
    result = []
    for low, upper in zip(edges, edges[1:]):
        first = max(1, min(N//2-1, int(low*N/rate)))
        last = max(first+1, min(N//2, int(upper*N/rate)+1))
        amplitude = max(abs(v) for v in values[first:last]) * 4 / N
        db = 20 * math.log10(max(amplitude, 1e-6))
        result.append(max(0., min(1., (db+60)/60)))
    return result
