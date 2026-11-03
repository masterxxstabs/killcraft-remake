"""Enemy models (blocky humanoids) and their AI."""
import heapq
import math
from collections import deque
import random
from panda3d.core import NodePath, Point3, Vec3 as PVec3
from ursina import Vec3, application
from .data.enemies import ENEMIES
from .render import box_mesh
from .textures import zombie_skin
from .net import new_id

# Hitboxes in the enemy's own (unscaled) space: (min, max)
RAGDOLLS = [True]          # dead zombies go limp (Settings → Ragdolls switches it off on slow PCs)
SEP_CELL = 2.2             # grid size for keeping zombies apart (at least the widest gap two bosses keep)
CORPSE_TIME = 7.0          # seconds a body lies there before it sinks away

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


_protos = {}


def zombie_proto(kind, d):
    """Build a zombie type's model once; every zombie of that type is a light copy (the meshes are shared)."""
    if kind in _protos:
        return _protos[kind]
    skin = zombie_skin(kind, d['colors'], d.get('look', {}))
    tex = skin.texture._texture

    def faces(front, side, back=None, top=None, bottom=None):
        r = skin.rect
        return {'north': r(front), 'south': r(back or front), 'east': r(side), 'west': r(side),
                'top': r(top or side), 'bottom': r(bottom or side)}

    def part(parent, size, center, uv):
        m = box_mesh(size, center, uv)
        m.reparentTo(parent)
        m.setTexture(tex, 1)
        return m

    root = NodePath('zombie_' + kind)
    body = root.attachNewNode('body')
    body.setScale(d['scale'])
    static = body.attachNewNode('static')             # the parts that never move on their own: one mesh
    part(static, (0.5, 0.72, 0.28), (0, 1.11, 0), faces('torso_front', 'torso_side', 'torso_back', 'torso_top',
                                                        'torso_bottom'))
    head = body.attachNewNode('head')
    part(head, (0.5, 0.5, 0.5), (0, 1.72, 0), faces('head_front', 'head_side', 'head_back', 'head_top', 'head_bottom'))
    leg = faces('leg_side', 'leg_side', 'leg_side', 'leg_top', 'leg_bottom')
    arm = faces('arm_side', 'arm_side', 'arm_side', 'arm_top', 'arm_bottom')
    for name, w, h, x, y, uv in (('leg_l', 0.24, 0.75, -0.13, 0.75, leg), ('leg_r', 0.24, 0.75, 0.13, 0.75, leg),
                                 ('arm_l', 0.2, 0.72, -0.36, 1.44, arm), ('arm_r', 0.2, 0.72, 0.36, 1.44, arm)):
        pivot = body.attachNewNode(name)
        pivot.setPos(x, y, 0)
        part(pivot, (w, h, w), (0, -h / 2, 0), uv)
    extras = d.get('look', {}).get('extras', [])
    if 'shoulder_pads' in extras:
        pad = faces('pad', 'pad')
        part(static, (0.3, 0.12, 0.34), (-0.37, 1.52, 0), pad)
        part(static, (0.3, 0.12, 0.34), (0.37, 1.52, 0), pad)
    if 'belly' in extras:
        part(static, (0.42, 0.34, 0.14), (0, 0.98, 0.18), faces('belly', 'belly'))
    if 'mohawk' in extras:
        part(static, (0.1, 0.14, 0.44), (0, 2.03, -0.02), faces('hair', 'hair'))
    if 'cape' in extras:
        part(static, (0.6, 1.25, 0.04), (0, 0.95, -0.17), faces('cape', 'cape'))
    if 'crown' in extras:
        crown = faces('crown', 'crown')
        part(static, (0.56, 0.12, 0.56), (0, 2.03, 0), crown)
        for x, z in ((-0.22, -0.22), (0.22, -0.22), (-0.22, 0.22), (0.22, 0.22), (0, 0.22)):
            part(static, (0.09, 0.16, 0.09), (x, 2.15, z), crown)
    static.flattenStrong()
    _protos[kind] = dict(np=root, tex=tex, leg=leg, arm=arm)
    return _protos[kind]


