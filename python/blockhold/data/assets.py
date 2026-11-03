# ─────────────────────────────────────────────────────────────────────────────
#  MAP ASSETS  (everything you can place in the map editor)
#
#  Each asset is built from simple low-poly shapes (see blockhold/lowpoly.py):
#    lp.box(centre, size, colour)              a box
#    lp.cylinder(base, radius, height, colour)  a post / trunk (top_radius=0 makes a cone)
#    lp.beam(a, b, radius, colour)              a stick between two points (branches, legs)
#    lp.blob(centre, radius, colour)            a lumpy ball (tree tops, bushes, rocks)
#    lp.prism(centre, width, depth, height, colour)   a gable roof
#    lp.blade(base, height, width, lean, colour)      a grass blade
#    lp.flat(centre, (w, d), colour)            a flat patch on the ground
#  Positions are in metres. (0, 0, 0) is the middle of the asset on the ground.
#  One map cell is 1 x 1 metre.
#
#  Fields:
#    name       shown in the editor
#    category   editor tab: trees, shrubs, buildings, props, town, military, farm, graveyard, special, mining
#    build      function(lp) that adds the shapes
#    solid      cells you can't walk through: (dx, dz, height) from the middle cell
#    nature     True = random turn, size and nudge when placed (looks natural)
#    variants   how many random versions to make (nature only)
#    editor_only  True = only visible in the editor (spawn markers)
#    spawn      'player' or 'zombie' = this asset is a spawn point
#    ore        an ore node grows here in game ('random' or a node type from resources.py)
#    station    'workbench' = players craft here (press E)
#    light      a light it gives off: dict(colour=(r, g, b), radius, strength, at=(x, y, z), flicker)
# ─────────────────────────────────────────────────────────────────────────────

BROWN = '#6b4528'
DARK_WOOD = '#4e3220'
LEAF = ['#4c8f3a', '#57a043', '#3f7d31']
PINE = ['#2f6b3a', '#357a42', '#3d8a4b']
STONE = ['#8a8a8a', '#7a7a7a', '#959595']


# ── trees ────────────────────────────────────────────────────────────────────
def pine(lp):
    lp.cylinder((0, 0, 0), 0.16, 1.1, BROWN, sides=6, top_radius=0.12)
    for (y, r, h), c in zip(((0.7, 1.3, 1.6), (1.6, 1.0, 1.4), (2.45, 0.7, 1.2)), PINE):
        lp.cylinder((0, y, 0), r, h, c, sides=7, top_radius=0)


def snowy_pine(lp):
    lp.cylinder((0, 0, 0), 0.16, 1.1, BROWN, sides=6, top_radius=0.12)
    for y, r, h in ((0.7, 1.3, 1.6), (1.6, 1.0, 1.4), (2.45, 0.7, 1.2)):
        lp.cylinder((0, y, 0), r, h * 0.55, PINE[0], sides=7, top_radius=r * 0.45, cap=False)
        lp.cylinder((0, y + h * 0.55, 0), r * 0.45, h * 0.45, '#eef4f7', sides=7, top_radius=0)


def oak(lp, leaves=LEAF):
    lp.cylinder((0, 0, 0), 0.24, 1.9, BROWN, sides=6, top_radius=0.16)
    lp.beam((0, 1.5, 0), (0.7, 2.2, 0.2), 0.09, BROWN, end_radius=0.05)
    lp.beam((0, 1.6, 0), (-0.6, 2.3, -0.3), 0.09, BROWN, end_radius=0.05)
    lp.blob((0, 2.7, 0), 1.35, leaves[0], squash=(1, 0.85, 1), colours=leaves)
    lp.blob((0.75, 2.3, 0.35), 0.85, leaves[1], colours=leaves)
    lp.blob((-0.65, 2.4, -0.4), 0.85, leaves[2], colours=leaves)


def autumn_tree(lp):
    oak(lp, ['#d9822b', '#c9542b', '#e0a93a'])


def birch(lp):
    lp.cylinder((0, 0, 0), 0.13, 2.8, '#e8e4d8', sides=6, top_radius=0.09)
    for y in (0.4, 0.9, 1.5, 2.0, 2.4):
        lp.box((0.11, y, 0.02), (0.06, 0.07, 0.12), '#2a2a2a')
    lp.blob((0, 2.8, 0), 0.85, '#8cc63f', colours=['#8cc63f', '#9ed04a', '#7db535'])
    lp.blob((0.3, 3.4, 0.1), 0.6, '#9ed04a', colours=['#8cc63f', '#9ed04a'])


def dead_tree(lp):
    c = '#5a4a3a'
    lp.beam((0, 0, 0), (0.1, 2.5, 0), 0.2, c, sides=6, end_radius=0.07)
    lp.beam((0.04, 1.3, 0), (0.85, 2.2, 0.2), 0.08, c, end_radius=0.02)
    lp.beam((0.06, 1.8, 0), (-0.7, 2.6, -0.3), 0.07, c, end_radius=0.02)
    lp.beam((0.08, 2.1, 0), (0.25, 3.0, 0.6), 0.06, c, end_radius=0.02)


def stump(lp):
    lp.cylinder((0, 0, 0), 0.36, 0.45, BROWN, sides=8, top_colour='#c9a26b')
    for a, b in (((0.3, 0.1, 0), (0.6, 0, 0.1)), ((-0.25, 0.1, 0.15), (-0.5, 0, 0.35)), ((0, 0.1, -0.3), (0.1, 0, -0.6))):
        lp.beam(a, b, 0.08, BROWN, end_radius=0.04)


# ── shrubs & small nature ────────────────────────────────────────────────────
def bush(lp):
    lp.blob((0, 0.45, 0), 0.55, LEAF[0], colours=LEAF)
    lp.blob((0.38, 0.32, 0.15), 0.4, LEAF[1], colours=LEAF)
    lp.blob((-0.32, 0.3, -0.2), 0.42, LEAF[2], colours=LEAF)


def flower_bush(lp):
    bush(lp)
    for _ in range(12):
        a = lp.rnd.random() * 6.28
        y = 0.3 + lp.rnd.random() * 0.55
        import math
        r = 0.5 if y < 0.6 else 0.35
        lp.blob((math.cos(a) * r, y, math.sin(a) * r), 0.07, lp.rnd.choice(['#e8414f', '#ffffff', '#f2d23a', '#e87fb0']),
                detail=0, jitter=0.1)


def tall_grass(lp):
    for _ in range(16):
        x, z = (lp.rnd.random() - 0.5) * 0.9, (lp.rnd.random() - 0.5) * 0.9
        lp.blade((x, 0, z), 0.4 + lp.rnd.random() * 0.45, 0.05, 0.15, lp.rnd.choice(['#5c9e3a', '#6db04a', '#4f8a32']),
                 yaw=lp.rnd.random() * 360)


def fern(lp):
    for i in range(9):
        lp.blade((0, 0, 0), 0.45 + lp.rnd.random() * 0.2, 0.09, 0.5, lp.rnd.choice(['#3f7d31', '#4c8f3a']), yaw=i * 40)


def flowers(lp):
    for _ in range(11):
        x, z = (lp.rnd.random() - 0.5) * 0.8, (lp.rnd.random() - 0.5) * 0.8
        h = 0.2 + lp.rnd.random() * 0.25
        lp.blade((x, 0, z), h, 0.015, 0.0, '#4f8a32', yaw=lp.rnd.random() * 360)
        lp.blob((x, h, z), 0.07, lp.rnd.choice(['#e8414f', '#f2d23a', '#ffffff', '#b768d6']), detail=0, jitter=0.1)


def mushrooms(lp):
    for x, z, s in ((0, 0, 1), (0.25, 0.15, 0.7), (-0.2, 0.2, 0.55)):
        lp.cylinder((x, 0, z), 0.05 * s, 0.22 * s, '#efe6d6', sides=5)
        lp.cylinder((x, 0.2 * s, z), 0.17 * s, 0.13 * s, '#c8322b', sides=7, top_radius=0)


def rock(lp):
    lp.blob((0, 0.15, 0), 0.35, STONE[0], squash=(1.25, 0.7, 1), jitter=0.25, detail=0, colours=STONE)


def boulder(lp):
    lp.blob((0, 0.55, 0), 1.0, STONE[0], squash=(1.2, 0.8, 1.05), jitter=0.2, colours=STONE)


def hedge(lp):
    lp.box((0, 0.5, 0), (1.0, 1.0, 1.0), '#3f7d31', top='#4c8f3a')


# ── buildings ────────────────────────────────────────────────────────────────
def house(lp):
    wall, wood, roof = '#d9c9a3', DARK_WOOD, '#a8432f'
    lp.flat((0, 0, 0), (7, 7), '#8a6a48', 0.03)
    lp.box((0, 1.4, -3), (7, 2.8, 1), wall)
    lp.box((-3, 1.4, 0), (1, 2.8, 5), wall)
    lp.box((3, 1.4, 0), (1, 2.8, 5), wall)
    lp.box((-2, 1.4, 3), (3, 2.8, 1), wall)
    lp.box((2, 1.4, 3), (3, 2.8, 1), wall)
    lp.box((0, 2.4, 3), (1, 0.8, 1), wall)
    for x, z in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        lp.box((x, 1.42, z), (1.06, 2.84, 1.06), wood)
    for x in (-3.53, 3.53):                       # side windows
        lp.box((x, 1.5, 0), (0.06, 0.9, 1.3), '#e9e2d0')
        lp.box((x * 1.002, 1.5, 0), (0.07, 0.75, 1.1), '#2b3a4a')
    lp.box((0, 1.5, -3.53), (1.3, 0.9, 0.06), '#e9e2d0')
    lp.box((0, 1.5, -3.54), (1.1, 0.75, 0.07), '#2b3a4a')
    lp.prism((0, 2.8, 0), 8.2, 8.2, 2.0, roof, gable=wall)
    lp.box((2, 4.1, -1.6), (0.7, 1.8, 0.7), '#7d7d80')


def cabin(lp):
    wall, roof = '#7a5230', '#4a3b2f'
    lp.flat((0, 0, 0), (5, 5), '#8a6a48', 0.03)
    for centre, size in (((0, 1.2, -2), (5, 2.4, 1)), ((-2, 1.2, 0), (1, 2.4, 3)), ((2, 1.2, 0), (1, 2.4, 3)),
                         ((-1.5, 1.2, 2), (2, 2.4, 1)), ((1.5, 1.2, 2), (2, 2.4, 1)), ((0, 2.1, 2), (1, 0.6, 1))):
        lp.box(centre, size, wall)
    for y in (0.5, 1.1, 1.7):                    # log lines
        lp.box((0, y, -2.52), (5.02, 0.08, 0.04), DARK_WOOD)
        lp.box((-2.52, y, 0), (0.04, 0.08, 5.02), DARK_WOOD)
        lp.box((2.52, y, 0), (0.04, 0.08, 5.02), DARK_WOOD)
    lp.box((2.53, 1.3, 0), (0.06, 0.7, 0.9), '#2b3a4a')
    lp.prism((0, 2.4, 0), 6.0, 6.0, 1.6, roof, gable=wall)


def ruin(lp):
    heights = {(-3, -3): 2.6, (-2, -3): 2.2, (-1, -3): 1.4, (1, -3): 0.8, (2, -3): 2.0, (3, -3): 2.8,
               (-3, -2): 2.4, (-3, -1): 1.6, (-3, 1): 1.0, (-3, 2): 2.0, (-3, 3): 2.6, (3, -2): 2.2,
               (3, -1): 2.6, (3, 0): 1.2, (3, 2): 0.7, (3, 3): 1.8, (-2, 3): 1.6, (2, 3): 2.2}
    for (x, z), h in heights.items():
        lp.box((x, h / 2, z), (1, h, 1), lp.rnd.choice(['#8f8f8a', '#858580', '#9a9a95']), top='#a3a39d')
    for _ in range(9):
        x, z = (lp.rnd.random() - 0.5) * 5, (lp.rnd.random() - 0.5) * 5
        s = 0.2 + lp.rnd.random() * 0.35
        lp.box((x, s / 2, z), (s, s, s), '#8f8f8a', yaw=lp.rnd.random() * 90)


RUIN_SOLID = [(x, z, 3 if h > 1.5 else 2 if h > 0.9 else 1) for (x, z), h in {
    (-3, -3): 2.6, (-2, -3): 2.2, (-1, -3): 1.4, (1, -3): 0.8, (2, -3): 2.0, (3, -3): 2.8, (-3, -2): 2.4,
    (-3, -1): 1.6, (-3, 1): 1.0, (-3, 2): 2.0, (-3, 3): 2.6, (3, -2): 2.2, (3, -1): 2.6, (3, 0): 1.2,
    (3, 2): 0.7, (3, 3): 1.8, (-2, 3): 1.6, (2, 3): 2.2}.items()]


