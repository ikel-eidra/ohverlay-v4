"""
Lightweight Perlin noise implementation for organic fish animation.
Uses permutation table and gradient interpolation for smooth, natural motion.
"""

import numpy as np


class PerlinNoise:
    """CPU-efficient Perlin noise generator for procedural animation."""

    def __init__(self, seed=0):
        rng = np.random.RandomState(seed)
        self.p = np.arange(256, dtype=int)
        rng.shuffle(self.p)
        self.p = np.tile(self.p, 2)

    @staticmethod
    def _fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def _lerp(a, b, t):
        return a + t * (b - a)

    @staticmethod
    def _grad(h, x, y):
        vectors = [(1, 1), (-1, 1), (1, -1), (-1, -1),
                   (1, 0), (-1, 0), (0, 1), (0, -1)]
        g = vectors[h % 8]
        return g[0] * x + g[1] * y

    def noise2d(self, x, y):
        """Generate 2D Perlin noise value at (x, y). Returns value in [-1, 1]."""
        xi = int(np.floor(x)) & 255
        yi = int(np.floor(y)) & 255
        xf = x - np.floor(x)
        yf = y - np.floor(y)

        u = self._fade(xf)
        v = self._fade(yf)

        aa = self.p[self.p[xi] + yi]
        ab = self.p[self.p[xi] + yi + 1]
        ba = self.p[self.p[xi + 1] + yi]
        bb = self.p[self.p[xi + 1] + yi + 1]

        x1 = self._lerp(self._grad(aa, xf, yf), self._grad(ba, xf - 1, yf), u)
        x2 = self._lerp(self._grad(ab, xf, yf - 1), self._grad(bb, xf - 1, yf - 1), u)

        return self._lerp(x1, x2, v)

    def octave_noise(self, x, y, octaves=3, persistence=0.5):
        """Multi-octave Perlin noise for richer organic motion."""
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0

        for _ in range(octaves):
            total += self.noise2d(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.0

        return total / max_value
