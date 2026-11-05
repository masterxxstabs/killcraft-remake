"""Random encounters: zones from the map editor where a group of zombies may climb out
of the ground when a player walks in (see data/zones.py, kind 'encounter').

Each zone rolls its chance once per visit, then waits its cooldown before it can roll
again. The group appears 6 to 12 m from the player, never inside a safe zone, at the
zone's level (or the level zone it's in). They don't count towards the current wave.
Events: encounter (zone position, how many).
"""
import math
import random
from ursina import Vec3
from .data.enemies import ENEMIES

MAX_EXTRA = 30          # never more than this many encounter zombies alive at once


class Encounters:
    def __init__(self, game):
        self.game = game
        self.state = {}         # id(zone prop) -> dict(cooldown, inside)
        self.tick = 0.0

    def clear(self):
        self.state = {}

    def pick_kind(self, kind):
        if kind in ENEMIES and not ENEMIES[kind].get('boss'):
            return kind
        normal = [k for k, d in ENEMIES.items() if not d.get('boss') and k != 'hollow_herald']
        return random.choice(normal)

    def trigger(self, zone, player):
        g, d = self.game, zone['data']
        alive_extra = sum(1 for e in g.enemies.alive() if not e.wave_member)
        n = random.randint(min(d['group_min'], d['group_max']), max(d['group_min'], d['group_max']))
        n = min(n, MAX_EXTRA - alive_extra)
        if n <= 0:
            return 0
        wave = g.wave if g.phase == 'wave' and g.wave else _calm_wave(g)
        made = 0
        w = g.world
        for _ in range(n * 4):
            if made >= n:
                break
            a, r = random.random() * math.tau, 6 + random.random() * 6
            x, z = player.position.x + math.cos(a) * r, player.position.z + math.sin(a) * r
            if abs(x) > w.half - 1.5 or abs(z) > w.half - 1.5 or w.height_at(x, z) > 0 or w.in_safe_zone(x, z):
                continue
            level = d.get('level') or None
            g.enemies.spawn(self.pick_kind(d.get('kind', 'mixed')), wave, Vec3(x, 0, z), level=level, wave_member=False)
            made += 1
        if made:
            g.sounds.play('groan', volume=0.9, pitch=0.6)
            g.events.emit('encounter', pos=Vec3(zone['x'], 0, zone['z']), count=made)
        return made

    def update(self, dt):
        g = self.game
        zones = g.world.zones.get('encounter', [])
        if not zones:
            return
        for st in self.state.values():
            st['cooldown'] = max(0.0, st['cooldown'] - dt)
        self.tick -= dt
        if self.tick > 0:
            return
        self.tick = 0.25
        for zone in zones:
            st = self.state.setdefault(id(zone), dict(cooldown=0.0, inside=False))
            r = zone['data']['radius']
            who = next((p for p in g.players if not p.dead and
                        (p.position.x - zone['x']) ** 2 + (p.position.z - zone['z']) ** 2 <= r * r), None)
            entered = who is not None and not st['inside']
            st['inside'] = who is not None
            if entered and st['cooldown'] <= 0:
                st['cooldown'] = zone['data']['cooldown']
                if random.random() * 100 < zone['data']['chance']:
                    self.trigger(zone, who)


def _calm_wave(g):
    """Wave stats to use between waves (encounters can happen any time)."""
    from .data.waves import build_wave
    return build_wave(max(1, g.wave_number))
