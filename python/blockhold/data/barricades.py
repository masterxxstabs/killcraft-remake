# ─────────────────────────────────────────────────────────────────────────────
#  BARRICADES  (crafted at a workbench, placed with G; they can't be bought)
#
#    name, desc   shown at the workbench
#    cost         resources to craft one
#    hp           how much damage it takes before it breaks
#    cells        the grid cells it covers, as (dx, dz) from the middle cell (it turns with R)
#    height       how tall it is for walking / climbing (0 = you walk over it). Height 1 can be
#                 vaulted or climbed by players, but zombies have to break through
#    thorns       hurts zombies that push against it or attack it
#    turret       shoots zombies by itself (refill its ammo by holding E next to it)
#    mine         explodes when a zombie steps on it
#    build        draws it (see blockhold/lowpoly.py); turrets also have build_head (the part that aims)
# ─────────────────────────────────────────────────────────────────────────────
import math

WOOD = ['#a47b48', '#97703f', '#ad8551']
BARK = ['#6e5233', '#634a2e', '#7a5b39']
TIP = '#cdb083'
ROPE = '#b9a27a'
METAL = '#2c2e33'
OLIVE = '#5b6340'


def _stake(lp, base, top, radius, colour, tip_len=0.16):
    """A sharpened wooden stake from base to top (the last bit is a lighter, cut point)."""
    d = [top[i] - base[i] for i in range(3)]
    length = math.sqrt(sum(v * v for v in d)) or 1
    k = max(0.0, 1 - tip_len / length)
    neck = tuple(base[i] + d[i] * k for i in range(3))
    lp.beam(base, neck, radius, colour, sides=5)
    lp.beam(neck, top, radius, TIP, sides=5, end_radius=0.0)


def spike_barricade(lp):
    """Crossed sharpened stakes pushed through a log (a cheval-de-frise)."""
    rnd = lp.rnd
    lp.beam((-1.45, 0.42, 0), (1.45, 0.42, 0), 0.12, BARK[0], sides=7)
    n = 8
    for i in range(n):
        x = -1.25 + i * 2.5 / (n - 1)
        for sgn in (1, -1):
            a = math.radians(40) * sgn + (rnd.random() - 0.5) * 0.18
            dy, dz = math.cos(a), math.sin(a)
            reach = 0.95 + rnd.random() * 0.2
            base = (x + sgn * 0.03, 0.42 - dy * 0.5, -dz * 0.5)
            top = (x + (rnd.random() - 0.5) * 0.08, 0.42 + dy * reach, dz * reach)
            _stake(lp, base, top, 0.045, rnd.choice(WOOD))
    for x in (-0.9, 0.0, 0.9):                                # rope lashings
        lp.cylinder((x, 0.29, 0), 0.135, 0.06, ROPE, sides=7)


def plank_barricade(lp):
    """Planks nailed across two posts with spikes sticking out of the front."""
    rnd = lp.rnd
    for x in (-1.25, 1.25):
        lp.box((x, 0.62, 0), (0.15, 1.24, 0.15), BARK[1])
        lp.beam((x, 1.0, -0.05), (x * 0.95, 0.0, -0.62), 0.05, BARK[0])    # struts behind
    for k, y in enumerate((0.32, 0.66, 1.0)):
        lp.box((0, y, 0.1), (2.75, 0.26, 0.07), WOOD[k % 3], yaw=(rnd.random() - 0.5) * 2)
        for x in (-1.25, 1.25):                                            # nail heads
            lp.box((x, y, 0.14), (0.035, 0.035, 0.02), '#3a3a3c')
        for j in range(4):                                                 # spikes
            x = -1.0 + j * 0.66 + (rnd.random() - 0.5) * 0.2
            _stake(lp, (x, y, 0.1), (x + (rnd.random() - 0.5) * 0.25, y + (rnd.random() - 0.3) * 0.25, 0.62),
                   0.035, rnd.choice(WOOD), tip_len=0.14)


def palisade(lp):
    """A wall of tall pointed logs bound with rope, braced front and back."""
    rnd = lp.rnd
    n = 11
    for i in range(n):
        x = -1.38 + i * 2.76 / (n - 1)
        r = 0.12 + rnd.random() * 0.025
        h = 2.25 + rnd.random() * 0.3
        lp.cylinder((x, 0, 0), r, h, rnd.choice(BARK), sides=7, top_radius=r * 0.94, cap=False)
        lp.cylinder((x, h, 0), r * 0.94, 0.3, TIP, sides=7, top_radius=0.0)
    for y in (0.55, 1.75):                                    # rope bands
        lp.box((0, y, 0), (2.98, 0.08, 0.3), ROPE)
    lp.beam((-1.6, 0.95, 0.3), (1.6, 0.95, 0.3), 0.1, BARK[0], sides=6)   # front rail
    for x in (-1.55, 1.55):                                   # leaning end posts
        lp.beam((x, 0.0, 0.62), (x * 0.97, 1.25, 0.24), 0.09, BARK[2], sides=6)
        lp.cylinder((x * 0.985, 0.88, 0.36), 0.12, 0.12, ROPE, sides=6)
    for x in (-0.9, 0.9):                                     # props behind
        lp.beam((x, 0.0, -0.95), (x, 1.6, -0.12), 0.08, BARK[1], sides=6)


def turret_base(lp):
    """Tripod and post of the sentry turret."""
    for a in (90, 210, 330):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        lp.beam((0, 0.78, 0), (c * 0.52, 0.02, s * 0.52), 0.035, '#3b3e43', sides=5)
        lp.cylinder((c * 0.52, 0, s * 0.52), 0.06, 0.03, '#202226', sides=6)
    lp.cylinder((0, 0.5, 0), 0.075, 0.42, METAL, sides=8)
    lp.cylinder((0, 0.55, 0), 0.1, 0.05, '#3b3e43', sides=8)
    lp.beam((0.06, 0.66, 0), (0.22, 0.66, 0.0), 0.012, '#555960', sides=4)  # crank handle
    lp.box((0.23, 0.66, 0.0), (0.03, 0.06, 0.03), '#202226')


