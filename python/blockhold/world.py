"""The arena: block columns, painted paths and low-poly props on a 1 m grid.

A world is either generated at random or loaded from a map (see maps.py).
Meshes are split into 8x8 chunks so the map editor can change one spot
without rebuilding everything.
"""
import math
import random
import time as pytime
from panda3d.core import NodePath, TransparencyAttrib
from ursina import Mesh, Vec2, Vec3, color as ucolor
from .data.assets import ASSETS, PATHS
from .lowpoly import LowPoly
from .render import WORLD_SHADER, add_box, node, set_glow, destroy
from .textures import Atlas
from .world_textures import smooth_texture

PATH_ORDER = list(PATHS)
SOFT_PATHS = {'dirt', 'gravel', 'sand'}     # these fade into the grass at the edges

NEIGHBOURS = {
    'top': (0, 1, 0), 'bottom': (0, -1, 0), 'east': (1, 0, 0),
    'west': (-1, 0, 0), 'north': (0, 0, 1), 'south': (0, 0, -1),
}
CHUNK = 8
NON_SOLID = {'leaves'}

_protos = {}          # (asset id, variant) -> NodePath with the mesh


def prototype(aid, variant=0):
    key = (aid, variant)
    if key not in _protos:
        lp = LowPoly(seed=sum(map(ord, aid)) * 31 + variant * 7919)
        ASSETS[aid]['build'](lp)
        holder = NodePath(f'proto_{aid}_{variant}')
        lp.mesh().reparentTo(holder)
        glow = lp.glow_mesh()
        if glow is not None:                  # lamp bulbs, flames: not darkened at night
            glow.reparentTo(holder)
            set_glow(glow, 1.0)
        _protos[key] = holder
    return _protos[key]


def rotate_cell(dx, dz, rot):
    """Rotate a footprint offset the same way the model turns (Ursina rotation_y)."""
    a = math.radians(round(rot / 90) * 90)
    c, s = round(math.cos(a)), round(math.sin(a))
    return dx * c + dz * s, -dx * s + dz * c


