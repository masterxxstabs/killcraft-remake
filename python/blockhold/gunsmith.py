"""Gunsmith: builds detailed low-poly guns and their attachments in code.

Guns are built from real-gun shapes: bevelled receivers and slides, round
barrels, curved magazines from side profiles, angled grips, rails with ridges.
Every recipe lives in data/gun_models.py; attachments in data/attachments.py.

Coordinates: x = right, y = up, z = forward, in metres. The hand holds the gun
at (0, 0, 0), so most guns stretch from about z = -0.25 (stock) to +0.7 (muzzle).
"""
import math
from .lowpoly import LowPoly, _cross, _dot, _norm, _sub

GUN_SUN = (0.55, 0.8, -0.3)        # light from above, to the right, slightly behind the camera

MATERIALS = {
    # name: (colour, shininess)
    'black': ('#1d1e22', 0.25), 'polymer': ('#26282d', 0.12), 'gunmetal': ('#383c43', 0.45),
    'steel': ('#666b73', 0.6), 'bright': ('#a3a9b0', 0.8), 'chrome': ('#cdd2d8', 1.0),
    'wood': ('#7a4a26', 0.15), 'wood_dark': ('#55321a', 0.12), 'tan': ('#a8916a', 0.1),
    'od': ('#555f43', 0.1), 'brass': ('#c9a227', 0.8), 'rubber': ('#121315', 0.05),
    'glass': ('#4f9ab8', 0.9), 'glass_dark': ('#23394a', 0.9), 'red': ('#ff3b3b', 0.2),
    'green': ('#52ff6e', 0.2), 'orange': ('#d9682b', 0.2), 'yellow': ('#e8c23a', 0.2),
    'white': ('#e8e8e4', 0.2), 'glow_cyan': ('#7fe7ff', 0.0), 'glow_purple': ('#c07bff', 0.0),
    'glow_orange': ('#ff9a3c', 0.0), 'frost': ('#a8e2ff', 0.5), 'red_paint': ('#a8242e', 0.35),
    'copper': ('#b8733a', 0.7),
}

# Camos repaint the 'main' and 'furniture' parts of a gun. Each face picks a
# colour from the list, which gives a faceted camo look.
CAMOS = {
    'factory': dict(name='Factory', price=0, colours=None),
    'woodland': dict(name='Woodland', price=150, colours=['#4f5a3a', '#6b5a3a', '#2f3322', '#7d7048']),
    'desert': dict(name='Desert', price=150, colours=['#c2a878', '#a8916a', '#d6c39b', '#8f7a55']),
    'arctic': dict(name='Arctic', price=200, colours=['#e8ecef', '#c7ced4', '#9aa3ab', '#f5f7f9']),
    'urban': dict(name='Urban', price=200, colours=['#55595f', '#3a3d42', '#7a7f86', '#2a2c30']),
    'tiger': dict(name='Tiger', price=300, colours=['#d9822b', '#1b1c1f', '#e09a3a', '#c06a1b']),
    'crimson': dict(name='Crimson', price=350, colours=['#8a1c24', '#a8242e', '#5a1218']),
    'toxic': dict(name='Toxic', price=400, colours=['#7dff3a', '#3a6b1c', '#1b1c1f', '#5ad12a']),
    'galaxy': dict(name='Galaxy', price=600, colours=['#2a1b4a', '#4a2b8a', '#1a1030', '#8a6bd6', '#ffffff']),
    'gold': dict(name='Gold', price=1500, colours=['#d9a92b', '#e8bd45', '#c4931f', '#f2d36b'], spec=1.0),
}


def _area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts))) / 2


