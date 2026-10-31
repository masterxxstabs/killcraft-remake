"""Coins and health cubes that enemies drop."""
import math
import random
from ursina import Vec3
from .render import block, col


class Pickups:
    def __init__(self, game):
        self.game = game
        self.list = []
        self.pool = []
        for _ in range(140):
            self.pool.append(block(game.world_root, color='#ffffff', enabled=False))

    def drop(self, pos, kind, value):
        if not self.pool:
            # out of pickup cubes: give the oldest one to the player right away
            self._collect(self.list[0])
        e = self.pool.pop()
        e.enabled = True
        e.color = col('#f2c230' if kind == 'coin' else '#ff3355')
        e.scale = 0.22 + min(0.2, value / 100) if kind == 'coin' else 0.35
        e.position = Vec3(pos.x, pos.y + 0.8, pos.z)
        vel = Vec3((random.random() - 0.5) * 4, 4 + random.random() * 2, (random.random() - 0.5) * 4)
        self.list.append(dict(e=e, kind=kind, value=value, vel=vel, life=30, t=random.random() * 6))

    def drop_coins(self, pos, total):
        pieces = min(6, max(1, round(total / 6)))
        left = total
        for i in range(pieces):
            v = left if i == pieces - 1 else round(total / pieces)
            left -= v
            if v > 0:
                self.drop(pos, 'coin', v)

    def _collect(self, p):
        g = self.game
        if p['kind'] == 'coin':
            g.coins += p['value']
            g.sounds.play('coin', volume=0.6)
        else:
            g.player.heal(p['value'])
            g.sounds.play('heal')
        self._release(p)

    def _release(self, p):
        p['e'].enabled = False
        self.pool.append(p['e'])
        self.list.remove(p)

    def update(self, dt):
        g, pl = self.game, self.game.player
        target = Vec3(pl.position.x, pl.position.y + 0.9, pl.position.z)
        for p in list(self.list):
            e = p['e']
            p['life'] -= dt
            p['t'] += dt
            d = (e.position - target).length()
            # between waves, everything left on the ground flies to you
            magnet = 999 if g.phase == 'intermission' else (pl.magnet if p['kind'] == 'coin' else 2)
            if d < magnet:
                pull = (target - e.position).normalized() * max(14 * (1.2 - d / magnet), 10)
                p['vel'] = p['vel'] + (pull - p['vel']) * min(1, dt * 8)
            else:
                p['vel'].y -= 20 * dt
                p['vel'].x *= 1 - dt * 2
                p['vel'].z *= 1 - dt * 2
            e.position += p['vel'] * dt
            floor = g.world.ground_at(e.x, e.z, 0.1, e.y) + 0.3
            if e.y < floor and d >= magnet:
                e.y = floor
                p['vel'].y = abs(p['vel'].y) * 0.3
            e.rotation_y += dt * 170
            e.rotation_x = math.sin(p['t'] * 2) * 17
            if d < 0.9:
                self._collect(p)
            elif p['life'] <= 0:
                self._release(p)
            else:
                e.visible = p['life'] > 4 or int(p['life'] * 6) % 2 == 0

    def clear(self):
        for p in list(self.list):
            self._release(p)
