"""Loot you scavenge: containers you search with E, and the sacks broken barrels leave.

Containers are map pieces with a `loot` kind (data/assets.py, the editor's Loot tab):
toolboxes, medical boxes, military crates and clothes racks. Each one is filled from its
loot table (data/loot.py) when the map loads. Search it with E: its grid opens next to
your own, and you drag across what you want. Once it's empty it fills up again after a
couple of minutes, but only while nobody is close enough to see it happen.

Barrels and supply crates are breakables (ore nodes, see mining.py). When one breaks it
leaves a sack with its loot on the ground; the sack rots away after a few minutes, or as
soon as it's empty.
Events: loot_opened, loot_refilled.
"""
import math
import random
from ursina import Vec3
from .data.loot import CONTAINERS, OPEN_RANGE, RESPAWN, RESPAWN_CLEAR, SACK_ROLLS, SACK_TTL, roll
from .inventory import Grid
from .lowpoly import LowPoly
from .net import new_id
from .render import destroy, node

_sack_mesh = []


def sack_mesh():
    if not _sack_mesh:
        lp = LowPoly(seed=11)
        lp.blob((0, 0.24, 0), 0.32, '#8a7350', squash=(1.1, 0.75, 1), detail=1, jitter=0.12)
        lp.blob((0, 0.5, 0), 0.1, '#7a6444', detail=0, jitter=0.1)
        lp.box((0, 0.56, 0), (0.08, 0.08, 0.08), '#5e4a30')
        _sack_mesh.append(lp.mesh())
    return _sack_mesh[0]


class Loot:
    def __init__(self, game):
        self.game = game
        self.list = []           # dicts: id, kind, d, pos, items, sack, ttl, refill, e, prop

    # ── setting up ───────────────────────────────────────────────────────────
    def clear(self):
        for c in self.list:
            if c['e'] is not None:
                destroy(c['e'])
        self.list = []

    def reset(self):
        """Fill every container on a freshly loaded map."""
        self.clear()
        for p in self.game.world.loot_spots:
            from .data.assets import ASSETS
            kind = ASSETS[p['id']]['loot']
            c = dict(id=new_id(), kind=kind, d=CONTAINERS[kind], pos=Vec3(p['x'], 0, p['z']), items=[], sack=False,
                     ttl=None, refill=None, e=None, prop=p)
            self.fill(c)
            self.list.append(c)

    def grid(self, c):
        cols, rows = c['d']['grid']
        return Grid('loot', c['d']['name'].upper(), cols, rows, c['items'])

    def fill(self, c, rolled=None):
        c['items'][:] = []
        g = self.grid(c)
        for item, n in rolled if rolled is not None else roll(c['d']['table'], c['d']['rolls']):
            g.add(item, n)
        c['refill'] = None

    def spawn_sack(self, pos, table):
        """A sack of loot where a barrel / crate broke."""
        d = dict(CONTAINERS['sack'], name='Barrel loot' if table == 'barrel' else 'Crate loot')
        e = node(self.game.world_root, position=(pos.x, 0, pos.z), rotation_y=random.random() * 360)
        sack_mesh().copyTo(e)
        c = dict(id=new_id(), kind='sack', d=d, pos=Vec3(pos.x, 0, pos.z), items=[], sack=True, ttl=SACK_TTL,
                 refill=None, e=e, prop=None)
        self.fill(c, roll(table, SACK_ROLLS.get(table, (2, 4))))
        self.list.append(c)
        self.game.effects.burst(c['pos'] + Vec3(0, 0.5, 0), '#c8a028', 8, speed=3, size=0.08)
        return c

    # ── finding and opening ──────────────────────────────────────────────────
    def nearest(self, pos, max_dist=OPEN_RANGE):
        best, best_d = None, max_dist
        for c in self.list:
            dist = math.hypot(c['pos'].x - pos.x, c['pos'].z - pos.z)
            if c['kind'] in ('military', 'clothes'):        # the long ones: you can reach them from the ends
                dist -= 0.8
            if dist < best_d:
                best, best_d = c, dist
        return best

    def is_open(self, c):
        bag = getattr(self.game.ui, 'bag', None)
        return bag is not None and bag.active and bag.container is c

    def prompt(self, player):
        c = self.nearest(player.position)
        if c is None or not c['items']:          # (empty ones say nothing, so a workbench beside one still shows)
            return ''
        return f"Press E to search the {c['d']['name'].lower()}"

    def open(self, player, c=None):
        c = c or self.nearest(player.position)
        if c is None or player.downed or player.dead:
            return False
        self.game.open_bag(container=c)
        self.game.sounds.play('equip', volume=0.6, pitch=0.8)
        self.game.events.emit('loot_opened', id=c['id'], kind=c['kind'], player=player)
        return True

    def take_all(self, player, c):
        """Move everything that fits into player's grids."""
        inv = player.inventory
        moved = 0
        for it in list(c['items']):
            c['items'].remove(it)
            if inv.put_back(it):
                moved += 1
            else:
                c['items'].append(it)
        return moved

    # ── per frame ────────────────────────────────────────────────────────────
    def update(self, dt):
        players = [p for p in self.game.players if not p.dead]
        for c in list(self.list):
            if self.is_open(c):
                continue
            if c['sack']:
                c['ttl'] -= dt
                if c['ttl'] <= 0 or not c['items']:
                    destroy(c['e'])
                    self.list.remove(c)
                continue
            if c['items']:
                continue
            if c['refill'] is None:
                c['refill'] = random.uniform(*RESPAWN)
                continue
            c['refill'] -= dt
            if c['refill'] <= 0:
                if any(math.hypot(p.position.x - c['pos'].x, p.position.z - c['pos'].z) < RESPAWN_CLEAR for p in players):
                    c['refill'] = 5.0                  # someone's watching: try again a bit later
                    continue
                self.fill(c)
                self.game.events.emit('loot_refilled', id=c['id'], kind=c['kind'])
