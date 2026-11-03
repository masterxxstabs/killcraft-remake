"""Passive animals: deer, pigs and chickens (see data/animals.py).

They come from spawners placed in the map editor (random arenas get a few herds of
their own). Each one wanders around its spawner, stops to graze, and runs away from
players and zombies that get close, or from whoever hurt it. Shoot or hit one to
kill it for raw meat (and feathers / hide); a new one comes back to the spawner a
while later. Meat goes to the player who made the kill.
Events: animal_spawned, animal_hurt, animal_killed.
"""
import math
import random
from ursina import Vec3
from .data.animals import ANIMALS, ANIMAL_KINDS, RANDOM_HERDS, SPREAD, ZOMBIE_SCARE
from .data.items import ITEMS
from .lowpoly import LowPoly
from .net import new_id

_meshes = {}
VARIANTS = 3
EXTRA_DROPS = {'chicken': ('feather', 2, 4), 'deer': ('hide', 1, 1)}     # besides meat


def walkable(w, x, z):
    gx, gz = w.to_grid(x, z)
    return w.inside(gx, gz, 1) and w.heights[w.gidx(gx, gz)] == 0


def part_mesh(kind, part, variant=0):
    key = (kind, part, variant)
    if key not in _meshes:
        lp = LowPoly(seed=variant * 53 + len(kind) * 11 + len(part), variation=0.05)
        ANIMALS[kind][part](lp)
        _meshes[key] = lp.mesh()
    return _meshes[key]


