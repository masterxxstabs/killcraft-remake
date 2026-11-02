"""Ore nodes you mine with melee weapons for crafting resources.

On random maps nodes pop up anywhere there's room. On custom maps they only grow
at the ore spawn markers placed in the editor (so you can build a mine). A mined
node grows back after a while. Resources belong to the player who mined them.
Events: node_spawned, node_mined, node_broken.
"""
import random
from ursina import Vec3
from .data.resources import RESOURCES, NODE_TYPES, MINE_DAMAGE, RANDOM_NODE_COUNT, RESPAWN_TIME, draw_node
from .lowpoly import LowPoly
from .net import new_id
from .render import node, destroy

_meshes = {}
VARIANTS = 3


def node_mesh(kind, variant=0):
    """A rock with ore chunks (or crystal spikes) sticking out of it."""
    key = (kind, variant)
    if key not in _meshes:
        lp = LowPoly(seed=variant * 31 + len(kind) * 7, variation=0.06)
        draw_node(lp, kind)
        _meshes[key] = lp.mesh()
    return _meshes[key]


def pick_kind(kind=None):
    if kind in NODE_TYPES:
        return kind
    kinds = list(NODE_TYPES)
    return random.choices(kinds, weights=[NODE_TYPES[k]['weight'] for k in kinds])[0]


