"""A tiny toolkit for building flat-shaded low-poly models in code.

Every triangle gets its own vertices and a colour shaded by a fixed sun, which
gives the classic faceted low-poly look without any lighting at run time.
"""
import math
import random
from ursina import Mesh, Vec3, color as ucolor

SUN = (0.42, 0.85, 0.32)
_l = math.sqrt(sum(c * c for c in SUN))
SUN = tuple(c / _l for c in SUN)


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    length = math.sqrt(_dot(a, a)) or 1
    return (a[0] / length, a[1] / length, a[2] / length)


class LowPoly:
    def __init__(self, seed=1, variation=0.05):
        self.verts = []
        self.cols = []
        self.rnd = random.Random(seed)
        self.variation = variation

    # ── triangles ────────────────────────────────────────────────────────────
    def tri(self, a, b, c, colour, outward=None):
        """Add a triangle. `outward` is any point inside the shape (or a direction
        hint) so the triangle faces the right way."""
        n = _cross(_sub(b, a), _sub(c, a))
        if outward is not None:
            centroid = ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3, (a[2] + b[2] + c[2]) / 3)
            out = _sub(centroid, outward)
            # Ursina's front faces have their right-handed normal pointing inwards
            if _dot(n, out) > 0:
                b, c = c, b
                n = (-n[0], -n[1], -n[2])
        face_out = _norm((-n[0], -n[1], -n[2]))
        light = 0.58 + 0.42 * max(0.0, _dot(face_out, SUN)) + 0.08 * max(0.0, face_out[1])
        r, g, bl = rgb(colour) if isinstance(colour, str) else colour
        v = 1 + (self.rnd.random() - 0.5) * 2 * self.variation
        cl = ucolor.Color(min(1, r * light * v), min(1, g * light * v), min(1, bl * light * v), 1)
        self.verts += [a, b, c]
        self.cols += [cl, cl, cl]

    def quad(self, a, b, c, d, colour, inside):
        self.tri(a, b, c, colour, inside)
        self.tri(a, c, d, colour, inside)

    # ── shapes ───────────────────────────────────────────────────────────────
    def box(self, centre, size, colour, top=None, yaw=0.0):
        """Axis-aligned box (optionally turned by `yaw` degrees). `top` = colour of the top face."""
        cx, cy, cz = centre
        hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

        def p(x, y, z):
            return (cx + x * ca + z * sa, cy + y, cz - x * sa + z * ca)
        c = [p(x, y, z) for x in (-hx, hx) for y in (-hy, hy) for z in (-hz, hz)]
        # corner index = xi*4 + yi*2 + zi
        faces = [((0, 1, 3, 2), colour), ((4, 6, 7, 5), colour), ((0, 4, 5, 1), colour),
                 ((2, 3, 7, 6), top or colour), ((0, 2, 6, 4), colour), ((1, 5, 7, 3), colour)]
        for (i, j, k, m), col in faces:
            self.quad(c[i], c[j], c[k], c[m], col, centre)

    def prism(self, centre, width, depth, height, colour, gable=None, yaw=0.0):
        """A gable roof: triangle front/back, two sloped sides. Ridge runs along z."""
        cx, cy, cz = centre
        hw, hd = width / 2, depth / 2
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

        def p(x, y, z):
            return (cx + x * ca + z * sa, cy + y, cz - x * sa + z * ca)
        l0, r0, t0 = p(-hw, 0, -hd), p(hw, 0, -hd), p(0, height, -hd)
        l1, r1, t1 = p(-hw, 0, hd), p(hw, 0, hd), p(0, height, hd)
        inside = p(0, height * 0.3, 0)
        self.quad(l0, t0, t1, l1, colour, inside)
        self.quad(r0, r1, t1, t0, colour, inside)
        self.tri(l0, r0, t0, gable or colour, inside)
        self.tri(l1, t1, r1, gable or colour, inside)
        self.quad(l0, l1, r1, r0, gable or colour, inside)

    def cylinder(self, base, radius, height, colour, sides=6, top_radius=None, top_colour=None, cap=True):
        """Upright cylinder or cone (top_radius=0)."""
        top_radius = radius if top_radius is None else top_radius
        bx, by, bz = base
        ring0, ring1 = [], []
        off = self.rnd.random() * math.tau
        for i in range(sides):
            a = off + i / sides * math.tau
            ring0.append((bx + math.cos(a) * radius, by, bz + math.sin(a) * radius))
            ring1.append((bx + math.cos(a) * top_radius, by + height, bz + math.sin(a) * top_radius))
        inside = (bx, by + height * 0.5, bz)
        for i in range(sides):
            j = (i + 1) % sides
            if top_radius > 0:
                self.quad(ring0[i], ring0[j], ring1[j], ring1[i], colour, inside)
            else:
                self.tri(ring0[i], ring0[j], ring1[0], colour, inside)
        if cap:
            top = (bx, by + height, bz)
            bottom = (bx, by, bz)
            for i in range(sides):
                j = (i + 1) % sides
                if top_radius > 0:
                    self.tri(top, ring1[i], ring1[j], top_colour or colour, (bx, by - 1, bz))
                self.tri(bottom, ring0[j], ring0[i], colour, (bx, by + 1, bz))

    def beam(self, a, b, radius, colour, sides=5, end_radius=None):
        """A cylinder from point a to point b (branches, legs, logs)."""
        end_radius = radius if end_radius is None else end_radius
        d = _norm(_sub(b, a))
        helper = (0, 1, 0) if abs(d[1]) < 0.9 else (1, 0, 0)
        u = _norm(_cross(d, helper))
        v = _cross(d, u)
        ring0, ring1 = [], []
        for i in range(sides):
            ang = i / sides * math.tau
            ca, sa = math.cos(ang), math.sin(ang)
            ring0.append(tuple(a[k] + (u[k] * ca + v[k] * sa) * radius for k in range(3)))
            ring1.append(tuple(b[k] + (u[k] * ca + v[k] * sa) * end_radius for k in range(3)))
        mid = tuple((a[k] + b[k]) / 2 for k in range(3))
        for i in range(sides):
            j = (i + 1) % sides
            self.quad(ring0[i], ring0[j], ring1[j], ring1[i], colour, mid)
            self.tri(b, ring1[i], ring1[j], colour, mid)
            self.tri(a, ring0[j], ring0[i], colour, mid)

    def blob(self, centre, radius, colour, squash=(1, 1, 1), jitter=0.15, detail=1, colours=None):
        """A lumpy low-poly sphere (tree tops, bushes, rocks)."""
        t = (1 + math.sqrt(5)) / 2
        verts = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
                 (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
        verts = [_norm(v) for v in verts]
        faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2),
                 (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5),
                 (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
        for _ in range(detail):
            cache, new = {}, []

            def mid(i, j):
                key = (min(i, j), max(i, j))
                if key not in cache:
                    a, b = verts[i], verts[j]
                    verts.append(_norm(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)))
                    cache[key] = len(verts) - 1
                return cache[key]
            for a, b, c in faces:
                ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
                new += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
            faces = new
        cx, cy, cz = centre
        pts = []
        for v in verts:
            k = radius * (1 + (self.rnd.random() - 0.5) * 2 * jitter)
            pts.append((cx + v[0] * k * squash[0], cy + v[1] * k * squash[1], cz + v[2] * k * squash[2]))
        for a, b, c in faces:
            col = self.rnd.choice(colours) if colours else colour
            self.tri(pts[a], pts[b], pts[c], col, centre)

    def flat(self, centre, size, colour, y_offset=0.02, yaw=0.0):
        """A flat rectangle lying on the ground (rugs, path stones, shadows)."""
        cx, cy, cz = centre
        hx, hz = size[0] / 2, size[1] / 2
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

        def p(x, z):
            return (cx + x * ca + z * sa, cy + y_offset, cz - x * sa + z * ca)
        self.quad(p(-hx, -hz), p(hx, -hz), p(hx, hz), p(-hx, hz), colour, (cx, cy - 1, cz))

    def blade(self, base, height, width, lean, colour, yaw=0.0):
        """A single grass blade / leaf: a thin upright triangle, visible from both sides."""
        bx, by, bz = base
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        a = (bx - ca * width, by, bz + sa * width)
        b = (bx + ca * width, by, bz - sa * width)
        tip = (bx + sa * lean, by + height, bz + ca * lean)
        self.tri(a, b, tip, colour, (bx + sa, by, bz + ca))
        self.tri(a, b, tip, colour, (bx - sa, by, bz - ca))

    # ── output ───────────────────────────────────────────────────────────────
    def mesh(self):
        verts = [Vec3(*v) for v in self.verts]
        return Mesh(vertices=verts, triangles=list(range(len(verts))), colors=self.cols, static=True)

    def triangle_count(self):
        return len(self.verts) // 3