class Enemy:
    def __init__(self, game, kind, wave, pos):
        d = ENEMIES[kind]
        self.game, self.kind, self.d = game, kind, d
        self.id = new_id()
        self.target = None          # the player (or ally) this enemy is chasing
        self.last_attacker = None   # who gets the kill
        self.retarget_t = 0
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
        self.ragdoll = None         # the limp body once it's dead (ragdoll.py)
        self.ragdoll_root = None
        self.death_push = None      # the push from the hit that killed it
        self.death_hit = 'body'
        self.stuck_t = 0
        self.detour = 0
        self.nav_t = 0.0
        self.progress_t = 0.0
        self.best_d = math.inf     # closest it has got to its target (in flow-field steps)
        self.no_progress = 0
        self.blocked = False      # True = a wall is in the way: follow the flow field
        self.smashing = None      # (barricade, x, z) it is breaking
        self.detour_side = 1
        self.last_pos = Vec3(pos)
        self.groan_t = 3 + random.random() * 8
        self.burn_dps = 0       # damage per second while burning
        self.burn_t = 0
        self.burn_tick = 0
        self.slow_mult = 1      # speed multiplier while frozen
        self.slow_t = 0
        self.build()

    # ── model ──────────────────────────────────────────────────────────────
    def build(self):
        """A copy of this zombie type's model (plain Panda3D nodes: fast to make, move and draw)."""
        pr = zombie_proto(self.kind, self.d)
        self.root = pr['np'].copyTo(self.game.world_root)
        self.body = self.root.find('body')
        self.head = self.body.find('head')
        self.leg_l, self.leg_r = self.body.find('leg_l'), self.body.find('leg_r')
        self.arm_l, self.arm_r = self.body.find('arm_l'), self.body.find('arm_r')
        self.tex, self.leg_uv, self.arm_uv = pr['tex'], pr['leg'], pr['arm']   # (the ragdoll needs these)
        self.root.setPos(self.position)

    def destroy(self):
        if self.ragdoll is not None:
            self.game.ragdolls.remove(self.ragdoll)
            self.ragdoll.destroy()
            self.ragdoll = None
        self.root.removeNode()

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
    def hurt(self, amount, headshot=False, knock=None, attacker=None):
        if self.dead:
            return
        g = self.game
        if attacker is not None or self.last_attacker is None:
            self.last_attacker = attacker or g.player
        if amount >= 0.01 and g.powerups.active('instakill') and not self.d.get('boss'):
            amount = max(amount, self.hp)          # Bonebreaker power-up
        self.hp -= amount
        if amount < 0.01:          # finishing blow from burning: no number, no flash
            if self.hp <= 0:
                self.dead = True
                self.hp = 0
                g.sounds.play('death', pitch=0.8 + random.random() * 0.4)
                g.on_enemy_killed(self, False, self.last_attacker)
            return
        self.flash = 0.1
        if knock is not None:
            self.kb += knock / max(1, self.scale * self.scale)
            self.death_push = knock
            self.death_hit = 'head' if headshot else 'body'
        top = Vec3(self.position.x, self.position.y + self.height + 0.2, self.position.z)
        g.effects.damage_number(self.head_pos() + Vec3(0, 0.4, 0) if headshot else top, amount, crit=headshot)
        g.effects.burst(self.head_pos() if headshot else self.chest_pos(), self.d['colors']['skin'],
                        8 if headshot else 4, speed=4, size=0.1)
        if self.hp <= 0:
            self.dead = True
            self.hp = 0
            g.sounds.play('death', pitch=0.8 + random.random() * 0.4)
            g.on_enemy_killed(self, headshot, self.last_attacker)

    def go_limp(self):
        """Turn into a ragdoll, pushed by whatever killed it."""
        from .ragdoll import Ragdoll
        k = self.death_push or Vec3(0, 0, 0)
        mass = max(1.0, self.scale ** 3)
        push = (k.x * 0.9 / mass, (0.8 + k.length() * 0.18) / mass, k.z * 0.9 / mass)
        self.ragdoll = Ragdoll(self, push, self.death_hit)
        self.game.ragdolls.add(self.ragdoll)
        self.root.setColorScale(1, 1, 1, 1)

    def ignite(self, dps, seconds):
        self.burn_dps = max(self.burn_dps, dps)
        self.burn_t = max(self.burn_t, seconds)

    def chill(self, mult, seconds):
        self.slow_mult = min(self.slow_mult, mult) if self.slow_t > 0 else mult
        self.slow_t = max(self.slow_t, seconds)

    def update_status(self, dt):
        g = self.game
        if self.burn_t > 0:
            self.burn_t -= dt
            self.burn_tick -= dt
            if random.random() < dt * 20:
                g.effects.burst(self.chest_pos() + Vec3((random.random() - 0.5) * 0.4 * self.scale, 0, 0),
                                random.choice(('#ff8c2a', '#ffcf3a', '#ff4a1a')), 1, speed=1.5, size=0.14, life=0.5, gravity=-6)
            if self.burn_tick <= 0:
                self.burn_tick = 0.25
                dmg = self.burn_dps * 0.25
                self.hp -= dmg
                if self.hp <= 0:
                    self.hurt(0.001)
            if self.burn_t <= 0:
                self.burn_dps = 0
        if self.slow_t > 0:
            self.slow_t -= dt
            if self.slow_t <= 0:
                self.slow_mult = 1

    def shoot(self, r):
        g = self.game
        start = self.head_pos()
        target = self.target.eye() - Vec3(0, 0.5, 0)
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
        if self.flash > 0:
            self.root.setColorScale(3, 3, 3, 1)
        elif self.slow_t > 0:
            self.root.setColorScale(0.6, 0.85, 1.6, 1)
        elif self.burn_t > 0:
            self.root.setColorScale(1.4, 0.8, 0.6, 1)
        else:
            self.root.setColorScale(1, 1, 1, 1)
        if not self.dead:
            self.update_status(dt)

        if self.dead:
            self.death_t += dt
            if self.ragdoll is None and RAGDOLLS[0] and self.rise <= 0.3:
                self.go_limp()
            if self.ragdoll is not None:
                self.ragdoll.step(dt)
                if self.death_t > CORPSE_TIME:
                    self.ragdoll.sink(dt * 0.5)                # into the ground
                return self.death_t < CORPSE_TIME + 2.5
            self.root.setP(min(90, self.death_t * 290))   # (ragdolls off: the old fall-over)
            self.position += self.kb * dt
            self.kb *= max(0, 1 - dt * 6)
            if self.death_t > 1.2:
                self.position.y -= dt * 1.5
            self.root.setPos(self.position)
            return self.death_t < 2.4

        self.retarget_t -= dt
        if self.target is None or self.retarget_t <= 0 or getattr(self.target, 'dead', False):
            self.target = g.nearest_target(self.position)
            self.retarget_t = 0.5 + random.random() * 0.5
        if self.target is None:
            self.root.setPos(self.position)
            return True
        p = self.target.position
        if self.rise > 0:
            self.rise -= dt
            self.position.y = -self.height * max(0, self.rise / 0.9)
            if random.random() < 0.3:
                g.effects.burst(Vec3(self.position.x, 0.1, self.position.z), '#6b4a2b', 1, speed=3, size=0.15)
            if self.rise <= 0:
                self.position.y = 0
            self.face(p)
            self.root.setPos(self.position)
            return True

        tx, tz = p.x - self.position.x, p.z - self.position.z
        dist = math.hypot(tx, tz)
        if dist > 1e-4:
            tx, tz = tx / dist, tz / dist
        mx, mz = tx, tz
        speed = self.speed * (self.slow_mult if self.slow_t > 0 else 1)

        r = self.d.get('ranged')
        if r:
            self.ranged_cd -= dt
            can_see = dist < r['range'] and g.world.line_of_sight(self.head_pos(), self.target.eye())
            if can_see:
                self.no_progress = 0        # happy shooting from where it is
            if can_see and dist > 6 and not self.d.get('boss'):
                side = 0.6 if math.sin(self.walk * 0.3) > 0 else -0.6
                mx, mz = -tz * side, tx * side
                speed *= 0.6
            if can_see and self.ranged_cd <= 0:
                self.ranged_cd = 1 / r['rate'] * (0.8 + random.random() * 0.4)
                self.shoot(r)

        self.nav_t -= dt
        if self.nav_t <= 0:                     # is the straight line to the target walkable?
            self.nav_t = 0.25 + random.random() * 0.2
            self.blocked = not g.world.walkable_line(self.position, p)
        if self.blocked and dist > 1.2:         # no: walk around walls and through doors instead
            way = g.enemies.flow.direction(self.position.x, self.position.z)
            if way is not None:
                mx, mz = way
                self.detour = 0
        self.smashing = None
        bars = getattr(g, 'barricades', None)
        if bars is not None and bars.list and dist > self.d['reach'] + self.target.radius:
            if self.blocked:                    # is the next step of the way a barricade? break it
                cell = g.enemies.flow.next_cell(self.position.x, self.position.z)
                b = bars.at_cell(cell) if cell else None
                if b is not None:
                    w = g.world
                    cx, cz = cell[0] - w.half + 0.5, cell[1] - w.half + 0.5
                    if math.hypot(cx - self.position.x, cz - self.position.z) < self.d['reach'] + 0.75:
                        self.smashing = (b, cx, cz)
                    else:
                        mx, mz = cx - self.position.x, cz - self.position.z
            if self.smashing is None:           # a turret right next to it gets smashed too
                b, bd = bars.nearest(self.position, self.d['reach'] + 0.4, kinds=('turret',))
                if b is not None:
                    self.smashing = (b, b['pos'].x, b['pos'].z)
            if self.smashing is not None:
                b, cx, cz = self.smashing
                mx = mz = 0.0
                self.detour = 0
                self.no_progress = 0
                self.face(Vec3(cx, 0, cz))

        if self.detour > 0:     # stuck: walk sideways for a moment
            self.detour -= dt
            s = self.detour_side
            mx, mz = -tz * s + tx * 0.3, tx * s + tz * 0.3

        # don't stand inside each other (only zombies in the grid cells around this one are checked)
        ex, ez = self.position.x, self.position.z
        grid = g.enemies.grid
        cx, cz = int(ex // SEP_CELL), int(ez // SEP_CELL)
        for gx in (cx - 1, cx, cx + 1):
            for gz in (cz - 1, cz, cz + 1):
                for o, ox, oz, orad in grid.get((gx, gz), ()):
                    if o is self:
                        continue
                    dx, dz = ex - ox, ez - oz
                    mn = self.radius + orad + 0.25
                    d2 = dx * dx + dz * dz
                    if 1e-6 < d2 < mn * mn:
                        d = math.sqrt(d2)
                        mx += dx / d * (mn - d) * 3
                        mz += dz / d * (mn - d) * 3

        reach = self.d['reach'] + self.target.radius
        if dist < reach * 0.8:
            speed = 0
        ml = math.hypot(mx, mz)
        if ml > 1:
            mx, mz = mx / ml, mz / ml

        self.position.x += (mx * speed + self.kb.x) * dt
        self.position.z += (mz * speed + self.kb.z) * dt
        self.kb *= max(0, 1 - dt * 8)
        self.position.y = 0
        # walls use a slim radius so even big zombies fit through doorways (they clip a little)
        self.position.x, self.position.z = g.world.collide(self.position, min(self.radius, 0.45))
        self.position.x, self.position.z = g.world.clamp(self.position.x, self.position.z, 0.3)

        # safety net: no progress towards the target for 10 s -> dig down and come up near it
        self.progress_t += dt
        if self.progress_t >= 1.0:
            self.progress_t = 0.0
            if dist > 80 and g.world.big:        # huge map: left far behind -> come back near the players
                self.resurface()
                return True
            here = g.enemies.flow.steps_at(self.position.x, self.position.z)
            if here is None:
                here = dist
            if dist < reach + 1.0 or here < self.best_d - 0.5:
                self.best_d = min(self.best_d, here)
                self.no_progress = 0
            else:
                self.no_progress += 1
                if self.no_progress >= 10:
                    self.resurface()

        self.stuck_t += dt
        if self.stuck_t > 0.6:
            moved = (self.last_pos - self.position).length()
            if speed > 0 and moved < self.speed * 0.15 and self.detour <= 0:
                self.detour = 0.8 + random.random() * 0.6
                self.detour_side = random.choice((1, -1))
            self.last_pos = Vec3(self.position)
            self.stuck_t = 0

        self.attack_cd -= dt
        if self.smashing is not None and self.attack_cd <= 0:
            self.attack_cd = 1 / self.d['attack_rate']
            self.attack_anim = 0.3
            g.barricades.hurt(self.smashing[0], self.damage, self)
        elif dist < reach and abs(p.y - self.position.y) < self.height * 0.8 + 0.6 and self.attack_cd <= 0:
            self.attack_cd = 1 / self.d['attack_rate']
            self.attack_anim = 0.3
            self.target.hurt(self.damage, self.position)

        self.groan_t -= dt
        if self.groan_t <= 0:
            self.groan_t = 6 + random.random() * 10
            if dist < 20:
                g.sounds.play('groan', volume=0.6, pitch=0.7 + random.random() * 0.6)

        self.face(Vec3(self.smashing[1], 0, self.smashing[2]) if self.smashing is not None else p)
        self.animate(dt, speed)
        self.root.setPos(self.position)
        return True

    def resurface(self):
        """Stuck somewhere: sink into the ground and climb out of a spawn point near the target."""
        g = self.game
        g.effects.burst(Vec3(self.position.x, 0.2, self.position.z), '#6b4a2b', 8, speed=3, size=0.2)
        t = self.target.position if self.target is not None else g.player.position
        self.position = g.world.random_spawn(t, min_dist=8)
        self.rise = 0.9
        self.position.y = -self.height
        self.best_d = math.inf
        self.no_progress = 0
        self.kb = Vec3(0, 0, 0)
        self.root.setPos(self.position)
        g.events.emit('enemy_resurfaced', enemy=self)

    def face(self, target):
        want = math.degrees(math.atan2(target.x - self.position.x, target.z - self.position.z))
        diff = (want - self.yaw + 180) % 360 - 180
        self.yaw += diff * 0.2
        self.root.setH(-self.yaw)

    def animate(self, dt, speed):
        self.walk += dt * (2 + speed * 2.2)
        swing = math.sin(self.walk) * 40 if speed > 0 else 0
        self.leg_l.setP(-swing)                  # (Ursina's rotation_x = -P)
        self.leg_r.setP(swing)
        pose = self.d['pose']
        arm = -85 if pose == 'reach' else 0
        arm_swing = swing * 1.3 if pose == 'run' else swing * 0.5 if pose == 'heavy' else math.sin(self.walk * 0.5) * 5
        if self.attack_anim > 0:
            self.attack_anim -= dt
            arm = -90 - math.sin(max(0, self.attack_anim) / 0.3 * math.pi) * 50
            arm_swing = 0
        self.arm_l.setP(-(arm + arm_swing))
        self.arm_r.setP(-(arm - arm_swing))


class FlowField:
    """How many steps every walkable cell is from the nearest target (player or ally),
    found with a breadth-first search. Zombies that can't walk straight to their target
    follow it downhill, which takes them around walls and through doorways."""
    INF = 1 << 30

    def __init__(self, world):
        self.world = world
        self.dist = None

    BREAK_COST = 12          # extra steps a barricade "costs": short detours win, long ones don't
    RANGE = 72               # huge maps: only search this far around the players (keeps it fast)

    def rebuild(self, targets, blockers=None):
        """blockers: {cell: barricade}. Zombies can go through those cells, but only by breaking them."""
        w, n, INF = self.world, self.world.n, self.INF
        heights = w.heights
        dist = [INF] * (n * n)
        queue = deque()
        cells = []
        for t in targets:
            gx, gz = w.to_grid(t.position.x, t.position.z)
            if w.inside(gx, gz) and dist[w.gidx(gx, gz)]:
                dist[w.gidx(gx, gz)] = 0
                queue.append((gx, gz))
                cells.append((gx, gz))
        # the search window: the whole map, or (on big maps) the area around the players
        if cells and n > self.RANGE * 2:
            x0 = max(0, min(c[0] for c in cells) - self.RANGE)
            x1 = min(n, max(c[0] for c in cells) + self.RANGE + 1)
            z0 = max(0, min(c[1] for c in cells) - self.RANGE)
            z1 = min(n, max(c[1] for c in cells) + self.RANGE + 1)
        else:
            x0, x1, z0, z1 = 0, n, 0, n
        self.window = (x0, x1, z0, z1)
        if blockers:
            self.dist = self._dijkstra(dist, queue, blockers)
            return
        while queue:
            gx, gz = queue.popleft()
            d = dist[gz * n + gx] + 1
            for nx, nz in ((gx + 1, gz), (gx - 1, gz), (gx, gz + 1), (gx, gz - 1)):
                if x0 <= nx < x1 and z0 <= nz < z1:
                    j = nz * n + nx
                    if dist[j] > d and heights[j] <= 0.05:
                        dist[j] = d
                        queue.append((nx, nz))
        self.dist = dist

    def _dijkstra(self, dist, starts, blockers):
        w, n = self.world, self.world.n
        heights = w.heights
        x0, x1, z0, z1 = self.window
        heap = [(0, gx, gz) for gx, gz in starts]
        heapq.heapify(heap)
        while heap:
            d, gx, gz = heapq.heappop(heap)
            if d > dist[gz * n + gx]:
                continue
            for nx, nz in ((gx + 1, gz), (gx - 1, gz), (gx, gz + 1), (gx, gz - 1)):
                if x0 <= nx < x1 and z0 <= nz < z1:
                    j = nz * n + nx
                    if heights[j] <= 0.05:
                        nd = d + 1
                    elif (nx, nz) in blockers:
                        nd = d + 1 + self.BREAK_COST
                    else:
                        continue
                    if nd < dist[j]:
                        dist[j] = nd
                        heapq.heappush(heap, (nd, nx, nz))
        return dist

    def next_cell(self, x, z):
        """The neighbouring cell a zombie at (x, z) should step into next, or None."""
        if self.dist is None:
            return None
        w, n = self.world, self.world.n
        gx, gz = w.to_grid(x, z)
        if not w.inside(gx, gz):
            return None
        best, cell = self.dist[gz * n + gx], None
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = gx + dx, gz + dz
            if 0 <= nx < n and 0 <= nz < n and self.dist[nz * n + nx] < best:
                best, cell = self.dist[nz * n + nx], (nx, nz)
        return cell

    def steps_at(self, x, z):
        """How many steps from (x, z) to the nearest target, or None if unknown / unreachable."""
        if self.dist is None:
            return None
        w = self.world
        gx, gz = w.to_grid(x, z)
        if not w.inside(gx, gz):
            return None
        best = min(self.dist[(gz + dz) * w.n + gx + dx] for dx in (-1, 0, 1) for dz in (-1, 0, 1)
                   if 0 <= gx + dx < w.n and 0 <= gz + dz < w.n)
        return None if best >= self.INF else best

    def direction(self, x, z):
        """Unit (dx, dz) towards the next cell on the way, or None."""
        if self.dist is None:
            return None
        w, n = self.world, self.world.n
        gx, gz = w.to_grid(x, z)
        if not w.inside(gx, gz):
            return None
        heights, dist = w.heights, self.dist
        best, bx, bz = dist[gz * n + gx], None, None
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nx, nz = gx + dx, gz + dz
            if not (0 <= nx < n and 0 <= nz < n):
                continue
            if dx and dz and (heights[gz * n + nx] > 0.05 or heights[nz * n + gx] > 0.05):
                continue                        # don't cut corners (or walls / barricades)
            dj = dist[nz * n + nx]
            if dj < best:
                best, bx, bz = dj, nx, nz
        if bx is None:
            return None
        cx, cz = bx - w.half + 0.5 - x, bz - w.half + 0.5 - z
        length = math.hypot(cx, cz) or 1
        return cx / length, cz / length


def _ray_dist2(o, d, p):
    """squared distance from point p to the ray o + t*d (d is unit)"""
    tx, ty, tz = p[0] - o[0], p[1] - o[1], p[2] - o[2]
    t = max(0.0, tx * d[0] + ty * d[1] + tz * d[2])
    x, y, z = tx - d[0] * t, ty - d[1] * t, tz - d[2] * t
    return x * x + y * y + z * z


class EnemyManager:
    def __init__(self, game):
        self.game = game
        self.list = []
        self.flow = FlowField(game.world)
        self.flow_t = 0.0
        self.grid = {}

    def spawn(self, kind, wave, pos):
        e = Enemy(self.game, kind, wave, pos)
        self.list.append(e)
        return e

    def alive(self):
        return (e for e in self.list if not e.dead)

    def alive_count(self):
        return sum(1 for e in self.list if not e.dead)

    def update(self, dt):
        g = self.game
        if self.flow.world is not g.world:
            self.flow = FlowField(g.world)
            self.flow_t = 0
        self.flow_t -= dt
        if self.flow_t <= 0 and self.list:
            self.flow_t = 0.4
            bar = getattr(g, 'barricades', None)
            self.flow.rebuild(g.targets(), bar.cells if bar is not None else None)
        grid = self.grid = {}                     # where everyone is, for keeping zombies apart
        for e in self.list:
            if e.dead or e.rise > 0:
                continue
            x, z = e.position.x, e.position.z
            grid.setdefault((int(x // SEP_CELL), int(z // SEP_CELL)), []).append((e, x, z, e.radius))
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
        self.game.ragdolls.clear()

    def shove_corpses(self, o, d, max_dist, force, at_end=None):
        """Bullets that pass a body knock it about (it's only cosmetic)."""
        for e in self.list:
            r = e.ragdoll
            if r is None:
                continue
            q = r.p[0]
            to = (q[0] - o[0], q[1] - o[1], q[2] - o[2])
            along = to[0] * d[0] + to[1] * d[1] + to[2] * d[2]
            if along < 0 or along > max_dist + 1:
                continue
            close = min(r.p, key=lambda pt: _ray_dist2(o, d, pt))
            if _ray_dist2(o, d, close) < (0.3 * e.scale) ** 2:
                r.push((d[0] * force, d[1] * force + 0.5, d[2] * force), close)
                self.game.effects.burst(Vec3(*close), e.d['colors']['skin'], 3, speed=3, size=0.08)
                return True
        return False

    def blast_corpses(self, pos, radius, force):
        for e in self.list:
            r = e.ragdoll
            if r is None:
                continue
            q = r.p[0]
            away = Vec3(q[0] - pos.x, q[1] - pos.y, q[2] - pos.z)
            dist = away.length()
            if dist < radius + 1:
                k = force * (1 - dist / (radius + 1))
                a = away.normalized() if dist > 0.01 else Vec3(0, 1, 0)
                r.push((a.x * k, abs(a.y) * k + k * 0.6, a.z * k))
