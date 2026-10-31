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
# ─────────────────────────────────────────────────────────────────────────────

RESOURCES = {
    'stone': dict(name='Stone', color='#a3a39f'),
    'iron': dict(name='Iron', color='#c3cfdb'),
    'copper': dict(name='Copper', color='#e0813a'),
    'crystal': dict(name='Crystal', color='#c07bff'),
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
