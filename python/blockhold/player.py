"""First-person movement, jumping and health."""
import math
import random
from ursina import Vec3, camera


class Player:
    radius = 0.35
    eye_height = 1.62

    def __init__(self, game):
        self.game = game
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
        self.ability_cd = 0.0

    def eye(self):
        return Vec3(self.position.x, self.position.y + self.eye_height, self.position.z)

    def forward(self):
        return camera.forward

    def look(self, dx, dy):
        self.yaw += dx
        self.pitch = max(-89, min(89, self.pitch + dy))

    def hurt(self, amount, source=None):
        g = self.game
        if self.dead or g.god_mode:
            return
        amount *= 1 - self.armor
        self.health -= amount
        g.ui.hurt(amount / self.max_health)
        g.sounds.play('hurt', pitch=0.9 + random.random() * 0.2)
        g.shake(min(0.25, amount / 60))
        if self.health <= 0:
            self.health = 0
            self.dead = True
            g.on_player_death()

    def heal(self, n):
        self.health = min(self.max_health, self.health + n)
        self.game.effects.damage_number(self.eye() + self.forward() * 1.5, n, color='#5dff7a')

    @property
    def move_speed(self):
        return 5.6 * self.speed_mult * (1.5 if self.buffs.get('adrenaline', 0) > 0 else 1)

    def update(self, dt, keys):
        world = self.game.world
        for k in self.buffs:
            self.buffs[k] = max(0, self.buffs[k] - dt)
        if self.ability_cd > 0:
            self.ability_cd -= dt
        if self.regen > 0 and self.health < self.max_health:
            self.health = min(self.max_health, self.health + self.regen * dt)

        fx = keys.get('d', 0) - keys.get('a', 0)
        fz = keys.get('w', 0) - keys.get('s', 0)
        length = math.hypot(fx, fz)
        if length:
            fx, fz = fx / length, fz / length
        yr = math.radians(self.yaw)
        sin, cos = math.sin(yr), math.cos(yr)
        wx = fz * sin + fx * cos
        wz = fz * cos - fx * sin
        sprint = 1.4 if keys.get('shift', 0) else 1
        speed = self.move_speed * sprint

        k = min(1, (14 if self.on_ground else 4) * dt)
        self.vel.x += (wx * speed - self.vel.x) * k
        self.vel.z += (wz * speed - self.vel.z) * k
        if keys.get('space', 0) and self.on_ground:
            self.vel.y = 7.2
            self.on_ground = False
        self.vel.y -= 22 * dt

        self.position.x += self.vel.x * dt
        self.position.z += self.vel.z * dt
        self.position.x, self.position.z = world.collide(self.position, self.radius)

        prev_y = self.position.y
        self.position.y += self.vel.y * dt
        floor = world.ground_at(self.position.x, self.position.z, self.radius, prev_y)
        if self.position.y <= floor:
            self.position.y = floor
            self.vel.y = 0
            self.on_ground = True
        else:
            self.on_ground = self.position.y - floor < 0.02

        moving = self.on_ground and length > 0
        if moving:
            self.bob += dt * speed * 1.8
        bob_y = abs(math.sin(self.bob)) * 0.06 if moving else 0
        self.recoil = max(0, self.recoil - dt * 6 * max(1.0, self.recoil))
        s = self.game.shake_amt * 0.3
        camera.position = (
            self.position.x + (random.random() - 0.5) * s,
            self.position.y + self.eye_height + bob_y + (random.random() - 0.5) * s,
            self.position.z + (random.random() - 0.5) * s,
        )
        camera.rotation = (-(self.pitch + self.recoil), self.yaw, 0)
        self.moving = moving
