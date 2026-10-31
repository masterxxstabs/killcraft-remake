"""Saving, loading and listing maps (JSON files in the maps/ folder)."""
import json
import re
from pathlib import Path
from PIL import Image
from .data.assets import ASSETS

MAPS_DIR = Path(__file__).resolve().parent.parent / 'maps'


def slug(name):
    s = re.sub(r'[^a-z0-9]+', '_', (name or '').lower()).strip('_')
    return s or 'my_map'


def list_maps():
    """[(file stem, map name)] for every map in maps/."""
    out = []
    if MAPS_DIR.is_dir():
        for f in sorted(MAPS_DIR.glob('*.json')):
            try:
                out.append((f.stem, json.loads(f.read_text()).get('name', f.stem)))
            except Exception as e:
                print('skipping broken map', f.name, e)
    return out


def load_map(stem):
    return json.loads((MAPS_DIR / f'{stem}.json').read_text())


def save_map(data, stem=None):
    MAPS_DIR.mkdir(exist_ok=True)
    stem = stem or slug(data.get('name'))
    text = json.dumps(data, separators=(',', ':'))
    # one prop / block / path per line keeps the files readable and easy to diff
    for key in ('blocks', 'paths', 'props'):
        text = text.replace(f'"{key}":[[', f'"{key}":[\n[').replace('],[', '],\n[')
    (MAPS_DIR / f'{stem}.json').write_text(text + '\n')
    return stem


def blank_map(name='My map', size=34):
    return dict(format=1, name=name, size=size, walls=True, blocks=[], paths=[],
                props=[['player_spawn', 0.5, 0.5, 0, 1]])


PATH_COLOURS = {'dirt': (122, 90, 58), 'gravel': (140, 138, 133), 'cobble': (134, 134, 138), 'road': (58, 59, 64),
                'sand': (216, 196, 143), 'floor': (168, 128, 74)}
BLOCK_COLOURS = {'stone': (125, 125, 128), 'brick': (141, 74, 58), 'planks': (168, 128, 74), 'crate': (176, 136, 80),
                 'log': (107, 74, 43), 'obsidian': (40, 30, 55), 'leaves': (63, 125, 42)}
CATEGORY_COLOURS = {'trees': (47, 107, 58), 'shrubs': (95, 160, 70), 'buildings': (168, 67, 47),
                    'props': (176, 136, 80), 'special': (214, 69, 65)}


def preview_image(data, scale=3):
    """A top-down picture of a map (used on the main menu)."""
    half = int(data.get('size', 34))
    n = half * 2
    img = Image.new('RGB', (n, n), (93, 155, 58))
    px = img.load()

    def put(x, z, c):
        gx, gz = int(x // 1) + half, int(z // 1) + half
        if 0 <= gx < n and 0 <= gz < n:
            px[gx, n - 1 - gz] = c
    for x, z, kind in data.get('paths', []):
        put(x, z, PATH_COLOURS.get(kind, (120, 100, 80)))
    for x, z, kind, h in data.get('blocks', []):
        put(x, z, BLOCK_COLOURS.get(kind, (120, 120, 120)))
    from .world import rotate_cell
    for entry in data.get('props', []):
        aid, x, z = entry[0], entry[1], entry[2]
        a = ASSETS.get(aid)
        if not a:
            continue
        c = (17, 151, 176) if a.get('spawn') == 'player' else CATEGORY_COLOURS.get(a['category'], (200, 200, 200))
        cells = a['solid'] or [(0, 0, 1)]
        for dx, dz, _ in cells:
            rx, rz = rotate_cell(dx, dz, entry[3] if len(entry) > 3 else 0)
            put(x + rx, z + rz, c)
    if data.get('walls', True):
        for i in range(n):
            for p in ((i, 0), (i, n - 1), (0, i), (n - 1, i)):
                px[p] = (90, 90, 95)
    return img.resize((n * scale, n * scale), Image.NEAREST)