class Animal:
    def __init__(self, game, kind, pos, home):
        d = ANIMALS[kind]
        self.game, self.kind, self.d = game, kind, d
        self.id = new_id()
        self.home = home                      # (position, spawner kind) it belongs to, or None
        self.position = Vec3(pos.x, 0, pos.z)
        self.yaw = random.random() * 360
        self.hp = float(d['hp'])
        self.state = 'idle'                   # idle, walk, graze, flee
        self.timer = random.uniform(0.5, 3.0)
        self.goal = None
        self.flee_from = None
        self.scared = 0.0                     # seconds left running after being hurt
        self.walk = random.random() * 6
        self.head_tilt = 0.0
        self.flash = 0.0
        self.dead = False
        self.speed = 0.0
        self.build()

    def build(self):
        d, v = self.d, random.randrange(VARIANTS)
        # plain Panda3D nodes (much cheaper than Ursina entities to move every frame)
        self.root = self.game.world_root.attachNewNode('animal')
        self.root.setPos(self.position)
        self.root.setH(-self.yaw)
        self.model = self.root.attachNewNode('model')
        part_mesh(self.kind, 'body', v).copyTo(self.model)
        self.head = self.model.attachNewNode('head')
        self.head.setPos(*d['head_at'])
        part_mesh(self.kind, 'head', v).copyTo(self.head)
        self.legs = []
        for hip in d['hips']:
            leg = self.model.attachNewNode('leg')
            leg.setPos(*hip)
            part_mesh(self.kind, 'leg', v).copyTo(leg)
            self.legs.append(leg)

    def destroy(self):
        self.root.removeNode()

    def centre(self):
        return Vec3(self.position.x, self.d['height'], self.position.z)

    # ── behaviour ────────────────────────────────────────────────────────────
    def threat(self):
        """The closest thing it's scared of right now, or None."""
        g = self.game
        best, best_d = None, None
        for p in g.players:
            if p.dead:
                continue
            dist = math.hypot(p.position.x - self.position.x, p.position.z - self.position.z)
            reach = self.d['shy'] * (0.55 if getattr(p, 'crouching', False) else 1)   # sneak up crouched
            if dist < reach and (best_d is None or dist < best_d):
                best, best_d = p.position, dist
        for e in g.enemies.list:
            if e.dead or e.rise > 0:
                continue
            dist = math.hypot(e.position.x - self.position.x, e.position.z - self.position.z)
            if dist < ZOMBIE_SCARE and (best_d is None or dist < best_d):
                best, best_d = e.position, dist
        return best

    def pick_goal(self):
        cx, cz = (self.home[0].x, self.home[0].z) if self.home else (self.position.x, self.position.z)
        for _ in range(8):
            a, r = random.random() * math.tau, random.random() * SPREAD
            x, z = cx + math.cos(a) * r, cz + math.sin(a) * r
            if walkable(self.game.world, x, z):
                return Vec3(x, 0, z)
        return Vec3(cx, 0, cz)

    def update(self, dt, check_threat):
        d = self.d
        self.flash = max(0.0, self.flash - dt)
        self.scared = max(0.0, self.scared - dt)
        if check_threat:
            t = self.threat()
            if t is not None:
                self.flee_from = Vec3(t)
                if self.state != 'flee':
                    self.state, self.timer = 'flee', random.uniform(2.5, 4.0)
        self.timer -= dt
        move = Vec3(0, 0, 0)
        want_speed = 0.0
        if self.state == 'flee':
            src = self.flee_from or self.position
            away = Vec3(self.position.x - src.x, 0, self.position.z - src.z)
            if away.length() < 0.01:
                away = Vec3(math.sin(math.radians(self.yaw)), 0, math.cos(math.radians(self.yaw)))
            move = away.normalized()
            if self.home and (self.position - self.home[0]).length() > SPREAD * 3:   # don't run off for ever
                move = (move + (self.home[0] - self.position).normalized() * 0.6).normalized()
            want_speed = d['run']
            if self.timer <= 0 and self.scared <= 0:
                self.state, self.timer, self.flee_from = 'idle', random.uniform(1, 3), None
        elif self.state == 'walk':
            to = Vec3(self.goal.x - self.position.x, 0, self.goal.z - self.position.z)
            if to.length() < 0.4 or self.timer <= 0:
                self.state, self.timer = random.choice(['idle', 'graze', 'graze']), random.uniform(2, 6)
            else:
                move = to.normalized()
                want_speed = d['walk']
        elif self.timer <= 0:                     # idle / grazing: now and then wander somewhere else
            if random.random() < 0.6:
                self.state, self.goal, self.timer = 'walk', self.pick_goal(), 8.0
            else:
                self.state, self.timer = random.choice(['idle', 'graze']), random.uniform(2, 5)
        self.speed += (want_speed - self.speed) * min(1, dt * 6)
        if move.length() > 0:
            before = Vec3(self.position)
            step = move * self.speed * dt
            self.position += step
            self.position.x, self.position.z = self.game.world.collide(self.position, d['radius'])
            moved = (self.position - before).length()
            if step.length() > 0.001 and moved < step.length() * 0.3:   # walked into a wall: try another way
                if self.state == 'walk':
                    self.goal = self.pick_goal()
                else:
                    side = Vec3(move.z, 0, -move.x) * random.choice((-1, 1))
                    self.position += side * self.speed * dt
                    self.position.x, self.position.z = self.game.world.collide(self.position, d['radius'])
            want = math.degrees(math.atan2(move.x, move.z))
            diff = (want - self.yaw + 180) % 360 - 180
            self.yaw += diff * min(1, dt * 8)
        # animation: legs swing while moving, head goes down to graze
        self.walk += dt * self.speed * (9 if self.kind == 'chicken' else 4.5)
        swing = math.sin(self.walk) * min(40, self.speed * 14) if self.speed > 0.1 else 0
        for i, leg in enumerate(self.legs):
            leg.setP(-swing if i in (0, 3) else swing)          # (Ursina's rotation_x = -P)
        tilt = 0.0
        if self.state == 'graze':
            tilt = dict(deer=85, pig=40).get(self.kind) or 50 + 25 * max(0.0, math.sin(self.game.time * 9))  # peck
        self.head_tilt += (tilt - self.head_tilt) * min(1, dt * 5)
        self.head.setP(-self.head_tilt)
        bob = abs(math.sin(self.walk)) * 0.04 * min(1, self.speed / 3) if self.speed > 0.1 else 0
        self.model.setY(bob)
        self.root.setPos(self.position)
        self.root.setH(-self.yaw)
        if self.flash > 0:
            self.root.setColorScale(2.2, 1.0, 1.0, 1)
        else:
            self.root.clearColorScale()