def tower(lp):
    wood = '#6b4a2b'
    for x, z in ((-1.1, -1.1), (1.1, -1.1), (-1.1, 1.1), (1.1, 1.1)):
        lp.beam((x * 1.05, 0, z * 1.05), (x, 3.6, z), 0.16, wood, end_radius=0.13)
    for y in (1.2, 2.4):
        lp.beam((-1.1, y, -1.1), (1.1, y + 0.6, -1.1), 0.06, DARK_WOOD)
        lp.beam((1.1, y, 1.1), (-1.1, y + 0.6, 1.1), 0.06, DARK_WOOD)
    lp.box((0, 3.65, 0), (3.2, 0.25, 3.2), '#8a6038')
    for x, z, sx, sz in ((0, -1.5, 3.2, 0.1), (0, 1.5, 3.2, 0.1), (-1.5, 0, 0.1, 3.2), (1.5, 0, 0.1, 3.2)):
        lp.box((x, 4.15, z), (sx, 0.7, sz), '#8a6038')
    for x, z in ((-1.5, -1.5), (1.5, -1.5), (-1.5, 1.5), (1.5, 1.5)):
        lp.beam((x, 3.7, z), (x, 5.2, z), 0.07, wood)
    lp.cylinder((0, 5.2, 0), 2.4, 1.3, '#a8432f', sides=4, top_radius=0)


def market_stall(lp):
    for x in (-1.4, 1.4):
        for z in (-0.45, 0.45):
            lp.beam((x, 0, z), (x, 2.2, z), 0.06, DARK_WOOD)
    lp.box((0, 0.5, 0.3), (3, 1.0, 0.5), '#8a6038', top='#a87848')
    for i in range(6):
        lp.box((-1.25 + i * 0.5, 2.3, 0), (0.5, 0.1, 1.4), '#c8322b' if i % 2 == 0 else '#f0ebe0')
    for x in (-0.9, -0.3, 0.4, 1.0):
        lp.blob((x, 1.1, 0.3), 0.14, lp.rnd.choice(['#e8414f', '#f2d23a', '#7dbf3f', '#e08a2b']), detail=0)


def well(lp):
    lp.cylinder((0, 0, 0), 0.8, 0.8, '#8f8f8a', sides=8, top_colour='#22262d')
    for x in (-0.7, 0.7):
        lp.beam((x, 0.8, 0), (x, 2.0, 0), 0.06, DARK_WOOD)
    lp.beam((-0.7, 1.7, 0), (0.7, 1.7, 0), 0.05, DARK_WOOD)
    lp.prism((0, 2.0, 0), 1.0, 1.9, 0.6, '#a8432f', yaw=90)


def stone_wall(lp):
    lp.box((0, 0.8, 0), (1.0, 1.6, 0.8), '#8f8f8a', top='#a3a39d')
    for x in (-0.25, 0.25):
        lp.box((x, 1.7, 0), (0.45, 0.2 + lp.rnd.random() * 0.15, 0.7), '#858580')


def fence(lp):
    for x in (-0.45, 0.45):
        lp.box((x, 0.5, 0), (0.12, 1.0, 0.12), '#8a6038')
    for y in (0.35, 0.75):
        lp.box((0, y, 0), (1.0, 0.1, 0.06), '#a87848')


def _bag_rows(lp, width, rows):
    """Rows of stacked sandbags, each row sitting on the one below, joints staggered."""
    tones = ['#b8a272', '#a8946a', '#c2ad7e']
    n = max(2, round(width / 0.36))
    for row in range(rows):
        y = 0.1 + row * 0.19
        k = n - (row % 2)
        x0 = -(k - 1) * 0.36 / 2
        for i in range(k):
            x = x0 + i * 0.36 + (lp.rnd.random() - 0.5) * 0.02
            c = lp.rnd.choice(tones)
            lp.box((x, y, 0), (0.34, 0.18, 0.5), c, yaw=(lp.rnd.random() - 0.5) * 6)
            lp.box((x, y + 0.095, 0), (0.28, 0.025, 0.42), c)          # the rounded top of the bag


def sandbags(lp):
    _bag_rows(lp, 1.0, 4)

def tent(lp):
    lp.prism((0, 0, 0), 2.6, 2.8, 1.7, '#c9b98a', gable='#b5a577')
    lp.box((0, 0.5, 1.41), (0.8, 0.9, 0.02), '#3a3226')


# ── props ────────────────────────────────────────────────────────────────────
def crate(lp):
    lp.box((0, 0.45, 0), (0.9, 0.9, 0.9), '#b08850', top='#c49a60')
    for y in (0.06, 0.84):
        lp.box((0, y, 0), (0.92, 0.1, 0.92), '#7a5a34')


def barrel(lp):
    lp.cylinder((0, 0, 0), 0.38, 0.95, '#8a5a2b', sides=8, top_colour='#6b4528')
    for y in (0.15, 0.75):
        lp.cylinder((0, y, 0), 0.4, 0.07, '#3a3a40', sides=8)


def hay_bale(lp):
    lp.box((0, 0.32, 0), (1.0, 0.64, 0.7), '#d9b84a', top='#e6c95a')


def log_pile(lp):
    for (x, y) in ((-0.25, 0.18), (0.2, 0.18), (0, 0.5)):
        lp.beam((-0.55, y, x), (0.55, y, x), 0.18, BROWN, sides=6)


def lamp_post(lp):
    lp.beam((0, 0, 0), (0, 3.0, 0), 0.07, '#2a2a30', sides=5)
    lp.beam((0, 2.9, 0), (0.45, 2.95, 0), 0.04, '#2a2a30', sides=4)
    lp.emissive = True
    lp.box((0.45, 2.75, 0), (0.3, 0.35, 0.3), '#ffe9a8')
    lp.emissive = False
    lp.box((0.45, 2.96, 0), (0.36, 0.08, 0.36), '#2a2a30')


def bench(lp):
    lp.box((0, 0.45, 0), (1.4, 0.08, 0.42), '#8a6038')
    lp.box((0, 0.8, -0.2), (1.4, 0.3, 0.06), '#8a6038')
    for x in (-0.6, 0.6):
        lp.box((x, 0.22, 0), (0.08, 0.45, 0.4), '#2a2a30')


def campfire(lp):
    import math
    for i in range(8):
        a = i / 8 * math.tau
        lp.blob((math.cos(a) * 0.45, 0.08, math.sin(a) * 0.45), 0.12, STONE[0], detail=0, colours=STONE)
    lp.beam((-0.35, 0.08, -0.2), (0.35, 0.2, 0.2), 0.07, BROWN)
    lp.beam((0.35, 0.08, -0.2), (-0.35, 0.2, 0.2), 0.07, BROWN)
    lp.emissive = True
    lp.cylinder((0, 0.1, 0), 0.25, 0.65, '#ff8c2a', sides=5, top_radius=0)
    lp.cylinder((0.05, 0.1, 0.03), 0.13, 0.45, '#ffd84a', sides=5, top_radius=0)
    lp.emissive = False


def car_wreck(lp):
    body, rust = '#8a3b2a', '#6e2e22'
    lp.box((0, 0.6, 0), (2.8, 0.65, 1.35), body, top=rust)
    lp.box((-0.2, 1.17, 0), (1.4, 0.5, 1.25), body)
    lp.box((0.51, 1.17, 0), (0.02, 0.4, 1.1), '#2b3a4a')
    lp.box((-0.91, 1.17, 0), (0.02, 0.4, 1.1), '#2b3a4a')
    for x in (-0.9, 0.9):
        for z in (-0.68, 0.68):
            lp.beam((x, 0.3, z - 0.1), (x, 0.3, z + 0.1), 0.3, '#1f1f22', sides=7)
    lp.box((1.42, 0.62, 0), (0.06, 0.25, 1.2), '#9aa0a8')


def signpost(lp):
    lp.beam((0, 0, 0), (0, 2.0, 0), 0.07, '#6b4a2b')
    lp.box((0.35, 1.7, 0), (0.8, 0.3, 0.06), '#a87848')
    lp.box((-0.3, 1.3, 0), (0.7, 0.26, 0.06), '#a87848')


def rubble(lp):
    for _ in range(10):
        x, z = (lp.rnd.random() - 0.5) * 1.1, (lp.rnd.random() - 0.5) * 1.1
        s = 0.12 + lp.rnd.random() * 0.25
        lp.box((x, s / 2, z), (s, s, s), lp.rnd.choice(STONE), yaw=lp.rnd.random() * 90)


# ── special ──────────────────────────────────────────────────────────────────
def zombie_grave(lp):
    lp.blob((0, 0.0, 0.1), 0.6, '#5a3f2a', squash=(0.9, 0.35, 1.4), detail=1, jitter=0.1)
    lp.box((0, 0.42, -0.65), (0.6, 0.84, 0.16), '#9a9a98', top='#aaaaa8')
    lp.box((0, 0.55, -0.56), (0.3, 0.06, 0.02), '#6a6a68')


def player_spawn(lp):
    lp.cylinder((0, 0, 0), 0.5, 0.06, '#1197b0', sides=10)
    lp.beam((0, 0, 0), (0, 2.2, 0), 0.05, '#f5f4f2')
    lp.tri((0, 2.2, 0), (0, 1.6, 0), (0.8, 1.9, 0), '#1197b0', (0.3, 1.9, 1))
    lp.tri((0, 2.2, 0), (0, 1.6, 0), (0.8, 1.9, 0), '#1197b0', (0.3, 1.9, -1))


