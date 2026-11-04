"""Rockets fired by the player and goo spat by enemies."""
import random
from ursina import Vec3
from .render import block, destroy
from .net import new_id


class Projectiles:
    def __init__(self, game):
        self.game = game
        self.list = []

    def spawn_rocket(self, pos, vel, radius, damage, knockback, owner=None):
        e = block(self.game.world_root, size=(0.15, 0.15, 0.45), color='#ff3b3b', position=pos)
        self.list.append(dict(id=new_id(), e=e, vel=vel, owner='player', shooter=owner or self.game.player, radius=radius,
                              damage=damage, knockback=knockback, life=4, gravity=3, trail='#ffc04a'))

    def spawn_enemy(self, pos, vel, damage, color):
        e = block(self.game.world_root, size=(0.3, 0.3, 0.3), color=color, position=pos)
        self.list.append(dict(id=new_id(), e=e, vel=vel, owner='enemy', damage=damage, life=4, gravity=2, trail=color))

    def _remove(self, p):
        destroy(p['e'])
        self.list.remove(p)

    def lights(self):
        """Rockets light up their surroundings as they fly."""
        return [(p['e'].position, (1.0, 0.6, 0.3), 5, 1.2) for p in self.list if p['owner'] == 'player']

    def explode(self, pos, p):
        g = self.game
        g.effects.explosion(pos, p['radius'])
        g.lighting.flash(pos + Vec3(0, 0.5, 0), (1.0, 0.62, 0.3), p['radius'] * 3.5, 3.0, life=0.4)
        g.sounds.play('boom')
        g.shake(0.35)
        g.enemies.blast_corpses(pos, p['radius'], 9 + p['knockback'])
        if getattr(g, 'animals', None) is not None:
            shooter = p['shooter'] if hasattr(p['shooter'], 'inventory') else None
            g.animals.blast(pos, p['radius'] + 0.5, p['damage'], shooter)
        for e in list(g.enemies.alive()):
            d = (e.chest_pos() - pos).length()
            if d < p['radius'] + e.radius:
                k = 1 - max(0, d - e.radius) / p['radius']
                away = Vec3(e.position.x - pos.x, 0, e.position.z - pos.z)
                away = away.normalized() if away.length() > 0.01 else Vec3(0, 0, 1)
                e.hurt(p['damage'] * (0.35 + 0.65 * k) * p['shooter'].damage_mult * e.d.get('blast_resist', 1), False,
                       away * p['knockback'] * k,
                       attacker=p['shooter'])

    def update(self, dt):
        g = self.game
        for p in list(self.list):
            p['life'] -= dt
            p['vel'].y -= p['gravity'] * dt
            step = p['vel'] * dt
            length = step.length()
            d = step / (length or 1)
            start = Vec3(p['e'].position)
            wall_t = g.world.raycast(start, d, length)

            if p['owner'] == 'player':
                hits = g.enemies.raycast(start, d, length + 0.3)
                if hits and hits[0][0] <= wall_t:
                    self.explode(start + d * hits[0][0], p)
                    self._remove(p)
                    continue
            else:
                hit = None
                for target in g.targets():
                    eye = target.eye()
                    body = Vec3(eye.x, eye.y - 0.6, eye.z)
                    # closest point on this frame's path to the target's body
                    t = max(0, min(length, (body - start).dot(d)))
                    cp = start + d * t
                    if (cp.x - body.x) ** 2 + (cp.z - body.z) ** 2 < 0.25 and abs(cp.y - body.y) < 1:
                        hit = (target, cp)
                        break
                if hit:
                    hit[0].hurt(p['damage'], start)
                    g.effects.burst(hit[1], p['trail'], 8, speed=3)
                    self._remove(p)
                    continue

            if wall_t < length or p['life'] <= 0:
                at = start + d * wall_t
                if p['owner'] == 'player':
                    self.explode(at, p)
                else:
                    g.effects.burst(at, p['trail'], 6, speed=3)
                self._remove(p)
                continue

            p['e'].position = start + step
            p['e'].look_at(p['e'].position + p['vel'])
            if random.random() < 0.7:
                g.effects.burst(p['e'].position, p['trail'], 1, speed=0.5, size=0.12, life=0.35, gravity=0)

    def clear(self):
        for p in list(self.list):
            self._remove(p)
