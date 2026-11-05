"""The hideout: an underground base built from the editor's tunnel pieces.

build_hideout() lays it out on a grid of 5 x 5 m tunnel cells and returns an ordinary
map (the same format the editor saves), so you can open maps/hideout.json in the editor
and change it however you like. The game loads that file; if it's missing, it builds a
fresh one.

  HUB       the middle: a radio desk, water tank, an old minecart and a few locals
  QUARTERS  north: your bunk, lockers, your STASH box and a workbench (you start here)
  BANK      west: the banker behind the counter, and the vault
  MARKET    east: merchant stalls (scrap dealer, tailor, medic, armorer, gunsmith)
  EXIT      south: the ladder up to the surface, where raids start

Run `python -m blockhold.hideout` to write a new maps/hideout.json.
"""
import math
from .data.assets import ASSETS
from .data.npcs import fill_npc

CELL = 5                      # one tunnel piece is 5 x 5 m
SIDES = {'+x': (1, 0), '-x': (-1, 0), '+z': (0, 1), '-z': (0, -1)}
PIECES = {'hall_open': (), 'hall_wall': ('+x',), 'hall_straight': ('+x', '-x'), 'hall_corner': ('+x', '+z'),
          'hall_end': ('+x', '-x', '+z')}


def rotate(dx, dz, rot):
    """How a local offset turns with a prop (the same as world.rotate_cell)."""
    a = math.radians(round(rot / 90) * 90)
    c, s = round(math.cos(a)), round(math.sin(a))
    return dx * c + dz * s, -dx * s + dz * c


def piece_for(walls):
    """(tunnel piece, rotation) with walls exactly on these world sides."""
    want = {SIDES[w] for w in walls}
    for aid, local in PIECES.items():
        if len(local) != len(want):
            continue
        for rot in (0, 90, 180, 270):
            if {rotate(*SIDES[s], rot) for s in local} == want:
                return aid, rot
    return None, 0


def facing(front, direction):
    """The rotation that turns a prop's front (a local (dx, dz)) to point along direction."""
    return next((rot for rot in (0, 90, 180, 270) if rotate(*front, rot) == direction), 0)


class Plan:
    def __init__(self):
        self.cells = set()
        self.props = []

    def room(self, i0, j0, i1, j1):
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                self.cells.add((i, j))

    def centre(self, i, j):
        return i * CELL + 0.5, j * CELL + 0.5

    def put(self, aid, x, z, rot=0, data=None):
        entry = [aid, round(x, 2), round(z, 2), rot, 1]
        if data is not None:
            entry.append(data)
        self.props.append(entry)

    def at_wall(self, aid, cell, side, along=0.0, inset=1.0, front=(0, -1), data=None, back=False):
        """A prop against a wall of a cell: `inset` metres in from the cell's centre towards the wall,
        `along` metres sideways, its front facing into the room (or towards the wall with back=True)."""
        x, z = self.centre(*cell)
        sx, sz = SIDES[side]
        px, pz = -sz, sx                                  # along the wall
        rot = facing(front, (sx, sz) if back else (-sx, -sz))
        self.put(aid, x + sx * inset + px * along, z + sz * inset + pz * along, rot, data)

    def tunnels(self):
        """A hall piece in every cell, with walls wherever the next cell isn't part of the plan, and a
        pillar in a corner where walls meet round it (rooms stay open inside)."""
        for i, j in sorted(self.cells):
            walls = [s for s, (dx, dz) in SIDES.items() if (i + dx, j + dz) not in self.cells]
            aid, rot = piece_for(walls)
            x, z = self.centre(i, j)
            if aid is not None:
                self.put(aid, x, z, rot)
            for sx in (-1, 1):
                for sz in (-1, 1):
                    if (i + sx, j) in self.cells and (i, j + sz) in self.cells and (i + sx, j + sz) not in self.cells:
                        self.put('tunnel_pillar', x + sx * 2, z + sz * 2)


def npc(role, **kw):
    return fill_npc(dict(kw, role=role))


