from engine.perlin import PerlinNoise


def test_perlin_range():
    pn = PerlinNoise(seed=0)
    for x in range(10):
        for y in range(10):
            val = pn.noise2d(x * 0.1, y * 0.1)
            assert -1.5 <= val <= 1.5


def test_perlin_deterministic():
    pn1 = PerlinNoise(seed=42)
    pn2 = PerlinNoise(seed=42)
    for i in range(10):
        assert pn1.noise2d(i * 0.5, i * 0.3) == pn2.noise2d(i * 0.5, i * 0.3)


def test_perlin_different_seeds():
    pn1 = PerlinNoise(seed=0)
    pn2 = PerlinNoise(seed=99)
    diffs = sum(
        1 for i in range(10)
        if pn1.noise2d(i * 0.5, i * 0.3) != pn2.noise2d(i * 0.5, i * 0.3)
    )
    assert diffs > 0


def test_perlin_octave():
    pn = PerlinNoise(seed=42)
    val = pn.octave_noise(1.0, 2.0, octaves=3)
    assert -1.5 <= val <= 1.5
