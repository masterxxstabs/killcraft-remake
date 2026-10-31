"""Real 3D gun models (glTF / GLB / OBJ / BAM) that replace the box models.

Put a model in  models/<weapon id>/  (for example models/pistol/scene.gltf) and
the game uses it for that weapon automatically. tools/sketchfab_guns.py does
this for you.

Each folder can have a model.json with tweaks:
    {"rotation": [heading, pitch, roll], "scale": 1.0, "offset": [x, y, z]}
In game, F8 turns the held model 90 degrees and F9 rolls it, and saves the result.
"""
import json
from pathlib import Path
from panda3d.core import Filename
from ursina import application

HERE = Path(__file__).resolve().parent
MODELS_DIR = HERE.parent / 'models'
EXTENSIONS = ('.glb', '.gltf', '.bam', '.egg', '.obj')

_cache = {}         # path -> loaded NodePath (we copy it for each use)
_auto_rotation = {}  # weapon id -> rotation picked automatically


def folder(wid):
    return MODELS_DIR / wid


def find(wid):
    f = folder(wid)
    if not f.is_dir():
        return None
    files = [p for p in f.rglob('*') if p.suffix.lower() in EXTENSIONS]
    files.sort(key=lambda p: (EXTENSIONS.index(p.suffix.lower()), len(p.parts)))
    return files[0] if files else None


def read_meta(wid):
    try:
        return json.loads((folder(wid) / 'model.json').read_text())
    except Exception:
        return {}


def write_meta(wid, meta):
    folder(wid).mkdir(parents=True, exist_ok=True)
    (folder(wid) / 'model.json').write_text(json.dumps(meta, indent=2))


def _size(np, relative_to):
    bounds = np.getTightBounds(relative_to)
    if not bounds:
        return None, None
    a, b = bounds
    return a, b


def load(d, parent, lights):
    """Attach the downloaded model for weapon d under parent. Returns the node or None."""
    path = find(d['id'])
    if path is None:
        return None
    try:
        if path not in _cache:
            _cache[path] = application.base.loader.loadModel(Filename.fromOsSpecific(str(path)), noCache=True)
        source = _cache[path]
    except Exception as e:
        print(f'could not load model for {d["id"]}: {e}')
        return None

    meta = read_meta(d['id'])
    fit = parent.attachNewNode('custom_fit')
    model = source.copyTo(fit)

    a, b = _size(model, fit)
    if a is None:
        fit.removeNode()
        return None
    rotation = meta.get('rotation')
    if rotation is None:
        # point the longest side forward (+z)
        size = b - a
        longest = max(range(3), key=lambda i: size[i])
        rotation = [90, 0, 0] if longest == 0 else [0, 90, 0] if longest == 1 else [0, 0, 0]
        _auto_rotation[d['id']] = rotation
    model.setHpr(*rotation)

    a, b = _size(model, fit)
    length = max(1e-4, max(b[i] - a[i] for i in range(3)))
    centre = (a + b) / 2
    model.setPos(model.getPos() - centre)
    target = d.get('length', 0.5) * meta.get('scale', 1.0)
    s = target / length
    fit.setScale(s)
    # like the block guns: top edge just above the hand, reaching forward
    height = (b[1] - a[1]) * s
    depth = (b[2] - a[2]) * s
    off = meta.get('offset', [0, 0, 0])
    fit.setPos(off[0], 0.06 - height / 2 + off[1], depth / 2 - 0.05 + off[2])

    # Panda's standard lighting shows the model's own materials and textures
    fit.setShaderOff(10)
    for light in lights:
        fit.setLight(light)
    fit.setTwoSided(True)
    return fit


def rotate(d, axis):
    meta = read_meta(d['id'])
    rot = list(meta.get('rotation') or _auto_rotation.get(d['id'], [0, 0, 0]))
    if axis == 'yaw':
        rot[0] = (rot[0] + 90) % 360
    else:
        rot[2] = (rot[2] + 90) % 360
    meta['rotation'] = rot
    write_meta(d['id'], meta)
    _cache.clear()


def credits():
    """Lines for the credits screen, from every model.json that has an author."""
    out = []
    if MODELS_DIR.is_dir():
        for f in sorted(MODELS_DIR.iterdir()):
            m = read_meta(f.name) if f.is_dir() else {}
            if m.get('author'):
                out.append(f"{m.get('name', f.name)} by {m['author']} ({m.get('license', '?')})")
    return out
