"""Pixel-art textures drawn in code with Pillow (no image files needed)."""
import random
from PIL import Image
from ursina import Texture

TILE = 16


def _rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _shade(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb) + (255,)


def pixel_image(base, variance=0.14, seed=1, size=TILE, draw=None):
    img = Image.new('RGBA', (size, size))
    px = img.load()
    rnd = random.Random(seed).random
    b = _rgb(base)
    for y in range(size):
        for x in range(size):
            px[x, y] = _shade(b, 1 + (rnd() - 0.5) * 2 * variance)
    if draw:
        draw(px, rnd, size, lambda h, f=1: _shade(_rgb(h), f))
    return img


def _grass_side(px, rnd, s, sh):
    for x in range(s):
        for y in range(3 + int(rnd() * 3)):
            px[x, y] = sh('#5d9b3a', 1 + (rnd() - 0.5) * 0.3)


def _stone(px, rnd, s, sh):
    for _ in range(10):
        x, y = int(rnd() * s), int(rnd() * s)
        px[x, y] = sh('#5a5a5e')
        px[min(s - 1, x + 1), y] = sh('#5a5a5e')


def _brick(px, rnd, s, sh):
    mortar = sh('#c9c0b0', 0.8)
    for y in range(0, s, 4):
        for x in range(s):
            px[x, y] = mortar
        off = 0 if (y // 4) % 2 else 4
        for x in range(off, s, 8):
            for k in range(4):
                if y + k < s:
                    px[x, y + k] = mortar


def _planks(px, rnd, s, sh):
    for y in range(3, s, 4):
        for x in range(s):
            px[x, y] = sh('#6b4f2a')


def _crate(px, rnd, s, sh):
    c = sh('#5e4322')
    for i in range(s):
        for k in (0, 1, s - 2, s - 1):
            px[i, k] = c
            px[k, i] = c
        px[i, i] = c
        if i + 1 < s:
            px[i + 1, i] = c


def _log_side(px, rnd, s, sh):
    for x in range(1, s, 3):
        for y in range(s):
            px[x, y] = sh('#4a321c')


def _log_top(px, rnd, s, sh):
    c = sh('#7a5a34')
    for rad in (2, 4, 6):
        for i in range(8 - rad, 8 + rad):
            px[i, 8 - rad] = c
            px[i, 8 + rad - 1] = c
            px[8 - rad, i] = c
            px[8 + rad - 1, i] = c


def _leaves(px, rnd, s, sh):
    for _ in range(20):
        px[int(rnd() * s), int(rnd() * s)] = sh('#2a5a1c')


# Atlas tiles, in order. Add new block looks here.
TILES = {
    'grass_top': lambda: pixel_image('#5d9b3a', 0.18, 3),
    'grass_side': lambda: pixel_image('#7a5534', 0.2, 7, draw=_grass_side),
    'dirt': lambda: pixel_image('#7a5534', 0.2, 5),
    'stone': lambda: pixel_image('#7d7d80', 0.12, 11, draw=_stone),
    'brick': lambda: pixel_image('#8d4a3a', 0.1, 13, draw=_brick),
    'planks': lambda: pixel_image('#a8804a', 0.1, 17, draw=_planks),
    'crate': lambda: pixel_image('#b08850', 0.1, 19, draw=_crate),
    'log_side': lambda: pixel_image('#6b4a2b', 0.12, 23, draw=_log_side),
    'log_top': lambda: pixel_image('#b38b5a', 0.14, 29, draw=_log_top),
    'leaves': lambda: pixel_image('#3f7d2a', 0.3, 31, draw=_leaves),
    'obsidian': lambda: pixel_image('#1d1528', 0.3, 37),
}

# Which tile each block type uses per face (top, bottom, side)
BLOCK_FACES = {
    'grass': ('grass_top', 'dirt', 'grass_side'),
    'log': ('log_top', 'log_top', 'log_side'),
}


class Atlas:
    def __init__(self):
        names = list(TILES)
        self.index = {n: i for i, n in enumerate(names)}
        img = Image.new('RGBA', (TILE * len(names), TILE))
        for i, n in enumerate(names):
            img.paste(TILES[n](), (i * TILE, 0))
        self.count = len(names)
        self.texture = Texture(img)

    def rect(self, tile):
        i = self.index[tile]
        inset = 0.02 / self.count
        return (i / self.count + inset, 0.01, (i + 1) / self.count - inset, 0.99)

    def block_rects(self, kind):
        top, bottom, side = BLOCK_FACES.get(kind, (kind, kind, kind))
        r = self.rect(side)
        return {'top': self.rect(top), 'bottom': self.rect(bottom),
                'east': r, 'west': r, 'north': r, 'south': r}


def grass_texture():
    return Texture(pixel_image('#5d9b3a', 0.18, 3))


def face_texture(skin, eyes):
    """8x8 enemy face. Corner pixel (0, 0) is plain skin, used for the other head faces."""
    def draw(px, rnd, s, sh):
        e = _rgb(eyes) + (255,)
        for x in (1, 2, 5, 6):
            px[x, 3] = e
        for x in range(2, 6):
            px[x, 6] = sh(skin, 0.45)
    return Texture(pixel_image(skin, 0.08, 41, size=8, draw=draw))


def vignette_texture(rgb=(200, 0, 0)):
    size = 128
    img = Image.new('RGBA', (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            dx, dy = (x - size / 2) / (size / 2), (y - size / 2) / (size / 2)
            d = (dx * dx + dy * dy) ** 0.5
            a = max(0.0, min(1.0, (d - 0.55) / 0.6))
            px[x, y] = rgb + (int(a * 200),)
    return Texture(img)
