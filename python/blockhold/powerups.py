"""Power-ups: rare drops from zombies that help the whole team for a short time.

The host decides when one drops and runs its effect; everyone sees the floating
token, the banner and the HUD timer. Events: powerup_dropped, powerup_taken,
powerup_ended.
"""
import math
import random
from ursina import Entity, Text, Vec3, destroy
from .data.powerups import POWERUPS, DROP_CHANCE, DROP_COOLDOWN, MAX_ON_GROUND, LIFETIME, BLAST_RADIUS
from .lowpoly import LowPoly
from .net import new_id
from .render import node, col

_meshes = {}


def token_mesh(kind):
    """A small low-poly emblem for each power-up (built once, then shared)."""
    if kind in _meshes:
        return _meshes[kind]
    lp = LowPoly(seed=11, variation=0.03)
    lp.spec = 0.6
    if kind == 'instakill':                                   # a skull
        lp.blob((0, 0.04, 0), 0.2, '#ece6d4', squash=(0.95, 1.0, 1.0), jitter=0.05, detail=1)
        lp.box((0, -0.14, 0.02), (0.2, 0.09, 0.2), '#d9d0b4')
        for x in (-0.075, 0.075):
            for z in (0.17, -0.17):
                lp.box((x, 0.03, z), (0.065, 0.075, 0.04), '#a81c24')
        lp.box((0, -0.04, 0.19), (0.03, 0.05, 0.02), '#2a1414')
        lp.box((0, -0.04, -0.19), (0.03, 0.05, 0.02), '#2a1414')
    elif kind == 'double':                                    # two stacks of coins
        for x, n in ((-0.1, 3), (0.11, 2)):
            for i in range(n):
                lp.cylinder((x, -0.18 + i * 0.07, 0), 0.11, 0.055, '#f2c230', sides=10, top_colour='#ffe27a')
        lp.cylinder((0, 0.05, 0), 0.12, 0.05, '#f2c230', sides=10, top_colour='#ffe27a')
    elif kind == 'overdrive':                                 # three rifle rounds
        for x in (-0.1, 0, 0.1):
            lp.cylinder((x, -0.2, 0), 0.04, 0.24, '#c9a227', sides=8)
            lp.cylinder((x, 0.04, 0), 0.04, 0.13, '#b8733a', sides=8, top_radius=0.0)
        lp.box((0, -0.22, 0), (0.32, 0.03, 0.1), '#5ad1ff')
    else:                                                     # a jagged energy star
        lp.blob((0, 0, 0), 0.2, '#ffffff', jitter=0.55, detail=0, colours=['#ffffff', '#ffe27a', '#ff9a3c'])
        lp.blob((0, 0, 0), 0.13, '#ffe27a', jitter=0.1, detail=0)
    _meshes[kind] = lp.mesh()
    return _meshes[kind]


class PowerUps:
    def __init__(self, game):
        self.game = game
        self.root = node(game.world_root)
        self.drops = []          # dicts: id, kind, pos, e, spin, life
        self.timers = {}         # kind -> seconds left (team-wide)
        self.cooldown = 0.0
        self.t = 0.0

    # ── queries used by gameplay ─────────────────────────────────────────────
    def active(self, kind):
        return self.timers.get(kind, 0) > 0

    def coin_mult(self):
        return 2 if self.active('double') else 1

    # ── dropping and picking up ──────────────────────────────────────────────
    def clear(self):
        for d in self.drops:
            destroy(d['e'])
        self.drops = []
        self.timers = {}
        self.cooldown = 0.0

    def on_kill(self, enemy):
        g = self.game
        if g.phase != 'wave' or self.cooldown > 0 or len(self.drops) >= MAX_ON_GROUND:
            return
        if random.random() < DROP_CHANCE:
            kinds = list(POWERUPS)
            kind = random.choices(kinds, weights=[POWERUPS[k]['weight'] for k in kinds])[0]
            self.drop(kind, enemy.position)

    def drop(self, kind, pos):
        g = self.game
        d = POWERUPS[kind]
        x, z = g.world.collide(Vec3(pos.x, 0, pos.z), 0.5)
        e = node(self.root, position=(x, 1.0, z))
        spin = node(e, scale=1.5)
        token_mesh(kind).copyTo(spin)          # copy: two tokens of one kind can't share the mesh itself
        tag = Entity(parent=e, y=0.62, billboard=True)
        Text(d['name'], parent=tag, scale=6, origin=(0, 0), color=col(d['color']))
        self.drops.append(dict(id=new_id(), kind=kind, pos=Vec3(x, 0, z), e=e, spin=spin, life=LIFETIME))
        self.cooldown = DROP_COOLDOWN
        g.sounds.play('powerup_drop', volume=0.7)
        g.effects.burst(Vec3(x, 1.0, z), d['color'], 14, speed=3, size=0.1, life=0.8, gravity=-2)
        g.events.emit('powerup_dropped', kind=kind, pos=Vec3(x, 0, z))

    def take(self, drop, player):
        g = self.game
        kind, d = drop['kind'], POWERUPS[drop['kind']]
        self.drops.remove(drop)
        destroy(drop['e'])
        if d['time'] > 0:
            self.timers[kind] = d['time']
        else:
            self.blast(player)
        g.ui.banner(d['name'], d['color'], 2.5, d['desc'])
        g.sounds.play('powerup')
        g.effects.burst(drop['pos'] + Vec3(0, 1, 0), d['color'], 26, speed=7, size=0.14)
        g.events.emit('powerup_taken', kind=kind, player=player)

    def blast(self, player):
        g = self.game
        for e in list(g.enemies.alive()):
            if (e.position - player.position).length() > BLAST_RADIUS:
                continue
            g.effects.burst(e.chest_pos(), '#ffe27a', 6, speed=6, size=0.12)
            if e.d.get('boss'):
                e.hurt(e.hp * 0.2, False, None, attacker=player)
            else:
                e.hurt(e.hp + 1, False, None, attacker=player)
        for q in g.players:
            q.coins += 150
        g.sounds.play('boom', volume=1.0)
        g.shake(0.6)

    # ── per frame ────────────────────────────────────────────────────────────
    def update(self, dt):
        g = self.game
        self.t += dt
        self.cooldown -= dt
        for kind in list(self.timers):
            self.timers[kind] -= dt
            if self.timers[kind] <= 0:
                del self.timers[kind]
                g.events.emit('powerup_ended', kind=kind)
                g.sounds.play('reload_out', volume=0.6, pitch=0.7)
        for drop in list(self.drops):
            drop['life'] -= dt
            if drop['life'] <= 0:
                self.drops.remove(drop)
                destroy(drop['e'])
                continue
            e = drop['e']
            e.y = 1.0 + math.sin(self.t * 2.5 + drop['id']) * 0.12
            drop['spin'].rotation_y += dt * 110
            e.enabled = drop['life'] > 6 or int(drop['life'] * 6) % 2 == 0
            if random.random() < dt * 4:
                g.effects.burst(Vec3(e.x, e.y, e.z), POWERUPS[drop['kind']]['color'], 1, speed=0.8, size=0.06,
                                life=0.7, gravity=-1.5)
            for p in g.players:
                if not p.dead and (Vec3(p.position.x, 0, p.position.z) - drop['pos']).length() < 1.4:
                    self.take(drop, p)
                    break

    def hud_rows(self):
        """[(name, colour, seconds left)] for the HUD, longest first."""
        rows = [(POWERUPS[k]['name'], POWERUPS[k]['color'], t) for k, t in self.timers.items()]
        return sorted(rows, key=lambda r: -r[2])
