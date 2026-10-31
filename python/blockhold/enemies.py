"""Enemy models (blocky humanoids) and their AI."""
import math
import random
from panda3d.core import Point3, Vec3 as PVec3
from ursina import Vec3, application, destroy
from .data.enemies import ENEMIES
from .render import block, col, node
from .textures import face_texture

_face_cache = {}
SKIN_UV = (0.01, 0.01, 0.06, 0.06)       # a plain-skin pixel of the face texture

# Hitboxes in the enemy's own (unscaled) space: (min, max)
HEAD_BOX = ((-0.27, 1.45, -0.27), (0.27, 1.99, 0.27))
BODY_BOX = ((-0.32, 0.0, -0.22), (0.32, 1.47, 0.22))


def _ray_box(o, d, lo, hi):
    """Slab test. Returns entry distance or None."""
    t0, t1 = -math.inf, math.inf
    for i in range(3):
        if abs(d[i]) < 1e-9:
            if o[i] < lo[i] or o[i] > hi[i]:
                return None
            continue
        a, b = (lo[i] - o[i]) / d[i], (hi[i] - o[i]) / d[i]
        if a > b:
            a, b = b, a
        t0, t1 = max(t0, a), min(t1, b)
        if t0 > t1:
            return None
    if t1 < 0:
        return None
    return max(t0, 0)


