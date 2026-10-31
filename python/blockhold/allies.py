"""Friendly survivors: hired in the shop, they follow their boss and shoot zombies.

Allies are "targets" like players (zombies attack them) and get kill credit for
their owner. When their health runs out they go down; a player can revive them
by holding E nearby, and everyone gets back up when the wave ends.
"""
import math
import random
from panda3d.core import Point3
from ursina import Entity, Text, Vec3, application, color as ucolor, destroy
from .data.allies import ALLY_TYPES
from .data.gun_models import MODELS
from .gunsmith import Smith
from .net import new_id
from .render import block, col, node
from .textures import zombie_skin


class Ally:
    radius = 0.35

    def __init__(self, game, kind, owner, pos, slot=0):
        d = ALLY_TYPES[kind]
        self.game, self.kind, self.d, self.owner, self.slot = game, kind, d, owner, slot
        self.id = new_id()
        self.name = d['name']
        self.max_hp = d['hp']
        self.hp = float(self.max_hp)
        self.position = Vec3(pos)
        self.yaw = 0.0
        self.downed = False
        self.revive_progress = 0.0
        self.cooldown = 0.0
        self.target = None
        self.retarget = 0.0
        self.walk = random.random() * 6
        self.flash = 0.0
        self.kills = 0
        self.build()

    @property
    def dead(self):
        """Zombies (and other code) treat a downed ally as out of the fight."""
        return self.downed

    def eye(self):
        return Vec3(self.position.x, self.position.y + 1.6, self.position.z)

    # ── model ────────────────────────────────────────────────────────────────
    def build(self):
        skin = zombie_skin('ally_' + self.kind, self.d['colors'], self.d['look'])
        tex = skin.texture
        r = skin.rect

        def faces(front, side, back=None, top=None, bottom=None):
            return {'north': r(front), 'south': r(back or front), 'east': r(side), 'west': r(side),
                    'top': r(top or side), 'bottom': r(bottom or side)}

        def part(parent, size, center, uv):
            return block(parent, size=size, center=center, texture=tex, uv_rects=uv)

        self.root = node(self.game.world_root)
        self.body = node(self.root)
        part(self.body, (0.5, 0.72, 0.28), (0, 1.11, 0), faces('torso_front', 'torso_side', 'torso_back', 'torso_top', 'torso_bottom'))
        part(self.body, (0.5, 0.5, 0.5), (0, 1.72, 0), faces('head_front', 'head_side', 'head_back', 'head_top', 'head_bottom'))
        leg = faces('leg_side', 'leg_side', 'leg_side', 'leg_top', 'leg_bottom')
        arm = faces('arm_side', 'arm_side', 'arm_side', 'arm_top', 'arm_bottom')
        self.legs = [self._limb(0.24, 0.75, x, 0.75, leg, part) for x in (-0.13, 0.13)]
        self.arms = [self._limb(0.2, 0.72, x, 1.44, arm, part) for x in (-0.36, 0.36)]
        look = self.d['look']
        if look.get('helmet'):
            block(self.body, size=(0.58, 0.2, 0.58), center=(0, 2.02, 0), color=look['helmet'])
            block(self.body, size=(0.6, 0.05, 0.64), center=(0, 1.93, 0.02), color=look['helmet'])
        if look.get('cross'):
            for z in (0.145, -0.145):
                block(self.body, size=(0.24, 0.07, 0.01), center=(0, 1.2, z), color='#d93a3a')
                block(self.body, size=(0.07, 0.24, 0.01), center=(0, 1.2, z), color='#d93a3a')
        # the gun, held in front at chest height
        gun_id = self.d['gun']
        self.muzzle_local = Vec3(0, 0, 0.5)
        if gun_id in MODELS:
            s = Smith(seed=self.id)
            MODELS[gun_id](s)
            self.gun = node(self.body, position=(0.16, 1.28, 0.32))
            node(self.gun, model=s.build())
            m = s.mounts.get('muzzle', (0, 0, 0.5))
            self.muzzle_local = Vec3(*m)
        else:
            self.gun = block(self.body, size=(0.08, 0.1, 0.6), center=(0.16, 1.28, 0.5), color='#26282d')
        for a in self.arms:
            a.rotation_x = -80
        self.arms[0].rotation_y = 25
        # name tag + health bar (always face the camera)
        self.tag = Entity(parent=self.root, y=2.45, billboard=True)
        Text(self.name, parent=self.tag, scale=7, origin=(0, 0), color=col('#f5f4f2'), y=0.12)
        Entity(parent=self.tag, model='quad', scale=(0.7, 0.07), color=col('#12121c'))
        self.hp_bar = Entity(parent=self.tag, model='quad', origin=(-0.5, 0), x=-0.34, z=-0.01, scale=(0.68, 0.045),
                             color=col('#2e9e6a'))
        self.root.position = self.position

    def _limb(self, w, h, x, y, uv, part):
        pivot = node(self.body, position=(x, y, 0))
        part(pivot, (w, h, w), (0, -h / 2, 0), uv)
        return pivot

    def destroy(self):
        destroy(self.root)

    # ── health ───────────────────────────────────────────────────────────────
    def hurt(self, amount, source=None):
        if self.downed:
            return
        self.hp -= amount
        self.flash = 0.12
        if self.hp <= 0:
            self.hp = 0
            self.downed = True
            self.revive_progress = 0
            self.target = None
            self.body.rotation_x = -80
            self.body.y = 0.25
            self.game.events.emit('ally_downed', ally=self)
            self.game.ui.kill_feed(f'{self.name} is down! Hold E near them')

    def revive(self, frac=0.5):
        if not self.downed:
            return
        self.downed = False
        self.hp = self.max_hp * frac
        self.body.rotation_x = 0
        self.body.y = 0
        self.game.events.emit('ally_revived', ally=self)

    # ── AI ───────────────────────────────────────────────────────────────────
    def update(self, dt):
        g = self.game
        self.flash = max(0, self.flash - dt)
        if self.flash > 0:
            self.root.setColorScale(2.5, 1.2, 1.2, 1)
        elif self.downed:
            k = 0.6 + 0.3 * math.sin(g.time * 6)
            self.root.setColorScale(1, k, k, 1)
        else:
            self.root.setColorScale(1, 1, 1, 1)
        self.hp_bar.scale_x = max(0.001, 0.68 * self.hp / self.max_hp)
        self.hp_bar.color = col('#2e9e6a' if self.hp > self.max_hp * 0.35 else '#d64541')
        if self.downed:
            return

        o = self.owner
        oy = math.radians(o.yaw)
        back = Vec3(-math.sin(oy), 0, -math.cos(oy))
        right = Vec3(math.cos(oy), 0, -math.sin(oy))
        goal = o.position + back * 2.4 + right * ((self.slot - 1) * 1.8)
        to_goal = Vec3(goal.x - self.position.x, 0, goal.z - self.position.z)
        dist = to_goal.length()
        if dist > 30:                                  # badly lost: catch up
            self.position = Vec3(o.position.x + back.x * 2, 0, o.position.z + back.z * 2)
            dist = 0
        move = Vec3(0, 0, 0)
        if dist > 1.0:
            move = to_goal.normalized() * min(1, dist / 3)
        for e in g.enemies.list:                        # back away from zombies that get too close
            if e.dead or e.rise > 0:
                continue
            away = Vec3(self.position.x - e.position.x, 0, self.position.z - e.position.z)
            dd = away.length()
            if 0.01 < dd < 2.6 + e.radius:
                move += away.normalized() * (2.6 + e.radius - dd) * 0.8
        # stay out of the boss's way: not too close, and not in front of their gun
        to_me = Vec3(self.position.x - o.position.x, 0, self.position.z - o.position.z)
        dme = to_me.length()
        if 0.01 < dme < 2.0:
            move += to_me.normalized() * (2.0 - dme)
        look = Vec3(math.sin(oy), 0, math.cos(oy))
        if 0.01 < dme < 9 and to_me.normalized().dot(look) > 0.8:
            side = Vec3(look.z, 0, -look.x)
            move += side * (1 if side.dot(to_me) >= 0 else -1) * 1.2
        for other in g.allies:                          # and give each other room
            if other is self:
                continue
            away = Vec3(self.position.x - other.position.x, 0, self.position.z - other.position.z)
            dd = away.length()
            if 0.01 < dd < 1.0:
                move += away.normalized() * (1.0 - dd)
        speed = self.d['speed'] * (1.5 if dist > 7 else 1)
        if move.length() > 1:
            move = move.normalized()
        self.position += move * speed * dt
        self.position.y = 0
        self.position.x, self.position.z = g.world.collide(self.position, self.radius)

        if self.d.get('heal') and (o.position - self.position).length() < 6 and not o.dead:
            o.health = min(o.max_health, o.health + self.d['heal'] * dt)

        self.retarget -= dt
        if self.retarget <= 0:
            self.retarget = 0.3
            self.target = self.pick_target()
        self.cooldown -= dt
        if self.target is not None:
            t = self.target.chest_pos()
            self.face(t.x, t.z, dt)
            if self.cooldown <= 0 and not self.target.dead:
                self.shoot(self.target)
        elif move.length() > 0.1:
            self.face(self.position.x + move.x, self.position.z + move.z, dt)
        self.walk += dt * move.length() * speed * 2.2
        swing = math.sin(self.walk) * 35 if move.length() > 0.1 else 0
        self.legs[0].rotation_x, self.legs[1].rotation_x = swing, -swing
        self.root.position = self.position

    def face(self, x, z, dt):
        want = math.degrees(math.atan2(x - self.position.x, z - self.position.z))
        diff = (want - self.yaw + 180) % 360 - 180
        self.yaw += diff * min(1, dt * 10)
        self.root.rotation_y = self.yaw

    def pick_target(self):
        g = self.game
        best, best_d = None, self.d['range']
        eye = self.eye()
        for e in g.enemies.alive():
            if e.rise > 0.3:
                continue
            d = (e.position - self.position).length()
            if d < best_d and g.world.line_of_sight(eye, e.chest_pos()):
                best, best_d = e, d
        return best

    def muzzle_world(self):
        render = application.base.render
        p = render.getRelativePoint(self.gun, Point3(*self.muzzle_local))
        return Vec3(p.x, p.y, p.z)

    def shoot(self, e):
        g = self.game
        d = self.d
        self.cooldown = 1 / d['rate'] * (0.85 + random.random() * 0.3)
        eye = self.eye()
        aim = (e.head_pos() if random.random() < 0.2 else e.chest_pos()) - eye
        aim = aim.normalized()
        s = d['spread']
        aim = Vec3(aim.x + (random.random() - 0.5) * 2 * s, aim.y + (random.random() - 0.5) * 2 * s,
                   aim.z + (random.random() - 0.5) * 2 * s).normalized()
        wall = g.world.raycast(eye, aim, d['range'])
        end = eye + aim * wall
        hits = g.enemies.raycast(eye, aim, wall)
        if hits:
            dist, enemy, head = hits[0]
            end = eye + aim * dist
            wave_bonus = 1 + 0.08 * max(0, g.wave_number - 1)
            enemy.hurt(d['damage'] * wave_bonus * (2 if head else 1), head, Vec3(aim.x, 0, aim.z) * 1.2, attacker=self)
        g.effects.tracer(self.muzzle_world(), end, '#fff2a8', 0.02, 0.06)
        g.sounds.play('shoot_' + d['sound'], volume=0.45, pitch=0.95 + random.random() * 0.1)
