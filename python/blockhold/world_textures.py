"""Detailed world textures: the grass ground, ground paths and stone walls.

Unlike the pixel-art block tiles in textures.py these are larger, noisy and
smoothly filtered, closer to the look of the original game. They're generated
once and cached as PNGs in _generated_textures (bump VERSION to regenerate).
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw
from ursina import Texture

VERSION = 1
from .paths import TEXTURE_CACHE as CACHE_DIR


# ── noise helpers ────────────────────────────────────────────────────────────
def value_noise(size, cells, seed):
    """Smooth random noise that tiles seamlessly, as a list of floats 0..1."""
    rnd = random.Random(seed)
    small = Image.new('L', (cells, cells))
    small.putdata([int(rnd.random() * 255) for _ in range(cells * cells)])
    big = Image.new('L', (cells * 3, cells * 3))
    for i in range(3):
        for j in range(3):
            big.paste(small, (i * cells, j * cells))
    big = big.resize((size * 3, size * 3), Image.BICUBIC).crop((size, size, size * 2, size * 2))
    return [v / 255 for v in big.getdata()]


def fractal(size, seed, octaves):
    """Sum of noise layers: octaves = [(cells, weight), ...]. Returns floats roughly 0..1."""
    total = sum(w for _, w in octaves)
    out = [0.0] * (size * size)
    for k, (cells, w) in enumerate(octaves):
        layer = value_noise(size, cells, seed * 31 + k)
        for i, v in enumerate(layer):
            out[i] += v * w / total
    lo, hi = min(out), max(out)
    return [(v - lo) / max(1e-6, hi - lo) for v in out]


def lerp3(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def from_values(size, values, palette):
    """Colour an image from 0..1 values with a gradient palette [(t, rgb), ...]."""
    img = Image.new('RGB', (size, size))
    data = []
    for v in values:
        for (t0, c0), (t1, c1) in zip(palette, palette[1:]):
            if v <= t1:
                data.append(lerp3(c0, c1, (v - t0) / max(1e-6, t1 - t0)))
                break
        else:
            data.append(palette[-1][1])
    img.putdata(data)
    return img


def wrap_draw(draw, size, fn):
    """Call fn(dx, dy) for the 9 tile offsets so shapes near an edge wrap around."""
    for dx in (-size, 0, size):
        for dy in (-size, 0, size):
            fn(dx, dy)


def voronoi(size, n, seed, mortar=1.4):
    """Stones: returns (cell index per pixel, edge strength per pixel) for n tileable cells."""
    rnd = random.Random(seed)
    pts = [(rnd.random() * size, rnd.random() * size) for _ in range(n)]
    cells, edges = [], []
    for y in range(size):
        for x in range(size):
            best = second = 1e9
            bi = 0
            for i, (px, py) in enumerate(pts):
                dx = abs(x - px)
                dy = abs(y - py)
                dx = min(dx, size - dx)
                dy = min(dy, size - dy)
                d = dx * dx + dy * dy
                if d < best:
                    second, best, bi = best, d, i
                elif d < second:
                    second = d
            cells.append(bi)
            edges.append(max(0.0, 1 - (math.sqrt(second) - math.sqrt(best)) / mortar))
    return cells, edges


# ── the textures ─────────────────────────────────────────────────────────────
def grass(size=256):
    """Dry, patchy grass with blades and bits of soil (4 x 4 m of ground)."""
    n = fractal(size, 5, [(8, 0.15), (16, 0.3), (48, 0.32), (128, 0.23)])
    dry = fractal(size, 9, [(6, 0.5), (12, 0.5)])
    img = from_values(size, n, [(0, (44, 54, 26)), (0.45, (78, 92, 40)), (0.8, (104, 112, 52)), (1, (126, 126, 62))])
    over = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    rnd = random.Random(17)
    px = img.load()
    for _ in range(4200):
        x, y = rnd.random() * size, rnd.random() * size
        a = rnd.random() * math.tau
        length = 2 + rnd.random() * 5
        k = rnd.random()
        if k < 0.45:
            c = (150, 152, 74, 150)          # light, dry blade
        elif k < 0.8:
            c = (98, 122, 50, 140)           # green blade
        else:
            c = (30, 38, 18, 150)            # shadow
        x2, y2 = x + math.cos(a) * length, y + math.sin(a) * length
        wrap_draw(d, size, lambda dx, dy: d.line((x + dx, y + dy, x2 + dx, y2 + dy), fill=c, width=1))
    for _ in range(260):                     # soil specks
        x, y = rnd.random() * size, rnd.random() * size
        r = 0.6 + rnd.random() * 1.2
        c = (52, 40, 28, 170)
        wrap_draw(d, size, lambda dx, dy: d.ellipse((x + dx - r, y + dy - r, x + dx + r, y + dy + r), fill=c))
    img = Image.alpha_composite(img.convert('RGBA'), over).convert('RGB')
    # dry, yellowish patches
    px = img.load()
    for i, t in enumerate(dry):
        if t > 0.6:
            x, y = i % size, i // size
            k = min(1.0, (t - 0.6) * 2.2) * 0.45
            r, g, b = px[x, y]
            px[x, y] = (int(r + (150 - r) * k), int(g + (138 - g) * k), int(b + (70 - b) * k))
    return img


def _pebbles(img, rnd, count, colours, rmin, rmax):
    size = img.size[0]
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for _ in range(count):
        x, y = rnd.random() * size, rnd.random() * size
        rx, ry = rmin + rnd.random() * (rmax - rmin), rmin + rnd.random() * (rmax - rmin)
        c = rnd.choice(colours)
        wrap_draw(d, size, lambda dx, dy: d.ellipse((x + dx - rx, y + dy - ry, x + dx + rx, y + dy + ry), fill=c))
    return Image.alpha_composite(img.convert('RGBA'), over).convert('RGB')


def path_dirt(size=128):
    """Reddish gravelly dirt, like the paths in the original game (2 x 2 m)."""
    n = fractal(size, 21, [(4, 0.4), (12, 0.3), (32, 0.2), (96, 0.1)])
    img = from_values(size, n, [(0, (84, 58, 50)), (0.5, (116, 84, 72)), (1, (146, 112, 96))])
    rnd = random.Random(23)
    img = _pebbles(img, rnd, 900, [(166, 132, 116, 200), (72, 50, 42, 190), (132, 104, 92, 200)], 0.5, 1.6)
    return _pebbles(img, rnd, 40, [(180, 160, 150, 220), (96, 84, 78, 220)], 1.5, 2.6)


def path_gravel(size=128):
    n = fractal(size, 31, [(6, 0.4), (24, 0.35), (96, 0.25)])
    img = from_values(size, n, [(0, (82, 80, 76)), (0.5, (112, 110, 104)), (1, (140, 138, 132))])
    rnd = random.Random(33)
    return _pebbles(img, rnd, 1400, [(160, 158, 150, 220), (70, 68, 64, 210), (124, 118, 108, 220),
                                     (100, 96, 92, 220)], 0.8, 2.2)


def _stone_tile(size, n, seed, stones, mortar_col, mortar=1.6, moss=0.0):
    cells, edges = voronoi(size, n, seed, mortar)
    rnd = random.Random(seed + 1)
    shades = [rnd.choice(stones) for _ in range(n)]
    tilt = [(rnd.random() - 0.5) * 0.1 for _ in range(n)]
    grain = fractal(size, seed + 2, [(size // 4, 0.6), (size // 2, 0.4)])
    moss_map = fractal(size, seed + 3, [(4, 0.6), (8, 0.4)]) if moss else None
    img = Image.new('RGB', (size, size))
    data = []
    for i, (c, e) in enumerate(zip(cells, edges)):
        x, y = i % size, i // size
        base = shades[c]
        k = 1 + tilt[c] * (y / size - 0.5) * 2 + (grain[i] - 0.5) * 0.22 - e * 0.35
        col = tuple(max(0, min(255, int(v * k))) for v in base)
        if e > 0.55:
            col = lerp3(col, mortar_col, min(1.0, (e - 0.55) * 2.5))
        if moss and moss_map[i] > 1 - moss:
            t = min(1.0, (moss_map[i] - (1 - moss)) * 3) * 0.75
            col = lerp3(col, (64, 88, 40), t)
        data.append(col)
    img.putdata(data)
    return img


def path_cobble(size=128):
    return _stone_tile(size, 34, 41, [(118, 116, 112), (104, 102, 100), (132, 128, 122), (96, 94, 92)], (52, 50, 48))


def path_road(size=128):
    n = fractal(size, 51, [(8, 0.4), (32, 0.3), (128, 0.3)])
    img = from_values(size, n, [(0, (46, 47, 52)), (0.6, (62, 63, 68)), (1, (80, 80, 84))])
    return _pebbles(img, random.Random(53), 500, [(96, 96, 100, 160), (34, 34, 38, 160)], 0.4, 0.9)


def path_sand(size=128):
    n = fractal(size, 61, [(4, 0.4), (16, 0.3), (64, 0.3)])
    img = from_values(size, n, [(0, (178, 156, 112)), (0.5, (202, 182, 138)), (1, (222, 206, 164))])
    return _pebbles(img, random.Random(63), 300, [(160, 140, 100, 150), (232, 220, 186, 150)], 0.4, 1.0)


def path_floor(size=128):
    """Wooden floor boards."""
    img = Image.new('RGB', (size, size))
    rnd = random.Random(71)
    grain = fractal(size, 72, [(4, 0.3), (64, 0.7)])
    board = size // 8
    tones = [(128, 92, 56), (116, 82, 48), (138, 100, 62), (108, 76, 44)]
    data = []
    shifts = [rnd.randrange(size) for _ in range(8)]
    for y in range(size):
        row = y // board
        tone = tones[(row * 3) % len(tones)]
        for x in range(size):
            g = grain[((x + shifts[row]) % size) + (y % size) * size]
            k = 0.85 + g * 0.3
            c = tuple(int(v * k) for v in tone)
            if y % board == 0 or (x + shifts[row]) % (size // 2) == 0:
                c = (52, 36, 22)
            data.append(c)
    img.putdata(data)
    return img


def block_stone(size=32):
    return _stone_tile(size, 9, 81, [(128, 128, 126), (112, 112, 112), (140, 138, 134), (100, 100, 102)],
                       (58, 58, 60), mortar=1.1)


def block_mossy(size=32):
    """Dark mossy cobblestone, for walls (like the original's stone walls)."""
    return _stone_tile(size, 9, 91, [(88, 90, 86), (76, 78, 76), (98, 98, 94), (70, 72, 72)],
                       (40, 42, 40), mortar=1.1, moss=0.38)


GENERATORS = {
    'grass': grass, 'path_dirt': path_dirt, 'path_gravel': path_gravel, 'path_cobble': path_cobble,
    'path_road': path_road, 'path_sand': path_sand, 'path_floor': path_floor,
    'block_stone': block_stone, 'block_mossy': block_mossy,
}


# ── cache + Panda textures ───────────────────────────────────────────────────
def image(name):
    """The PIL image for a texture (generated once, then loaded from the cache)."""
    path = CACHE_DIR / f'{name}_v{VERSION}.png'
    try:
        if path.exists():
            return Image.open(path).convert('RGB')
    except Exception:
        pass
    img = GENERATORS[name]()
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        img.save(path)
    except Exception as e:
        print('could not cache texture', name, e)
    return img


_textures = {}


def smooth_texture(name):
    """A repeating, smoothly filtered (mipmapped) Ursina texture."""
    if name not in _textures:
        from panda3d.core import SamplerState
        t = Texture(image(name).transpose(Image.FLIP_TOP_BOTTOM))
        pt = t._texture
        pt.setMinfilter(SamplerState.FT_linear_mipmap_linear)
        pt.setMagfilter(SamplerState.FT_linear)
        pt.setAnisotropicDegree(8)
        pt.setWrapU(SamplerState.WM_repeat)
        pt.setWrapV(SamplerState.WM_repeat)
        _textures[name] = t
    return _textures[name]
