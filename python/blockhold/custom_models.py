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
from panda3d.core import Filename, GeomVertexReader, LPoint3f
from ursina import application

from .paths import BUNDLED_MODELS, MODELS_DIR
EXTENSIONS = ('.glb', '.gltf', '.bam', '.egg', '.obj')

_cache = {}         # path -> loaded NodePath (we copy it for each use)
_auto_rotation = {}  # weapon id -> rotation picked automatically


def folder(wid):
    return MODELS_DIR / wid


def find(wid):
    """The model file for weapon wid: one you downloaded (models/) wins over one that ships with the game."""
    for f in (folder(wid), BUNDLED_MODELS / wid):
        if not f.is_dir():
            continue
        files = [p for p in f.rglob('*') if p.suffix.lower() in EXTENSIONS]
        files.sort(key=lambda p: (EXTENSIONS.index(p.suffix.lower()), len(p.parts)))
        if files:
            return files[0]
    return None


def read_meta(wid):
    """model.json next to the model (how it's turned, set with F8 / F9): yours first, then the bundled one."""
    for f in (folder(wid), BUNDLED_MODELS / wid):
        try:
            return json.loads((f / 'model.json').read_text())
        except Exception:
            continue
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


def _sample_points(model, relative_to, per_geom=3000):
    """A sample of the model's vertex positions, in relative_to's space."""
    pts = []
    for gnp in model.findAllMatches('**/+GeomNode'):
        mat = gnp.getMat(relative_to)
        for geom in gnp.node().getGeoms():
            vdata = geom.getVertexData()
            reader = GeomVertexReader(vdata, 'vertex')
            rows = vdata.getNumRows()
            for i in range(0, rows, max(1, rows // per_geom)):
                reader.setRow(i)
                pts.append(mat.xformPoint(LPoint3f(reader.getData3())))
    return pts


def _muzzle_is_forward(model, relative_to):
    """Guns have their grip / stock hanging lower than the barrel, so the end
    that reaches lowest is the back. True if the barrel already points +z."""
    pts = _sample_points(model, relative_to)
    if len(pts) < 8:
        return True
    zs = [p.z for p in pts]
    lo, hi = min(zs), max(zs)
    cut = (hi - lo) * 0.3
    back = [p.y for p in pts if p.z < lo + cut]
    front = [p.y for p in pts if p.z > hi - cut]
    if not back or not front:
        return True
    return min(back) <= min(front)


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
        model.setHpr(*rotation)
        if not _muzzle_is_forward(model, fit):      # barrel pointing at us: turn around
            rotation[0] = (rotation[0] + 180) % 360
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