class Enemy:
    def __init__(self, game, kind, wave, pos):
        d = ENEMIES[kind]
        self.game, self.kind, self.d = game, kind, d
        self.max_hp = round(d['hp'] * wave['hp_mult'])
        self.hp = self.max_hp
        self.speed = d['speed'] * wave['speed_mult'] * (0.9 + random.random() * 0.2)
        self.damage = d['damage'] * wave['damage_mult']
        self.coin_mult = wave['coin_mult']
        self.scale = d['scale']
        self.radius = 0.35 * self.scale
        self.height = 2 * self.scale
        self.position = Vec3(pos.x, -self.height, pos.z)
        self.kb = Vec3(0, 0, 0)
        self.yaw = 0.0
        self.attack_cd = 0.5
        self.ranged_cd = 1 + random.random() * 2
        self.attack_anim = 0
        self.flash = 0
        self.walk = random.random() * 10
        self.rise = 0.9
        self.dead = False
        self.death_t = 0
        self.stuck_t = 0
        self.detour = 0
        self.detour_side = 1
        self.last_pos = Vec3(pos)
        self.groan_t = 3 + random.random() * 8
        self.build()

    # ── model ────────────────────────────────────────────────────────────────
    def build(self):
        c = self.d['colors']
        if self.kind not in _face_cache:
            _face_cache[self.kind] = face_texture(c['skin'], c['eyes'])
        self.root = node(self.game.world_root)
        self.body = node(self.root, scale=self.scale)
        skin, shirt, pants = c['skin'], c['shirt'], c['pants']
        block(self.body, size=(0.5, 0.72, 0.28), center=(0, 1.11, 0), color=shirt)
        head_uv = {f: SKIN_UV for f in ('top', 'bottom', 'east', 'west', 'south')}
        head_uv['north'] = (0, 0, 1, 1)
        self.head = block(self.body, size=(0.5, 0.5, 0.5), center=(0, 1.72, 0), texture=_face_cache[self.kind], uv_rects=head_uv)
        self.leg_l = self._limb(pants, 0.24, 0.75, -0.13, 0.75)
        self.leg_r = self._limb(pants, 0.24, 0.75, 0.13, 0.75)
        self.arm_l = self._limb(skin, 0.2, 0.72, -0.36, 1.44, sleeve=shirt)
        self.arm_r = self._limb(skin, 0.2, 0.72, 0.36, 1.44, sleeve=shirt)
        if self.d.get('boss'):
            gold = '#e0b030'
            block(self.body, size=(0.56, 0.12, 0.56), center=(0, 2.03, 0), color=gold)
            for x, z in ((-0.22, -0.22), (0.22, -0.22), (-0.22, 0.22), (0.22, 0.22), (0, 0.22)):
                block(self.body, size=(0.09, 0.16, 0.09), center=(x, 2.15, z), color=gold)
        self.root.position = self.position

    def _limb(self, color, w, h, x, y, sleeve=None):
        pivot = node(self.body, position=(x, y, 0))
        block(pivot, size=(w, h, w), center=(0, -h / 2, 0), color=color)
        if sleeve:
            block(pivot, size=(w + 0.02, 0.24, w + 0.02), center=(0, -0.1, 0), color=sleeve)
        return pivot

    def destroy(self):
        destroy(self.root)

    # ── helpers ──────────────────────────────────────────────────────────────
    def head_pos(self):
        return Vec3(self.position.x, self.position.y + 1.72 * self.scale, self.position.z)

    def chest_pos(self):
        return Vec3(self.position.x, self.position.y + 1.1 * self.scale, self.position.z)

    def ray_hit(self, o, d):
        """(distance, is_head) where a world ray hits this enemy, or None."""
        render = application.base.render
        lo = self.body.getRelativePoint(render, Point3(*o))
        ld = self.body.getRelativeVector(render, PVec3(*d))
        th = _ray_box(lo, ld, *HEAD_BOX)
        tb = _ray_box(lo, ld, *BODY_BOX)
        if th is None and tb is None:
            return None
        if tb is None or (th is not None and th <= tb):
            return th, True
        return tb, False

    # ── combat ───────────────────────────────────────────────────────────────
    def hurt(self, amount, headshot=False, knock=None):
        if self.dead:
            return
        g = self.game
        self.hp -= amount
        self.flash = 0.1
        if knock is not None:
            self.kb += knock / max(1, self.scale * self.scale)
        top = Vec3(self.position.x, self.position.y + self.height + 0.2, self.position.z)
        g.effects.damage_number(self.head_pos() + Vec3(0, 0.4, 0) if headshot else top, amount, crit=headshot)
        g.effects.burst(self.head_pos() if headshot else self.chest_pos(), self.d['colors']['skin'],
                        8 if headshot else 4, speed=4, size=0.1)
        if self.hp <= 0:
            self.dead = True
            self.hp = 0
            g.sounds.play('death', pitch=0.8 + random.random() * 0.4)
            g.on_enemy_killed(self, headshot)

    def shoot(self, r):
        g = self.game
        start = self.head_pos()
        target = g.player.eye() - Vec3(0, 0.5, 0)
        base_dir = (target - start).normalized()
        g.sounds.play('spit')
        for i in range(r['count']):
            off = (i - (r['count'] - 1) / 2) * r['spread']
            ca, sa = math.cos(off), math.sin(off)
            d = Vec3(base_dir.x * ca + base_dir.z * sa, base_dir.y, -base_dir.x * sa + base_dir.z * ca)
            g.projectiles.spawn_enemy(start + d * (self.radius + 0.4), d * r['speed'],
                                      r['damage'] * (self.damage / self.d['damage']), r['color'])
        self.attack_anim = 0.25

    # ── per frame ────────────────────────────────────────────────────────────
    def update(self, dt):
        """Returns False when the enemy should be removed."""
        g = self.game
        if self.flash > 0:
            self.flash -= dt
        k = 3 if self.flash > 0 else 1
        self.root.setColorScale(k, k, k, 1)

        if self.dead:
            self.death_t += dt
            self.root.rotation_x = -min(90, self.death_t * 290)
            self.position += self.kb * dt
            self.kb *= max(0, 1 - dt * 6)
            if self.death_t > 1.2:
                self.position.y -= dt * 1.5
            self.root.position = self.position
            return self.death_t < 2.4

        p = g.player.position
        if self.rise > 0:
            self.rise -= dt
            self.position.y = -self.height * max(0, self.rise / 0.9)
            if random.random() < 0.3:
                g.effects.burst(Vec3(self.position.x, 0.1, self.position.z), '#6b4a2b', 1, speed=3, size=0.15)
            if self.rise <= 0:
                self.position.y = 0
            self.face(p)
            self.root.position = self.position
            return True

        tx, tz = p.x - self.position.x, p.z - self.position.z
        dist = math.hypot(tx, tz)
        if dist > 1e-4:
            tx, tz = tx / dist, tz / dist
        mx, mz = tx, tz
        speed = self.speed

        r = self.d.get('ranged')
        if r:
            self.ranged_cd -= dt
            can_see = dist < r['range'] and g.world.line_of_sight(self.head_pos(), g.player.eye())
            if can_see and dist > 6 and not self.d.get('boss'):
                side = 0.6 if math.sin(self.walk * 0.3) > 0 else -0.6
                mx, mz = -tz * side, tx * side
                speed *= 0.6
            if can_see and self.ranged_cd <= 0:
                self.ranged_cd = 1 / r['rate'] * (0.8 + random.random() * 0.4)
                self.shoot(r)

        if self.detour > 0:     # stuck: walk sideways for a moment
            self.detour -= dt
            s = self.detour_side
            mx, mz = -tz * s + tx * 0.3, tx * s + tz * 0.3

        for o in g.enemies.list:      # don't stand inside each other
            if o is self or o.dead or o.rise > 0:
                continue
            dx, dz = self.position.x - o.position.x, self.position.z - o.position.z
            mn = self.radius + o.radius + 0.25
            d2 = dx * dx + dz * dz
            if 1e-6 < d2 < mn * mn:
                d = math.sqrt(d2)
                mx += dx / d * (mn - d) * 3
                mz += dz / d * (mn - d) * 3

        reach = self.d['reach'] + g.player.radius
        if dist < reach * 0.8:
            speed = 0
        ml = math.hypot(mx, mz)
        if ml > 1:
            mx, mz = mx / ml, mz / ml

        self.position.x += (mx * speed + self.kb.x) * dt
        self.position.z += (mz * speed + self.kb.z) * dt
        self.kb *= max(0, 1 - dt * 8)
        self.position.y = 0
        self.position.x, self.position.z = g.world.collide(self.position, self.radius)

        self.stuck_t += dt
        if self.stuck_t > 0.6:
            moved = (self.last_pos - self.position).length()
            if speed > 0 and moved < self.speed * 0.15 and self.detour <= 0:
                self.detour = 0.8 + random.random() * 0.6
                self.detour_side = random.choice((1, -1))
            self.last_pos = Vec3(self.position)
            self.stuck_t = 0

        self.attack_cd -= dt
        if dist < reach and abs(p.y - self.position.y) < self.height * 0.8 + 0.6 and self.attack_cd <= 0:
            self.attack_cd = 1 / self.d['attack_rate']
            self.attack_anim = 0.3
            g.player.hurt(self.damage, self.position)

        self.groan_t -= dt
        if self.groan_t <= 0:
            self.groan_t = 6 + random.random() * 10
            if dist < 20:
                g.sounds.play('groan', volume=0.6, pitch=0.7 + random.random() * 0.6)

        self.face(p)
        self.animate(dt, speed)
        self.root.position = self.position
        return True

    def face(self, target):
        want = math.degrees(math.atan2(target.x - self.position.x, target.z - self.position.z))
        diff = (want - self.yaw + 180) % 360 - 180
        self.yaw += diff * 0.2
        self.root.rotation_y = self.yaw

    def animate(self, dt, speed):
        self.walk += dt * (2 + speed * 2.2)
        swing = math.sin(self.walk) * 40 if speed > 0 else 0
        self.leg_l.rotation_x = swing
        self.leg_r.rotation_x = -swing
        pose = self.d['pose']
        arm = -85 if pose == 'reach' else 0
        arm_swing = swing * 1.3 if pose == 'run' else swing * 0.5 if pose == 'heavy' else math.sin(self.walk * 0.5) * 5
        if self.attack_anim > 0:
            self.attack_anim -= dt
            arm = -90 - math.sin(max(0, self.attack_anim) / 0.3 * math.pi) * 50
            arm_swing = 0
        self.arm_l.rotation_x = arm + arm_swing
        self.arm_r.rotation_x = arm - arm_swing