class Mining:
    def __init__(self, game):
        self.game = game
        self.root = node(game.world_root)
        self.nodes = []          # dicts: id, kind, d, pos, cell, hp, max_hp, given, e, shake, spot, scale
        self.pending = []        # [seconds left, spot] waiting to grow back

    # ── setting up ───────────────────────────────────────────────────────────
    def clear(self):
        for n in self.nodes:
            destroy(n['e'])
            self.game.world.set_dynamic_solid(*n['cell'], 0)
        self.nodes = []
        self.pending = []

    def reset(self):
        """Fill a freshly loaded world with nodes."""
        self.nodes = []
        self.pending = []
        spots = self.game.world.ore_spawns
        if spots:
            for spot in spots:
                self.spawn(spot)
        else:
            w = self.game.world
            for _ in range(min(160, round(RANDOM_NODE_COUNT * max(1.0, w.area_scale())))):   # bigger map, more nodes
                self.spawn(None)

    def random_spot(self):
        w = self.game.world
        for _ in range(80):
            gx, gz = 3 + random.randrange(w.n - 6), 3 + random.randrange(w.n - 6)
            pos = Vec3(gx - w.half + 0.5, 0, gz - w.half + 0.5)
            if not w.free(gx, gz, 1, paths_ok=False):
                continue
            if any((n['pos'] - pos).length() < 4 for n in self.nodes):
                continue
            if any((b - pos).length() < 4 for b in w.benches):
                continue
            if any((p.position - pos).length() < 4 for p in self.game.players):
                continue
            return pos
        return None

    def spawn(self, spot):
        """spot = (position, kind) from a map marker, or None for anywhere on a random map."""
        w = self.game.world
        if spot is None:
            pos, kind = self.random_spot(), pick_kind()
            if pos is None:
                self.pending.append([10.0, None])
                return None
        else:
            pos, kind = spot[0], pick_kind(spot[1])
            if any((Vec3(p.position.x, 0, p.position.z) - pos).length() < 1.0 for p in self.game.players):
                return None
        gx, gz = w.to_grid(pos.x, pos.z)
        if any(n['cell'] == (gx, gz) for n in self.nodes):
            return None
        d = NODE_TYPES[kind]
        scale = 0.9 + random.random() * 0.25
        e = node(self.root, position=(pos.x, 0, pos.z), rotation_y=random.random() * 360, scale=scale)
        node_mesh(kind, random.randrange(VARIANTS)).copyTo(e)     # a light copy: the shared mesh stays put
        n = dict(id=new_id(), kind=kind, d=d, pos=Vec3(pos.x, 0, pos.z), cell=(gx, gz), hp=float(d['hp']),
                 max_hp=float(d['hp']), given={}, e=e, shake=0.0, spot=spot, scale=scale, grow=0.0)
        w.set_dynamic_solid(gx, gz, 1)
        self.nodes.append(n)
        self.game.events.emit('node_spawned', id=n['id'], kind=kind, pos=n['pos'])
        return n

    # ── mining ───────────────────────────────────────────────────────────────
    def find(self, eye, fwd, reach):
        """The node a melee swing from eye towards fwd would hit."""
        best, best_d = None, reach + 0.7
        for n in self.nodes:
            to = n['pos'] + Vec3(0, 0.45, 0) - eye
            dist = to.length()
            if dist < best_d and (dist < 1.1 or to.normalized().dot(fwd) > 0.6):
                best, best_d = n, dist
        return best

    def mine(self, n, player, power=1.0, hit_pos=None):
        g = self.game
        n['hp'] = max(0.0, n['hp'] - MINE_DAMAGE * power)
        done = 1 - n['hp'] / n['max_hp']
        gained = {}
        for res, total in n['d']['yields'].items():
            should = total if n['hp'] <= 0 else int(total * done)
            give = should - n['given'].get(res, 0)
            if give > 0:
                n['given'][res] = should
                player.resources[res] = player.resources.get(res, 0) + give
                gained[res] = give
        n['shake'] = 0.18
        at = hit_pos or (n['pos'] + Vec3(0, 0.6, 0))
        g.effects.burst(at, random.choice(n['d']['rock']), 6, speed=4, size=0.1)
        if n['d']['ore']:
            g.effects.burst(at, n['d']['ore'][0], 4, speed=4, size=0.08)
        g.events.emit('node_mined', id=n['id'], player=player, gained=gained)
        if player.is_local:
            g.sounds.play('chop' if n['d'].get('wood') else 'mine_hit', pitch=0.9 + random.random() * 0.2)
            for i, (res, amt) in enumerate(gained.items()):
                g.effects.damage_number(n['pos'] + Vec3(0, 1.3 + i * 0.3, 0), amt, color=RESOURCES[res]['color'],
                                        label=f"+{amt} {RESOURCES[res]['name']}")
        if n['hp'] <= 0:
            self.break_node(n, player)
        return gained

    def break_node(self, n, player=None):
        g = self.game
        self.nodes.remove(n)
        destroy(n['e'])
        g.world.set_dynamic_solid(*n['cell'], 0)
        g.effects.burst(n['pos'] + Vec3(0, 0.5, 0), n['d']['rock'][0], 18, speed=6, size=0.16)
        if n['d']['ore']:
            g.effects.burst(n['pos'] + Vec3(0, 0.5, 0), n['d']['ore'][0], 10, speed=6, size=0.12)
        g.sounds.play('barricade_break' if n['d'].get('wood') else 'mine_break')
        g.events.emit('node_broken', id=n['id'], player=player)
        self.pending.append([random.uniform(*RESPAWN_TIME), n['spot']])

    def lights(self):
        """Crystal nodes glow a little."""
        return [(n['pos'] + Vec3(0, 0.8, 0), (0.72, 0.45, 1.0), 4.5, 0.8 * n['grow'])
                for n in self.nodes if n['kind'] == 'crystal']

    # ── per frame ────────────────────────────────────────────────────────────
    def update(self, dt):
        for n in self.nodes:
            e = n['e']
            n['grow'] = min(1.0, n['grow'] + dt * 2)              # pops up when it spawns
            n['shake'] = max(0.0, n['shake'] - dt)
            s = n['shake'] * 0.25
            e.x = n['pos'].x + (random.random() - 0.5) * s
            e.z = n['pos'].z + (random.random() - 0.5) * s
            e.scale = n['scale'] * (0.6 + 0.4 * n['hp'] / n['max_hp']) * (0.3 + 0.7 * n['grow'])
        for p in list(self.pending):
            p[0] -= dt
            if p[0] <= 0:
                self.pending.remove(p)
                if self.spawn(p[1]) is None and p[1] is not None:
                    self.pending.append([5.0, p[1]])            # someone's standing on it: try again soon
