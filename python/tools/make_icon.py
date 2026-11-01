"""Draws the BLOCKHOLD icon (a blocky zombie head) and saves installer/blockhold.ico.

    python tools/make_icon.py
"""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
FACE = [                       # 8 x 8 zombie face: g = skin, d = dark skin, h = hair, e = eye, m = mouth, b = blood
    'hhhhhhhh',
    'hhhhhhhh',
    'gggdgggg',
    'geegggee',
    'gbegdgeg',
    'gggddggg',
    'gdmmmmdg',
    'ggbmmggg',
]
COLOURS = {'g': (98, 156, 72), 'd': (74, 122, 54), 'h': (58, 42, 30), 'e': (20, 20, 24), 'm': (52, 24, 24),
           'b': (150, 30, 34)}


def draw(size=256):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = size // 6
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=r, fill=(30, 26, 30, 255))      # dark tile
    pad = size // 8
    cell = (size - 2 * pad) // 8
    off = (size - cell * 8) // 2
    for y, row in enumerate(FACE):
        for x, c in enumerate(row):
            d.rectangle((off + x * cell, off + y * cell, off + (x + 1) * cell - 1, off + (y + 1) * cell - 1),
                        fill=COLOURS[c] + (255,))
    eye = max(1, cell // 3)                       # a glint in the eyes
    for ex in (1, 6):
        d.rectangle((off + ex * cell + eye, off + 3 * cell + eye, off + ex * cell + 2 * eye - 1,
                     off + 3 * cell + 2 * eye - 1), fill=(214, 69, 65, 255))
    return img


if __name__ == '__main__':
    out = HERE / 'installer' / 'blockhold.ico'
    out.parent.mkdir(exist_ok=True)
    draw(256).save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    draw(256).save(HERE / 'installer' / 'blockhold.png')
    print('saved', out)
