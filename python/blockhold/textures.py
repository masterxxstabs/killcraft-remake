"""Pixel-art textures drawn in code with Pillow (no image files needed)."""
import math
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
    """Packs square tiles into one texture laid out in a grid."""
    def __init__(self, tiles=None, tile=TILE):
        tiles = tiles or TILES
        names = list(tiles)
        self.cols = math.ceil(math.sqrt(len(names)))
        self.rows = math.ceil(len(names) / self.cols)
        self.index = {n: i for i, n in enumerate(names)}
        img = Image.new('RGBA', (tile * self.cols, tile * self.rows))
        for i, n in enumerate(names):
            t = tiles[n]()
            if t.size != (tile, tile):
                t = t.resize((tile, tile), Image.NEAREST)
            img.paste(t, ((i % self.cols) * tile, (i // self.cols) * tile))
        self.image = img
        self.texture = Texture(img)

    def rect(self, name):
        i = self.index[name]
        c, r = i % self.cols, i // self.cols
        inset = 0.02
        u0, u1 = (c + inset) / self.cols, (c + 1 - inset) / self.cols
        # image rows go top-down, texture v goes bottom-up
        v1 = 1 - (r + inset) / self.rows
        v0 = 1 - (r + 1 - inset) / self.rows
        return (u0, v0, u1, v1)

    def block_rects(self, kind):
        top, bottom, side = BLOCK_FACES.get(kind, (kind, kind, kind))
        r = self.rect(side)
        return {'top': self.rect(top), 'bottom': self.rect(bottom),
                'east': r, 'west': r, 'north': r, 'south': r}

    def all_faces(self, name):
        r = self.rect(name)
        return {f: r for f in ('top', 'bottom', 'east', 'west', 'north', 'south')}


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


# ── weapon materials ─────────────────────────────────────────────────────────
#  Every gun part uses one of these. Add your own and use its name in weapons.py.

def _scratches(colour, n=6):
    def draw(px, rnd, s, sh):
        for _ in range(n):
            x, y, length = int(rnd() * s), int(rnd() * s), 2 + int(rnd() * 5)
            for k in range(length):
                if x + k < s:
                    px[x + k, y] = sh(colour)
    return draw


def _edges(colour, f=0.7):
    def draw(px, rnd, s, sh):
        for i in range(s):
            for p in ((i, 0), (i, s - 1), (0, i), (s - 1, i)):
                r, g, b, a = px[p]
                px[p] = (int(r * f), int(g * f), int(b * f), 255)
    return draw


def _combine(*draws):
    def draw(px, rnd, s, sh):
        for d in draws:
            d(px, rnd, s, sh)
    return draw


def _wood_grain(px, rnd, s, sh):
    for y in range(s):
        if rnd() < 0.35:
            for x in range(s):
                if rnd() < 0.8:
                    px[x, y] = sh('#5e3a19', 1 + (rnd() - 0.5) * 0.2)
    kx, ky = int(rnd() * (s - 3)), int(rnd() * (s - 3))
    for dx in range(3):
        for dy in range(2):
            px[kx + dx, ky + dy] = sh('#4a2c12')


def _grip(px, rnd, s, sh):
    for y in range(s):
        for x in range(s):
            if (x + y) % 3 == 0 or (x - y) % 3 == 0:
                px[x, y] = sh('#151515')


def _rust(px, rnd, s, sh):
    for _ in range(26):
        x, y = int(rnd() * s), int(rnd() * s)
        px[x, y] = sh(rnd() < 0.5 and '#b0602a' or '#6e3d1d')
    for _ in range(8):
        x, y = int(rnd() * s), int(rnd() * s)
        px[x, y] = sh('#8a8f99')


def _glow(core):
    def draw(px, rnd, s, sh):
        for y in range(s):
            for x in range(s):
                d = abs(x - s / 2 + 0.5) + abs(y - s / 2 + 0.5)
                px[x, y] = sh(core, 1.25 - d / s * 0.7 + (rnd() - 0.5) * 0.15)
        for _ in range(5):
            px[int(rnd() * s), int(rnd() * s)] = (255, 255, 255, 255)
    return draw


def _camo(px, rnd, s, sh):
    for colour in ('#3e4a2a', '#6b5a3a', '#2a2f22'):
        for _ in range(5):
            cx, cy, r = int(rnd() * s), int(rnd() * s), 1 + int(rnd() * 2)
            for y in range(cy - r, cy + r + 1):
                for x in range(cx - r, cx + r + 1):
                    px[x % s, y % s] = sh(colour, 1 + (rnd() - 0.5) * 0.1)


def _frost(px, rnd, s, sh):
    for _ in range(14):
        x, y = int(rnd() * s), int(rnd() * s)
        px[x, y] = (240, 252, 255, 255)
        if x + 1 < s:
            px[x + 1, y] = sh('#d6f4ff')


def _blade(px, rnd, s, sh):
    for x in range(s):
        px[x, 0] = (250, 252, 255, 255)
        px[x, 1] = sh('#e8edf2')


def _stripes(colour):
    def draw(px, rnd, s, sh):
        for y in range(0, s, 6):
            for x in range(s):
                px[x, y] = sh(colour)
                px[x, y + 1] = sh(colour)
    return draw


WEAPON_TILES = {
    'steel': lambda: pixel_image('#9aa0a8', 0.06, 101, draw=_combine(_scratches('#c4c9cf'), _edges(0, 0.8))),
    'dark': lambda: pixel_image('#3a3f48', 0.07, 103, draw=_combine(_scratches('#4c525c', 4), _edges(0, 0.7))),
    'polymer': lambda: pixel_image('#26292e', 0.05, 107, draw=_edges(0, 0.75)),
    'black': lambda: pixel_image('#0e0e10', 0.05, 109),
    'wood': lambda: pixel_image('#8a5a2b', 0.08, 113, draw=_combine(_wood_grain, _edges(0, 0.8))),
    'grip': lambda: pixel_image('#2a2a2a', 0.05, 127, draw=_grip),
    'brass': lambda: pixel_image('#c9a227', 0.1, 131, draw=_combine(_scratches('#f0d060', 4), _edges(0, 0.75))),
    'rust': lambda: pixel_image('#7d4a2a', 0.15, 137, draw=_combine(_rust, _edges(0, 0.8))),
    'orange': lambda: pixel_image('#d9682b', 0.05, 139, draw=_combine(_stripes('#b9501b'), _edges(0, 0.75))),
    'red': lambda: pixel_image('#b0263c', 0.07, 149, draw=_combine(_scratches('#d9d9d9', 3), _edges(0, 0.75))),
    'camo': lambda: pixel_image('#55603a', 0.08, 151, draw=_camo),
    'chrome': lambda: pixel_image('#d8dde3', 0.04, 157, draw=_combine(_stripes('#f4f7fa'), _edges(0, 0.7))),
    'blade': lambda: pixel_image('#b9c0c8', 0.04, 163, draw=_blade),
    'tape': lambda: pixel_image('#9a9a9a', 0.15, 167),
    'frost': lambda: pixel_image('#9fdcff', 0.08, 173, draw=_combine(_frost, _edges(0, 0.85))),
    'tan': lambda: pixel_image('#a8916a', 0.06, 199, draw=_combine(_scratches('#c2ad85', 4), _edges(0, 0.75))),
    'gold': lambda: pixel_image('#e6b830', 0.08, 179, draw=_combine(_scratches('#fff0a0', 5), _edges(0, 0.7))),
    'glow_cyan': lambda: pixel_image('#5fe0ff', 0.1, 181, draw=_glow('#5fe0ff')),
    'glow_green': lambda: pixel_image('#8cff3a', 0.1, 191, draw=_glow('#8cff3a')),
    'glow_orange': lambda: pixel_image('#ff8c2a', 0.1, 193, draw=_glow('#ff8c2a')),
    'glow_purple': lambda: pixel_image('#c07bff', 0.1, 197, draw=_glow('#c07bff')),
}

_weapon_atlas = None


def weapon_atlas():
    global _weapon_atlas
    if _weapon_atlas is None:
        _weapon_atlas = Atlas(WEAPON_TILES)
    return _weapon_atlas


# ── zombie skins ─────────────────────────────────────────────────────────────
#  Each enemy type gets its own painted skin, built from its colours and its
#  `look` settings in data/enemies.py.

def _rgba(h, f=1.0):
    return _shade(_rgb(h), f)


def _fill(px, x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(16, y1)):
        for x in range(max(0, x0), min(16, x1)):
            px[x, y] = c


def _noise_fill(px, rnd, x0, y0, x1, y1, h, var=0.1):
    for y in range(max(0, y0), min(16, y1)):
        for x in range(max(0, x0), min(16, x1)):
            px[x, y] = _rgba(h, 1 + (rnd() - 0.5) * 2 * var)


def _rot(px, rnd, skin, n=6):
    """Rotting blotches on skin."""
    for _ in range(n):
        x, y = int(rnd() * 15), int(rnd() * 15)
        c = _rgba(skin, 0.7)
        px[x, y] = c
        if rnd() < 0.6:
            px[x + 1, y] = c
        if rnd() < 0.4:
            px[x, y + 1] = _rgba(skin, 0.8)


def _blood(px, rnd, n=4):
    for _ in range(n):
        x, y = int(rnd() * 14), int(rnd() * 14)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            if rnd() < 0.75:
                px[x + dx, y + dy] = _rgba('#6e0f0f', 1 + (rnd() - 0.5) * 0.4)
        for k in range(int(rnd() * 3)):          # drip
            if y + 2 + k < 16:
                px[x, y + 2 + k] = _rgba('#5a0c0c')


def _tears(px, rnd, skin, n=3):
    for _ in range(n):
        x, y, w, h = int(rnd() * 13), int(rnd() * 13), 2 + int(rnd() * 2), 1 + int(rnd() * 2)
        _fill(px, x, y, x + w, y + h, _rgba(skin, 0.85))
        _fill(px, x, y + h, x + w, y + h + 1, _rgba('#000000'))


def skin_tiles(colors, look):
    skin, shirt, pants, eyes = colors['skin'], colors['shirt'], colors['pants'], colors['eyes']
    hair = look.get('hair')
    top = look.get('top', 'shirt')
    shoes = look.get('shoes', '#2a1f16')
    bloody = look.get('blood', True)
    mouth = look.get('mouth', 'teeth')
    seed = sum(map(ord, skin + shirt))
    tiles = {}

    def tile(name, draw):
        def make():
            img = Image.new('RGBA', (16, 16))
            px = img.load()
            draw(px, random.Random(seed + len(name) * 31 + ord(name[-1])).random)
            return img
        tiles[name] = make

    def head_front(px, rnd):
        _noise_fill(px, rnd, 0, 0, 16, 16, skin, 0.08)
        _rot(px, rnd, skin, 5)
        if hair:
            _noise_fill(px, rnd, 0, 0, 16, 3, hair, 0.12)
            for x in range(16):
                if rnd() < 0.5:
                    px[x, 3] = _rgba(hair, 0.9)
        _fill(px, 2, 5, 7, 6, _rgba(skin, 0.45))           # brows
        _fill(px, 9, 5, 14, 6, _rgba(skin, 0.45))
        _fill(px, 3, 6, 6, 8, _rgba('#120c0c'))             # eye sockets
        _fill(px, 10, 6, 13, 8, _rgba('#120c0c'))
        px[4, 6] = px[11, 6] = _rgba(eyes)                   # glowing pupils
        px[4, 7] = px[11, 7] = _rgba(eyes, 0.7)
        _fill(px, 7, 8, 9, 10, _rgba(skin, 0.65))           # nose
        if mouth == 'open':
            _fill(px, 4, 11, 12, 14, _rgba('#1a0606'))
            for x in range(4, 12, 2):
                px[x, 11] = _rgba('#e8e0c8')
                px[x + 1, 13] = _rgba('#d8d0b8')
        else:
            _fill(px, 4, 11, 12, 13, _rgba('#1a0606'))
            for x in range(4, 12):
                if x % 2 == 0:
                    px[x, 11] = _rgba('#e8e0c8')
        if mouth == 'drool':
            for x in (5, 9, 10):
                for y in range(13, 13 + 1 + int(rnd() * 3)):
                    px[x, min(15, y)] = _rgba('#9cff3a', 0.9)
        elif bloody:
            for x in (5, 10):
                for y in range(13, 13 + 1 + int(rnd() * 3)):
                    px[x, min(15, y)] = _rgba('#7a0f0f')
        if look.get('scar'):
            for y in range(2, 11):
                px[13, y] = _rgba('#3a1a1a')
                if y % 2 == 0:
                    px[12, y] = px[14, y] = _rgba('#3a1a1a')

    def head_side(px, rnd):
        _noise_fill(px, rnd, 0, 0, 16, 16, skin, 0.08)
        _rot(px, rnd, skin, 4)
        if hair:
            _noise_fill(px, rnd, 0, 0, 16, 5, hair, 0.12)
            _noise_fill(px, rnd, 0, 5, 5, 11, hair, 0.12)
        _fill(px, 7, 7, 10, 11, _rgba(skin, 0.7))            # ear

    def head_back(px, rnd):
        _noise_fill(px, rnd, 0, 0, 16, 16, hair or skin, 0.1)
        if not hair:
            _rot(px, rnd, skin, 6)

    def head_top(px, rnd):
        _noise_fill(px, rnd, 0, 0, 16, 16, hair or skin, 0.1)
        if not hair:
            _rot(px, rnd, skin, 5)

    def plain(h, var=0.08, rot=False):
        def d(px, rnd):
            _noise_fill(px, rnd, 0, 0, 16, 16, h, var)
            if rot:
                _rot(px, rnd, h, 4)
        return d

    def torso_front(px, rnd):
        if top == 'vest':
            _noise_fill(px, rnd, 0, 0, 16, 16, skin, 0.08)
            _rot(px, rnd, skin, 5)
            _noise_fill(px, rnd, 0, 0, 5, 16, shirt, 0.1)
            _noise_fill(px, rnd, 11, 0, 16, 16, shirt, 0.1)
            for i in range(16):                               # diagonal strap
                px[min(15, 3 + i // 2 * 1 + i // 3), i] = _rgba('#3a2a1a')
        elif top == 'robe':
            _noise_fill(px, rnd, 0, 0, 16, 16, shirt, 0.1)
            _fill(px, 7, 0, 9, 16, _rgba('#e0b030'))          # gold trim
            for dy, w in ((5, 1), (6, 2), (7, 3), (8, 2), (9, 1)):
                _fill(px, 8 - w, dy, 8 + w, dy + 1, _rgba('#e0b030'))
            px[8, 7] = _rgba('#ff8c1a')
        else:
            _noise_fill(px, rnd, 0, 0, 16, 16, shirt, 0.1)
            if top == 'tank':
                _fill(px, 5, 0, 11, 3, _rgba(skin))
                _fill(px, 0, 0, 3, 16, _rgba(skin, 0.95))
                _fill(px, 13, 0, 16, 16, _rgba(skin, 0.95))
            else:
                for y in range(4):                           # collar
                    _fill(px, 6 + y // 2, y, 10 - y // 2, y + 1, _rgba(skin))
                for y in (6, 9, 12):
                    px[8, y] = _rgba(shirt, 0.6)
            _tears(px, rnd, skin, 3)
        if bloody:
            _blood(px, rnd, 4)
        if look.get('belt'):
            _fill(px, 0, 14, 16, 16, _rgba('#3a2a1a'))
            _fill(px, 7, 14, 9, 16, _rgba('#c9a227'))

    def torso_back(px, rnd):
        _noise_fill(px, rnd, 0, 0, 16, 16, shirt, 0.1)
        if top in ('shirt', 'tank'):
            _tears(px, rnd, skin, 2)
        if bloody:
            _blood(px, rnd, 2)

    def arm_side(px, rnd):
        sleeve = shirt if top in ('shirt', 'robe') else None
        _noise_fill(px, rnd, 0, 0, 16, 16, skin, 0.08)
        _rot(px, rnd, skin, 4)
        if sleeve:
            _noise_fill(px, rnd, 0, 0, 16, 16 if top == 'robe' else 6, sleeve, 0.1)
            for x in range(16):
                if top != 'robe' and rnd() < 0.5:
                    px[x, 6] = _rgba(sleeve, 0.9)
        _fill(px, 0, 13, 16, 16, _rgba(skin, 0.85))           # hand
        if bloody and rnd() < 0.7:
            _blood(px, rnd, 1)

    def leg_side(px, rnd):
        _noise_fill(px, rnd, 0, 0, 16, 16, pants, 0.1)
        if rnd() < 0.8:                                       # torn knee
            x = int(rnd() * 12)
            _fill(px, x, 7, x + 3, 9, _rgba(skin, 0.85))
        _noise_fill(px, rnd, 0, 13, 16, 16, shoes, 0.08)
        if bloody and rnd() < 0.5:
            _blood(px, rnd, 1)

    tile('head_front', head_front)
    tile('head_side', head_side)
    tile('head_back', head_back)
    tile('head_top', head_top)
    tile('head_bottom', plain(skin, rot=True))
    tile('torso_front', torso_front)
    tile('torso_back', torso_back)
    tile('torso_side', plain(skin if top == 'vest' else shirt))
    tile('torso_top', plain(skin if top in ('vest', 'tank') else shirt))
    tile('torso_bottom', plain(pants))
    tile('arm_side', arm_side)
    tile('arm_top', plain(shirt if top in ('shirt', 'robe') else skin))
    tile('arm_bottom', plain(skin, rot=True))
    tile('leg_side', leg_side)
    tile('leg_top', plain(pants))
    tile('leg_bottom', plain(shoes))
    tile('pad', lambda px, rnd: (_noise_fill(px, rnd, 0, 0, 16, 16, '#6d737c', 0.08),
                                 _scratches('#9aa0a8', 5)(px, rnd, 16, lambda h, f=1: _rgba(h, f)),
                                 [px.__setitem__(p, _rgba('#c9c9c9')) for p in ((2, 2), (13, 2), (2, 13), (13, 13))]))
    tile('belly', lambda px, rnd: (_noise_fill(px, rnd, 0, 0, 16, 16, skin, 0.1), _rot(px, rnd, skin, 8),
                                   [px.__setitem__((int(rnd() * 16), int(rnd() * 16)), _rgba('#9cff3a', 0.8)) for _ in range(10)]))
    tile('crown', lambda px, rnd: (_noise_fill(px, rnd, 0, 0, 16, 16, '#e0b030', 0.1),
                                   _fill(px, 3, 6, 6, 9, _rgba('#c0192c')), _fill(px, 10, 6, 13, 9, _rgba('#2a6cc0'))))
    tile('cape', lambda px, rnd: (_noise_fill(px, rnd, 0, 0, 16, 16, shirt, 0.12),
                                  _fill(px, 0, 14, 16, 16, _rgba('#e0b030'))))
    tile('hair', plain(hair or skin, 0.12))
    return tiles


_skin_cache = {}


def zombie_skin(kind, colors, look):
    """Returns an Atlas with all body-part tiles for this enemy type."""
    if kind not in _skin_cache:
        _skin_cache[kind] = Atlas(skin_tiles(colors, look))
    return _skin_cache[kind]


def scope_texture():
    """Black sniper-scope mask with a clear circle and crosshair."""
    size = 256
    img = Image.new('RGBA', (size, size))
    px = img.load()
    c = size / 2
    for y in range(size):
        for x in range(size):
            d = ((x - c) ** 2 + (y - c) ** 2) ** 0.5 / c
            if d > 0.96:
                px[x, y] = (0, 0, 0, 255)
            elif d > 0.92:
                px[x, y] = (0, 0, 0, int(255 * (d - 0.92) / 0.04))
            elif abs(x - c) < 1 or abs(y - c) < 1:
                px[x, y] = (0, 0, 0, 230 if d > 0.08 else 0)
    return Texture(img)