def build_hideout():
    p = Plan()
    p.room(-1, -1, 1, 1)                 # the hub
    p.room(0, 2, 0, 3)                   # corridor north
    p.room(-1, 4, 1, 5)                  # quarters
    p.room(-3, 0, -2, 0)                 # corridor west
    p.room(-6, -1, -4, 1)                # the bank
    p.room(2, 0, 3, 0)                   # corridor east
    p.room(4, -1, 7, 1)                  # the market
    p.room(0, -4, 0, -2)                 # corridor south
    p.room(0, -5, 0, -5)                 # the ladder up
    p.tunnels()

    # ── quarters (you start here) ──
    p.put('player_spawn', *p.centre(0, 4))
    p.at_wall('bunk_bed', (-1, 5), '-x', inset=0.9, along=0.5)
    p.at_wall('bunk_bed', (-1, 4), '-x', inset=0.9, along=-0.5)
    p.at_wall('locker_row', (1, 5), '+x', inset=1.15)
    p.at_wall('stash_box', (0, 5), '+z', inset=1.0)
    p.at_wall('wall_light', (0, 5), '+z', inset=1.45)
    p.at_wall('workbench', (1, 4), '+x', inset=0.8, front=(0, 1), back=False)
    p.at_wall('supply_shelf', (-1, 5), '+z', inset=1.2, along=0.6)
    p.at_wall('vent_fan', (1, 5), '+z', inset=1.4)
    for c in ((0, 4), (0, 5)):
        p.put('hanging_lamp', *p.centre(*c))

    # ── the hub ──
    p.put('radio_desk', *p.centre(0, 0))
    p.at_wall('water_tank', (-1, 1), '-x', inset=0.8, along=-0.8)
    p.at_wall('wall_pipes', (1, 1), '+z', inset=1.4)
    p.at_wall('wall_pipes', (-1, -1), '-z', inset=1.4)
    p.at_wall('rail_track', (1, -1), '+x', inset=0.6)
    p.at_wall('minecart', (1, -1), '+x', inset=0.6, along=0.8)
    p.at_wall('supply_shelf', (-1, -1), '-x', inset=1.1)
    for c in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        p.put('hanging_lamp', *p.centre(*c))
    cx, cz = p.centre(1, -1)
    for dx, dz, aid in ((-1.2, -1.2, 'crate'), (-0.2, -1.3, 'crate'), (-1.3, -0.2, 'barrel')):
        p.put(aid, cx + dx, cz + dz, 15)
    hx, hz = p.centre(-1, 0)
    p.put('npc_talker', hx + 0.5, hz, 270, npc('talker', name='Radio Ruth', shirt='#556043', hat='beanie',
          greeting="Still breathing? Good. The radio says it's bad up top today.",
          lines=["Grab a bigger bag before your first trip. You'll thank me.",
                 "The Outskirts are calm. The Wildlands, less so. Nobody comes back from the Blacksite smiling.",
                 "Find an extraction point and stand in it. The flare shows you where.",
                 "Anything you put in the bank is safe. Anything you carry up the ladder isn't.",
                 "Die up there and whatever's on your back stays there. Remember that."],
          farewell="Keep your head down."))

    # ── the bank (west) ──
    p.at_wall('vault_door', (-6, 0), '-x', inset=1.75)
    bx, bz = p.centre(-5, 0)
    for k in range(-2, 3):                          # one long counter across the room
        p.put('bank_counter', bx + 0.6, bz + k * 3.0, facing((0, 1), (1, 0)))
    p.put('npc_trader', bx - 0.8, bz, facing((0, 1), (1, 0)), npc('banker'))
    p.at_wall('locker_row', (-6, -1), '-z', inset=1.15)
    p.at_wall('locker_row', (-6, 1), '+z', inset=1.15)
    p.at_wall('stash_box', (-4, 1), '+z', inset=1.0)
    p.at_wall('wall_light', (-4, -1), '-z', inset=1.45)
    for c in ((-5, -1), (-5, 1), (-4, 0), (-6, 0)):
        p.put('hanging_lamp', *p.centre(*c))

    # ── the market (east) ──
    stalls = [((5, 1), '+z', npc('merchant', shop='scrapper')), ((6, 1), '+z', npc('merchant', shop='tailor')),
              ((7, 1), '+z', npc('merchant', shop='medic')), ((5, -1), '-z', npc('merchant', shop='armorer')),
              ((6, -1), '-z', npc('gunsmith')), ((7, -1), '-z', None)]
    for cell, side, who in stalls:
        p.at_wall('merchant_stall', cell, side, inset=0.7, front=(0, 1))
        if who is not None:
            x, z = p.centre(*cell)
            sx, sz = SIDES[side]
            p.put('npc_trader', x + sx * 0.75, z + sz * 0.75, facing((0, 1), (-sx, -sz)), who)
    p.at_wall('supply_shelf', (7, -1), '-z', inset=0.3)
    p.at_wall('water_tank', (7, 0), '+x', inset=0.8)
    p.at_wall('vent_fan', (7, 1), '+x', inset=1.4)
    p.at_wall('wall_light', (4, 1), '+z', inset=1.45)
    p.at_wall('wall_light', (4, -1), '-z', inset=1.45)
    for c in ((4, 0), (5, 0), (6, 0), (7, 0)):
        p.put('hanging_lamp', *p.centre(*c))
    qx, qz = p.centre(4, -1)
    p.put('npc_quest', qx, qz - 0.6, 0, npc('quest', name='Foreman Kade', shirt='#b5803a', hat='helmet',
          greeting="You look like you can carry things. I've got work.",
          quest=dict(kind='bring', item='spring', n=4, reward_coins=300, reward_item='chest_rig', reward_n=1,
                     repeat=True, offer="Bring me 4 springs from up top and I'll throw in a chest rig.",
                     progress="Springs. Four of them. Barrels and toolboxes have them.",
                     done="That'll keep the pumps running. Here.")))

    # ── the way out (south) ──
    p.at_wall('exit_ladder', (0, -5), '-z', inset=1.2, front=(0, -1), back=True)
    p.at_wall('tarp_curtain', (0, -2), '+z', inset=2.2)
    for c in ((0, -3), (0, -5)):
        p.put('hanging_lamp', *p.centre(*c))
    p.at_wall('wall_light', (0, -4), '+x', inset=1.45)
    p.at_wall('wall_light', (0, -2), '-x', inset=1.45)

    # the whole place is a safe zone
    p.put('zone_safe', *p.centre(0, 0), 0, {'radius': 60})
    xs = [i for i, _ in p.cells]
    zs = [j for _, j in p.cells]
    half = int(max(abs(min(xs)), abs(max(xs)), abs(min(zs)), abs(max(zs))) * CELL + CELL + 4)
    return dict(format=1, name='Hideout', size=half, walls=True, hideout=True, atmosphere='hideout',
                blocks=[], paths=[], props=p.props)


if __name__ == '__main__':
    from .maps import save_map
    print('wrote', save_map(build_hideout(), 'hideout'))
