"""First-person movement (walk, sprint, jump, crouch, slide, mantle), health and
each player's own economy (coins, score, upgrades).

Movement only reads a PlayerInput, so remote players can be driven the same way.
"""
import math
import random
from ursina import Vec3, camera
from .net import PlayerInput, new_id

STAND_EYE, CROUCH_EYE, SLIDE_EYE, DOWNED_EYE = 1.62, 1.08, 0.92, 0.55
BLEED_OUT = 25          # seconds a downed player has before they die
REVIVE_TIME = 3.0       # seconds an ally needs to get a downed player up
GRAVITY = 22
JUMP_SPEED = 7.2


class Player:
    radius = 0.35

    def __init__(self, game, name='Player', is_local=True):
        self.game = game
        self.id = new_id()
        self.name = name
        self.is_local = is_local
        self.reset()

    def reset(self):
        self.position = Vec3(0, 0, 0)
        self.vel = Vec3(0, 0, 0)
        self.yaw = 0.0          # degrees, 0 = looking +z
        self.pitch = 0.0        # degrees, positive = looking up
        self.recoil = 0.0
        self.on_ground = True
        self.moving = False
        self.bob = 0.0
        self.eye_height = STAND_EYE
        self.crouching = False
        self.slide_t = 0.0
        self.slide_cd = 0.0
        self.mantle = None       # (start, end, t, duration) while climbing
        self.land_dip = 0.0
        self.step_t = 0.0
        self.max_health = 100
        self.health = 100.0
        self.damage_mult = 1.0
        self.speed_mult = 1.0
        self.regen = 0.0
        self.reload_mult = 1.0
        self.fire_rate_mult = 1.0
        self.armor = 0.0
        self.magnet = 3.0
        self.buffs = {}
        self.dead = False
        self.downed = False      # on the ground, waiting for an ally to revive them
        self.bleed = 0.0
        self.revive_progress = 0.0
        self.ability_cd = 0.0
        # each player's own economy (shared screens show the local player's)
        self.coins = 0
        self.score = 0
        self.kills = 0
        self.upgrade_levels = {}

    def eye(self):
        return Vec3(self.position.x, self.position.y + self.eye_height, self.position.z)

    def forward(self):
        yr, pr = math.radians(self.yaw), math.radians(self.pitch)
        return Vec3(math.sin(yr) * math.cos(pr), math.sin(pr), math.cos(yr) * math.cos(pr))

    def look(self, dx, dy):
        self.yaw += dx
        self.pitch = max(-89, min(89, self.pitch + dy))

    def hurt(self, amount, source=None):
        g = self.game
        if self.dead or self.downed or g.god_mode:
            return
        amount *= 1 - self.armor
        self.health -= amount
        g.events.emit('player_hurt', player=self, amount=amount)
        if self.is_local:
            g.ui.hurt(amount / self.max_health)
            g.sounds.play('hurt', pitch=0.9 + random.random() * 0.2)
            g.shake(min(0.25, amount / 60))
        if self.health <= 0:
            self.health = 0
            if g.can_go_down(self):
                self.go_down()
            else:
                self.die()

    def go_down(self):
        """Out of health, but an ally can still get this player back up."""
        g = self.game
        self.downed = True
        self.bleed = BLEED_OUT
        self.revive_progress = 0.0
        self.slide_t = 0
        self.mantle = None
        g.events.emit('player_downed', player=self)
        if self.is_local:
            g.ui.banner('YOU ARE DOWN', '#d64541', 3, 'Hold on, an ally is coming to get you up')
            g.sounds.play('hurt', pitch=0.6)

    def revive(self, frac=0.4):
        if not self.downed:
            return
        self.downed = False
        self.health = self.max_health * frac
        self.revive_progress = 0.0
        self.game.events.emit('player_revived', player=self)
        if self.is_local:
            self.game.sounds.play('heal')

    def die(self):
        g = self.game
        self.downed = False
        self.dead = True
        g.events.emit('player_died', player=self)
        g.on_player_death(self)

    def heal(self, n):
        if self.downed or self.dead:
            return
        self.health = min(self.max_health, self.health + n)
        if self.is_local:
            self.game.effects.damage_number(self.eye() + self.forward() * 1.5, n, color='#5dff7a')

    @property
    def move_speed(self):
        weapons = getattr(self.game, 'weapons', None)
        held = weapons.d.get('move_mult', 1) if weapons and weapons.held else 1
        return 5.6 * self.speed_mult * held * (1.5 if self.buffs.get('adrenaline', 0) > 0 else 1)

    @property
    def sliding(self):
        return self.slide_t > 0

    # ── movement ─────────────────────────────────────────────────────────────
    def update(self, dt, inp=None):
        inp = inp or PlayerInput()
        world = self.game.world
        for k in self.buffs:
            self.buffs[k] = max(0, self.buffs[k] - dt)
        if self.ability_cd > 0:
            self.ability_cd -= dt
        if self.regen > 0 and self.health < self.max_health and not self.downed:
            self.health = min(self.max_health, self.health + self.regen * dt)
        self.slide_cd = max(0, self.slide_cd - dt)
        self.land_dip = max(0, self.land_dip - dt * 3)

        if self.mantle:
            self.update_mantle(dt)
            return
        if self.downed:
            self.crawl(dt, inp)
            return

        fx, fz = inp.move_x, inp.move_z
        length = math.hypot(fx, fz)
        if length > 1:
            fx, fz = fx / length, fz / length
        yr = math.radians(self.yaw)
        sin, cos = math.sin(yr), math.cos(yr)
        wx = fz * sin + fx * cos
        wz = fz * cos - fx * sin
        sprinting = inp.sprint and fz > 0 and not inp.crouch
        flat_speed = math.hypot(self.vel.x, self.vel.z)

        # slide: crouch while sprinting fast
        if inp.crouch_pressed and self.on_ground and flat_speed > self.move_speed * 1.15 and self.slide_cd <= 0:
            boost = max(flat_speed * 1.35, 9.5)
            d = Vec3(self.vel.x, 0, self.vel.z).normalized()
            self.vel.x, self.vel.z = d.x * boost, d.z * boost
            self.slide_t = 0.8
            self.game.events.emit('player_slide', player=self)
            if self.is_local:
                self.game.sounds.play('slide')
        if self.sliding:
            self.slide_t -= dt
            if not inp.crouch and self.slide_t < 0.6:      # let go of crouch to stop early
                self.slide_t = 0
            friction = 1.6 if self.on_ground else 0.3
            self.vel.x *= max(0, 1 - friction * dt)
            self.vel.z *= max(0, 1 - friction * dt)
            self.vel.x += wx * 3 * dt                         # a little steering
            self.vel.z += wz * 3 * dt
            if self.slide_t <= 0:
                self.slide_cd = 0.35
        else:
            self.crouching = inp.crouch and self.on_ground
            speed = self.move_speed * (1.4 if sprinting else 1) * (0.55 if self.crouching else 1)
            k = min(1, (14 if self.on_ground else 4) * dt)
            self.vel.x += (wx * speed - self.vel.x) * k
            self.vel.z += (wz * speed - self.vel.z) * k

        # jump, or mantle onto a ledge in front of us
        want_up = inp.jump_pressed or (not self.on_ground and inp.jump and fz > 0)
        if want_up and fz > 0 and self.try_mantle(wx, wz, sprinting or inp.jump_pressed):
            return
        if inp.jump_pressed and self.on_ground:
            self.vel.y = JUMP_SPEED
            self.on_ground = False
            if self.sliding:                                  # slide-jump keeps the speed
                self.slide_t = 0
                self.slide_cd = 0.35
        elif sprinting and self.on_ground and fz > 0 and self.try_vault(wx, wz):
            return
        self.vel.y -= GRAVITY * dt

        self.position.x += self.vel.x * dt
        self.position.z += self.vel.z * dt
        self.position.x, self.position.z = world.collide(self.position, self.radius)

        prev_y = self.position.y
        self.position.y += self.vel.y * dt
        floor = world.ground_at(self.position.x, self.position.z, self.radius, prev_y)
        if self.position.y <= floor:
            if not self.on_ground and self.vel.y < -9:
                self.land_dip = min(0.25, -self.vel.y / 60)
                if self.is_local:
                    self.game.sounds.play('land', volume=min(1, -self.vel.y / 16))
            self.position.y = floor
            self.vel.y = 0
            self.on_ground = True
        else:
            self.on_ground = self.position.y - floor < 0.02

        target_eye = SLIDE_EYE if self.sliding else CROUCH_EYE if self.crouching else STAND_EYE
        self.eye_height += (target_eye - self.eye_height) * min(1, dt * 12)

        self.moving = self.on_ground and length > 0 and not self.sliding
        if self.moving:
            self.bob += dt * math.hypot(self.vel.x, self.vel.z) * 1.8
            self.step_t -= dt * math.hypot(self.vel.x, self.vel.z)
            if self.step_t <= 0:
                self.step_t = 2.1
                if self.is_local and not self.crouching:
                    self.game.sounds.play('step', volume=0.35, pitch=0.85 + random.random() * 0.3)

    def ledge(self, wx, wz, reach):
        """Height of a ledge right in front of us, or None."""
        w = self.game.world
        d = math.hypot(wx, wz)
        if d < 1e-3:
            return None
        wx, wz = wx / d, wz / d
        px = self.position.x + wx * (self.radius + reach)
        pz = self.position.z + wz * (self.radius + reach)
        h = w.height_at(px, pz)
        rise = h - self.position.y
        if h <= 0 or rise < 0.4:
            return None
        return h, (px + wx * 0.25, pz + wz * 0.25)

    def try_mantle(self, wx, wz, allowed):
        if not allowed:
            return False
        found = self.ledge(wx, wz, 0.35)
        if not found:
            return False
        h, (tx, tz) = found
        rise = h - self.position.y
        if rise > 2.15 or rise < 0.9:              # small steps are just jumped
            return False
        if self.game.world.blocked(tx, tz, self.radius * 0.8, h):
            return False
        self.start_climb(Vec3(tx, h, tz), 0.22 + rise * 0.14)
        return True

    def try_vault(self, wx, wz):
        """While sprinting, hop over waist-high obstacles without stopping."""
        found = self.ledge(wx, wz, 0.25)
        if not found:
            return False
        h, (tx, tz) = found
        rise = h - self.position.y
        if not 0.4 <= rise <= 1.1 or self.game.world.blocked(tx, tz, self.radius * 0.8, h):
            return False
        self.start_climb(Vec3(tx, h, tz), 0.2)
        return True

    def start_climb(self, end, duration):
        self.mantle = (Vec3(self.position), end, 0.0, duration, Vec3(self.vel.x, 0, self.vel.z))
        self.slide_t = 0
        self.game.events.emit('player_mantle', player=self)
        if self.is_local:
            self.game.sounds.play('mantle')

    def update_mantle(self, dt):
        start, end, t, dur, vel = self.mantle
        t = min(1, t + dt / dur)
        e = t * t * (3 - 2 * t)
        lift = math.sin(t * math.pi) * 0.25
        self.position = Vec3(start.x + (end.x - start.x) * e, start.y + (end.y - start.y) * min(1, e * 1.4) + lift,
                             start.z + (end.z - start.z) * e)
        self.eye_height += (STAND_EYE - 0.2 - self.eye_height) * min(1, dt * 10)
        if t >= 1:
            self.position = Vec3(end)
            self.vel = Vec3(vel.x * 0.6, 0, vel.z * 0.6)
            self.on_ground = True
            self.mantle = None
        else:
            self.mantle = (start, end, t, dur, vel)

    # ── camera (local player only) ───────────────────────────────────────────
    def crawl(self, dt, inp):
        """Downed: drag yourself along the ground while the bleed-out timer runs."""
        g = self.game
        self.bleed -= dt
        if self.bleed <= 0 or not g.can_go_down(self):      # time's up, or nobody left to help
            self.die()
            return
        yr = math.radians(self.yaw)
        fx, fz = inp.move_x, inp.move_z
        length = math.hypot(fx, fz)
        if length > 1:
            fx, fz = fx / length, fz / length
        wx = fz * math.sin(yr) + fx * math.cos(yr)
        wz = fz * math.cos(yr) - fx * math.sin(yr)
        self.vel = Vec3(wx * 1.3, 0, wz * 1.3)
        self.position += self.vel * dt
        self.position.x, self.position.z = g.world.collide(self.position, self.radius)
        self.position.y = g.world.ground_at(self.position.x, self.position.z, self.radius, self.position.y)
        self.moving = False
        self.eye_height += (DOWNED_EYE - self.eye_height) * min(1, dt * 6)

    def apply_camera(self, dt):
        bob_y = abs(math.sin(self.bob)) * 0.06 if self.moving else 0
        self.recoil = max(0, self.recoil - dt * 6 * max(1.0, self.recoil))
        s = self.game.shake_amt * 0.3
        camera.position = (
            self.position.x + (random.random() - 0.5) * s,
            self.position.y + self.eye_height + bob_y - self.land_dip + (random.random() - 0.5) * s,
            self.position.z + (random.random() - 0.5) * s,
        )
        roll = 14 if self.downed else 6 if self.sliding else (-3 if self.mantle else 0)
        dip = 8 if self.mantle else 0
        camera.rotation = (-(self.pitch + self.recoil) + dip, self.yaw, roll)