# ── mining and crafting ──────────────────────────────────────────────────────
def workbench(lp):
    top, dark, metal = '#8a5a32', '#5e3b1f', '#5b6067'
    for x in (-0.9, 0.9):
        for z in (-0.36, 0.36):
            lp.box((x, 0.42, z), (0.1, 0.84, 0.1), dark)
    lp.box((0, 0.25, 0), (1.8, 0.06, 0.72), dark)                       # lower shelf
    lp.box((0, 0.88, 0), (2.0, 0.08, 0.9), top, top='#9c6b3f')          # table top
    for x in (-0.97, 0.97):                                              # back board posts
        lp.box((x, 1.3, -0.42), (0.08, 1.0, 0.08), dark)
    lp.box((0, 1.38, -0.43), (1.86, 0.78, 0.04), '#7a4e2b')
    lp.box((-0.62, 1.42, -0.39), (0.05, 0.36, 0.03), metal)              # hanging wrench
    lp.box((-0.62, 1.62, -0.39), (0.16, 0.06, 0.03), metal)
    lp.box((-0.3, 1.36, -0.39), (0.05, 0.38, 0.03), '#a87848')           # hammer
    lp.box((-0.3, 1.57, -0.38), (0.2, 0.08, 0.06), metal)
    lp.box((0.25, 1.42, -0.39), (0.5, 0.17, 0.02), '#aab1b9')            # saw
    lp.box((0.56, 1.42, -0.38), (0.12, 0.16, 0.04), '#a8242e')
    lp.box((0.25, 1.55, -0.39), (0.5, 0.02, 0.03), '#5b6067')
    lp.box((-0.65, 0.97, 0.08), (0.3, 0.1, 0.2), '#3a3d42')              # anvil
    lp.box((-0.65, 1.07, 0.08), (0.44, 0.1, 0.24), '#4a4e55')
    lp.beam((-0.43, 1.08, 0.08), (-0.27, 1.08, 0.08), 0.05, '#4a4e55', sides=5, end_radius=0.0)
    lp.box((0.78, 0.99, 0.3), (0.22, 0.14, 0.2), '#2f5d8a')              # vise
    lp.box((0.78, 1.0, 0.45), (0.04, 0.04, 0.18), metal)
    lp.box((0.1, 0.95, 0.12), (0.72, 0.05, 0.08), '#26282d', yaw=12)     # a rifle being built
    lp.box((-0.2, 0.95, 0.19), (0.26, 0.07, 0.09), '#7a4a26', yaw=12)
    lp.box((0.08, 0.92, 0.12), (0.05, 0.1, 0.05), '#26282d', yaw=12)
    lp.box((0.42, 0.4, 0.05), (0.42, 0.24, 0.42), '#a87848')             # crate of ore under the table
    lp.box((-0.88, 1.84, -0.42), (0.12, 0.06, 0.12), '#2a2a30')          # a lantern on the back board
    lp.emissive = True
    lp.box((-0.88, 1.68, -0.42), (0.1, 0.16, 0.1), '#ffc46b')
    lp.emissive = False
    for i, c in enumerate(('#c3cfdb', '#e0813a', '#a3a39f', '#c07bff')):
        lp.blob((0.3 + (i % 2) * 0.22, 0.56, -0.05 + (i // 2) * 0.2), 0.08, c, jitter=0.3, detail=0)



# ── more nature ──────────────────────────────────────────────────────────────
def fallen_log(lp):
    lp.beam((-1.3, 0.26, 0), (1.3, 0.24, 0.05), 0.26, BROWN, sides=7)
    lp.beam((0.3, 0.4, 0.1), (0.7, 0.85, 0.35), 0.05, BROWN, end_radius=0.02)
    lp.blob((-0.6, 0.5, 0.1), 0.18, '#4c8f3a', detail=0)                 # moss


def dead_bush(lp):
    import math
    for i in range(7):
        a = i / 7 * math.tau + lp.rnd.random() * 0.5
        lp.beam((0, 0, 0), (math.cos(a) * 0.5, 0.5 + lp.rnd.random() * 0.4, math.sin(a) * 0.5), 0.03, '#6b5a44',
                end_radius=0.01)


# ── town ─────────────────────────────────────────────────────────────────────
GLASS = '#2b3a4a'
TYRE = '#1f1f22'


def _wheels(lp, xs, z, r=0.3, y=None):
    for x in xs:
        for sz in (-z, z):
            lp.beam((x, y or r, sz - 0.1), (x, y or r, sz + 0.1), r, TYRE, sides=7)


def pickup_truck(lp):
    body = lp.rnd.choice(['#3f5e7a', '#6b7a3a', '#8a8a86'])
    lp.box((0, 0.65, 0), (3.0, 0.6, 1.45), body)
    lp.box((0.35, 1.2, 0), (1.0, 0.55, 1.35), body)
    lp.box((0.86, 1.2, 0), (0.02, 0.42, 1.2), GLASS)
    lp.box((0.35, 1.2, 0.68), (0.8, 0.4, 0.02), GLASS)
    lp.box((0.35, 1.2, -0.68), (0.8, 0.4, 0.02), GLASS)
    lp.box((-0.9, 0.98, 0), (1.15, 0.06, 1.35), '#3a3a3c')               # bed floor
    lp.box((1.52, 0.62, 0), (0.06, 0.3, 1.3), '#9aa0a8')                 # grille
    lp.box((-0.9, 1.05, 0.2), (0.6, 0.3, 0.5), '#b08850')                # a crate in the back
    _wheels(lp, (-0.95, 0.95), 0.7, 0.32)


def bus_wreck(lp):
    yellow, dark = '#d9a521', '#a87d18'
    lp.box((0, 1.25, 0), (7.2, 2.0, 1.75), yellow, top='#c9c9c4')
    lp.box((0, 0.5, 0), (7.22, 0.12, 1.77), '#2a2a30')
    lp.box((0, 1.0, 0.885), (7.0, 0.08, 0.01), '#2a2a30')
    lp.box((0, 1.0, -0.885), (7.0, 0.08, 0.01), '#2a2a30')
    for i in range(8):                                                   # windows (some smashed)
        x = -2.9 + i * 0.75
        c = GLASS if lp.rnd.random() > 0.3 else '#151a20'
        lp.box((x, 1.75, 0.885), (0.6, 0.55, 0.02), c)
        lp.box((x, 1.75, -0.885), (0.6, 0.55, 0.02), c)
    lp.box((3.61, 1.7, 0), (0.02, 0.7, 1.5), GLASS)
    lp.box((3.62, 0.85, 0), (0.06, 0.35, 1.5), '#2a2a30')
    lp.box((-3.61, 1.3, 0), (0.02, 1.2, 1.4), dark)
    _wheels(lp, (-2.6, 2.4), 0.8, 0.42)


def traffic_cone(lp):
    lp.box((0, 0.02, 0), (0.42, 0.04, 0.42), '#2a2a30')
    lp.cylinder((0, 0.04, 0), 0.17, 0.62, '#ff6a1a', sides=8, top_radius=0.03)
    lp.cylinder((0, 0.3, 0), 0.115, 0.1, '#f5f4f2', sides=8, top_radius=0.1, cap=False)


def road_barrier(lp):
    concrete = '#b9b7b0'
    lp.box((0, 0.12, 0), (1.0, 0.24, 0.6), concrete)
    lp.box((0, 0.5, 0), (1.0, 0.55, 0.26), concrete, top='#c9c7c0')
    lp.box((0, 0.6, 0.135), (0.5, 0.1, 0.01), '#d64541')
    lp.box((0, 0.6, -0.135), (0.5, 0.1, 0.01), '#d64541')


def stop_sign(lp):
    lp.beam((0, 0, 0), (0, 2.2, 0), 0.04, '#8a8f96', sides=5)
    lp.beam((0, 2.0, 0.04), (0, 2.0, 0.08), 0.32, '#c62f2a', sides=8)
    lp.box((0, 2.0, 0.085), (0.38, 0.08, 0.005), '#f5f4f2')


def fire_hydrant(lp):
    red = '#c62f2a'
    lp.cylinder((0, 0, 0), 0.16, 0.06, red, sides=8)
    lp.cylinder((0, 0.06, 0), 0.12, 0.55, red, sides=8)
    lp.cylinder((0, 0.61, 0), 0.13, 0.12, red, sides=8, top_radius=0.06)
    lp.beam((-0.2, 0.42, 0), (0.2, 0.42, 0), 0.05, red, sides=6)
    lp.beam((0, 0.4, 0), (0, 0.4, 0.2), 0.06, '#d9a521', sides=6)


def mailbox(lp):
    lp.beam((0, 0, 0), (0, 1.0, 0), 0.04, '#5e3b1f', sides=4)
    lp.box((0, 1.12, 0), (0.25, 0.25, 0.5), '#3f5e7a')
    lp.box((0.14, 1.25, -0.1), (0.02, 0.2, 0.05), '#c62f2a')


def phone_booth(lp):
    red = '#b8282a'
    lp.box((0, 0.05, 0), (1.0, 0.1, 1.0), red)
    for x, z in ((-0.45, -0.45), (0.45, -0.45), (-0.45, 0.45), (0.45, 0.45)):
        lp.box((x, 1.2, z), (0.1, 2.3, 0.1), red)
    for x, z, sx, sz in ((0, -0.45, 0.8, 0.04), (0, 0.45, 0.8, 0.04), (-0.45, 0, 0.04, 0.8), (0.45, 0, 0.04, 0.8)):
        lp.box((x, 1.3, z), (sx, 1.7, sz), '#3c5266')
        lp.box((x, 0.35, z), (sx, 0.5, sz), red)
    lp.box((0, 2.4, 0), (1.05, 0.2, 1.05), red)
    lp.emissive = True
    lp.box((0, 2.25, 0.5), (0.6, 0.1, 0.02), '#fff6d8')
    lp.emissive = False


def dumpster(lp):
    green = lp.rnd.choice(['#2f5d3a', '#3f5e7a'])
    lp.box((0, 0.6, 0), (1.7, 1.0, 1.05), green, top='#26402c')
    lp.box((0, 1.13, 0), (1.74, 0.06, 1.08), '#1f2a22')                               # lid, flush on top
    lp.box((0, 0.6, 0.53), (1.6, 0.08, 0.02), '#1f2a22')
    for x in (-0.7, 0.7):
        for z in (-0.4, 0.4):
            lp.cylinder((x, 0, z), 0.06, 0.1, TYRE, sides=6)


def trash_bags(lp):
    for i in range(3 + lp.rnd.randrange(3)):
        x, z = (lp.rnd.random() - 0.5) * 0.9, (lp.rnd.random() - 0.5) * 0.9
        lp.blob((x, 0.2, z), 0.24 + lp.rnd.random() * 0.08, lp.rnd.choice(['#1f1f22', '#2a2a30', '#3a3a3c']),
                squash=(1, 0.85, 1), detail=0, jitter=0.12)


def utility_pole(lp):
    wood = '#5a4330'
    lp.beam((0, 0, 0), (0, 6.5, 0), 0.13, wood, sides=6, end_radius=0.1)
    lp.box((0, 6.0, 0), (1.8, 0.12, 0.12), wood)
    for x in (-0.8, -0.3, 0.3, 0.8):
        lp.cylinder((x, 6.06, 0), 0.04, 0.16, '#6f8f9a', sides=5)
    lp.box((0.18, 5.1, 0), (0.3, 0.45, 0.3), '#8a8f96')                 # transformer
    for x in (-0.8, -0.3, 0.3, 0.8):                                      # cut wires hanging down
        lp.beam((x, 6.2, 0), (x + 0.05, 5.0 + lp.rnd.random(), 0.6), 0.008, '#1f1f22', sides=3)


def bus_stop(lp):
    metal, glass = '#5b6067', '#7e9aac'
    for x in (-1.4, 1.4):
        lp.box((x, 1.2, -0.5), (0.08, 2.4, 0.08), metal)
        lp.box((x, 1.2, 0.5), (0.08, 2.4, 0.08), metal)
    lp.box((0, 2.45, 0), (3.1, 0.1, 1.3), metal)
    lp.box((0, 1.3, -0.5), (2.8, 1.8, 0.03), glass)
    lp.box((-1.4, 1.3, 0), (0.03, 1.8, 0.9), glass)
    lp.box((0, 0.45, -0.3), (2.2, 0.06, 0.35), '#8a6038')
    lp.box((1.4, 1.5, 0.05), (0.05, 0.9, 0.6), '#d9a521')               # timetable


def gas_pump(lp):
    lp.box((0, 0.08, 0), (1.0, 0.16, 0.6), '#b9b7b0')
    lp.box((0, 0.95, 0), (0.7, 1.6, 0.45), '#c62f2a', top='#f5f4f2')
    lp.box((0, 1.25, 0.23), (0.5, 0.35, 0.02), '#1f2a22')
    lp.box((0, 0.65, 0.23), (0.5, 0.3, 0.02), '#f5f4f2')
    lp.beam((0.36, 1.2, 0.1), (0.5, 0.4, 0.3), 0.03, '#1f1f22', sides=4)
    lp.box((0.42, 1.35, 0.12), (0.08, 0.25, 0.12), '#2a2a30')


def billboard(lp):
    for x in (-1.4, 1.4):
        lp.beam((x, 0, 0), (x, 3.0, 0), 0.1, '#5b6067', sides=6)
    lp.box((0, 3.9, 0), (4.4, 2.0, 0.12), '#2a2a30')
    lp.box((0, 3.9, 0.07), (4.2, 1.8, 0.02), lp.rnd.choice(['#d9a521', '#1197b0', '#c62f2a']))
    lp.box((-0.8, 4.2, 0.085), (2.0, 0.35, 0.01), '#f5f4f2')
    lp.box((0.9, 3.5, 0.085), (1.6, 0.5, 0.01), '#12121c')
    lp.box((0, 2.85, 0.3), (4.2, 0.06, 0.5), '#5b6067')                   # catwalk


def vending_machine(lp):
    lp.box((0, 0.95, 0), (0.9, 1.9, 0.7), lp.rnd.choice(['#c62f2a', '#1f6fb0']))
    lp.box((-0.15, 1.15, 0.36), (0.5, 1.2, 0.02), '#151a20')
    lp.emissive = True
    for i in range(4):
        lp.box((-0.15, 0.7 + i * 0.28, 0.375), (0.42, 0.08, 0.01), '#ffd06b')
    lp.box((0.3, 1.4, 0.36), (0.14, 0.3, 0.01), '#9fe8ff')
    lp.emissive = False
    lp.box((0, 0.3, 0.36), (0.6, 0.18, 0.02), '#12121c')


def picnic_table(lp):
    wood = '#9c6b3f'
    lp.box((0, 0.75, 0), (1.8, 0.07, 0.8), wood)
    for z in (-0.62, 0.62):
        lp.box((0, 0.45, z), (1.8, 0.06, 0.3), wood)
    for x in (-0.7, 0.7):
        lp.beam((x, 0, -0.75), (x, 0.75, 0.0), 0.04, wood, sides=4)
        lp.beam((x, 0, 0.75), (x, 0.75, 0.0), 0.04, wood, sides=4)


# ── military ─────────────────────────────────────────────────────────────────
OLIVE_DRAB = '#4f5a35'


def shipping_container(lp):
    c = lp.rnd.choice(['#a8432f', '#2f5d8a', '#4f7a3a', '#c98a2b'])
    lp.box((0, 1.3, 0), (6.6, 2.6, 2.4), c, top='#7a7a74')
    for i in range(23):                                                   # ribs
        x = -3.1 + i * 0.28
        lp.box((x, 1.3, 1.21), (0.08, 2.4, 0.02), c)
        lp.box((x, 1.3, -1.21), (0.08, 2.4, 0.02), c)
    lp.box((3.31, 1.3, 0), (0.02, 2.5, 2.3), '#5b5e63')
    for z in (-0.4, 0.4):
        lp.box((3.33, 1.3, z), (0.03, 2.3, 0.04), '#8a8f96')
    lp.box((0, 2.0, 1.225), (1.6, 0.3, 0.01), '#f5f4f2')


def barbed_wire(lp):
    import math
    wood = '#6b5a44'
    for x in (-0.48, 0.48):
        lp.beam((x - 0.2, 0, -0.25), (x + 0.2, 0.9, 0.25), 0.04, wood, sides=4)
        lp.beam((x + 0.2, 0, -0.25), (x - 0.2, 0.9, 0.25), 0.04, wood, sides=4)
    pts = []
    for i in range(25):
        a = i / 24 * math.tau * 6
        pts.append((-0.5 + i / 24, 0.45 + math.sin(a) * 0.3, math.cos(a) * 0.3))
    for a, b in zip(pts, pts[1:]):
        lp.beam(a, b, 0.01, '#8a8f96', sides=3)


def tank_trap(lp):
    steel = '#3a3d42'
    lp.beam((-0.6, 0.0, -0.3), (0.6, 1.1, 0.3), 0.08, steel, sides=4)
    lp.beam((0.6, 0.0, -0.3), (-0.6, 1.1, 0.3), 0.08, steel, sides=4)
    lp.beam((0, 0.0, 0.65), (0, 1.1, -0.65), 0.08, steel, sides=4)


def ammo_crate(lp):
    lp.box((0, 0.25, 0), (0.95, 0.5, 0.55), OLIVE_DRAB, top='#5b6640')
    lp.box((0, 0.52, 0), (0.97, 0.05, 0.57), '#3f4829')
    lp.box((0, 0.3, 0.28), (0.4, 0.12, 0.01), '#d9c98a')
    for x in (-0.48, 0.48):
        lp.box((x, 0.32, 0), (0.03, 0.08, 0.25), '#2a2a30')


def fuel_drums(lp):
    for x, z, c in ((-0.25, -0.2, '#2f5d8a'), (0.25, -0.2, '#a8432f'), (0, 0.25, '#2f5d8a')):
        lp.cylinder((x, 0, z), 0.27, 0.85, c, sides=8, top_colour='#3a3a3c')
        for y in (0.28, 0.58):
            lp.cylinder((x, y, z), 0.28, 0.04, '#2a2a30', sides=8)


def generator(lp):
    lp.box((0, 0.1, 0), (1.3, 0.2, 0.8), '#2a2a30')
    lp.box((0, 0.55, 0), (1.2, 0.7, 0.7), '#d9a521', top='#e6b83a')
    lp.box((0.35, 0.6, 0.36), (0.35, 0.3, 0.02), '#1f2a22')
    lp.beam((-0.45, 0.9, -0.2), (-0.45, 1.35, -0.2), 0.05, '#3a3d42', sides=5)
    lp.cylinder((0.2, 0.9, -0.15), 0.12, 0.12, '#2a2a30', sides=6)


def radio_mast(lp):
    steel = '#8a8f96'
    import math
    for i in range(3):
        a = i / 3 * math.tau
        lp.beam((math.cos(a) * 0.5, 0, math.sin(a) * 0.5), (math.cos(a) * 0.12, 8.0, math.sin(a) * 0.12), 0.04, steel,
                sides=4)
    for y in range(1, 8):
        r = 0.5 - y * 0.05
        lp.cylinder((0, y, 0), r, 0.04, steel, sides=3, cap=False)
    lp.box((0.3, 5.5, 0), (0.12, 0.6, 0.4), '#5b6067')
    lp.emissive = True
    lp.blob((0, 8.1, 0), 0.12, '#ff3a2a', detail=0, jitter=0)
    lp.emissive = False


def helicopter_wreck(lp):
    body = OLIVE_DRAB
    lp.blob((0.6, 1.0, 0), 1.2, body, squash=(1.5, 0.85, 0.8), detail=1, jitter=0.05)
    lp.box((1.6, 1.15, 0), (0.6, 0.7, 1.3), '#2b3a4a')
    lp.beam((-0.5, 1.2, 0), (-4.0, 1.5, 0.3), 0.22, body, end_radius=0.1)       # tail boom (bent)
    lp.box((-4.0, 1.9, 0.3), (0.5, 1.0, 0.08), body)
    lp.cylinder((0.5, 1.9, 0), 0.15, 0.35, '#2a2a30', sides=6)
    for a, b in (((0.5, 2.3, 0), (3.5, 1.7, 1.5)), ((0.5, 2.3, 0), (-1.5, 2.0, 2.8)), ((0.5, 2.3, 0), (0.0, 0.1, -3.0))):
        lp.beam(a, b, 0.06, '#2a2a30', sides=4)
    lp.beam((-0.6, 0.06, -0.85), (1.6, 0.06, -0.85), 0.05, '#2a2a30', sides=4)
    lp.beam((-0.6, 0.06, 0.85), (1.6, 0.06, 0.85), 0.05, '#2a2a30', sides=4)
    lp.blob((-0.8, 0.3, 0.9), 0.4, '#3a3a3c', detail=0)                  # smoke-blackened debris


def floodlight(lp):
    import math
    for i in range(3):
        a = i / 3 * math.tau
        lp.beam((math.cos(a) * 0.45, 0, math.sin(a) * 0.45), (0, 2.0, 0), 0.03, '#3a3d42', sides=4)
    lp.box((0, 2.15, 0.05), (0.7, 0.45, 0.2), '#2a2a30')
    lp.emissive = True
    lp.box((0, 2.15, 0.16), (0.6, 0.36, 0.02), '#fffbe8')
    lp.emissive = False


def bunker(lp):
    concrete = '#8f8d86'
    lp.box((0, 1.0, -1), (3.0, 2.0, 1.0), concrete)
    lp.box((-1, 1.0, 0.5), (1.0, 2.0, 2.0), concrete)
    lp.box((1, 1.0, 0.5), (1.0, 2.0, 2.0), concrete)
    lp.box((0, 2.15, 0), (3.4, 0.3, 3.4), '#7a7872')
    lp.box((0, 1.5, -1.51), (1.8, 0.2, 0.02), '#151515')                  # gun slit
    for x in (-1.6, 1.6):
        lp.box((x, 0.35, 1.6), (0.5, 0.7, 0.5), '#b8a272')                 # sandbags by the door


def jerry_cans(lp):
    for i, x in enumerate((-0.18, 0.18)):
        c = ('#4f5a35', '#a8432f')[i]
        lp.box((x, 0.25, 0), (0.18, 0.5, 0.36), c)
        lp.box((x, 0.53, -0.08), (0.04, 0.06, 0.12), '#2a2a30')


# ── farm ─────────────────────────────────────────────────────────────────────
def barn(lp):
    red, white, roof = '#9c2f25', '#efe9dc', '#4a4a4c'
    lp.flat((0, 0, 0), (7, 7), '#8a6a48', 0.03)
    lp.box((0, 1.6, -3), (7, 3.2, 1), red)
    lp.box((-3, 1.6, 0), (1, 3.2, 5), red)
    lp.box((3, 1.6, 0), (1, 3.2, 5), red)
    lp.box((-2, 1.6, 3), (3, 3.2, 1), red)
    lp.box((2, 1.6, 3), (3, 3.2, 1), red)
    lp.box((0, 2.6, 3), (1, 1.2, 1), red)
    for x, z in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        lp.box((x, 1.62, z), (1.06, 3.24, 1.06), white)
    for x in (-1.2, 1.2):                                                   # big doors (open) with an X
        lp.box((x, 1.0, 3.55), (0.9, 2.0, 0.08), red)
        lp.beam((x - 0.4, 0.1, 3.6), (x + 0.4, 1.9, 3.6), 0.04, white, sides=4)
        lp.beam((x + 0.4, 0.1, 3.6), (x - 0.4, 1.9, 3.6), 0.04, white, sides=4)
    lp.prism((0, 3.2, 0), 8.0, 8.0, 3.0, roof, gable=red)
    lp.box((0, 4.3, 4.01), (1.0, 0.8, 0.02), '#2a2a30')                   # hay loft door


def silo(lp):
    lp.cylinder((0, 0, 0), 1.3, 7.0, '#b9bcc0', sides=12, top_colour='#9aa0a8')
    for y in (1.5, 3.0, 4.5, 6.0):
        lp.cylinder((0, y, 0), 1.32, 0.08, '#8a8f96', sides=12)
    lp.cylinder((0, 7.0, 0), 1.3, 1.2, '#8a8f96', sides=12, top_radius=0.15)
    lp.beam((1.32, 0, 0), (1.32, 7.0, 0), 0.03, '#5b6067', sides=4)        # ladder


def windmill(lp):
    import math
    steel = '#8a8f96'
    for x, z in ((-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7), (0.7, 0.7)):
        lp.beam((x, 0, z), (x * 0.15, 6.0, z * 0.15), 0.05, steel, sides=4)
    for y in (1.5, 3.0, 4.5):
        k = 1 - y / 6 * 0.85
        lp.cylinder((0, y, 0), 0.7 * k * 1.41, 0.04, steel, sides=4, cap=False)
    lp.box((0, 6.1, 0), (0.25, 0.25, 0.5), '#5b6067')
    for i in range(12):                                                    # the fan
        a = i / 12 * math.tau
        lp.beam((0, 6.1, 0.3), (math.cos(a) * 1.4, 6.1 + math.sin(a) * 1.4, 0.35), 0.06, '#c9c7c0', sides=3,
                end_radius=0.12)
    lp.box((0, 6.1, -0.9), (0.04, 0.7, 1.0), '#a8432f')                    # tail vane


def water_tower(lp):
    wood = '#6b4a2b'
    for x, z in ((-1.1, -1.1), (1.1, -1.1), (-1.1, 1.1), (1.1, 1.1)):
        lp.beam((x * 1.1, 0, z * 1.1), (x, 4.5, z), 0.12, wood)
    for y in (1.5, 3.0):
        lp.beam((-1.1, y, -1.1), (1.1, y + 0.8, 1.1), 0.05, wood)
        lp.beam((1.1, y, -1.1), (-1.1, y + 0.8, 1.1), 0.05, wood)
    lp.box((0, 4.55, 0), (2.8, 0.15, 2.8), '#8a6038')
    lp.cylinder((0, 4.6, 0), 1.45, 2.2, '#9c6b3f', sides=10)
    for y in (5.0, 5.8, 6.5):
        lp.cylinder((0, y, 0), 1.47, 0.08, '#2a2a30', sides=10)
    lp.cylinder((0, 6.8, 0), 1.55, 0.8, '#4a3b2f', sides=10, top_radius=0)


def scarecrow(lp):
    lp.beam((0, 0, 0), (0, 2.0, 0), 0.05, '#6b4a2b', sides=4)
    lp.beam((-0.75, 1.55, 0), (0.75, 1.55, 0), 0.04, '#6b4a2b', sides=4)
    lp.box((0, 1.35, 0), (0.5, 0.6, 0.25), '#7a5a9a')                    # shirt
    lp.box((-0.45, 1.52, 0), (0.45, 0.16, 0.18), '#7a5a9a')
    lp.box((0.45, 1.52, 0), (0.45, 0.16, 0.18), '#7a5a9a')
    lp.blob((0, 1.88, 0), 0.2, '#d9b84a', detail=0)                        # sack head
    lp.cylinder((0, 2.02, 0), 0.32, 0.03, '#8a6a3a', sides=8)              # hat
    lp.cylinder((0, 2.05, 0), 0.16, 0.18, '#8a6a3a', sides=8, top_radius=0.14)
    lp.box((0, 1.9, 0.19), (0.12, 0.03, 0.01), '#2a2a30')


def tractor(lp):
    red = '#b8282a'
    lp.box((0.5, 0.95, 0), (1.9, 0.75, 0.9), red, top='#c9332f')
    lp.box((-0.75, 1.5, 0), (0.9, 1.2, 1.0), red)
    lp.box((-0.75, 1.65, 0), (0.92, 0.65, 0.95), GLASS)
    lp.box((-0.75, 2.15, 0), (1.1, 0.08, 1.2), '#2a2a30')
    lp.beam((1.1, 1.3, 0.2), (1.1, 2.0, 0.2), 0.05, '#2a2a30', sides=5)     # exhaust
    for z in (-0.7, 0.7):
        lp.beam((-0.75, 0.62, z - 0.18), (-0.75, 0.62, z + 0.18), 0.62, TYRE, sides=9)
        lp.beam((-0.75, 0.62, z * 1.3), (-0.75, 0.62, z * 1.31), 0.3, '#d9a521', sides=9)
        lp.beam((1.15, 0.36, z - 0.1), (1.15, 0.36, z + 0.1), 0.36, TYRE, sides=8)


def wheelbarrow(lp):
    lp.box((0, 0.55, 0), (0.9, 0.3, 0.6), '#5b6067', top='#6b4a2b')
    lp.beam((0.55, 0.22, -0.05), (0.55, 0.22, 0.05), 0.22, TYRE, sides=7)
    for z in (-0.25, 0.25):
        lp.beam((0.5, 0.35, z * 0.5), (-0.9, 0.55, z), 0.03, '#6b4a2b', sides=4)
        lp.beam((-0.3, 0.0, z), (-0.3, 0.42, z), 0.03, '#5b6067', sides=4)


def outhouse(lp):
    wood = '#7a5230'
    lp.box((0, 1.1, 0), (1.1, 2.2, 1.1), wood, top='#5e3b1f')
    lp.box((0, 1.0, 0.56), (0.7, 1.9, 0.02), '#8a6038')
    lp.box((0, 1.65, 0.575), (0.14, 0.14, 0.01), '#2a2a30')               # the moon-shaped hole
    lp.prism((0, 2.2, 0), 1.3, 1.3, 0.35, '#4a3b2f', gable=wood)


def corn_crop(lp):
    for i in range(4):
        x = -0.36 + i * 0.24 + (lp.rnd.random() - 0.5) * 0.06
        h = 1.2 + lp.rnd.random() * 0.6
        lp.beam((x, 0, 0), (x, h, 0), 0.025, '#6f8f3a', sides=4)
        for k in range(3):
            y = 0.4 + k * 0.35
            lp.blade((x, y, 0), 0.5, 0.06, 0.8, '#7fa045', yaw=lp.rnd.random() * 360)
        lp.box((x + 0.04, h * 0.6, 0), (0.06, 0.2, 0.06), '#e0c35a')


def pumpkins(lp):
    for i in range(2 + lp.rnd.randrange(3)):
        x, z = (lp.rnd.random() - 0.5) * 0.9, (lp.rnd.random() - 0.5) * 0.9
        r = 0.16 + lp.rnd.random() * 0.12
        lp.blob((x, r * 0.8, z), r, '#e07a1f', squash=(1, 0.8, 1), detail=0, jitter=0.05)
        lp.beam((x, r * 1.5, z), (x + 0.03, r * 1.5 + 0.1, z), 0.025, '#4c6b2a', sides=4)


def picket_fence(lp):
    white = '#efe9dc'
    for i in range(5):
        x = -0.4 + i * 0.2
        lp.box((x, 0.45, 0), (0.1, 0.9, 0.04), white)
        lp.cylinder((x, 0.9, 0), 0.05, 0.1, white, sides=4, top_radius=0)
    for y in (0.3, 0.65):
        lp.box((0, y, -0.04), (1.0, 0.07, 0.03), white)


# ── graveyard ────────────────────────────────────────────────────────────────
def gravestone(lp):
    stone = lp.rnd.choice(['#8a8a88', '#9a9a98', '#7a7c80'])
    kind = lp.rnd.randrange(3)
    lp.flat((0, 0, 0.55), (0.7, 1.2), '#5a4a38', 0.02)                                # the grave in front of it
    lp.box((0, 0.05, 0.55), (0.55, 0.1, 1.0), '#5f4c38')
    if kind == 0:
        lp.box((0, 0.42, -0.1), (0.55, 0.84, 0.14), stone)
        lp.box((0, 0.9, -0.1), (0.4, 0.12, 0.14), stone)
    elif kind == 1:
        lp.box((0, 0.5, -0.1), (0.14, 1.0, 0.12), stone)
        lp.box((0, 0.72, -0.1), (0.55, 0.13, 0.12), stone)
    else:
        lp.box((0, 0.3, -0.1), (0.6, 0.6, 0.2), stone, top='#a8a8a6')
        lp.box((0.05, 0.33, -0.1), (0.62, 0.5, 0.18), stone, yaw=8)
    lp.box((0, 0.55, -0.02), (0.3, 0.04, 0.01), '#5a5a58')


def stone_cross(lp):
    stone = '#8f8f8c'
    lp.box((0, 0.15, 0), (0.6, 0.3, 0.5), stone)
    lp.box((0, 1.1, 0), (0.2, 1.7, 0.18), stone)
    lp.box((0, 1.5, 0), (0.85, 0.2, 0.18), stone)


def iron_fence(lp):
    iron = '#26282d'
    for i in range(6):
        x = -0.42 + i * 0.168
        lp.beam((x, 0, 0), (x, 1.3, 0), 0.02, iron, sides=4)
        lp.cylinder((x, 1.3, 0), 0.04, 0.12, iron, sides=4, top_radius=0)
    for y in (0.2, 1.1):
        lp.box((0, y, 0), (1.0, 0.05, 0.04), iron)
    lp.box((0.5, 0.7, 0), (0.09, 1.4, 0.09), '#7a7c80')


def crypt(lp):
    stone, dark = '#8f8d86', '#6f6d68'
    lp.box((0, 0.1, 0), (3.2, 0.2, 3.4), dark)
    lp.box((0, 1.4, -0.4), (2.8, 2.4, 2.4), stone)
    for x in (-1.15, 1.15):
        lp.cylinder((x, 0.2, 1.2), 0.17, 2.4, '#a5a39c', sides=8)
    lp.box((0, 1.1, 0.81), (1.0, 1.8, 0.02), '#2a2622')                   # door
    lp.prism((0, 2.6, 0), 3.2, 3.4, 0.9, dark, gable=stone)
    lp.box((0, 3.6, 1.6), (0.12, 0.5, 0.1), stone)
    lp.box((0, 3.68, 1.6), (0.35, 0.1, 0.1), stone)


def coffin(lp):
    wood = '#4e3220'
    lp.box((0, 0.2, 0), (0.7, 0.4, 1.9), wood, top='#2a1d12')
    lp.box((0, 0.36, 0), (0.6, 0.02, 1.8), '#1a120b')                                 # dark inside
    lp.box((0.78, 0.04, 0.12), (0.72, 0.08, 1.92), '#5e3b1f', yaw=9)                  # lid knocked off beside it
    lp.box((0.78, 0.085, 0.12), (0.4, 0.01, 0.1), '#c9a227', yaw=9)

def grave_lantern(lp):
    lp.beam((0, 0, 0), (0, 1.3, 0), 0.05, '#26282d', sides=4)
    lp.beam((0, 1.3, 0), (0.3, 1.35, 0), 0.03, '#26282d', sides=4)
    lp.box((0.3, 1.12, 0), (0.18, 0.26, 0.18), '#26282d')
    lp.emissive = True
    lp.box((0.3, 1.1, 0), (0.14, 0.18, 0.14), '#ffb85a')
    lp.emissive = False


def church(lp):
    wall, roof = '#b8b2a4', '#4a4a4c'
    lp.flat((0, 0, 0), (7, 9), '#7a7872', 0.03)
    lp.box((0, 2.0, -4), (7, 4.0, 1), wall)
    lp.box((-3, 2.0, 0), (1, 4.0, 7), wall)
    lp.box((3, 2.0, 0), (1, 4.0, 7), wall)
    lp.box((-2, 2.0, 4), (3, 4.0, 1), wall)
    lp.box((2, 2.0, 4), (3, 4.0, 1), wall)
    lp.box((0, 3.3, 4), (1, 1.4, 1), wall)
    for z in (-2, 0, 2):                                                     # tall windows
        for x in (-3.52, 3.52):
            lp.box((x, 2.4, z), (0.05, 1.8, 0.6), '#5a3b6b')
    lp.prism((0, 4.0, 0), 8.0, 10.0, 3.0, roof, gable=wall)
    lp.box((0, 5.5, 4.0), (1.6, 3.0, 1.6), wall)                             # bell tower
    lp.cylinder((0, 7.0, 4.0), 1.2, 2.2, roof, sides=4, top_radius=0)
    lp.box((0, 9.4, 4.0), (0.1, 0.6, 0.1), '#c9a227')
    lp.box((0, 9.5, 4.0), (0.35, 0.1, 0.1), '#c9a227')


# ── caves ────────────────────────────────────────────────────────────────────
def cave_lantern(lp):
    lp.beam((0, 0, 0), (0, 1.6, 0), 0.04, '#5e3b1f', sides=4)
    lp.beam((0, 1.58, 0), (0.28, 1.6, 0), 0.025, '#5e3b1f', sides=4)
    lp.beam((0.25, 1.6, 0), (0.25, 1.52, 0), 0.008, '#2a2a30', sides=3)            # the hook it hangs from
    lp.box((0.25, 1.5, 0), (0.12, 0.03, 0.12), '#2a2a30')
    lp.box((0.25, 1.36, 0), (0.16, 0.24, 0.16), '#2a2a30')
    lp.emissive = True
    lp.box((0.25, 1.36, 0), (0.12, 0.2, 0.12), '#ffb85a')
    lp.emissive = False
    for _ in range(3):                                                               # a few stones at its foot
        lp.blob(((lp.rnd.random() - 0.5) * 0.5, 0.05, (lp.rnd.random() - 0.5) * 0.5), 0.1, STONE[1], detail=0)

# ── more military ────────────────────────────────────────────────────────────
CANVAS = '#6b6a48'


def military_truck(lp):
    lp.box((1.55, 0.95, 0), (1.1, 1.1, 1.6), OLIVE_DRAB, top='#5b6640')               # cab
    lp.box((1.75, 1.2, 0), (0.6, 0.45, 1.5), GLASS)
    lp.box((-0.6, 0.7, 0), (3.4, 0.25, 1.7), '#3f4829')                              # flatbed
    lp.box((-0.6, 1.55, 0), (3.3, 1.5, 1.65), CANVAS, top='#77764f')                 # canvas cover
    for x in (-2.0, -1.0, 0.0, 0.9):
        lp.box((x, 1.55, 0), (0.06, 1.52, 1.67), '#5a5a3c')
    lp.box((2.12, 0.75, 0), (0.06, 0.4, 1.4), '#2a2a30')
    _wheels(lp, (-1.6, -0.6, 1.5), 0.85, 0.42)


def humvee(lp):
    tan = lp.rnd.choice(['#a89a72', OLIVE_DRAB])
    lp.box((0, 0.8, 0), (3.2, 0.7, 1.85), tan, top='#968a66')
    lp.box((-0.3, 1.4, 0), (1.7, 0.55, 1.7), tan)
    lp.box((0.56, 1.4, 0), (0.02, 0.4, 1.5), GLASS)
    lp.box((1.1, 1.16, 0), (0.95, 0.02, 1.7), '#5b5e4a')                             # bonnet, flush on top
    lp.cylinder((-0.3, 1.68, 0), 0.32, 0.25, '#4a4a3c', sides=8)                     # turret ring
    lp.beam((-0.3, 1.88, 0), (0.6, 1.92, 0), 0.04, '#26282d', sides=5)              # gun
    lp.box((1.62, 0.8, 0), (0.06, 0.4, 1.6), '#2a2a30')
    _wheels(lp, (-1.05, 1.05), 0.9, 0.42)


def tank_wreck(lp):
    hull, dark = '#5a6040', '#3f4530'
    lp.box((0, 0.7, 0), (5.6, 0.9, 2.6), hull, top='#626a46')
    for z in (-1.3, 1.3):                                                              # tracks
        lp.box((0, 0.45, z), (5.8, 0.9, 0.5), '#2a2a2c')
        for x in (-2.2, -1.1, 0.0, 1.1, 2.2):
            lp.beam((x, 0.42, z - 0.27), (x, 0.42, z + 0.27), 0.32, '#3a3a3c', sides=8)
    lp.box((-0.3, 1.5, 0), (2.4, 0.7, 2.0), hull, yaw=18)                           # turret, knocked askew
    lp.beam((0.6, 1.55, 0.35), (3.6, 1.3, 1.3), 0.11, dark, sides=6)               # barrel
    lp.blob((-2.2, 1.2, -0.5), 0.45, '#2a2622', detail=0)                           # scorch / debris
    lp.box((2.7, 0.75, 0), (0.15, 0.6, 2.2), dark)


def guard_tower(lp):
    steel, wall = '#5b6067', OLIVE_DRAB
    for x, z in ((-1.1, -1.1), (1.1, -1.1), (-1.1, 1.1), (1.1, 1.1)):
        lp.box((x, 2.5, z), (0.18, 5.0, 0.18), steel)
    for y in (1.6, 3.2):
        lp.beam((-1.1, y, 1.1), (1.1, y + 0.9, 1.1), 0.05, steel, sides=4)
        lp.beam((-1.1, y, -1.1), (1.1, y + 0.9, -1.1), 0.05, steel, sides=4)
    lp.box((0, 5.0, 0), (2.8, 0.15, 2.8), '#4a4e55')
    for x, z, sx, sz in ((0, -1.35, 2.8, 0.1), (0, 1.35, 2.8, 0.1), (-1.35, 0, 0.1, 2.8), (1.35, 0, 0.1, 2.8)):
        lp.box((x, 5.5, z), (sx, 0.9, sz), wall)
    for x, z in ((-1.3, -1.3), (1.3, -1.3), (-1.3, 1.3), (1.3, 1.3)):
        lp.box((x, 6.3, z), (0.1, 1.6, 0.1), steel)
    lp.box((0, 7.15, 0), (3.2, 0.12, 3.2), '#3a3d42')
    lp.box((0.7, 5.95, 1.25), (0.4, 0.3, 0.3), '#2a2a30')                          # searchlight
    lp.emissive = True
    lp.box((0.7, 5.95, 1.41), (0.3, 0.22, 0.02), '#fffbe8')
    lp.emissive = False
    lp.beam((0.95, 0, 1.25), (0.95, 5.0, 1.25), 0.025, steel, sides=4)              # ladder rails and rungs
    lp.beam((0.55, 0, 1.25), (0.55, 5.0, 1.25), 0.025, steel, sides=4)
    for k in range(1, 17):
        lp.box((0.75, k * 0.3, 1.25), (0.42, 0.03, 0.03), steel)


def sandbag_wall(lp):
    _bag_rows(lp, 2.9, 5)

def military_tent(lp):
    lp.box((0, 0.9, 0), (4.0, 1.8, 3.0), '#5b6640')
    lp.prism((0, 1.8, 0), 4.2, 3.2, 1.0, '#4f5a35', gable='#5b6640', yaw=90)
    lp.box((0, 0.85, 1.51), (1.0, 1.6, 0.02), '#2a2c22')                            # door flap open
    lp.box((0.65, 0.85, 1.55), (0.3, 1.6, 0.04), '#4f5a35', yaw=-25)
    for x in (-1.4, 1.4):                                                            # guy ropes
        lp.beam((x, 1.8, 1.5), (x * 1.2, 0, 2.5), 0.01, '#c9b98a', sides=3)
        lp.beam((x, 1.8, -1.5), (x * 1.2, 0, -2.5), 0.01, '#c9b98a', sides=3)


def hesco_barrier(lp):
    lp.box((0, 0.6, 0), (0.98, 1.2, 0.98), '#a8946a', top='#8f7d58')
    for x in (-0.49, 0.49):                                                          # wire mesh frame
        for z in (-0.49, 0.49):
            lp.box((x, 0.6, z), (0.04, 1.22, 0.04), '#6f7378')
    for y in (0.3, 0.6, 0.9):
        lp.box((0, y, 0.495), (1.0, 0.02, 0.01), '#6f7378')
        lp.box((0, y, -0.495), (1.0, 0.02, 0.01), '#6f7378')
        lp.box((0.495, y, 0), (0.01, 0.02, 1.0), '#6f7378')
        lp.box((-0.495, y, 0), (0.01, 0.02, 1.0), '#6f7378')


def checkpoint(lp):
    lp.box((-1.5, 1.15, 0), (1.2, 2.3, 1.2), '#b9b7b0', top='#8f8d86')              # guard booth
    lp.box((-1.5, 1.45, 0.61), (0.8, 0.6, 0.02), GLASS)
    lp.box((-0.89, 1.45, 0), (0.02, 0.6, 0.8), GLASS)
    lp.box((-1.5, 2.38, 0), (1.5, 0.12, 1.5), '#5b6067')
    lp.box((-0.6, 0.5, 0), (0.25, 1.0, 0.25), '#2a2a30')                            # barrier post
    for i in range(6):                                                                # red and white arm
        lp.box((-0.3 + i * 0.5, 0.95, 0), (0.5, 0.12, 0.1), '#d64541' if i % 2 == 0 else '#f5f4f2')
    lp.box((2.6, 0.45, 0), (0.15, 0.9, 0.15), '#2a2a30')


def supply_pallet(lp):
    lp.box((0, 0.07, 0), (1.3, 0.14, 1.1), '#a87848')
    for x, z in ((-0.32, -0.27), (0.32, -0.27), (-0.32, 0.27), (0.32, 0.27)):
        lp.box((x, 0.39, z), (0.6, 0.5, 0.52), lp.rnd.choice([OLIVE_DRAB, '#5b6640', '#8a7a52']))
    lp.box((0, 0.865, 0), (0.6, 0.45, 0.52), lp.rnd.choice([OLIVE_DRAB, '#8a7a52']))          # one on top
    lp.box((0, 0.39, 0), (1.23, 0.05, 1.07), '#2a2a30')                              # a band round the bottom layer
    lp.box((0, 0.865, 0), (0.62, 0.05, 0.54), '#2a2a30')                               # and one round the top crate
    lp.box((0, 1.092, 0), (0.05, 0.01, 0.54), '#2a2a30')
    lp.box((0, 0.865, 0.265), (0.05, 0.45, 0.01), '#2a2a30')
    lp.box((0, 0.865, -0.265), (0.05, 0.45, 0.01), '#2a2a30')

def field_gun(lp):
    steel = '#4f5a35'
    lp.box((0, 0.75, 0), (1.2, 0.6, 0.9), steel)                                      # shield and body
    lp.box((0.35, 1.0, 0), (0.08, 1.1, 1.5), steel)
    lp.beam((0.5, 0.95, 0), (2.6, 1.15, 0), 0.09, '#3a3d2a', sides=6)
    lp.beam((2.5, 1.14, 0), (2.7, 1.16, 0), 0.12, '#2a2a2c', sides=6)                 # muzzle brake
    for z in (-0.6, 0.6):
        lp.beam((0, 0.45, z), (0, 0.45, z * 1.25), 0.45, TYRE, sides=9)
    lp.beam((-0.3, 0.45, 0.1), (-2.3, 0.05, 0.6), 0.06, steel, sides=4)               # trail legs
    lp.beam((-0.3, 0.45, -0.1), (-2.3, 0.05, -0.6), 0.06, steel, sides=4)


def radar_dish(lp):
    lp.box((0, 0.6, 0), (1.2, 1.2, 1.2), '#5b6067')
    lp.beam((0, 1.2, 0), (0, 2.1, 0), 0.12, '#3a3d42', sides=6)
    lp.box((0, 2.15, 0.05), (0.35, 0.2, 0.35), '#3a3d42')
    lp.beam((0, 2.2, 0.1), (0, 2.75, 0.7), 0.15, '#c9c7c0', sides=12, end_radius=1.25)   # the dish (a shallow cone)
    lp.beam((0, 2.5, 0.4), (0, 3.15, 1.25), 0.03, '#3a3d42', sides=4)                  # feed arm and horn
    lp.box((0, 3.17, 1.27), (0.12, 0.12, 0.12), '#2a2a30')
    lp.emissive = True
    lp.box((0.45, 1.0, 0.61), (0.15, 0.08, 0.01), '#7dff8a')
    lp.emissive = False

def helipad(lp):
    lp.cylinder((0, 0, 0), 3.2, 0.06, '#5b5e63', sides=16)
    lp.cylinder((0, 0.06, 0), 2.6, 0.01, '#f5f4f2', sides=16)
    lp.cylinder((0, 0.07, 0), 2.45, 0.01, '#5b5e63', sides=16)
    for x in (-0.6, 0.6):                                                            # the H
        lp.box((x, 0.085, 0), (0.25, 0.01, 1.8), '#d9a521')
    lp.box((0, 0.085, 0), (1.2, 0.01, 0.25), '#d9a521')


def weapon_rack(lp):
    wood = '#5e3b1f'
    lp.box((0, 0.1, 0), (1.6, 0.2, 0.4), wood)
    lp.box((0, 1.25, -0.15), (1.6, 0.12, 0.1), wood)
    for x in (-0.75, 0.75):
        lp.box((x, 0.7, -0.15), (0.1, 1.4, 0.1), wood)
    for i in range(5):                                                               # rifles leaning in it
        x = -0.55 + i * 0.27
        lp.box((x, 0.75, 0.0), (0.05, 1.2, 0.1), '#26282d', yaw=0)
        lp.box((x, 0.35, 0.03), (0.07, 0.35, 0.14), '#6b4a2b')


def camo_net(lp):
    for x, z in ((-1.8, -1.3), (1.8, -1.3), (-1.8, 1.3), (1.8, 1.3)):
        lp.beam((x, 0, z), (x, 2.35, z), 0.05, '#5e3b1f', sides=4)
    tones = ['#4f5a35', '#5b6640', '#3f4829', '#6b6a48']
    for i in range(5):                                                               # a net that covers the posts
        for j in range(4):
            x = -2.0 + i * 1.0 + (lp.rnd.random() - 0.5) * 0.3
            z = -1.5 + j * 1.0 + (lp.rnd.random() - 0.5) * 0.3
            sag = 0.12 * (1 - abs(x) / 2.0) * (1 - abs(z) / 1.5)
            lp.blob((x, 2.4 - sag, z), 0.62, lp.rnd.choice(tones), squash=(1.2, 0.22, 1.2), detail=0, jitter=0.15)

def burning_barrel(lp):
    import math
    lp.cylinder((0, 0, 0), 0.32, 0.9, '#4a3a30', sides=8, top_colour='#1a1410')
    for y in (0.2, 0.65):
        lp.cylinder((0, y, 0), 0.33, 0.05, '#2a2622', sides=8)
    lp.emissive = True
    for i in range(6):                                                               # ragged tongues of flame
        a = i / 6 * math.tau + lp.rnd.random() * 0.4
        r = 0.08 + lp.rnd.random() * 0.12
        x, z = math.cos(a) * r, math.sin(a) * r
        h = 0.25 + lp.rnd.random() * 0.35
        lp.cylinder((x, 0.86, z), 0.07 + lp.rnd.random() * 0.04, h, lp.rnd.choice(['#ff8c2a', '#ff6a1a']), sides=4,
                    top_radius=0)
    lp.cylinder((0, 0.86, 0), 0.12, 0.42, '#ffd84a', sides=5, top_radius=0)
    lp.emissive = False

# ── more town ────────────────────────────────────────────────────────────────
def _car(lp, body, top_h=0.5, length=3.0):
    lp.box((0, 0.6, 0), (length, 0.55, 1.4), body)
    lp.box((-0.15, 1.12, 0), (length * 0.48, top_h, 1.3), body)
    lp.box((length * 0.24 - 0.12, 1.12, 0), (0.02, top_h - 0.08, 1.15), GLASS)
    lp.box((-length * 0.24 - 0.18, 1.12, 0), (0.02, top_h - 0.08, 1.15), GLASS)
    lp.box((-0.15, 1.12, 0.66), (length * 0.42, top_h - 0.12, 0.02), GLASS)
    lp.box((-0.15, 1.12, -0.66), (length * 0.42, top_h - 0.12, 0.02), GLASS)
    lp.box((length / 2 + 0.01, 0.62, 0), (0.04, 0.2, 1.1), '#9aa0a8')
    _wheels(lp, (-length * 0.32, length * 0.32), 0.68, 0.3)


def sedan(lp):
    body = lp.rnd.choice(['#2f5d8a', '#8a3b2a', '#c9c7c0', '#2a2a30', '#4f7a3a'])
    _car(lp, body)
    if lp.rnd.random() < 0.6:                                                        # smashed window, flat look
        lp.box((-0.15, 1.12, 0.67), (0.5, 0.3, 0.02), '#151a20')


def police_car(lp):
    _car(lp, '#f5f4f2')
    lp.box((0, 0.6, 0.71), (1.6, 0.3, 0.01), '#1f2a44')
    lp.box((0, 0.6, -0.71), (1.6, 0.3, 0.01), '#1f2a44')
    lp.box((-0.15, 1.39, 0), (0.2, 0.06, 1.1), '#2a2a30')
    lp.emissive = True
    lp.box((-0.15, 1.45, 0.3), (0.18, 0.1, 0.4), '#3a6bff')
    lp.box((-0.15, 1.45, -0.3), (0.18, 0.1, 0.4), '#ff3a3a')
    lp.emissive = False


def ambulance(lp):
    white = '#f5f4f2'
    lp.box((-0.5, 1.2, 0), (2.8, 1.9, 1.8), white)                                   # box body
    lp.box((1.4, 0.85, 0), (1.1, 1.1, 1.7), white)                                   # cab
    lp.box((1.75, 1.15, 0), (0.5, 0.45, 1.55), GLASS)
    lp.box((-0.5, 1.0, 0.91), (2.6, 0.18, 0.01), '#d64541')
    lp.box((-0.5, 1.0, -0.91), (2.6, 0.18, 0.01), '#d64541')
    for z in (0.915, -0.915):                                                        # red crosses
        lp.box((-0.5, 1.6, z), (0.5, 0.15, 0.01), '#d64541')
        lp.box((-0.5, 1.6, z), (0.15, 0.5, 0.01), '#d64541')
    lp.emissive = True
    lp.box((0.85, 2.18, 0.5), (0.15, 0.1, 0.3), '#ff3a3a')
    lp.box((0.85, 2.18, -0.5), (0.15, 0.1, 0.3), '#3a6bff')
    lp.emissive = False
    _wheels(lp, (-1.3, 1.4), 0.85, 0.36)


def street_light(lp):
    lp.beam((0, 0, 0), (0, 4.4, 0), 0.08, '#5b6067', sides=6, end_radius=0.06)
    for sx in (-1, 1):
        lp.beam((0, 4.3, 0), (sx * 1.1, 4.55, 0), 0.04, '#5b6067', sides=4)
        lp.box((sx * 1.2, 4.5, 0), (0.5, 0.1, 0.25), '#3a3d42')
        lp.emissive = True
        lp.box((sx * 1.2, 4.43, 0), (0.42, 0.04, 0.2), '#fff1c8')
        lp.emissive = False


def traffic_light(lp):
    lp.beam((0, 0, 0), (0, 2.6, 0), 0.06, '#3a3d42', sides=6)
    lp.box((0, 3.0, 0), (0.32, 0.9, 0.28), '#26282d')
    lp.emissive = True
    for y, c in ((3.28, '#ff3a3a'), (3.0, '#3a2a10'), (2.72, '#15301a')):
        lp.box((0, y, 0.145), (0.18, 0.18, 0.02), c)
    lp.emissive = False


def trash_can(lp):
    lp.cylinder((0, 0, 0), 0.3, 0.85, '#5b6067', sides=10, top_colour='#3a3d42')
    lp.cylinder((0, 0.85, 0), 0.32, 0.06, '#4a4e55', sides=10)
    for y in (0.25, 0.6):
        lp.cylinder((0, y, 0), 0.31, 0.03, '#3a3d42', sides=10)
    if lp.rnd.random() < 0.5:                                                         # knocked over rubbish
        lp.blob((0.45, 0.08, 0.2), 0.15, '#3a3a3c', detail=0)


def news_stand(lp):
    lp.box((0, 0.55, 0), (0.55, 1.1, 0.45), '#2f5d8a')
    lp.box((0, 0.85, 0.23), (0.45, 0.4, 0.02), '#7e9aac')
    lp.box((0, 0.78, 0.21), (0.38, 0.3, 0.01), '#e9e2d0')
    lp.box((0, 1.15, 0), (0.6, 0.08, 0.5), '#26405e')


def shop_store(lp):
    wall = lp.rnd.choice(['#d9c9a3', '#b9b7b0', '#a8b5a0'])
    lp.flat((0, 0, 0), (5, 5), '#7a7872', 0.03)
    lp.box((0, 1.5, -2), (5, 3.0, 1), wall)
    lp.box((-2, 1.5, 0), (1, 3.0, 3), wall)
    lp.box((2, 1.5, 0), (1, 3.0, 3), wall)
    lp.box((-1.5, 1.5, 2), (2, 3.0, 1), wall)
    lp.box((1.5, 1.5, 2), (2, 3.0, 1), wall)
    lp.box((0, 2.5, 2), (1, 1.0, 1), wall)
    for x in (-1.5, 1.5):                                                            # shop windows (broken)
        lp.box((x, 1.2, 2.52), (1.3, 1.2, 0.02), lp.rnd.choice([GLASS, '#151a20']))
    lp.box((0, 3.05, 0), (5.2, 0.1, 5.2), '#5b5e63')                                 # flat roof
    lp.box((0, 2.75, 2.56), (4.2, 0.5, 0.06), lp.rnd.choice(['#c62f2a', '#1197b0', '#2f5d3a']))   # sign
    lp.box((0, 2.75, 2.6), (2.4, 0.18, 0.01), '#f5f4f2')
    lp.box((0, 2.2, 2.8), (4.6, 0.06, 0.8), '#d9a521', yaw=0)                        # awning
    lp.box((1.5, 3.3, -1.2), (0.9, 0.5, 0.7), '#8a8f96')                             # roof AC unit


def apartment(lp):
    wall = lp.rnd.choice(['#b5a48a', '#9c8a78', '#a8a29a'])
    lp.flat((0, 0, 0), (7, 7), '#7a7872', 0.03)
    lp.box((0, 4.5, -3), (7, 9.0, 1), wall)
    lp.box((-3, 4.5, 0), (1, 9.0, 5), wall)
    lp.box((3, 4.5, 0), (1, 9.0, 5), wall)
    lp.box((-2, 4.5, 3), (3, 9.0, 1), wall)
    lp.box((2, 4.5, 3), (3, 9.0, 1), wall)
    lp.box((0, 5.3, 3), (1, 7.4, 1), wall)
    lp.box((0, 9.05, 0), (7.2, 0.15, 7.2), '#5b5e63')
    for floor in range(3):                                                           # rows of windows
        y = 1.4 + floor * 2.9 + (0.0 if floor else 0.3)
        for k in (-2.2, -0.9, 0.9, 2.2):
            for z, w in ((3.52, (0.8, 1.1, 0.02)), (-3.52, (0.8, 1.1, 0.02))):
                if floor == 0 and z > 0 and abs(k) < 1:
                    continue
                c = '#151a20' if lp.rnd.random() < 0.3 else GLASS
                lp.box((k, y + 0.6, z), w, c)
            lp.box((3.52, y + 0.6, k), (0.02, 1.1, 0.8), GLASS)
            lp.box((-3.52, y + 0.6, k), (0.02, 1.1, 0.8), GLASS)
    lp.box((0, 2.4, 3.6), (1.4, 0.1, 0.6), '#5b5e63')                                # porch roof


def gas_station(lp):
    for x in (-2.2, 2.2):
        for z in (-1.2, 1.2):
            lp.box((x, 1.8, z), (0.3, 3.6, 0.3), '#e9e2d0')
    lp.box((0, 3.75, 0), (6.0, 0.35, 3.6), '#c62f2a', top='#e9e2d0')
    lp.box((0, 3.75, 1.81), (6.0, 0.3, 0.02), '#f5f4f2')
    lp.emissive = True
    lp.box((0, 3.55, 0), (4.0, 0.03, 0.4), '#fff6d8')
    lp.emissive = False
    for x in (-1.0, 1.0):                                                             # two pumps on islands
        lp.box((x, 0.1, 0), (0.9, 0.2, 1.6), '#b9b7b0')
        lp.box((x, 0.95, 0), (0.45, 1.5, 0.6), '#c62f2a', top='#f5f4f2')
        lp.box((x, 1.2, 0.31), (0.3, 0.3, 0.02), '#1f2a22')


def chainlink_fence(lp):
    for x in (-0.48, 0.48):
        lp.beam((x, 0, 0), (x, 2.0, 0), 0.04, '#8a8f96', sides=5)
    lp.beam((-0.5, 1.95, 0), (0.5, 1.95, 0), 0.025, '#8a8f96', sides=4)
    for i in range(6):                                                               # diamond mesh
        x = -0.45 + i * 0.18
        lp.beam((x, 0.05, 0), (x + 0.18, 1.9, 0), 0.006, '#a8adb3', sides=3)
        lp.beam((x + 0.18, 0.05, 0), (x, 1.9, 0), 0.006, '#a8adb3', sides=3)
    for i in range(4):                                                               # barbed top
        lp.beam((-0.5 + i * 0.25, 2.0, 0), (-0.38 + i * 0.25, 2.15, 0.1), 0.008, '#6f7378', sides=3)


def shopping_cart(lp):
    metal = '#a8adb3'
    lp.box((0, 0.75, 0), (0.85, 0.5, 0.55), metal)
    lp.box((0, 0.78, 0), (0.8, 0.45, 0.5), '#5b6067')
    lp.beam((-0.45, 1.0, -0.28), (-0.45, 1.0, 0.28), 0.03, '#d64541', sides=4)       # handle
    for x in (-0.35, 0.35):
        for z in (-0.22, 0.22):
            lp.beam((x, 0.5, z), (x, 0.08, z), 0.015, metal, sides=3)
            lp.cylinder((x, 0.0, z), 0.06, 0.08, '#1f1f22', sides=6)


def tire_stack(lp):
    for i in range(3 + lp.rnd.randrange(2)):
        x, z = (lp.rnd.random() - 0.5) * 0.12, (lp.rnd.random() - 0.5) * 0.12
        lp.cylinder((x, i * 0.24, z), 0.4, 0.23, TYRE, sides=10, top_colour='#2a2a2c')
        lp.cylinder((x, i * 0.24 + 0.231, z), 0.2, 0.002, '#111113', sides=8)


def pallet_stack(lp):
    for i in range(3 + lp.rnd.randrange(3)):
        y = i * 0.15
        lp.box((0, y + 0.03, 0), (1.2, 0.03, 1.0), '#a87848')
        for z in (-0.42, 0, 0.42):
            lp.box((0, y + 0.09, z), (1.2, 0.09, 0.12), '#8a6038')
        lp.box((0, y + 0.13, 0), (1.2, 0.03, 1.0), '#b08850', yaw=(lp.rnd.random() - 0.5) * 6)


def parking_meter(lp):
    lp.beam((0, 0, 0), (0, 1.1, 0), 0.04, '#5b6067', sides=5)
    lp.box((0, 1.25, 0), (0.22, 0.32, 0.16), '#3a3d42')
    lp.box((0, 1.3, 0.085), (0.14, 0.1, 0.01), '#9fe8ff')


def broken_wall(lp):
    brick = '#8d4a3a'
    for i in range(6):
        h = 0.6 + lp.rnd.random() * 2.2 if i not in (2, 3) else 0.3 + lp.rnd.random() * 0.6
        lp.box((-1.25 + i * 0.5, h / 2, 0), (0.5, h, 0.5), lp.rnd.choice([brick, '#7a4032', '#9a5444']))
    for _ in range(6):
        x, z = (lp.rnd.random() - 0.5) * 2.6, 0.5 + lp.rnd.random() * 0.8
        s = 0.15 + lp.rnd.random() * 0.2
        lp.box((x, s / 2, z), (s * 1.5, s, s), brick, yaw=lp.rnd.random() * 90)


def road_sign(lp):
    lp.beam((0, 0, 0), (0, 2.2, 0), 0.04, '#8a8f96', sides=5)
    lp.box((0, 2.0, 0.05), (0.7, 0.45, 0.03), '#2f6b3a')
    lp.box((0, 2.0, 0.07), (0.5, 0.06, 0.01), '#f5f4f2')
    lp.box((0.22, 2.0, 0.07), (0.08, 0.2, 0.01), '#f5f4f2')

def _ore_marker(kind):
    from .resources import draw_node

    def build(lp):
        draw_node(lp, kind)
    return build


def ore_random(lp):
    from .resources import draw_node
    draw_node(lp, 'stone')
    lp.beam((0.05, 0.6, 0), (0.05, 1.9, 0), 0.03, '#f5f4f2', sides=4)
    for i, c in enumerate(('#c3cfdb', '#e0813a', '#c07bff')):
        lp.box((0.25, 1.78 - i * 0.12, 0), (0.4, 0.12, 0.02), c)


def _perimeter(half, door=None, height=3):
    cells = []
    for dx in range(-half, half + 1):
        for dz in range(-half, half + 1):
            if max(abs(dx), abs(dz)) == half and (dx, dz) != door:
                cells.append((dx, dz, height))
    return cells


def A(name, category, build, solid=(), nature=False, variants=1, **extra):
    return dict(name=name, category=category, build=build, solid=list(solid), nature=nature, variants=variants, **extra)


ASSETS = {
    # trees
    'pine': A('Pine tree', 'trees', pine, [(0, 0, 3)], nature=True, variants=3),
    'snowy_pine': A('Snowy pine', 'trees', snowy_pine, [(0, 0, 3)], nature=True, variants=2),
    'oak': A('Oak tree', 'trees', oak, [(0, 0, 3)], nature=True, variants=3),
    'autumn_tree': A('Autumn tree', 'trees', autumn_tree, [(0, 0, 3)], nature=True, variants=3),
    'birch': A('Birch tree', 'trees', birch, [(0, 0, 3)], nature=True, variants=3),
    'dead_tree': A('Dead tree', 'trees', dead_tree, [(0, 0, 3)], nature=True, variants=3),
    'stump': A('Tree stump', 'trees', stump, [(0, 0, 1)], nature=True, variants=2),
    # shrubs
    'bush': A('Bush', 'shrubs', bush, nature=True, variants=3),
    'flower_bush': A('Flower bush', 'shrubs', flower_bush, nature=True, variants=3),
    'tall_grass': A('Tall grass', 'shrubs', tall_grass, nature=True, variants=3),
    'fern': A('Fern', 'shrubs', fern, nature=True, variants=2),
    'flowers': A('Flowers', 'shrubs', flowers, nature=True, variants=3),
    'mushrooms': A('Mushrooms', 'shrubs', mushrooms, nature=True, variants=2),
    'rock': A('Small rock', 'shrubs', rock, nature=True, variants=3),
    'boulder': A('Boulder', 'shrubs', boulder, [(0, 0, 2)], nature=True, variants=3),
    'hedge': A('Hedge', 'shrubs', hedge, [(0, 0, 1)]),
    # buildings
    'house': A('House', 'buildings', house, _perimeter(3, door=(0, 3))),
    'cabin': A('Log cabin', 'buildings', cabin, _perimeter(2, door=(0, 2))),
    'ruin': A('Ruined house', 'buildings', ruin, RUIN_SOLID),
    'tower': A('Watchtower', 'buildings', tower, [(-1, -1, 4), (1, -1, 4), (-1, 1, 4), (1, 1, 4)]),
    'market_stall': A('Market stall', 'buildings', market_stall, [(-1, 0, 1), (0, 0, 1), (1, 0, 1)]),
    'well': A('Well', 'buildings', well, [(0, 0, 2)]),
    'tent': A('Tent', 'buildings', tent, [(dx, dz, 2) for dx in (-1, 0, 1) for dz in (-1, 0, 1)]),
    'stone_wall': A('Stone wall', 'buildings', stone_wall, [(0, 0, 2)]),
    'fence': A('Wood fence', 'buildings', fence, [(0, 0, 1)]),
    'sandbags': A('Sandbags', 'buildings', sandbags, [(0, 0, 1)]),
    # props
    'crate': A('Crate', 'props', crate, [(0, 0, 1)]),
    'barrel': A('Barrel', 'props', barrel, [(0, 0, 1)]),
    'hay_bale': A('Hay bale', 'props', hay_bale, [(0, 0, 1)]),
    'log_pile': A('Log pile', 'props', log_pile, [(0, 0, 1)]),
    'lamp_post': A('Lamp post', 'props', lamp_post, [(0, 0, 3)],
                   light=dict(colour=(1.0, 0.85, 0.55), radius=11, strength=1.1, at=(0.45, 2.6, 0), flicker=0.03)),
    'bench': A('Bench', 'props', bench),
    'campfire': A('Campfire', 'props', campfire,
                  light=dict(colour=(1.0, 0.55, 0.22), radius=10, strength=1.5, at=(0, 0.7, 0), flicker=0.22)),
    'car_wreck': A('Car wreck', 'props', car_wreck, [(-1, 0, 2), (0, 0, 2), (1, 0, 2)]),
    'signpost': A('Signpost', 'props', signpost, [(0, 0, 2)]),
    'rubble': A('Rubble', 'props', rubble, nature=True, variants=2),
    # more nature
    'fallen_log': A('Fallen log', 'trees', fallen_log, [(-1, 0, 1), (0, 0, 1), (1, 0, 1)]),
    'dead_bush': A('Dead bush', 'shrubs', dead_bush, nature=True, variants=2),
    # town
    'pickup_truck': A('Pickup truck', 'town', pickup_truck, [(-1, 0, 2), (0, 0, 2), (1, 0, 2)], variants=3),
    'bus_wreck': A('Bus wreck', 'town', bus_wreck, [(dx, 0, 3) for dx in range(-3, 4)]),
    'traffic_cone': A('Traffic cone', 'town', traffic_cone),
    'road_barrier': A('Road barrier', 'town', road_barrier, [(0, 0, 1)]),
    'stop_sign': A('Stop sign', 'town', stop_sign),
    'fire_hydrant': A('Fire hydrant', 'town', fire_hydrant, [(0, 0, 1)]),
    'mailbox': A('Mailbox', 'town', mailbox),
    'phone_booth': A('Phone booth', 'town', phone_booth, [(0, 0, 3)],
                     light=dict(colour=(1.0, 0.95, 0.8), radius=4, strength=0.7, at=(0, 2.2, 0.6))),
    'dumpster': A('Dumpster', 'town', dumpster, [(0, 0, 2)], variants=2),
    'trash_bags': A('Trash bags', 'town', trash_bags, nature=True, variants=3),
    'utility_pole': A('Utility pole', 'town', utility_pole, [(0, 0, 3)]),
    'bus_stop': A('Bus stop', 'town', bus_stop, [(-1, 0, 3), (1, 0, 3)]),
    'gas_pump': A('Gas pump', 'town', gas_pump, [(0, 0, 2)]),
    'billboard': A('Billboard', 'town', billboard, [(-1, 0, 3), (1, 0, 3)], variants=3),
    'vending_machine': A('Vending machine', 'town', vending_machine, [(0, 0, 2)], variants=2,
                         light=dict(colour=(1.0, 0.85, 0.55), radius=4, strength=0.8, at=(0, 1.1, 0.6), flicker=0.02)),
    'picnic_table': A('Picnic table', 'town', picnic_table),
    # military
    'shipping_container': A('Shipping container', 'military', shipping_container,
                            [(dx, dz, 3) for dx in range(-3, 4) for dz in (-1, 0, 1)], variants=4),
    'barbed_wire': A('Barbed wire', 'military', barbed_wire, [(0, 0, 1)]),
    'tank_trap': A('Tank trap', 'military', tank_trap, [(0, 0, 1)]),
    'ammo_crate': A('Ammo crate', 'military', ammo_crate, [(0, 0, 1)]),
    'fuel_drums': A('Fuel drums', 'military', fuel_drums, [(0, 0, 1)]),
    'generator': A('Generator', 'military', generator, [(0, 0, 1)]),
    'radio_mast': A('Radio mast', 'military', radio_mast, [(0, 0, 3)],
                    light=dict(colour=(1.0, 0.2, 0.15), radius=6, strength=0.9, at=(0, 8.1, 0), flicker=0.3)),
    'helicopter_wreck': A('Helicopter wreck', 'military', helicopter_wreck, [(-1, 0, 2), (0, 0, 2), (1, 0, 2)]),
    'floodlight': A('Floodlight', 'military', floodlight,
                    light=dict(colour=(1.0, 0.97, 0.9), radius=14, strength=1.4, at=(0, 2.0, 1.2))),
    'bunker': A('Bunker', 'military', bunker, _perimeter(1, door=(0, 1), height=2)),
    'jerry_cans': A('Jerry cans', 'military', jerry_cans),
    # caves
    'cave_lantern': A('Cave lantern', 'props', cave_lantern,
                      light=dict(colour=(1.0, 0.65, 0.3), radius=7, strength=1.1, at=(0.25, 1.4, 0), flicker=0.12)),
    # more military
    'military_truck': A('Army truck', 'military', military_truck, [(dx, 0, 2) for dx in (-2, -1, 0, 1, 2)]),
    'humvee': A('Armored jeep', 'military', humvee, [(-1, 0, 2), (0, 0, 2), (1, 0, 2)], variants=2),
    'tank_wreck': A('Tank wreck', 'military', tank_wreck, [(dx, dz, 2) for dx in range(-3, 4) for dz in (-1, 0, 1)]),
    'guard_tower': A('Guard tower', 'military', guard_tower, [(-1, -1, 4), (1, -1, 4), (-1, 1, 4), (1, 1, 4)],
                     light=dict(colour=(1.0, 0.97, 0.9), radius=12, strength=1.2, at=(0.7, 5.9, 2.2))),
    'sandbag_wall': A('Sandbag wall', 'military', sandbag_wall, [(-1, 0, 1), (0, 0, 1), (1, 0, 1)]),
    'military_tent': A('Army tent', 'military', military_tent, [(dx, dz, 2) for dx in (-2, -1, 0, 1, 2)
                                                                for dz in (-1, 0, 1) if (dx, dz) != (0, 1)]),
    'hesco_barrier': A('Hesco barrier', 'military', hesco_barrier, [(0, 0, 2)]),
    'checkpoint': A('Checkpoint gate', 'military', checkpoint, [(-2, 0, 3), (-1, 0, 3)]),
    'supply_pallet': A('Supply pallet', 'military', supply_pallet, [(0, 0, 1)], variants=2),
    'field_gun': A('Field gun', 'military', field_gun, [(0, 0, 1), (1, 0, 1)]),
    'radar_dish': A('Radar dish', 'military', radar_dish, [(0, 0, 2)]),
    'helipad': A('Helipad', 'military', helipad),
    'weapon_rack': A('Weapon rack', 'military', weapon_rack, [(0, 0, 1)]),
    'camo_net': A('Camo net', 'military', camo_net),
    'burning_barrel': A('Burning barrel', 'military', burning_barrel, [(0, 0, 1)],
                        light=dict(colour=(1.0, 0.55, 0.22), radius=8, strength=1.3, at=(0, 1.2, 0), flicker=0.25)),
    # more town
    'sedan': A('Abandoned car', 'town', sedan, [(-1, 0, 2), (0, 0, 2), (1, 0, 2)], variants=5),
    'police_car': A('Police car', 'town', police_car, [(-1, 0, 2), (0, 0, 2), (1, 0, 2)]),
    'ambulance': A('Ambulance', 'town', ambulance, [(-1, 0, 3), (0, 0, 3), (1, 0, 3)]),
    'street_light': A('Street light', 'town', street_light, [(0, 0, 3)],
                      light=dict(colour=(1.0, 0.9, 0.7), radius=13, strength=1.1, at=(0, 4.3, 0), flicker=0.02)),
    'traffic_light': A('Traffic light', 'town', traffic_light, [(0, 0, 2)],
                       light=dict(colour=(1.0, 0.25, 0.2), radius=3, strength=0.6, at=(0, 3.28, 0.4))),
    'trash_can': A('Trash can', 'town', trash_can, [(0, 0, 1)], variants=2),
    'news_stand': A('News stand', 'town', news_stand),
    'shop_store': A('Corner shop', 'town', shop_store, _perimeter(2, door=(0, 2)), variants=3),
    'apartment': A('Apartment block', 'town', apartment, _perimeter(3, door=(0, 3), height=5), variants=3),
    'gas_station': A('Gas station', 'town', gas_station, [(-2, -1, 3), (2, -1, 3), (-2, 1, 3), (2, 1, 3),
                                                          (-1, 0, 2), (1, 0, 2)],
                     light=dict(colour=(1.0, 0.97, 0.88), radius=10, strength=1.0, at=(0, 3.4, 0))),
    'chainlink_fence': A('Chain-link fence', 'town', chainlink_fence, [(0, 0, 2)]),
    'shopping_cart': A('Shopping cart', 'town', shopping_cart),
    'tire_stack': A('Tire stack', 'town', tire_stack, [(0, 0, 1)], variants=2),
    'pallet_stack': A('Pallet stack', 'town', pallet_stack, [(0, 0, 1)], variants=2),
    'parking_meter': A('Parking meter', 'town', parking_meter),
    'broken_wall': A('Broken wall', 'town', broken_wall, [(-1, 0, 2), (0, 0, 2), (1, 0, 2)], variants=3),
    'road_sign': A('Road sign', 'town', road_sign),
    # farm
    'barn': A('Barn', 'farm', barn, _perimeter(3, door=(0, 3))),
    'silo': A('Silo', 'farm', silo, [(dx, dz, 4) for dx in (-1, 0, 1) for dz in (-1, 0, 1)]),
    'windmill': A('Windmill', 'farm', windmill, [(0, 0, 3)]),
    'water_tower': A('Water tower', 'farm', water_tower, [(-1, -1, 3), (1, -1, 3), (-1, 1, 3), (1, 1, 3)]),
    'scarecrow': A('Scarecrow', 'farm', scarecrow),
    'tractor': A('Tractor', 'farm', tractor, [(-1, 0, 2), (0, 0, 2), (1, 0, 2)]),
    'wheelbarrow': A('Wheelbarrow', 'farm', wheelbarrow),
    'outhouse': A('Outhouse', 'farm', outhouse, [(0, 0, 3)]),
    'corn_crop': A('Corn', 'farm', corn_crop, nature=True, variants=3),
    'pumpkins': A('Pumpkins', 'farm', pumpkins, nature=True, variants=3),
    'picket_fence': A('Picket fence', 'farm', picket_fence, [(0, 0, 1)]),
    # graveyard
    'gravestone': A('Gravestone', 'graveyard', gravestone, variants=3),
    'stone_cross': A('Stone cross', 'graveyard', stone_cross, [(0, 0, 2)]),
    'iron_fence': A('Iron fence', 'graveyard', iron_fence, [(0, 0, 1)]),
    'crypt': A('Crypt', 'graveyard', crypt, _perimeter(1, door=(0, 1))),
    'coffin': A('Coffin', 'graveyard', coffin),
    'grave_lantern': A('Grave lantern', 'graveyard', grave_lantern,
                       light=dict(colour=(1.0, 0.65, 0.3), radius=5, strength=0.9, at=(0.3, 1.1, 0), flicker=0.15)),
    'church': A('Old church', 'graveyard', church, [(dx, dz, 4) for dx in range(-3, 4) for dz in range(-4, 5)
                                                     if (abs(dx) == 3 or abs(dz) == 4) and (dx, dz) != (0, 4)]),
    # special
    'zombie_grave': A('Zombie grave (spawn)', 'special', zombie_grave, spawn='zombie'),
    'player_spawn': A('Player start', 'special', player_spawn, editor_only=True, spawn='player'),
    # mining and crafting (ore spawns only show in the editor; the real nodes grow there in game)
    'workbench': A('Workbench (crafting)', 'mining', workbench, [(-1, 0, 1), (0, 0, 1), (1, 0, 1)], station='workbench',
                   light=dict(colour=(1.0, 0.75, 0.42), radius=6, strength=1.0, at=(-0.88, 1.6, -0.2), flicker=0.08)),
    'ore_random': A('Ore spawn (random)', 'mining', ore_random, editor_only=True, ore='random'),
    'ore_stone': A('Stone node spawn', 'mining', _ore_marker('stone'), editor_only=True, ore='stone'),
    'ore_iron': A('Iron node spawn', 'mining', _ore_marker('iron'), editor_only=True, ore='iron'),
    'ore_copper': A('Copper node spawn', 'mining', _ore_marker('copper'), editor_only=True, ore='copper'),
    'ore_crystal': A('Crystal node spawn', 'mining', _ore_marker('crystal'), editor_only=True, ore='crystal'),
    'ore_logs': A('Log pile spawn (wood)', 'mining', _ore_marker('logs'), editor_only=True, ore='logs'),
    'loot_crate': A('Loot crate (breakable)', 'mining', _ore_marker('crate'), editor_only=True, ore='crate'),
}

ASSET_CATEGORIES = [('trees', 'Trees'), ('shrubs', 'Shrubs'), ('buildings', 'Buildings'), ('props', 'Props'),
                    ('town', 'Town'), ('military', 'Military'), ('farm', 'Farm'), ('graveyard', 'Graveyard'),
                    ('special', 'Special'), ('mining', 'Mining'), ('caves', 'Caves'), ('paths', 'Paths'),
                    ('blocks', 'Blocks')]

# Ground paths you can paint (texture tiles live in textures.py PATH_TILES)
PATHS = {'dirt': 'Dirt path', 'gravel': 'Gravel', 'cobble': 'Cobblestone', 'road': 'Road', 'sand': 'Sand',
         'floor': 'Wood floor'}

# Block columns you can paint (the blocky style from the random arena)
BLOCKS = {'stone': 'Stone', 'mossy': 'Mossy stone', 'brick': 'Brick', 'planks': 'Planks', 'crate': 'Crate block', 'log': 'Log',
          'obsidian': 'Obsidian', 'leaves': 'Leaves'}
