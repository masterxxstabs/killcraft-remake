"""Procedural ragdolls for dead zombies.

When a zombie dies its body goes limp: a skeleton of 15 points (pelvis, neck, head,
shoulders, elbows, hands, hips, knees, feet) joined by "bones" of fixed length is
simulated with Verlet physics (gravity, joint limits, the ground and blocks), and the
zombie's own body parts are hung on it, so it crumples, folds at the knees and
elbows and slumps over things like in GTA. The hit that killed it pushes it: a
headshot snaps the head back, a shotgun blast or an explosion throws it.
After a few seconds it settles ("sleeps") and stops costing anything; later it sinks
into the ground and is removed.
"""
import math
from panda3d.core import Mat4, Point3
from .render import block, node, destroy

GRAVITY = 20.0
ITERATIONS = 4           # constraint passes per step (more = stiffer bones)
# how thick the body is at each joint (keeps it lying on the ground, not half inside it)
RADIUS = dict(pelvis=0.14, neck=0.14, head=0.24, sh=0.12, el=0.1, ha=0.1, hip=0.12, kn=0.12, ft=0.12)
FRICTION = 0.55          # how much ground contact slows a sliding point (per step)
SLEEP_AFTER = 3.5        # seconds: stop simulating even if it's still twitching
MAX_ACTIVE = 14          # ragdolls simulated at once; older ones freeze in place

# point names and where they are on the model (body space, before scaling)
P = ['pelvis', 'neck', 'head', 'sh_l', 'el_l', 'ha_l', 'sh_r', 'el_r', 'ha_r',
     'hip_l', 'kn_l', 'ft_l', 'hip_r', 'kn_r', 'ft_r']
