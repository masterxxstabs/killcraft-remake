"""Visual-only stuff: particles, tracers, rings, muzzle flashes, damage numbers.
Everything is pooled so we never create entities in the middle of a fight."""
import math
import random
from panda3d.core import Point2, Point3
from ursina import Entity, Mesh, Text, Vec3, application, camera, color as ucolor, window
from .render import WORLD_SHADER, block, col, node


def _ring_mesh(segments=40, inner=0.85):
    verts, tris = [], []
    for i in range(segments + 1):
        a = i / segments * math.tau
        verts += [Vec3(math.cos(a) * inner, 0, math.sin(a) * inner), Vec3(math.cos(a), 0, math.sin(a))]
    for i in range(segments):
        a, b, c, d = i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 3
        tris += [a, b, c, c, b, d, a, c, b, c, d, b]    # both sides
    return Mesh(vertices=verts, triangles=tris, colors=[ucolor.white] * len(verts))


class Effects:
    def __init__(self, game):
        self.game = game
        self.root = node()
        self.particles = []
        for _ in range(220):
            e = block(self.root, color=ucolor.white, enabled=False)
            self.particles.append(dict(e=e, v=Vec3(0, 0, 0), life=0, max=1, g=0, s=0.1))
        self.tracers = []
        for _ in range(80):
            e = block(self.root, size=(1, 1, 1), center=(0, 0, 0.5), color=ucolor.white, enabled=False)
            self.tracers.append(dict(e=e, life=0, max=1))
        self.rings = []
        for _ in range(6):
            e = Entity(parent=self.root, model=_ring_mesh(), shader=WORLD_SHADER, enabled=False)
            self.rings.append(dict(e=e, life=0, max=1, r=1))
        self.numbers = []
        for _ in range(30):
            t = Text('', parent=game.ui.hud, origin=(0, 0), scale=1.4, enabled=False)   # hides with the HUD
            self.numbers.append(dict(t=t, pos=Vec3(0, 0, 0), life=0, max=1))
        self._p = 0
        self._t = 0
        self._n = 0

    # ── spawners ─────────────────────────────────────────────────────────────
    def burst(self, pos, color, count=8, speed=5, size=0.12, life=0.7, gravity=18):
        c = col(color) if isinstance(color, str) else color
        for _ in range(count):
            p = self.particles[self._p]
            self._p = (self._p + 1) % len(self.particles)
            v = Vec3(random.random() - 0.5, random.random() * 0.8 + 0.2, random.random() - 0.5).normalized()
            p.update(v=v * speed * (0.4 + random.random()), life=life, max=life, g=gravity,
                     s=size * (0.6 + random.random() * 0.8))
            e = p['e']
            e.enabled = True
            e.position = pos
            e.color = c
            e.scale = p['s']
            e.rotation = (random.random() * 90, random.random() * 90, 0)

    def spray(self, pos, direction, colors, count=3, speed=14, spread=0.2, life=0.5, size=0.18, gravity=-4):
        """Particles shot forward in a cone (flamethrower)."""
        for _ in range(count):
            p = self.particles[self._p]
            self._p = (self._p + 1) % len(self.particles)
            d = Vec3(direction) + Vec3((random.random() - 0.5) * 2 * spread, (random.random() - 0.5) * 2 * spread,
                                       (random.random() - 0.5) * 2 * spread)
            d = d.normalized()
            p.update(v=d * speed * (0.7 + random.random() * 0.5), life=life * (0.7 + random.random() * 0.5),
                     max=life, g=gravity, s=size * (0.6 + random.random() * 0.8))
            e = p['e']
            e.enabled = True
            e.position = pos
            e.color = col(random.choice(colors))
            e.scale = p['s']

    def lightning(self, start, end, color='#c07bff', segments=5, life=0.12):
        """A jagged bolt made of short tracers."""
        pts = [Vec3(start)]
        d = end - start
        jitter = min(0.6, d.length() * 0.08)
        for i in range(1, segments):
            t = i / segments
            pts.append(start + d * t + Vec3((random.random() - 0.5) * 2 * jitter, (random.random() - 0.5) * 2 * jitter,
                                            (random.random() - 0.5) * 2 * jitter))
        pts.append(Vec3(end))
        for a, b in zip(pts, pts[1:]):
            self.tracer(a, b, color, 0.045, life)
        self.burst(end, color, 3, speed=3, size=0.08, life=0.3)

    def tracer(self, start, end, color='#fff2a8', width=0.025, life=0.07):
        t = self.tracers[self._t]
        self._t = (self._t + 1) % len(self.tracers)
        e = t['e']
        e.enabled = True
        e.position = start
        e.look_at(end)
        e.scale = (width, width, max(0.01, (end - start).length()))
        e.color = col(color)
        t.update(life=life, max=life, c=col(color))

    def ring(self, pos, radius, color):
        r = min(self.rings, key=lambda x: x['life'])
        e = r['e']
        e.enabled = True
        e.position = Vec3(pos.x, pos.y + 0.1, pos.z)
        r.update(life=0.45, max=0.45, r=radius, c=col(color))

    def explosion(self, pos, radius):
        self.burst(pos, '#ffb13b', 16, speed=radius * 3, size=0.35, life=0.7, gravity=4)
        self.burst(pos, '#ff4d2e', 10, speed=radius * 2, size=0.3, life=0.6, gravity=4)
        self.burst(pos, '#444444', 8, speed=radius * 1.5, size=0.45, life=1.1, gravity=-2)
        self.ring(Vec3(pos.x, max(0, pos.y - 0.5), pos.z), radius, '#ffa040')

    def damage_number(self, pos, amount, crit=False, color=None):
        n = self.numbers[self._n]
        self._n = (self._n + 1) % len(self.numbers)
        t = n['t']
        t.text = str(round(amount))
        t.color = col(color) if color else (col('#ffd54a') if crit else ucolor.white)
        t.scale = 1.9 if crit else 1.4
        jitter = Vec3((random.random() - 0.5) * 0.4, 0, (random.random() - 0.5) * 0.4)
        n.update(pos=Vec3(pos) + jitter, life=0.8, max=0.8)

    def clear(self):
        for p in self.particles:
            p['life'] = 0
            p['e'].enabled = False
        for t in self.tracers:
            t['life'] = 0
            t['e'].enabled = False
        for r in self.rings:
            r['life'] = 0
            r['e'].enabled = False
        for n in self.numbers:
            n['life'] = 0
            n['t'].enabled = False

    # ── per frame ────────────────────────────────────────────────────────────
    def world_to_ui(self, pos):
        base = application.base
        p3 = base.cam.getRelativePoint(base.render, Point3(pos.x, pos.y, pos.z))
        p2 = Point2()
        if not base.camLens.project(p3, p2):
            return None
        return Vec3(p2.x * window.aspect_ratio / 2, p2.y / 2, 0)

    def update(self, dt):
        for p in self.particles:
            if p['life'] <= 0:
                continue
            p['life'] -= dt
            e = p['e']
            if p['life'] <= 0:
                e.enabled = False
                continue
            p['v'].y -= p['g'] * dt
            e.position += p['v'] * dt
            if e.y < p['s'] / 2:
                e.y = p['s'] / 2
                p['v'] *= 0.5
                p['v'].y *= -0.3
            e.scale = p['s'] * max(0.01, p['life'] / p['max'])
        for t in self.tracers:
            if t['life'] <= 0:
                continue
            t['life'] -= dt
            if t['life'] <= 0:
                t['e'].enabled = False
            else:
                c = t['c']
                t['e'].color = ucolor.Color(c[0], c[1], c[2], t['life'] / t['max'])
        for r in self.rings:
            if r['life'] <= 0:
                continue
            r['life'] -= dt
            if r['life'] <= 0:
                r['e'].enabled = False
                continue
            k = 1 - r['life'] / r['max']
            r['e'].scale = 0.5 + k * r['r']
            c = r['c']
            r['e'].color = ucolor.Color(c[0], c[1], c[2], 0.8 * (1 - k))
        for n in self.numbers:
            if n['life'] <= 0:
                continue
            n['life'] -= dt
            t = n['t']
            if n['life'] <= 0:
                t.enabled = False
                continue
            n['pos'].y += dt * 1.4
            ui = self.world_to_ui(n['pos'])
            t.enabled = ui is not None
            if ui is not None:
                t.position = ui
                t.alpha = min(1, n['life'] / n['max'] * 2)