class World:
    def __init__(self, seed=None, map_data=None, editor=False):
        self.half = int((map_data or {}).get('size', 34))
        self.n = self.half * 2
        n2 = self.n * self.n
        self.block_h = [0] * n2           # solid block column height per cell
        self.prop_h = [0] * n2            # solid prop height per cell
        self.heights = [0] * n2           # what physics uses: the higher of the two
        self.columns = {}                 # (gx, gz) -> {y: kind}
        self.paths = {}                   # (gx, gz) -> kind
        self.props = []                   # placed props (dicts)
        self.editor = editor
        self.walls = (map_data or {}).get('walls', True)
        self.name = (map_data or {}).get('name', 'Random arena')
        self.player_spawn = Vec3(0, 0, 0)
        self.zombie_spawns = []
        self.ore_spawns = []              # (position, ore kind or 'random') from map markers
        self.benches = []                 # workbench positions
        self.rnd = random.Random(seed).random
        self.atlas = Atlas(tile=32)
        self.prop_lights = []              # (prop, light dict) for props that glow
        self.root = node()
        self.props_root = self.root.attachNewNode('props')
        self.block_chunks = {}
        self.path_chunks = {}
        self.dirty_blocks = set()
        self.dirty_paths = set()
        self.build_ground()
        if self.walls:
            self.build_walls()
        if map_data is None:
            self.build_random()
        else:
            self.load(map_data)
        self.flush()
        if not editor:
            self.props_root.flattenStrong()      # merge all props into a few big meshes: much faster

    # ── grid helpers ───────────────────────────────────────────────────────
    def gidx(self, gx, gz):
        return gz * self.n + gx

    def inside(self, gx, gz, margin=0):
        return margin <= gx < self.n - margin and margin <= gz < self.n - margin

    def cell_height(self, ix, iz):
        if ix < 0 or iz < 0 or ix >= self.n or iz >= self.n:
            return 99
        return self.heights[iz * self.n + ix]

    def height_at(self, x, z):
        return self.cell_height(math.floor(x) + self.half, math.floor(z) + self.half)

    def to_grid(self, x, z):
        return math.floor(x) + self.half, math.floor(z) + self.half

    def _refresh_height(self, gx, gz):
        i = self.gidx(gx, gz)
        self.heights[i] = max(self.block_h[i], self.prop_h[i])

    def _mark_blocks(self, gx, gz):
        cx, cz = gx // CHUNK, gz // CHUNK
        self.dirty_blocks.add((cx, cz))
        # faces on chunk borders depend on the neighbour chunk too
        for nx, nz in ((gx - 1, gz), (gx + 1, gz), (gx, gz - 1), (gx, gz + 1)):
            self.dirty_blocks.add((nx // CHUNK, nz // CHUNK))

    # ── blocks ───────────────────────────────────────────────────────────────
    def place(self, kind, gx, y, gz, solid=True):
        if not self.inside(gx, gz):
            return
        self.columns.setdefault((gx, gz), {})[y] = kind
        if solid and kind not in NON_SOLID:
            i = self.gidx(gx, gz)
            self.block_h[i] = max(self.block_h[i], y + 1)
            self._refresh_height(gx, gz)
        self._mark_blocks(gx, gz)

    def column(self, kind, gx, gz, h, top=None):
        for y in range(h):
            self.place(top if (top and y == h - 1) else kind, gx, y, gz)

    def set_column(self, gx, gz, kind, h):
        """Replace whatever stands on a cell with a column (editor)."""
        self.clear_column(gx, gz)
        self.column(kind, gx, gz, h)

    def clear_column(self, gx, gz):
        if (gx, gz) in self.columns:
            del self.columns[(gx, gz)]
            self.block_h[self.gidx(gx, gz)] = 0
            self._refresh_height(gx, gz)
            self._mark_blocks(gx, gz)

    def block_at(self, gx, y, gz):
        return self.columns.get((gx, gz), {}).get(y)

    def free(self, gx, gz, pad=0, paths_ok=True):
        for dx in range(-pad, pad + 1):
            for dz in range(-pad, pad + 1):
                x, z = gx + dx, gz + dz
                if not self.inside(x, z, 1) or self.heights[self.gidx(x, z)] > 0 or (x, z) in self.columns:
                    return False
                if not paths_ok and (x, z) in self.paths:
                    return False
        cx, cz = gx - self.half, gz - self.half
        return cx * cx + cz * cz > 30       # keep the middle clear for the player

    # ── paths ────────────────────────────────────────────────────────────────
    def set_path(self, gx, gz, kind):
        if not self.inside(gx, gz):
            return
        if kind is None:
            if self.paths.pop((gx, gz), None) is None:
                return
        elif self.paths.get((gx, gz)) == kind:
            return
        else:
            self.paths[(gx, gz)] = kind
        for dx in (-1, 0, 1):                     # soft edges depend on the cells around
            for dz in (-1, 0, 1):
                self.dirty_paths.add(((gx + dx) // CHUNK, (gz + dz) // CHUNK))

    # ── props ────────────────────────────────────────────────────────────────
    def add_prop(self, aid, x, z, rot=0.0, scale=1.0):
        a = ASSETS.get(aid)
        if a is None:
            print('unknown asset in map:', aid)
            return None
        p = dict(id=aid, x=x, z=z, rot=rot, scale=scale, np=None, cells=[])
        if self.editor or not a.get('editor_only'):
            variant = int(abs(x * 7.31 + z * 13.17)) % a.get('variants', 1)
            np = self.props_root.attachNewNode(aid)
            np.setPos(x, 0, z)
            np.setH(-rot)
            np.setScale(scale)
            prototype(aid, variant).copyTo(np)        # a light copy: the geometry itself is shared
            p['np'] = np
        gx0, gz0 = self.to_grid(x, z)
        for dx, dz, h in a['solid']:
            rx, rz = rotate_cell(dx, dz, rot)
            gx, gz = gx0 + rx, gz0 + rz
            if self.inside(gx, gz):
                p['cells'].append((gx, gz, h))
                i = self.gidx(gx, gz)
                self.prop_h[i] = max(self.prop_h[i], h)
                self._refresh_height(gx, gz)
        self.props.append(p)
        if a.get('spawn') == 'player':
            self.player_spawn = Vec3(x, 0, z)
        elif a.get('spawn') == 'zombie':
            self.zombie_spawns.append(Vec3(x, 0, z))
        if a.get('ore'):
            self.ore_spawns.append((Vec3(x, 0, z), a['ore']))
        if a.get('station') == 'workbench':
            self.benches.append(Vec3(x, 0, z))
        if a.get('light') and not self.editor:
            self.prop_lights.append((p, a['light']))
        return p

    def remove_prop(self, p):
        if p not in self.props:
            return
        self.props.remove(p)
        if p['np'] is not None:
            p['np'].removeNode()
        for gx, gz, _ in p['cells']:
            i = self.gidx(gx, gz)
            self.prop_h[i] = max([h for o in self.props for (x, z, h) in o['cells'] if (x, z) == (gx, gz)] or [0])
            self._refresh_height(gx, gz)
        a = ASSETS[p['id']]
        if a.get('spawn') == 'zombie':
            self.zombie_spawns = [v for v in self.zombie_spawns if (v.x, v.z) != (p['x'], p['z'])]
        elif a.get('spawn') == 'player':
            self.player_spawn = Vec3(0, 0, 0)
        if a.get('ore'):
            self.ore_spawns = [s for s in self.ore_spawns if (s[0].x, s[0].z) != (p['x'], p['z'])]
        if a.get('station') == 'workbench':
            self.benches = [b for b in self.benches if (b.x, b.z) != (p['x'], p['z'])]
        self.prop_lights = [pl for pl in self.prop_lights if pl[0] is not p]

    def set_dynamic_solid(self, gx, gz, h):
        """Make a cell solid up to height h (0 = back to normal) for things that come and go, like ore nodes."""
        if not self.inside(gx, gz):
            return
        i = self.gidx(gx, gz)
        base = max([ph for o in self.props for (x, z, ph) in o['cells'] if (x, z) == (gx, gz)] or [0])
        self.prop_h[i] = max(base, h)
        self._refresh_height(gx, gz)

    def prop_at(self, x, z, radius=0.8):
        """The prop under a point: one whose footprint covers it, or the nearest small one."""
        gx, gz = self.to_grid(x, z)
        for p in reversed(self.props):
            if any((cx, cz) == (gx, gz) for cx, cz, _ in p['cells']):
                return p
        best, best_d = None, radius
        for p in self.props:
            d = math.hypot(p['x'] - x, p['z'] - z)
            if d < best_d:
                best, best_d = p, d
        return best

    # ── building meshes ──────────────────────────────────────────────────────
    def build_ground(self):
        step = 4
        cells = (self.n + 64) // step
        half = cells * step / 2
        rnd = random.Random(self.n * 7 + 3)
        coarse = [[rnd.random() for _ in range(cells // 3 + 3)] for _ in range(cells // 3 + 3)]
        dry = [[rnd.random() for _ in range(cells // 2 + 3)] for _ in range(cells // 2 + 3)]

        def smooth(grid, u, v):
            i, j = int(u), int(v)
            fu, fv = u - i, v - j
            fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
            a = grid[i][j] + (grid[i + 1][j] - grid[i][j]) * fu
            b = grid[i][j + 1] + (grid[i + 1][j + 1] - grid[i][j + 1]) * fu
            return a + (b - a) * fv

        verts, uvs, cols, tris = [], [], [], []
        for i in range(cells + 1):
            for j in range(cells + 1):
                x, z = -half + i * step, -half + j * step
                verts.append(Vec3(x, 0, z))
                uvs.append(Vec2(x / 4, z / 4))
                f = 0.78 + 0.36 * smooth(coarse, i / 3, j / 3)
                d = max(0.0, smooth(dry, i / 2, j / 2) - 0.55) * 1.6
                cols.append(ucolor.Color(f * (1 + 0.18 * d), f * (1 + 0.08 * d), f * (1 - 0.12 * d), 1))
        w = cells + 1
        for i in range(cells):
            for j in range(cells):
                a, b, c, e = i * w + j, (i + 1) * w + j, (i + 1) * w + j + 1, i * w + j + 1
                tris += [a, c, b, a, e, c]
        self.ground = node(self.root, model=Mesh(vertices=verts, triangles=tris, uvs=uvs, colors=cols),
                           texture=smooth_texture('grass'))
        self.ground.setTwoSided(True)

    def build_walls(self):
        n = self.n
        for i in range(n):
            for x, z in ((i, 0), (i, n - 1), (0, i), (n - 1, i)):
                if (x, z) not in self.columns:
                    self.column('mossy', x, z, 3)

    def flush(self):
        """Rebuild the meshes of every chunk that changed."""
        for key in self.dirty_blocks:
            self._build_block_chunk(*key)
        for key in self.dirty_paths:
            self._build_path_chunk(*key)
        self.dirty_blocks.clear()
        self.dirty_paths.clear()

    def _build_block_chunk(self, cx, cz):
        old = self.block_chunks.pop((cx, cz), None)
        if old:
            destroy(old)
        verts, tris, uvs, cols = [], [], [], []
        for gx in range(cx * CHUNK, cx * CHUNK + CHUNK):
            for gz in range(cz * CHUNK, cz * CHUNK + CHUNK):
                col = self.columns.get((gx, gz))
                if not col:
                    continue
                for y, kind in col.items():
                    skip = [f for f, (dx, dy, dz) in NEIGHBOURS.items()
                            if self.block_at(gx + dx, y + dy, gz + dz) is not None]
                    if y == 0:
                        skip.append('bottom')
                    if len(skip) == 6:
                        continue
                    centre = (gx - self.half + 0.5, y + 0.5, gz - self.half + 0.5)
                    add_box(verts, tris, uvs, cols, centre, (1, 1, 1), self.atlas.block_rects(kind), skip=skip)
        if verts:
            self.block_chunks[(cx, cz)] = node(self.root, model=Mesh(vertices=verts, triangles=tris, uvs=uvs, colors=cols),
                                               texture=self.atlas.texture)

    def _path_alpha(self, gx, gz):
        """How opaque the path is at grid corner (gx, gz): from the 4 cells around it."""
        around = [(gx - 1, gz - 1), (gx, gz - 1), (gx - 1, gz), (gx, gz)]
        n = sum(1 for c in around if c in self.paths)
        if n == 4:
            return 1.0
        if n == 3:
            return 0.75
        if n == 2:
            a, b, c, d = (p in self.paths for p in around)
            return 0.4 if (a and b) or (c and d) or (a and c) or (b and d) else 0.25
        return 0.0

    @staticmethod
    def _jitter(x, z):
        h = math.sin(x * 12.9898 + z * 78.233) * 43758.5453
        return h - math.floor(h)

    def _build_path_chunk(self, cx, cz):
        for old in self.path_chunks.pop((cx, cz), []):
            destroy(old)
        meshes = {}
        for gx in range(cx * CHUNK, cx * CHUNK + CHUNK):
            for gz in range(cz * CHUNK, cz * CHUNK + CHUNK):
                kind = self.paths.get((gx, gz))
                if kind is None:
                    continue
                verts, uvs, cols, tris = meshes.setdefault(kind, ([], [], [], []))
                soft = kind in SOFT_PATHS
                x0, z0 = gx - self.half, gz - self.half
                y = 0.02 + PATH_ORDER.index(kind) * 0.003 if kind in PATH_ORDER else 0.02
                base = len(verts)
                for iz in range(3):
                    for ix in range(3):
                        x, z = x0 + ix * 0.5, z0 + iz * 0.5
                        if ix == 1 and iz == 1:
                            a = 1.0
                        elif ix == 1 or iz == 1:          # middle of an edge: the two cells beside it
                            nx, nz = (gx + (ix - 1), gz) if iz == 1 else (gx, gz + (iz - 1))
                            a = 1.0 if (nx, nz) in self.paths else (0.3 if soft else 0.9)
                        else:                             # a corner: the four cells around it
                            a = self._path_alpha(gx + ix // 2, gz + iz // 2)
                            a = a if soft else max(a, 0.9)
                        if soft and a < 1:
                            a = max(0.0, min(1.0, a * (0.6 + 0.8 * self._jitter(x, z))))
                        verts.append(Vec3(x, y, z))
                        uvs.append(Vec2(x / 2, z / 2))
                        cols.append(ucolor.Color(1, 1, 1, a))
                for iz in range(2):
                    for ix in range(2):
                        a = base + iz * 3 + ix
                        tris += [a, a + 3, a + 4, a, a + 4, a + 1]
        nodes = []
        for kind, (verts, uvs, cols, tris) in meshes.items():
            e = node(self.root, model=Mesh(vertices=verts, triangles=tris, uvs=uvs, colors=cols),
                     texture=smooth_texture('path_' + kind))
            e.setTwoSided(True)
            e.setTransparency(TransparencyAttrib.M_alpha)
            e.setDepthWrite(False)
            e.setBin('transparent', 0)
            nodes.append(e)
        if nodes:
            self.path_chunks[(cx, cz)] = nodes

    def lights(self):
        """Light from lamp posts, campfires, workbench lanterns... (see Lighting)."""
        t = pytime.time()
        out = []
        for p, l in self.prop_lights:
            ox, oy, oz = l.get('at', (0, 1, 0))
            r = math.radians(p['rot'])
            s = p.get('scale', 1)
            x = p['x'] + (ox * math.cos(r) + oz * math.sin(r)) * s
            z = p['z'] + (-ox * math.sin(r) + oz * math.cos(r)) * s
            k = 1 + l.get('flicker', 0) * (math.sin(t * 9 + p['x']) * 0.6 + math.sin(t * 23 + p['z']) * 0.4)
            out.append((Vec3(x, oy * s, z), l['colour'], l['radius'], l['strength'] * k))
        return out

    def destroy(self):
        destroy(self.root)

    # ── random arena ─────────────────────────────────────────────────────────
    def build_random(self):
        n, r = self.n, self.rnd

        def rand_cell(margin):
            return margin + int(r() * (n - margin * 2)), margin + int(r() * (n - margin * 2))

        for k in range(3):                        # winding dirt tracks out from the middle
            a = k * math.tau / 3 + r() * 1.2
            x, z = (r() - 0.5) * 4, (r() - 0.5) * 4
            turn = 0.0
            for _ in range(80):
                turn = turn * 0.9 + (r() - 0.5) * 0.35
                a += turn
                x += math.cos(a) * 0.7
                z += math.sin(a) * 0.7
                if abs(x) > self.half - 3 or abs(z) > self.half - 3:
                    break
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if dx * dx + dz * dz <= 1 or r() < 0.25:
                            gx, gz = self.to_grid(x + dx * 0.8, z + dz * 0.8)
                            if self.inside(gx, gz, 2):
                                self.set_path(gx, gz, 'dirt')
        for _ in range(22):                       # block trees
            gx, gz = rand_cell(2)
            if not self.free(gx, gz, 2, paths_ok=False):
                continue
            h = 3 + int(r() * 3)
            self.column('log', gx, gz, h)
            for y in range(h - 1, h + 2):
                rad = 1 if y == h + 1 else 2
                for dx in range(-rad, rad + 1):
                    for dz in range(-rad, rad + 1):
                        if (dx or dz) or y >= h:
                            if abs(dx) == rad and abs(dz) == rad and r() < 0.6:
                                continue
                            if self.block_at(gx + dx, y, gz + dz) is None:
                                self.place('leaves', gx + dx, y, gz + dz, solid=False)
        for _ in range(26):                       # crate piles
            gx, gz = rand_cell(2)
            if not self.free(gx, gz, 1, paths_ok=False):
                continue
            w, d = 1 + int(r() * 2), 1 + int(r() * 2)
            for dx in range(w):
                for dz in range(d):
                    self.column('crate', gx + dx, gz + dz, 2 if r() < 0.3 else 1)
        for _ in range(10):                       # ruined walls
            gx, gz = rand_cell(4)
            horiz, length = r() < 0.5, 4 + int(r() * 6)
            cells = [(gx + k, gz) if horiz else (gx, gz + k) for k in range(length)]
            if not all(self.free(x, z, 1, paths_ok=False) for x, z in cells):
                continue
            for x, z in cells:
                kind = 'mossy' if r() < 0.6 else ('brick' if r() < 0.6 else 'planks')
                self.column(kind, x, z, 1 + int(r() * 3))
        for _ in range(12):                       # pillars
            gx, gz = rand_cell(3)
            if not self.free(gx, gz, 1, paths_ok=False):
                continue
            self.column('stone', gx, gz, 3 + int(r() * 3), top='obsidian')
        benches = 0
        for attempt in range(240):                # two workbenches: one near the start, one further out
            a = r() * math.tau
            dist = 7 + r() * 5 if benches == 0 else 16 + r() * max(2, self.half - 20)
            gx, gz = self.to_grid(math.cos(a) * dist, math.sin(a) * dist)
            if not self.free(gx, gz, 1, paths_ok=attempt > 140):    # crowded map: beside a track is fine
                continue
            self.add_prop('workbench', gx - self.half + 0.5, gz - self.half + 0.5, (int(r() * 4)) * 90)
            benches += 1
            if benches == 2:
                break
        fires = 0
        for _ in range(40):                       # a couple of campfires
            gx, gz = rand_cell(5)
            if fires < 2 and self.free(gx, gz, 1, paths_ok=False):
                self.add_prop('campfire', gx - self.half + 0.5, gz - self.half + 0.5, r() * 360)
                fires += 1
        path_cells = sorted(self.paths)
        lamps = 0
        for _ in range(60):                       # lamp posts beside the tracks
            if not path_cells or lamps >= 5:
                break
            gx, gz = path_cells[int(r() * len(path_cells))]
            side = (2, 0) if r() < 0.5 else (0, 2)
            gx, gz = gx + side[0] * (1 if r() < 0.5 else -1), gz + side[1] * (1 if r() < 0.5 else -1)
            if self.free(gx, gz, 0, paths_ok=False) and all(
                    math.hypot(p['x'] - (gx - self.half + 0.5), p['z'] - (gz - self.half + 0.5)) > 9
                    for p in self.props if p['id'] == 'lamp_post'):
                self.add_prop('lamp_post', gx - self.half + 0.5, gz - self.half + 0.5, int(r() * 4) * 90)
                lamps += 1
        for _ in range(45):                       # low-poly bushes and flowers
            gx, gz = rand_cell(2)
            if self.free(gx, gz, 0, paths_ok=False):
                aid = ('bush', 'tall_grass', 'flowers', 'fern', 'rock', 'flower_bush')[int(r() * 6)]
                self.add_prop(aid, gx - self.half + 0.2 + r() * 0.6, gz - self.half + 0.2 + r() * 0.6,
                              r() * 360, 0.85 + r() * 0.35)

    # ── maps ─────────────────────────────────────────────────────────────────
    def load(self, data):
        for x, z, kind, h in data.get('blocks', []):
            gx, gz = self.to_grid(x, z)
            if self.inside(gx, gz, 1 if self.walls else 0):
                self.set_column(gx, gz, kind, int(h))
        for x, z, kind in data.get('paths', []):
            self.set_path(*self.to_grid(x, z), kind)
        for entry in data.get('props', []):
            aid, x, z = entry[0], entry[1], entry[2]
            rot = entry[3] if len(entry) > 3 else 0
            scale = entry[4] if len(entry) > 4 else 1
            self.add_prop(aid, x, z, rot, scale)

    def to_map(self, name=None):
        edge = 1 if self.walls else 0
        blocks = []
        for (gx, gz), col in sorted(self.columns.items()):
            if not self.inside(gx, gz, edge) or not col:
                continue
            kinds = list(col.values())
            blocks.append([gx - self.half, gz - self.half, kinds[0], max(col) + 1])
        paths = [[gx - self.half, gz - self.half, kind] for (gx, gz), kind in sorted(self.paths.items())]
        props = [[p['id'], round(p['x'], 2), round(p['z'], 2), round(p['rot'], 1), round(p['scale'], 2)]
                 for p in self.props]
        return dict(format=1, name=name or self.name, size=self.half, walls=self.walls,
                    blocks=blocks, paths=paths, props=props)

    # ── physics queries ────────────────────────────────────────────────────
    def _cells(self, x, z, radius):
        """Yield (height, cell_x, cell_z) for solid columns overlapping a circle."""
        for cx in range(math.floor(x - radius), math.floor(x + radius) + 1):
            for cz in range(math.floor(z - radius), math.floor(z + radius) + 1):
                h = self.cell_height(cx + self.half, cz + self.half)
                if not h:
                    continue
                px = max(cx, min(x, cx + 1))
                pz = max(cz, min(z, cz + 1))
                if (x - px) ** 2 + (z - pz) ** 2 < radius * radius:
                    yield h, cx, cz

    def ground_at(self, x, z, radius, feet_y):
        """Highest floor under a circle that is at or below feet_y."""
        g = 0
        for h, _, _ in self._cells(x, z, radius):
            if feet_y + 0.05 >= h > g:
                g = h
        return g

    def blocked(self, x, z, radius, feet_y):
        return any(h > feet_y + 0.05 for h, _, _ in self._cells(x, z, radius))

    def walkable_line(self, a, b, step=0.5):
        """True if nothing solid stands on the ground between a and b (x/z only)."""
        dx, dz = b[0] - a[0], b[2] - a[2]
        n = int(math.hypot(dx, dz) / step)
        for k in range(1, n):
            gx, gz = self.to_grid(a[0] + dx * k / n, a[2] + dz * k / n)
            if self.inside(gx, gz) and self.heights[self.gidx(gx, gz)] > 0.05:
                return False
        return True

    def collide(self, pos, radius):
        """Push a circle (pos.x, pos.z) out of columns taller than pos.y. Returns new (x, z)."""
        x, z, y = pos[0], pos[2], pos[1]
        for _ in range(3):
            moved = False
            for cx in range(math.floor(x - radius), math.floor(x + radius) + 1):
                for cz in range(math.floor(z - radius), math.floor(z + radius) + 1):
                    h = self.cell_height(cx + self.half, cz + self.half)
                    if h <= y + 0.05:
                        continue
                    px = max(cx, min(x, cx + 1))
                    pz = max(cz, min(z, cz + 1))
                    dx, dz = x - px, z - pz
                    d2 = dx * dx + dz * dz
                    if d2 >= radius * radius:
                        continue
                    if d2 < 1e-8:      # centre inside the column: shortest way out
                        options = [(x - cx, 'l'), (cx + 1 - x, 'r'), (z - cz, 'b'), (cz + 1 - z, 't')]
                        side = min(options)[1]
                        if side == 'l': x = cx - radius
                        elif side == 'r': x = cx + 1 + radius
                        elif side == 'b': z = cz - radius
                        else: z = cz + 1 + radius
                    else:
                        d = math.sqrt(d2)
                        x += dx / d * (radius - d)
                        z += dz / d * (radius - d)
                    moved = True
            if not moved:
                break
        return x, z

    def raycast(self, o, d, max_dist):
        """Distance along a ray until it hits a solid column or the ground (voxel DDA)."""
        ox, oy, oz = o
        dx, dy, dz = d
        limit = min(max_dist, -oy / dy if dy < -1e-6 else math.inf)
        ix, iz = math.floor(ox), math.floor(oz)
        step_x, step_z = (1 if dx > 0 else -1), (1 if dz > 0 else -1)
        tdx = abs(1 / dx) if abs(dx) > 1e-9 else math.inf
        tdz = abs(1 / dz) if abs(dz) > 1e-9 else math.inf
        tmx = ((ix + 1 - ox) if dx > 0 else (ox - ix)) * tdx if abs(dx) > 1e-9 else math.inf
        tmz = ((iz + 1 - oz) if dz > 0 else (oz - iz)) * tdz if abs(dz) > 1e-9 else math.inf
        t = 0.0
        while t < limit:
            h = self.cell_height(ix + self.half, iz + self.half)
            t_next = min(tmx, tmz, limit)
            if h > 0:
                y0, y1 = oy + dy * t, oy + dy * t_next
                if y0 < h:
                    return t
                if y1 < h:
                    return t + (h - y0) / dy
            if t_next >= limit:
                break
            if tmx < tmz:
                t, tmx, ix = tmx, tmx + tdx, ix + step_x
            else:
                t, tmz, iz = tmz, tmz + tdz, iz + step_z
        return limit

    def line_of_sight(self, a, b):
        d = b - a
        length = d.length()
        if length < 1e-6:
            return True
        return self.raycast(a, d / length, length) >= length - 0.05

    def random_spawn(self, away_from, min_dist=16):
        if self.zombie_spawns:
            far = [s for s in self.zombie_spawns if math.hypot(s.x - away_from[0], s.z - away_from[2]) >= 10]
            s = random.choice(far or self.zombie_spawns)
            for _ in range(10):
                x, z = s.x + (random.random() - 0.5) * 1.6, s.z + (random.random() - 0.5) * 1.6
                if not self.blocked(x, z, 0.8, 0):
                    return Vec3(x, 0, z)
            return Vec3(s.x, 0, s.z)
        for _ in range(60):
            edge = random.randrange(4)
            along = (random.random() * 2 - 1) * (self.half - 3)
            inset = self.half - 2 - random.random() * 4
            x, z = [(along, -inset), (along, inset), (-inset, along), (inset, along)][edge]
            if self.height_at(x, z) > 0 or self.blocked(x, z, 0.8, 0):
                continue
            if math.hypot(x - away_from[0], z - away_from[2]) < min_dist:
                continue
            return Vec3(x, 0, z)
        return Vec3(self.half - 3, 0, self.half - 3)
