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
#    category   editor tab: trees, shrubs, buildings, props, special
#    build      function(lp) that adds the shapes
#    solid      cells you can't walk through: (dx, dz, height) from the middle cell
#    nature     True = random turn, size and nudge when placed (looks natural)
#    variants   how many random versions to make (nature only)
#    editor_only  True = only visible in the editor (spawn markers)
#    spawn      'player' or 'zombie' = this asset is a spawn point
#    ore        an ore node grows here in game ('random' or a node type from resources.py)
#    station    'workbench' = players craft here (press E)
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


def sandbags(lp):
    for row, y in enumerate((0.15, 0.42, 0.68)):
        for i in range(3 - (row == 2)):
            x = -0.32 + i * 0.32 + (0.16 if row == 2 else 0)
            lp.blob((x, y, 0), 0.2, '#b8a272', squash=(1, 0.55, 0.9), detail=0, jitter=0.05)


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
    lp.box((0.45, 2.75, 0), (0.3, 0.35, 0.3), '#fff0b0')
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
    lp.cylinder((0, 0.1, 0), 0.25, 0.65, '#ff8c2a', sides=5, top_radius=0)
    lp.cylinder((0.05, 0.1, 0.03), 0.13, 0.45, '#ffd84a', sides=5, top_radius=0)


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
    for i, c in enumerate(('#c3cfdb', '#e0813a', '#a3a39f', '#c07bff')):
        lp.blob((0.3 + (i % 2) * 0.22, 0.56, -0.05 + (i // 2) * 0.2), 0.08, c, jitter=0.3, detail=0)


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
    'lamp_post': A('Lamp post', 'props', lamp_post, [(0, 0, 3)]),
    'bench': A('Bench', 'props', bench),
    'campfire': A('Campfire', 'props', campfire),
    'car_wreck': A('Car wreck', 'props', car_wreck, [(-1, 0, 2), (0, 0, 2), (1, 0, 2)]),
    'signpost': A('Signpost', 'props', signpost, [(0, 0, 2)]),
    'rubble': A('Rubble', 'props', rubble, nature=True, variants=2),
    # special
    'zombie_grave': A('Zombie grave (spawn)', 'special', zombie_grave, spawn='zombie'),
    'player_spawn': A('Player start', 'special', player_spawn, editor_only=True, spawn='player'),
    # mining and crafting (ore spawns only show in the editor; the real nodes grow there in game)
    'workbench': A('Workbench (crafting)', 'mining', workbench, [(-1, 0, 1), (0, 0, 1), (1, 0, 1)], station='workbench'),
    'ore_random': A('Ore spawn (random)', 'mining', ore_random, editor_only=True, ore='random'),
    'ore_stone': A('Stone node spawn', 'mining', _ore_marker('stone'), editor_only=True, ore='stone'),
    'ore_iron': A('Iron node spawn', 'mining', _ore_marker('iron'), editor_only=True, ore='iron'),
    'ore_copper': A('Copper node spawn', 'mining', _ore_marker('copper'), editor_only=True, ore='copper'),
    'ore_crystal': A('Crystal node spawn', 'mining', _ore_marker('crystal'), editor_only=True, ore='crystal'),
}

ASSET_CATEGORIES = [('trees', 'Trees'), ('shrubs', 'Shrubs'), ('buildings', 'Buildings'), ('props', 'Props'),
                    ('special', 'Special'), ('mining', 'Mining'), ('paths', 'Paths'), ('blocks', 'Blocks')]

# Ground paths you can paint (texture tiles live in textures.py PATH_TILES)
PATHS = {'dirt': 'Dirt path', 'gravel': 'Gravel', 'cobble': 'Cobblestone', 'road': 'Road', 'sand': 'Sand',
         'floor': 'Wood floor'}

# Block columns you can paint (the blocky style from the random arena)
BLOCKS = {'stone': 'Stone', 'brick': 'Brick', 'planks': 'Planks', 'crate': 'Crate block', 'log': 'Log',
          'obsidian': 'Obsidian', 'leaves': 'Leaves'}