class EnemyManager:
    def __init__(self, game):
        self.game = game
        self.list = []

    def spawn(self, kind, wave, pos):
        e = Enemy(self.game, kind, wave, pos)
        self.list.append(e)
        return e

    def alive(self):
        return (e for e in self.list if not e.dead)

    def alive_count(self):
        return sum(1 for e in self.list if not e.dead)

    def update(self, dt):
        for e in list(self.list):
            if not e.update(dt):
                e.destroy()
                self.list.remove(e)

    def raycast(self, o, d, max_dist):
        """Every enemy hit along a ray, closest first: [(dist, enemy, is_head)]"""
        hits = []
        for e in self.list:
            if e.dead or e.rise > 0.3:
                continue
            # cheap distance check first
            to = e.chest_pos() - o
            along = to.x * d[0] + to.y * d[1] + to.z * d[2]
            if along < -2 or along > max_dist + 3:
                continue
            perp2 = to.length_squared() - along * along
            if perp2 > (1.3 * e.scale) ** 2:
                continue
            h = e.ray_hit(o, d)
            if h and h[0] <= max_dist:
                hits.append((h[0], e, h[1]))
        hits.sort(key=lambda h: h[0])
        return hits

    def clear(self):
        for e in self.list:
            e.destroy()
        self.list = []
