"""The arena: a grid of 1x1 block columns, drawn as one merged mesh."""
import math
import random
from ursina import Entity, Mesh, Vec3
from .render import WORLD_SHADER, add_box, node
from .textures import Atlas, grass_texture

NEIGHBOURS = {
    'top': (0, 1, 0), 'bottom': (0, -1, 0), 'east': (1, 0, 0),
    'west': (-1, 0, 0), 'north': (0, 0, 1), 'south': (0, 0, -1),
}


class World:
    def __init__(self, seed=None):
        self.half = 34                      # arena spans -half .. +half
        self.n = self.half * 2
        self.heights = [0] * (self.n * self.n)
        self.blocks = {}                    # (ix, y, iz) -> kind
        self.rnd = random.Random(seed).random
        self.atlas = Atlas()
        self.root = node()
        self.build()
        self.build_mesh()

    # ── grid helpers ───────────────────────────────────────────────────────
    def cell_height(self, ix, iz):
        if ix < 0 or iz < 0 or ix >= self.n or iz >= self.n:
            return 99
        return self.heights[iz * self.n + ix]

    def height_at(self, x, z):
        return self.cell_height(math.floor(x) + self.half, math.floor(z) + self.half)

    def place(self, kind, ix, y, iz, solid=True):
        self.blocks[(ix, y, iz)] = kind
        if solid and 0 <= ix < self.n and 0 <= iz < self.n:
            i = iz * self.n + ix
            self.heights[i] = max(self.heights[i], y + 1)

    def column(self, kind, ix, iz, h, top=None):
        for y in range(h):
            self.place(top if (top and y == h - 1) else kind, ix, y, iz)

    def free(self, ix, iz, pad=0):
        for dx in range(-pad, pad + 1):
            for dz in range(-pad, pad + 1):
                x, z = ix + dx, iz + dz
                if x < 1 or z < 1 or x >= self.n - 1 or z >= self.n - 1:
                    return False
                if self.heights[z * self.n + x] > 0:
                    return False
        cx, cz = ix - self.half, iz - self.half
        return cx * cx + cz * cz > 30       # keep the middle clear for the player

    def rand_cell(self, margin):
        return (margin + int(self.rnd() * (self.n - margin * 2)),
                margin + int(self.rnd() * (self.n - margin * 2)))

    # ── level layout ───────────────────────────────────────────────────────
    def build(self):
        n, r = self.n, self.rnd

        # outer wall
        for i in range(n):
            for x, z in ((i, 0), (i, n - 1), (0, i), (n - 1, i)):
                if (x, 0, z) not in self.blocks:
                    self.column('stone', x, z, 3, top='brick')

        # trees
        for _ in range(22):
            ix, iz = self.rand_cell(2)
            if not self.free(ix, iz, 2):
                continue
            h = 3 + int(r() * 3)
            self.column('log', ix, iz, h)
            for y in range(h - 1, h + 2):
                rad = 1 if y == h + 1 else 2
                for dx in range(-rad, rad + 1):
                    for dz in range(-rad, rad + 1):
                        if (dx or dz) or y >= h:
                            if abs(dx) == rad and abs(dz) == rad and r() < 0.6:
                                continue
                            if (ix + dx, y, iz + dz) not in self.blocks:
                                self.place('leaves', ix + dx, y, iz + dz, solid=False)

        # crate piles
        for _ in range(26):
            ix, iz = self.rand_cell(2)
            if not self.free(ix, iz, 1):
                continue
            w, d = 1 + int(r() * 2), 1 + int(r() * 2)
            for dx in range(w):
                for dz in range(d):
                    self.column('crate', ix + dx, iz + dz, 2 if r() < 0.3 else 1)

        # ruined walls
        for _ in range(10):
            ix, iz = self.rand_cell(4)
            horiz, length = r() < 0.5, 4 + int(r() * 6)
            cells = [(ix + k, iz) if horiz else (ix, iz + k) for k in range(length)]
            if not all(self.free(x, z, 1) for x, z in cells):
                continue
            for x, z in cells:
                self.column('planks' if r() < 0.3 else 'brick', x, z, 1 + int(r() * 3))

        # pillars
        for _ in range(12):
            ix, iz = self.rand_cell(3)
            if not self.free(ix, iz, 1):
                continue
            self.column('stone', ix, iz, 3 + int(r() * 3), top='obsidian')

    def build_mesh(self):
        verts, tris, uvs, cols = [], [], [], []
        for (ix, y, iz), kind in self.blocks.items():
            skip = [f for f, (dx, dy, dz) in NEIGHBOURS.items() if (ix + dx, y + dy, iz + dz) in self.blocks]
            if y == 0:
                skip.append('bottom')
            if len(skip) == 6:
                continue
            centre = (ix - self.half + 0.5, y + 0.5, iz - self.half + 0.5)
            add_box(verts, tris, uvs, cols, centre, (1, 1, 1), self.atlas.block_rects(kind), skip=skip)
        self.mesh = Entity(parent=self.root, model=Mesh(vertices=verts, triangles=tris, uvs=uvs, colors=cols),
                           texture=self.atlas.texture, shader=WORLD_SHADER)
        size = self.n + 60
        gv, gt, gu, gc = [], [], [], []
        add_box(gv, gt, gu, gc, (0, -0.5, 0), (size, 1, size), {'top': (0, 0, size, size)},
                skip=('bottom', 'east', 'west', 'north', 'south'))
        self.ground = Entity(parent=self.root, model=Mesh(vertices=gv, triangles=gt, uvs=gu, colors=gc),
                             texture=grass_texture(), shader=WORLD_SHADER)

    def destroy(self):
        from ursina import destroy
        destroy(self.root)

    # ── physics queries ────────────────────────────────────────────────────
    def _cells(self, x, z, radius):
        """Yield (height, cell_x, cell_z) for block columns overlapping a circle."""
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

    def collide(self, pos, radius):
        """Push a circle (pos.x, pos.z) out of block columns taller than pos.y. Returns new (x, z)."""
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
                    if d2 < 1e-8:      # centre inside the block: shortest way out
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
        """Distance along a ray until it hits a block or the ground (voxel DDA)."""
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