I = {n: i for i, n in enumerate(P)}


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _len(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _norm(a):
    n = _len(a) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _perp(v, ref):
    """ref made perpendicular to v (unit), or some perpendicular if they're parallel."""
    d = _dot(ref, v)
    r = (ref[0] - v[0] * d, ref[1] - v[1] * d, ref[2] - v[2] * d)
    if _len(r) < 1e-4:
        r = _cross(v, (0, 0, 1)) if abs(v[2]) < 0.9 else _cross(v, (1, 0, 0))
    return _norm(r)


class Ragdoll:
    def __init__(self, enemy, impulse=(0, 0, 0), hit='body'):
        self.e = enemy
        self.game = enemy.game
        self.world = enemy.game.world
        self.t = 0.0
        self.asleep = False
        self.calm = 0.0
        s = enemy.scale
        self.s = s
        render = self.game.world_root
        body = enemy.body

        def wp(np, local):
            p = render.getRelativePoint(np, Point3(*local))
            return [p.x, p.y, p.z]
        # where every joint is right now (so it falls from the pose it died in)
        pts = {
            'pelvis': wp(body, (0, 0.75, 0)), 'neck': wp(body, (0, 1.47, 0)), 'head': wp(body, (0, 1.97, 0)),
            'hip_l': wp(body, (-0.13, 0.75, 0)), 'hip_r': wp(body, (0.13, 0.75, 0)),
            'sh_l': wp(body, (-0.36, 1.44, 0)), 'sh_r': wp(body, (0.36, 1.44, 0)),
        }
        for side, arm, leg in (('l', enemy.arm_l, enemy.leg_l), ('r', enemy.arm_r, enemy.leg_r)):
            pts['el_' + side] = wp(arm, (0, -0.36, 0))
            pts['ha_' + side] = wp(arm, (0, -0.72, 0))
            pts['kn_' + side] = wp(leg, (0, -0.375, 0))
            pts['ft_' + side] = wp(leg, (0, -0.75, 0))
        self.p = [pts[n] for n in P]
        self.r = [RADIUS[n.split('_')[0]] * s for n in P]
        # starting speed: how it was moving, plus the push from the killing hit
        vx, vz = enemy.kb.x, enemy.kb.z
        ix, iy, iz = impulse
        self.o = []
        dt0 = 1 / 60
        for n, q in zip(P, self.p):
            k = 1.0
            if hit == 'head' and n in ('head', 'neck'):
                k = 2.2
            elif hit == 'head' and n.startswith(('ft', 'kn')):
                k = 0.2
            elif hit == 'body' and n.startswith(('ft', 'kn')):
                k = 0.35                                # feet stay put, the top goes over
            vel = (vx * 0.3 + ix * k, iy * k, vz * 0.3 + iz * k)
            self.o.append([q[0] - vel[0] * dt0, q[1] - vel[1] * dt0, q[2] - vel[2] * dt0])
        self.dt0 = dt0
        # bones: (a, b, shortest, longest)
        c = []

        def rigid(names):
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    a, b = I[names[i]], I[names[j]]
                    d = _len(_sub(self.p[a], self.p[b]))
                    c.append((a, b, d, d))

        def bone(a, b):
            a, b = I[a], I[b]
            d = _len(_sub(self.p[a], self.p[b]))
            c.append((a, b, d, d))

        def limit(a, b, lo, hi=None):
            """keep two points between lo and hi times the length they'd be when straight"""
            a, b = I[a], I[b]
            c.append((a, b, lo, hi if hi is not None else 99.0))
        rigid(['pelvis', 'neck', 'sh_l', 'sh_r', 'hip_l', 'hip_r'])      # the torso doesn't bend
        bone('neck', 'head')
        torso = 0.72 * s
        limit('head', 'pelvis', torso * 1.25, torso * 1.75)            # the neck flops, but not all the way
        limit('head', 'sh_l', 0.3 * s)
        limit('head', 'sh_r', 0.3 * s)
        for side in ('l', 'r'):
            bone('sh_' + side, 'el_' + side)
            bone('el_' + side, 'ha_' + side)
            limit('sh_' + side, 'ha_' + side, 0.36 * s, 0.72 * s)       # elbows bend to about 120°
            bone('hip_' + side, 'kn_' + side)
            bone('kn_' + side, 'ft_' + side)
            limit('hip_' + side, 'ft_' + side, 0.42 * s, 0.75 * s)      # knees too
            limit('ha_' + side, 'pelvis', 0.2 * s)
            limit('ft_' + side, 'neck', 0.55 * s)                     # legs can't fold up into the chest
        limit('kn_l', 'kn_r', 0.16 * s)
        limit('ft_l', 'ft_r', 0.14 * s)
        limit('el_l', 'el_r', 0.2 * s)
        self.c = c
        self.build_parts()
        self.pose()

    # ── the model hung on the skeleton ───────────────────────────────────────
    def build_parts(self):
        e, s = self.e, self.s
        root = self.game.world_root
        self.root = node(root)
        # the torso (with any extras: shoulder pads, cape, crown...) rides on the pelvis-neck bone
        self.torso = node(self.root)
        inner = node(self.torso, position=(0, -0.75 * s, 0), scale=s)
        for child in list(e.body.children):
            if child in (e.head, e.arm_l, e.arm_r, e.leg_l, e.leg_r):
                continue
            child.parent = inner
        self.head = node(self.root)
        hin = node(self.head, position=(0, -1.47 * s, 0), scale=s)
        e.head.parent = hin
        # limbs in two halves so they bend at elbows and knees
        self.segs = []
        for a, b, uv, w, h in (('sh_l', 'el_l', e.arm_uv, 0.2, 0.72), ('el_l', 'ha_l', e.arm_uv, 0.2, 0.72),
                               ('sh_r', 'el_r', e.arm_uv, 0.2, 0.72), ('el_r', 'ha_r', e.arm_uv, 0.2, 0.72),
                               ('hip_l', 'kn_l', e.leg_uv, 0.24, 0.75), ('kn_l', 'ft_l', e.leg_uv, 0.24, 0.75),
                               ('hip_r', 'kn_r', e.leg_uv, 0.24, 0.75), ('kn_r', 'ft_r', e.leg_uv, 0.24, 0.75)):
            seg = node(self.root)
            part = node(seg, scale=s)
            block(part, size=(w, h / 2, w), center=(0, -h / 4, 0), texture=e.tex, uv_rects=uv)
            self.segs.append((seg, I[a], I[b]))
        for limb in (e.arm_l, e.arm_r, e.leg_l, e.leg_r):
            limb.enabled = False
        e.body.enabled = False
        e.ragdoll_root = self.root

    def _place(self, np, origin, up, right):
        up = _norm(up)
        right = _perp(up, right)
        fwd = _cross(right, up)                  # a proper rotation: never mirrors the model
        np.setMat(Mat4(right[0], right[1], right[2], 0, up[0], up[1], up[2], 0,
                       fwd[0], fwd[1], fwd[2], 0, origin[0], origin[1], origin[2], 1))

    def pose(self):
        p = self.p
        right = _sub(p[I['sh_r']], p[I['sh_l']])
        self._place(self.torso, p[I['pelvis']], _sub(p[I['neck']], p[I['pelvis']]), right)
        self._place(self.head, p[I['neck']], _sub(p[I['head']], p[I['neck']]), right)
        for seg, a, b in self.segs:
            self._place(seg, p[a], _sub(p[a], p[b]), right)

    # ── physics ──────────────────────────────────────────────────────────────
    def push(self, impulse, at=None):
        """A shot or blast hits the body: everything moves, the part that got hit most."""
        self.asleep = False
        self.t = min(self.t, SLEEP_AFTER - 1.0)
        self.calm = 0.0
        for i, (q, o) in enumerate(zip(self.p, self.o)):
            k = 1.0
            if at is not None:
                d = _len(_sub(q, at))
                k = max(0.2, 1.6 - d)
            o[0] -= impulse[0] * k * self.dt0
            o[1] -= impulse[1] * k * self.dt0
            o[2] -= impulse[2] * k * self.dt0

    def ground(self, x, z):
        return self.world.height_at(x, z)

    def step(self, dt):
        if self.asleep:
            return
        dt = min(dt, 1 / 30)
        self.t += dt
        g2 = GRAVITY * dt * dt
        moved = 0.0
        w = self.world
        lim = w.half - 0.6
        for q, o in zip(self.p, self.o):
            vx, vy, vz = (q[0] - o[0]) * 0.995, (q[1] - o[1]) * 0.995, (q[2] - o[2]) * 0.995
            o[0], o[1], o[2] = q[0], q[1], q[2]
            q[0] += vx
            q[1] += vy - g2
            q[2] += vz
            moved = max(moved, abs(vx) + abs(vy) + abs(vz))
        c = self.c
        p = self.p
        for _ in range(ITERATIONS):
            for a, b, lo, hi in c:
                pa, pb = p[a], p[b]
                dx, dy, dz = pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]
                d = math.sqrt(dx * dx + dy * dy + dz * dz) or 1e-6
                if d < lo:
                    k = (d - lo) / d * 0.5
                elif d > hi:
                    k = (d - hi) / d * 0.5
                else:
                    continue
                pa[0] += dx * k
                pa[1] += dy * k
                pa[2] += dz * k
                pb[0] -= dx * k
                pb[1] -= dy * k
                pb[2] -= dz * k
            # the ground, blocks and props: a joint can't go inside them
            for q, o, rad in zip(p, self.o, self.r):
                q[0] = max(-lim, min(lim, q[0]))
                q[2] = max(-lim, min(lim, q[2]))
                h = self.ground(q[0], q[2])
                if q[1] < h + rad:
                    if o[1] < h - 0.25:                   # came in from the side: back out the way it came
                        q[0], q[2] = o[0], o[2]
                        h = self.ground(q[0], q[2])
                        if q[1] < h + rad:
                            q[1] = h + rad
                    else:
                        q[1] = h + rad
                        o[0] += (q[0] - o[0]) * FRICTION     # scrape along the ground
                        o[2] += (q[2] - o[2]) * FRICTION
                        if o[1] < q[1]:
                            o[1] = q[1] - (q[1] - o[1]) * 0.2
        self.pose()
        self.calm = self.calm + dt if moved < 0.004 else 0.0
        if self.calm > 0.4 or self.t > SLEEP_AFTER:
            self.asleep = True

    def sink(self, amount):
        self.root.y -= amount

    def destroy(self):
        destroy(self.root)
        self.e.ragdoll_root = None


class Ragdolls:
    """Keeps the number of ragdolls being simulated down (the oldest go still first)."""

    def __init__(self, game):
        self.game = game
        self.active = []

    def add(self, r):
        self.active.append(r)
        awake = [x for x in self.active if not x.asleep]
        while len(awake) > MAX_ACTIVE:
            awake.pop(0).asleep = True

    def remove(self, r):
        if r in self.active:
            self.active.remove(r)

    def clear(self):
        self.active = []
