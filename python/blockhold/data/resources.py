# ─────────────────────────────────────────────────────────────────────────────
#  RESOURCES AND ORE NODES
#  Ore nodes appear around the map. Hit them with a melee weapon to mine them
#  (the Pickaxe is much faster). Resources are spent at workbenches (crafting.py).
#
#  Node fields:
#    name      shown when you look at it
#    hp        how much mining it takes to break
#    yields    resources you get in total, handed out a bit with every hit
#    rock      colours of the rock, ore = colours of the ore chunks in it
#    weight    how often it spawns compared to the others
#    loot      breakable crates: (resource, min, max, chance) rolled when it breaks
#              (crates can be shot as well as hit, and give nothing until they break)
# ─────────────────────────────────────────────────────────────────────────────

RESOURCES = {
    'stone': dict(name='Stone', color='#a3a39f'),
    'iron': dict(name='Iron', color='#c3cfdb'),
    'copper': dict(name='Copper', color='#e0813a'),
    'crystal': dict(name='Crystal', color='#c07bff'),
    'wood': dict(name='Wood', color='#b98a52'),
}

NODE_TYPES = {
    'stone': dict(name='Stone', hp=120, yields={'stone': 30}, weight=5,
                  rock=['#8f8f8b', '#7e7e7a', '#9c9c97'], ore=None),
    'iron': dict(name='Iron ore', hp=160, yields={'iron': 18, 'stone': 6}, weight=3,
                 rock=['#77767a', '#6a696d', '#828186'], ore=['#c3cfdb', '#dfe7ef', '#a9b6c4']),
    'copper': dict(name='Copper ore', hp=160, yields={'copper': 18, 'stone': 6}, weight=2.5,
                   rock=['#7b7166', '#6e655b', '#877c70'], ore=['#e0813a', '#c96a2b', '#f09a55']),
    'crystal': dict(name='Crystal', hp=220, yields={'crystal': 4, 'stone': 4}, weight=0.7,
                    rock=['#4a4458', '#3d384a', '#565066'], ore=['#c07bff', '#d6a3ff', '#9b5ae0']),
    # chopped rather than mined: the Fire Axe is fastest (its `chop` in weapons.py)
    'logs': dict(name='Log pile', hp=140, yields={'wood': 30}, weight=4, wood=True,
                 rock=['#6e5233', '#634a2e', '#7a5b39'], ore=['#cdb083', '#c4a574', '#d8bd92']),
    # supply crates: smash or shoot them open for a random handful of crafting resources
    'crate': dict(name='Supply crate', hp=60, yields={}, weight=1.5, wood=True, crate=True,
                  loot=[('wood', 6, 14, 1.0), ('stone', 4, 10, 0.6), ('iron', 3, 9, 0.6), ('copper', 3, 8, 0.5),
                        ('crystal', 1, 2, 0.12)],
                  rock=['#9a7448', '#8a6a40', '#a87e50'], ore=['#4a4e55', '#3a3d42', '#5b6067']),
}

MINE_DAMAGE = 20            # mining done by one swing of a weapon with gather=1
RANDOM_NODE_COUNT = 14      # nodes kept on random maps (custom maps use their ore spawn markers)
RESPAWN_TIME = (45, 75)     # seconds before a mined node grows back (random between the two)


def draw_node(lp, kind):
    """Add an ore node to a LowPoly builder: a rock with ore chunks or crystal spikes."""
    import math
    t = NODE_TYPES[kind]
    rnd = lp.rnd
    rock, ore = t['rock'], t['ore']
    if t.get('crate'):                     # a banded wooden supply crate
        lp.box((0, 0.42, 0), (0.86, 0.84, 0.86), rock[0], top=rock[2])
        for y in (0.08, 0.76):
            lp.box((0, y, 0), (0.9, 0.08, 0.9), ore[0])
        for x in (-0.4, 0.4):
            lp.box((x, 0.42, 0), (0.08, 0.84, 0.9), rock[1])
        lp.box((0, 0.46, 0.44), (0.4, 0.16, 0.01), '#d9c98a')            # stencil plate
        lp.box((0, 0.46, -0.44), (0.4, 0.16, 0.01), '#d9c98a')
        lp.box((0.2, 0.86, 0.1), (0.3, 0.06, 0.2), ore[2], yaw=20)        # a crowbar left on top
        return
    if t.get('wood'):                      # a pile of cut logs instead of a rock
        for y, z, n in ((0.16, 0.0, 3), (0.42, 0.0, 2), (0.66, 0.0, 1)):
            for k in range(n):
                x0 = (k - (n - 1) / 2) * 0.34 + (rnd.random() - 0.5) * 0.05
                a = (rnd.random() - 0.5) * 0.15
                lp.beam((x0 + a, y, z - 0.62), (x0 - a, y, z + 0.62), 0.16, rnd.choice(rock), sides=7)
                for end in (-0.625, 0.625):           # the pale cut ends
                    lp.box((x0 + a * (1 if end < 0 else -1), y, z + end), (0.25, 0.25, 0.012), rnd.choice(ore))
        return
    lp.blob((0, 0.32, 0), 0.6, rock[0], squash=(1.1, 0.72, 1.0), jitter=0.22, detail=1, colours=rock)
    lp.blob((0.45, 0.18, 0.22), 0.34, rock[1], jitter=0.25, detail=0, colours=rock)
    lp.blob((-0.4, 0.16, -0.25), 0.3, rock[2], jitter=0.25, detail=0, colours=rock)
    lp.spec = 0.8
    if kind == 'crystal':
        for i in range(6):
            a = i / 6 * math.tau + rnd.random() * 0.6
            r = 0.15 + rnd.random() * 0.2
            base = (math.cos(a) * r, 0.42, math.sin(a) * r)
            out = 0.2 + rnd.random() * 0.25
            tip = (base[0] + math.cos(a) * out, 0.85 + rnd.random() * 0.45, base[2] + math.sin(a) * out)
            lp.beam(base, tip, 0.07 + rnd.random() * 0.04, rnd.choice(ore), sides=5, end_radius=0.0)
    elif ore:
        for i in range(8):
            a = rnd.random() * math.tau
            e = 0.2 + rnd.random() * 1.0
            p = (math.cos(a) * math.cos(e) * 0.6, 0.32 + math.sin(e) * 0.42, math.sin(a) * math.cos(e) * 0.58)
            lp.blob(p, 0.08 + rnd.random() * 0.07, ore[0], jitter=0.35, detail=0, colours=ore)
    else:
        lp.spec = 0.0
        lp.blob((0.1, 0.62, -0.05), 0.22, rock[1], jitter=0.3, detail=0, colours=rock)
    lp.spec = 0.0