def turret_head(lp):
    """The gun that turns to aim: six spinning barrels, ammo box and a sight. Pivot at (0, 0, 0)."""
    lp.spec = 0.6
    lp.box((0, 0, -0.06), (0.2, 0.2, 0.34), METAL)                          # housing
    lp.beam((0, 0, 0.1), (0, 0, 0.3), 0.09, '#3a3d42', sides=10)           # barrel shroud
    for k in range(6):
        a = k / 6 * math.tau
        x, y = math.cos(a) * 0.05, math.sin(a) * 0.05
        lp.beam((x, y, 0.28), (x, y, 0.78), 0.018, '#45484e', sides=5)
    lp.beam((0, 0, 0.52), (0, 0, 0.56), 0.078, METAL, sides=10)            # barrel clamp
    lp.beam((0, 0, 0.74), (0, 0, 0.8), 0.08, '#202226', sides=10)          # muzzle ring
    lp.box((0.17, -0.03, -0.04), (0.12, 0.24, 0.28), OLIVE)                # ammo box
    lp.box((0.17, 0.095, -0.04), (0.125, 0.02, 0.285), '#4b5235')
    for k in range(5):                                                     # brass belt
        lp.box((0.1, 0.06 - k * 0.012, -0.04 + k * 0.045), (0.03, 0.012, 0.03), '#c9a227')
    lp.box((0, 0.14, -0.04), (0.06, 0.06, 0.16), '#1f2124')                # sight
    lp.spec = 0.0
    lp.emissive = True
    lp.box((0, 0.14, 0.045), (0.035, 0.035, 0.01), '#7fe7ff')              # sight lens
    lp.emissive = False
    lp.beam((-0.02, -0.02, -0.23), (-0.02, -0.1, -0.33), 0.018, '#202226', sides=4)   # handles
    lp.beam((0.02, -0.02, -0.23), (0.02, -0.1, -0.33), 0.018, '#202226', sides=4)


def landmine(lp):
    """A round olive mine half buried in the dirt, with a fuze and a pull ring."""
    lp.cylinder((0, -0.01, 0), 0.36, 0.025, '#6b5039', sides=12)           # disturbed soil
    lp.cylinder((0, 0.0, 0), 0.27, 0.07, OLIVE, sides=16, top_colour='#687047')
    lp.cylinder((0, 0.07, 0), 0.21, 0.015, '#626a43', sides=16)
    lp.cylinder((0, 0.085, 0), 0.075, 0.02, '#2b2d28', sides=10)            # fuze well
    lp.cylinder((0, 0.1, 0), 0.035, 0.045, '#3b3e3a', sides=8)
    ring = [(0.075 + math.cos(k / 8 * math.tau) * 0.045, 0.12, math.sin(k / 8 * math.tau) * 0.045) for k in range(8)]
    for k in range(8):                                                      # pull ring
        lp.beam(ring[k], ring[(k + 1) % 8], 0.006, '#4a4d50', sides=4)
    lp.box((-0.13, 0.071, 0.07), (0.075, 0.004, 0.05), '#a89a78')            # stencilled label
    lp.emissive = True
    lp.box((0.15, 0.088, 0.04), (0.025, 0.012, 0.025), '#e03a3a')            # armed light
    lp.emissive = False


THREE_WIDE = [(-1, 0), (0, 0), (1, 0)]

BARRICADES = {
    'spikes': dict(
        name='Spike barricade', build=spike_barricade, cells=THREE_WIDE, height=1, hp=450,
        cost={'wood': 20, 'iron': 5},
        desc='Crossed sharpened stakes. Zombies that push against it or attack it get hurt.',
        thorns=dict(dps=22, hit=30)),
    'planks': dict(
        name='Plank barricade', build=plank_barricade, cells=THREE_WIDE, height=1, hp=650,
        cost={'wood': 25, 'iron': 5},
        desc='Waist-high planks with spikes. Zombies have to break it; you can vault over it.'),
    'palisade': dict(
        name='Palisade wall', build=palisade, cells=THREE_WIDE, height=3, hp=1400,
        cost={'wood': 40, 'stone': 10},
        desc='A tall wall of pointed logs. Takes a long time to break and stops spit.'),
    'turret': dict(
        name='Sentry turret', build=turret_base, build_head=turret_head, cells=[(0, 0)], height=1, hp=400,
        cost={'iron': 60, 'copper': 40, 'crystal': 2},
        desc='Shoots zombies by itself. Hold E next to it to refill its ammo.',
        turret=dict(range=18, rate=9, damage=16, ammo=300, head_y=0.95, reload_cost={'iron': 10, 'copper': 10})),
    'landmine': dict(
        name='Landmine', build=landmine, cells=[(0, 0)], height=0, hp=1,
        cost={'iron': 15, 'copper': 10, 'stone': 5},
        desc='Explodes when a zombie steps on it. Arms 2 seconds after you place it.',
        mine=dict(radius=3.6, damage=450, trigger=1.1, arm=2.0)),
}

MAX_CARRIED = 10           # how many of each kind you can carry
MAX_PLACED = 40            # how many one player can have standing at once (all kinds together)
REPAIR_RATE = 120          # hp per second while holding E next to a damaged barricade
REPAIR_COST = 10           # hp repaired per 1 wood
PLACE_RANGE = 7.0          # metres in front of you