class Animals:
    def __init__(self, game):
        self.game = game
        self.list = []
        self.pending = []        # [seconds left, (position, spawner kind)] waiting to come back
        self.tick = 0

    def clear(self):
        for a in self.list:
            a.destroy()
        self.list = []
        self.pending = []

    def reset(self):
        """Fill a freshly loaded world: every spawner makes its animals; random arenas get some herds."""
        self.clear()
        w = self.game.world
        spawners = list(w.animal_spawns)
        if not spawners and w.random_arena:
            for _ in range(round(RANDOM_HERDS * max(1.0, w.area_scale() ** 0.5))):
                gx, gz = 4 + random.randrange(w.n - 8), 4 + random.randrange(w.n - 8)
                if w.free(gx, gz, 1):
                    spawners.append((Vec3(gx - w.half + 0.5, 0, gz - w.half + 0.5), 'random'))
            for s in spawners:
                w.animal_spawns.append(s)
        for spot in spawners:
            kind = self.kind_for(spot)
            for _ in range(ANIMALS[kind]['count']):
                self.spawn(kind, spot)

    @staticmethod
    def kind_for(spot):
        return spot[1] if spot[1] in ANIMALS else random.choice(ANIMAL_KINDS)

    def spawn(self, kind, spot):
        w = self.game.world
        pos = None
        for _ in range(10):
            a, r = random.random() * math.tau, random.random() * 2.5
            x, z = spot[0].x + math.cos(a) * r, spot[0].z + math.sin(a) * r
            if walkable(w, x, z):
                pos = Vec3(x, 0, z)
                break
        if pos is None:
            pos = Vec3(spot[0].x, 0, spot[0].z)
        a = Animal(self.game, kind, pos, spot)
        self.list.append(a)
        self.game.events.emit('animal_spawned', id=a.id, kind=kind, pos=pos)
        return a

    # ── getting hit ──────────────────────────────────────────────────────────
    def raycast(self, o, d, max_dist):
        """The closest animal a ray hits: (dist, animal) or None."""
        best = None
        for a in self.list:
            c = a.centre()
            to = c - o
            along = to.x * d[0] + to.y * d[1] + to.z * d[2]
            if along < 0 or along > max_dist + a.d['radius']:
                continue
            r = a.d['radius'] * 1.25
            perp2 = to.length_squared() - along * along
            if perp2 > r * r:
                continue
            dist = max(0.0, along - math.sqrt(max(0.0, r * r - perp2)))
            if dist <= max_dist and (best is None or dist < best[0]):
                best = (dist, a)
        return best

    def find(self, eye, fwd, reach):
        """The animal a melee swing would hit."""
        best, best_d = None, reach + 0.6
        for a in self.list:
            to = a.centre() - eye
            dist = max(0.0, to.length() - a.d['radius'])
            if dist < best_d and to.normalized().dot(fwd) > 0.55:
                best, best_d = a, dist
        return best

    def blast(self, pos, radius, damage, player=None):
        """Explosions hurt animals too."""
        for a in list(self.list):
            dist = (a.centre() - pos).length()
            if dist < radius:
                self.hurt(a, damage * (1 - dist / radius * 0.6), player, a.centre() - pos)

    def hurt(self, a, amount, player=None, push=None):
        g = self.game
        if a.dead:
            return
        a.hp -= amount
        a.flash = 0.12
        a.scared = 5.0
        src = player.position if player is not None else (a.position - push if push is not None else None)
        a.flee_from = Vec3(src) if src is not None else None
        a.state, a.timer = 'flee', 4.0
        g.effects.burst(a.centre(), '#a82a2a', 6, speed=3, size=0.07)
        g.sounds.play('hit', volume=0.6, pitch=a.d['sound'])
        g.events.emit('animal_hurt', id=a.id, kind=a.kind, player=player)
        if a.hp <= 0:
            self.kill(a, player)

    def kill(self, a, player=None):
        g = self.game
        a.dead = True
        self.list.remove(a)
        g.effects.burst(a.centre(), '#a82a2a', 14, speed=4, size=0.1)
        if a.kind == 'chicken':
            g.effects.burst(a.centre(), '#f2efe6', 12, speed=3, size=0.08, life=1.2)
        gained = {}
        if player is not None:
            n = random.randint(*a.d['meat'])
            gained['raw_meat'] = n
            extra = EXTRA_DROPS.get(a.kind)
            if extra:
                gained[extra[0]] = random.randint(extra[1], extra[2])
            for i, (item, amt) in enumerate(gained.items()):
                left = player.inventory.add(item, amt)
                if left and getattr(g, 'drops', None) is not None:      # backpack full: it lands on the ground
                    g.drops.spawn(dict(item=dict(uid=new_id(), id=item, n=left, x=0, y=0, rot=False)),
                                  a.position)
                if player.is_local:
                    g.effects.damage_number(a.centre() + Vec3(0, 0.8 + i * 0.3, 0), amt,
                                            color=ITEMS[item]['colour'], label=f"+{amt} {ITEMS[item]['name']}")
        g.events.emit('animal_killed', id=a.id, kind=a.kind, player=player, gained=gained)
        a.destroy()
        if a.home is not None:
            self.pending.append([random.uniform(*a.d['respawn']), a.home, a.kind])

    # ── per frame ────────────────────────────────────────────────────────────
    def update(self, dt):
        self.tick += 1
        for i, a in enumerate(self.list):
            a.update(dt, (i + self.tick) % 6 == 0)          # look around every few frames, not every frame
        for p in list(self.pending):
            p[0] -= dt
            if p[0] <= 0:
                self.pending.remove(p)
                spot = p[1]
                near = any((pl.position - spot[0]).length() < 10 for pl in self.game.players)
                if near:                                    # don't pop up in front of someone
                    self.pending.append([8.0, spot, p[2]])
                else:
                    self.spawn(p[2] if spot[1] not in ANIMALS else spot[1], spot)