def _ear_clip(pts):
    """Triangulate a simple counter-clockwise polygon."""
    idx = list(range(len(pts)))
    tris = []

    def inside(p, a, b, c):
        def s(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
    guard = 0
    while len(idx) > 3 and guard < 500:
        guard += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-12:
                continue                      # reflex corner
            if any(inside(pts[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


class Smith:
    def __init__(self, camo='factory', seed=7):
        self.lp = LowPoly(seed=seed, variation=0.02, sun=GUN_SUN)
        self.camo = CAMOS.get(camo or 'factory', CAMOS['factory'])
        self.mounts = {}

    # ── colours ──────────────────────────────────────────────────────────────
    def paint(self, mat, slot):
        """Pick the colour (or camo palette) and shininess for a part."""
        colour, spec = MATERIALS.get(mat, (mat, 0.2))
        if self.camo['colours'] and slot in ('main', 'furniture'):
            return self.camo['colours'], self.camo.get('spec', 0.15)
        return colour, spec

    def _use(self, mat, slot):
        colour, spec = self.paint(mat, slot)
        self.lp.spec = spec
        return colour

    def mount(self, name, pos):
        self.mounts[name] = pos

    # ── basic shapes ─────────────────────────────────────────────────────────
    def extrude(self, pts, axis, a0, a1, mat, slot='main'):
        """Extrude a 2D outline. axis 'z': outline in (x, y), depth along z.
        axis 'x': outline in (z, y) seen from the side, thickness along x."""
        colour = self._use(mat, slot)
        if _area(pts) < 0:
            pts = pts[::-1]

        def P(u, v, w):
            return (u, v, w) if axis == 'z' else (w, v, u)
        n = len(pts)
        for i in range(n):
            (u0, v0), (u1, v1) = pts[i], pts[(i + 1) % n]
            du, dv = u1 - u0, v1 - v0
            length = math.hypot(du, dv) or 1
            nu, nv = dv / length, -du / length            # outward in 2D
            mu, mv = (u0 + u1) / 2 - nu * 0.001, (v0 + v1) / 2 - nv * 0.001
            inside = P(mu, mv, (a0 + a1) / 2)
            self.lp.quad(P(u0, v0, a0), P(u1, v1, a0), P(u1, v1, a1), P(u0, v0, a1), colour, inside)
        for i0, i1, i2 in _ear_clip(pts):
            cu = (pts[i0][0] + pts[i1][0] + pts[i2][0]) / 3
            cv = (pts[i0][1] + pts[i1][1] + pts[i2][1]) / 3
            self.lp.tri(P(*pts[i0], a1), P(*pts[i1], a1), P(*pts[i2], a1), colour, P(cu, cv, a1 - 0.001 * (a1 - a0 > 0 or -1)))
            self.lp.tri(P(*pts[i0], a0), P(*pts[i1], a0), P(*pts[i2], a0), colour, P(cu, cv, a0 + 0.001 * (a1 - a0 > 0 or -1)))

    def box(self, x0, x1, y0, y1, z0, z1, mat, slot='main', bevel=0.0):
        """A box between two corners; bevel rounds off the long (z) edges."""
        b = min(bevel, (x1 - x0) / 2.2, (y1 - y0) / 2.2)
        if b <= 0:
            pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        else:
            pts = [(x0 + b, y0), (x1 - b, y0), (x1, y0 + b), (x1, y1 - b), (x1 - b, y1), (x0 + b, y1), (x0, y1 - b), (x0, y0 + b)]
        self.extrude(pts, 'z', z0, z1, mat, slot)

    def side(self, pts, width, mat, slot='main', x=0.0):
        """A part drawn as its side outline (z, y), centred on x with the given width."""
        self.extrude(pts, 'x', x - width / 2, x + width / 2, mat, slot)

    def tube(self, z0, z1, r, mat, slot='metal', y=0.0, x=0.0, sides=10, r1=None):
        colour = self._use(mat, slot)
        self.lp.beam((x, y, z0), (x, y, z1), r, colour, sides=sides, end_radius=r1)

    def cyl_x(self, x0, x1, y, z, r, mat, slot='metal', sides=10):
        colour = self._use(mat, slot)
        self.lp.beam((x0, y, z), (x1, y, z), r, colour, sides=sides)

    # ── gun parts ────────────────────────────────────────────────────────────
    def rail(self, z0, z1, y, width=0.026, mat='black', x=0.0):
        """Picatinny rail with ridges; the top of the ridges ends at y."""
        self.box(x - width / 2, x + width / 2, y - 0.012, y - 0.004, z0, z1, mat, 'metal', bevel=0.002)
        z = z0 + 0.005
        while z < z1 - 0.006:
            self.box(x - width / 2 - 0.002, x + width / 2 + 0.002, y - 0.006, y, z, z + 0.0055, mat, 'metal')
            z += 0.01

    def grip(self, z, y_top, length=0.11, angle=18, width=0.034, mat='polymer', slot='furniture', back=0.035):
        """A pistol grip hanging from (z, y_top), leaning back by `angle` degrees."""
        t = math.tan(math.radians(angle))
        pts = [(z - back, y_top), (z + 0.012, y_top), (z + 0.012 - length * t, y_top - length),
               (z - back - length * t - 0.006, y_top - length + 0.006), (z - back - length * t * 0.95, y_top - length * 0.55)]
        self.side(pts, width, mat, slot)
        for k in range(3):                        # finger grooves / texture lines
            yy = y_top - 0.03 - k * 0.025
            zz = z + 0.012 - (y_top - yy) * t
            self.box(-width / 2 - 0.001, width / 2 + 0.001, yy - 0.003, yy, zz - 0.004, zz + 0.0005, 'rubber', 'metal')

    def trigger_guard(self, z0, z1, y, depth=0.03, mat='black', slot='main'):
        w = 0.008
        self.box(-w / 2, w / 2, y - depth, y - depth + 0.006, z0, z1, mat, slot)
        self.side([(z1 - 0.006, y), (z1, y), (z1, y - depth), (z1 - 0.006, y - depth)], w, mat, slot)
        self.side([(z0 + 0.02, y - 0.004), (z0 + 0.025, y - 0.004), (z0 + 0.018, y - 0.022), (z0 + 0.014, y - 0.022)],
                  0.006, 'steel', 'metal')          # trigger

    def magazine(self, z, y_top, length, depth=0.05, width=0.026, curve=0.0, angle=0.0, mat='black', slot='main',
                 base=True):
        """A box magazine. curve > 0 bends it forward (AK style)."""
        t = math.tan(math.radians(angle))
        segs = 5 if curve else 1
        front, back = [], []
        for i in range(segs + 1):
            f = i / segs
            yy = y_top - length * f
            bend = curve * f * f
            zz = z + (y_top - yy) * t + bend
            back.append((zz - depth / 2, yy))
            front.append((zz + depth / 2 + curve * f * 0.25, yy))
        pts = back + front[::-1]
        self.side(pts, width, mat, slot)
        if base:
            (bz0, by), (bz1, _) = back[-1], front[-1]
            self.box(-width / 2 - 0.003, width / 2 + 0.003, by - 0.008, by, bz0 - 0.004, bz1 + 0.004, mat, slot)

    def iron_front(self, z, y, mat='black'):
        self.side([(z - 0.012, y), (z + 0.012, y), (z + 0.006, y + 0.035), (z - 0.006, y + 0.035)], 0.012, mat, 'metal')
        self.box(-0.0025, 0.0025, y + 0.03, y + 0.045, z - 0.003, z + 0.003, mat, 'metal')

    def iron_rear(self, z, y, mat='black'):
        self.box(-0.012, 0.012, y, y + 0.025, z - 0.01, z + 0.01, mat, 'metal')
        self.box(-0.004, 0.004, y + 0.012, y + 0.026, z - 0.011, z + 0.011, 'rubber', 'metal')

    def muzzle_brake(self, z, y, r=0.017, length=0.05, mat='black', x=0.0):
        self.tube(z, z + length, r, mat, y=y, x=x)
        for k in range(3):
            zz = z + 0.01 + k * 0.013
            self.box(x - r - 0.001, x + r + 0.001, y - 0.004, y + 0.004, zz, zz + 0.006, 'rubber', 'metal')
        self.mount('muzzle', (x, y, z + length))

    def flash_hider(self, z, y, r=0.014, length=0.045, mat='black', x=0.0):
        self.tube(z, z + length, r, mat, y=y, x=x, sides=8, r1=r * 1.08)
        for a in range(4):
            ang = a / 4 * math.tau + 0.4
            cx, cy = x + math.cos(ang) * r * 0.85, y + math.sin(ang) * r * 0.85
            self.box(cx - 0.002, cx + 0.002, cy - 0.002, cy + 0.002, z + length * 0.4, z + length + 0.001, 'rubber', 'metal')
        self.mount('muzzle', (x, y, z + length))

    def stock_ar(self, z, y):
        """Collapsible AR-style stock behind z (the end of the receiver)."""
        self.tube(z - 0.11, z, 0.016, 'black', y=y)
        self.side([(z - 0.11, y + 0.03), (z - 0.03, y + 0.022), (z - 0.03, y - 0.03), (z - 0.06, y - 0.045),
                   (z - 0.25, y - 0.075), (z - 0.26, y - 0.07), (z - 0.26, y + 0.035), (z - 0.25, y + 0.04)],
                  0.04, 'polymer', 'furniture')
        self.box(-0.022, 0.022, y - 0.075, y + 0.04, z - 0.27, z - 0.258, 'rubber', 'metal')

    def stock_wood(self, z, y, drop=0.06, length=0.28, mat='wood'):
        self.side([(z, y + 0.02), (z, y - 0.035), (z - length, y - 0.035 - drop - 0.06), (z - length - 0.01, y - drop - 0.095),
                   (z - length - 0.01, y - drop + 0.015), (z - length * 0.5, y - drop * 0.4 + 0.012)],
                  0.042, mat, 'furniture')
        self.box(-0.023, 0.023, y - drop - 0.095, y - drop + 0.015, z - length - 0.022, z - length - 0.008, 'rubber', 'metal')

    def stock_skeleton(self, z, y, length=0.24):
        for yy in (y + 0.015, y - 0.045):
            self.box(-0.006, 0.006, yy - 0.012, yy, z - length, z, 'steel', 'metal')
        self.box(-0.018, 0.018, y - 0.07, y + 0.02, z - length - 0.015, z - length, 'rubber', 'metal')

    def stock_folding(self, z, y):
        self.side([(z, y + 0.01), (z - 0.03, y + 0.01), (z - 0.22, y - 0.01), (z - 0.23, y - 0.06), (z - 0.21, y - 0.075),
                   (z - 0.2, y - 0.03), (z - 0.03, y - 0.02)], 0.03, 'polymer', 'furniture')

    def build(self):
        return self.lp.mesh()


# ── attachments (placed at the gun's mount points) ───────────────────────────

def att_reddot(s, m):
    y, z = m
    s.box(-0.016, 0.016, y, y + 0.012, z - 0.03, z + 0.03, 'black', 'metal', bevel=0.003)
    s.tube(z - 0.03, z + 0.03, 0.017, 'black', y=y + 0.03, sides=10)
    s.tube(z - 0.031, z - 0.028, 0.0125, 'glass_dark', y=y + 0.03, sides=10)
    s.box(-0.0015, 0.0015, y + 0.029, y + 0.032, z - 0.034, z - 0.031, 'red', 'metal')


def att_holo(s, m):
    y, z = m
    s.box(-0.018, 0.018, y, y + 0.014, z - 0.04, z + 0.035, 'black', 'metal', bevel=0.004)
    for x in (-0.018, 0.015):
        s.box(x, x + 0.004, y + 0.014, y + 0.05, z - 0.01, z + 0.03, 'black', 'metal')
    s.box(-0.018, 0.019, y + 0.046, y + 0.052, z - 0.01, z + 0.03, 'black', 'metal')
    s.box(-0.014, 0.015, y + 0.016, y + 0.046, z + 0.005, z + 0.008, 'glass', 'metal')
    s.box(-0.003, 0.003, y + 0.029, y + 0.032, z + 0.0045, z + 0.005, 'red', 'metal')


def att_scope(s, m):
    y, z = m
    for zz in (z - 0.04, z + 0.04):
        s.box(-0.012, 0.012, y, y + 0.03, zz - 0.008, zz + 0.008, 'black', 'metal')
    yy = y + 0.045
    s.tube(z - 0.11, z + 0.11, 0.016, 'black', y=yy, sides=12)
    s.tube(z + 0.08, z + 0.16, 0.019, 'black', y=yy, sides=12, r1=0.026)
    s.tube(z - 0.16, z - 0.09, 0.024, 'black', y=yy, sides=12, r1=0.017)
    s.tube(z + 0.16, z + 0.161, 0.023, 'glass', y=yy, sides=12)
    s.tube(z - 0.161, z - 0.16, 0.021, 'glass_dark', y=yy, sides=12)
    s.tube(z - 0.012, z + 0.012, 0.007, 'black', y=yy + 0.02, sides=8)     # turret


def att_suppressor(s, m):
    x, y, z = m
    s.tube(z, z + 0.16, 0.022, 'gunmetal', y=y, x=x, sides=12)
    s.tube(z - 0.005, z + 0.01, 0.024, 'black', y=y, x=x, sides=12)
    s.tube(z + 0.155, z + 0.161, 0.019, 'rubber', y=y, x=x, sides=12)


def att_compensator(s, m):
    x, y, z = m
    s.muzzle_brake(z, y, r=0.019, length=0.06, mat='steel', x=x)


def att_foregrip(s, m):
    y, z = m
    s.box(-0.012, 0.012, y - 0.012, y, z - 0.03, z + 0.03, 'black', 'metal')
    s.side([(z - 0.016, y - 0.01), (z + 0.016, y - 0.01), (z + 0.014, y - 0.1), (z - 0.014, y - 0.1)], 0.026,
           'polymer', 'furniture')


def att_laser(s, m):
    y, z = m
    s.box(-0.016, 0.016, y - 0.03, y, z - 0.035, z + 0.035, 'black', 'metal', bevel=0.004)
    s.tube(z + 0.035, z + 0.037, 0.005, 'red', y=y - 0.015, x=-0.006, sides=6)
    s.tube(z + 0.035, z + 0.037, 0.008, 'glass', y=y - 0.015, x=0.007, sides=8)
