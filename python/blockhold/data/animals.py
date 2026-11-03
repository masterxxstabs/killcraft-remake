# ─────────────────────────────────────────────────────────────────────────────
#  PASSIVE ANIMALS  (placed with spawners in the map editor: ANIMALS & NPCS tab)
#
#  Animals wander around their spawner, stop to graze, and run off when a player
#  or a zombie gets close (or when they get hurt). Kill one for raw meat, then cook
#  it in a furnace and eat it from your backpack (right-click it) to heal.
#
#    name           shown when you hit it
#    hp             health
#    walk / run     speeds (metres per second) when wandering / running away
#    shy            how close (metres) a player can get before it runs
#    radius         how wide it is (for bumping into walls and getting shot)
#    height         how high its middle is off the ground (where bullets hit it)
#    meat           (fewest, most) raw meat it drops
#    count          how many one spawner makes
#    respawn        seconds until a new one comes back to the spawner
#    sound          pitch of its hurt sound
#
#  The model is in three parts so they can move: the body, the head (turned down to
#  graze around head_at) and one leg (copied to every hip, swings when it walks).
#  Animals face +z. Each part is drawn with the LowPoly builder (see assets.py).
# ─────────────────────────────────────────────────────────────────────────────


def deer_body(lp):
    fur, belly = '#9a6a3f', '#d9c3a0'
    lp.box((0, 1.0, 0), (0.42, 0.42, 1.05), fur)
    lp.box((0, 0.8, 0), (0.36, 0.06, 0.9), belly)
    lp.box((0, 1.12, -0.55), (0.14, 0.18, 0.08), '#f5f1ea')                           # white tail
    for x in (-0.12, 0.12):                                                         # spots
        lp.box((x * 1.8, 1.12, 0.1), (0.01, 0.06, 0.06), belly)
        lp.box((x * 1.8, 1.0, -0.2), (0.01, 0.06, 0.06), belly)


def deer_head(lp):
    """Neck and head together, so the whole neck bends down when it grazes."""
    fur = '#9a6a3f'
    lp.beam((0, 0, 0), (0, 0.4, 0.2), 0.12, fur, sides=6, end_radius=0.09)            # neck
    ox, oy, oz = 0, 0.42, 0.22                                                       # the head sits on top

    def at(x, y, z):
        return (ox + x, oy + y, oz + z)
    lp.box(at(0, 0.02, 0.1), (0.2, 0.2, 0.3), fur)
    lp.box(at(0, -0.03, 0.29), (0.14, 0.12, 0.12), '#7a5232')
    lp.box(at(0, -0.03, 0.36), (0.07, 0.05, 0.02), '#1f1a16')                       # nose
    for x in (-0.1, 0.1):
        lp.box(at(x, 0.06, 0.15), (0.02, 0.04, 0.04), '#1f1a16')                    # eyes
        lp.box(at(x * 1.4, 0.13, -0.02), (0.1, 0.05, 0.03), fur, yaw=x * 200)       # ears
    if lp.rnd.random() < 0.6:                                                       # a buck: antlers
        for sd in (-1, 1):
            a = at(sd * 0.06, 0.1, 0.0)
            b = at(sd * 0.2, 0.42, -0.05)
            lp.beam(a, b, 0.018, '#d9c7a0', sides=4)
            lp.beam(b, at(sd * 0.3, 0.55, 0.05), 0.014, '#d9c7a0', sides=4)
            lp.beam(b, at(sd * 0.12, 0.58, -0.1), 0.014, '#d9c7a0', sides=4)
            lp.beam(at(sd * 0.14, 0.3, -0.03), at(sd * 0.24, 0.36, 0.12), 0.012, '#d9c7a0', sides=4)


def deer_leg(lp):
    lp.beam((0, 0, 0), (0, -0.62, 0), 0.05, '#8a5c35', sides=5, end_radius=0.035)
    lp.beam((0, -0.62, 0), (0, -0.82, 0), 0.035, '#8a5c35', sides=5)
    lp.box((0, -0.81, 0.01), (0.07, 0.04, 0.08), '#2a2420')                         # hoof


def pig_body(lp):
    pink = '#e8a5a0'
    lp.box((0, 0.55, 0), (0.55, 0.48, 0.85), pink)
    lp.box((0, 0.33, 0), (0.45, 0.04, 0.7), '#d8908a')
    lp.beam((0, 0.66, -0.43), (0.05, 0.72, -0.5), 0.02, '#d8908a', sides=4)         # curly tail
    lp.beam((0.05, 0.72, -0.5), (-0.02, 0.76, -0.52), 0.02, '#d8908a', sides=4)
    if lp.rnd.random() < 0.4:                                                       # some have mud patches
        lp.box((0.2, 0.6, -0.15), (0.17, 0.3, 0.3), '#7a5a3f')


def pig_head(lp):
    pink = '#eaaaa5'
    lp.box((0, 0, 0.14), (0.4, 0.38, 0.3), pink)
    lp.box((0, -0.05, 0.33), (0.2, 0.15, 0.08), '#f0b8b2')                           # snout
    for x in (-0.05, 0.05):
        lp.box((x, -0.05, 0.375), (0.03, 0.04, 0.01), '#7a3a3a')                    # nostrils
    for x in (-0.11, 0.11):
        lp.box((x, 0.06, 0.29), (0.04, 0.04, 0.01), '#1f1a16')                      # eyes
        lp.box((x * 1.3, 0.2, 0.1), (0.12, 0.04, 0.12), '#d8908a', yaw=x * 150)    # ears


def pig_leg(lp):
    lp.box((0, -0.12, 0), (0.12, 0.24, 0.12), '#e0a09a')
    lp.box((0, -0.26, 0), (0.12, 0.04, 0.12), '#5a3a32')                            # trotter


def chicken_body(lp):
    white = lp.rnd.choice(['#f2efe6', '#f2efe6', '#b5713a', '#3a3530'])
    lp.blob((0, 0.36, 0), 0.17, white, squash=(0.85, 0.85, 1.15), jitter=0.1)
    lp.box((0, 0.5, -0.17), (0.12, 0.16, 0.06), white)                              # tail feathers
    for x in (-0.15, 0.15):
        lp.box((x, 0.37, -0.02), (0.03, 0.12, 0.2), white)                          # wings


def chicken_head(lp):
    white = '#f2efe6'
    lp.box((0, 0.05, 0.02), (0.11, 0.14, 0.11), white)
    lp.box((0, 0.05, 0.1), (0.05, 0.03, 0.06), '#f0b030')                           # beak
    lp.box((0, 0.13, 0.02), (0.03, 0.06, 0.09), '#d63a2a')                           # comb
    lp.box((0, 0.0, 0.08), (0.03, 0.05, 0.02), '#d63a2a')                           # wattle
    for x in (-0.056, 0.056):
        lp.box((x, 0.07, 0.04), (0.01, 0.025, 0.025), '#1f1a16')


def chicken_leg(lp):
    lp.beam((0, 0, 0), (0, -0.2, 0), 0.012, '#e0a030', sides=4)
    for yaw in (-30, 0, 30):                                                        # toes
        lp.box((0, -0.2, 0.03), (0.012, 0.01, 0.07), '#e0a030', yaw=yaw)


ANIMALS = {
    'deer': dict(name='Deer', hp=55, walk=1.6, run=8.5, shy=14, radius=0.45, height=1.0, meat=(2, 3),
                 count=3, respawn=(60, 90), sound=0.8,
                 body=deer_body, head=deer_head, leg=deer_leg, head_at=(0, 1.08, 0.42),
                 hips=[(-0.15, 0.86, 0.38), (0.15, 0.86, 0.38), (-0.15, 0.86, -0.38), (0.15, 0.86, -0.38)]),
    'pig': dict(name='Pig', hp=40, walk=1.1, run=4.8, shy=4, radius=0.45, height=0.55, meat=(2, 3),
                count=3, respawn=(45, 70), sound=0.7,
                body=pig_body, head=pig_head, leg=pig_leg, head_at=(0, 0.62, 0.42),
                hips=[(-0.17, 0.32, 0.27), (0.17, 0.32, 0.27), (-0.17, 0.32, -0.27), (0.17, 0.32, -0.27)]),
    'chicken': dict(name='Chicken', hp=10, walk=0.9, run=4.2, shy=3, radius=0.25, height=0.35, meat=(1, 1),
                    count=4, respawn=(30, 50), sound=1.5,
                    body=chicken_body, head=chicken_head, leg=chicken_leg, head_at=(0, 0.48, 0.15),
                    hips=[(-0.06, 0.21, 0.0), (0.06, 0.21, 0.0)]),
}
ANIMAL_KINDS = list(ANIMALS)

SPREAD = 7.0          # animals wander up to this far from their spawner
ZOMBIE_SCARE = 9.0    # and run from zombies closer than this
RANDOM_HERDS = 5      # on random arenas: this many groups (more on bigger maps)


def draw_whole(lp, kind, offset=(0, 0, 0), scale=1.0):
    """The whole animal in one mesh, standing still (for the editor's spawner marker)."""
    d = ANIMALS[kind]
    orig = lp.tri

    def shifted(off):
        def tri(a, b, c, colour, outward=None):
            def f(p):
                return (offset[0] + (p[0] + off[0]) * scale, offset[1] + (p[1] + off[1]) * scale,
                        offset[2] + (p[2] + off[2]) * scale)
            return orig(f(a), f(b), f(c), colour, f(outward) if outward is not None else None)
        return tri

    lp.tri = shifted((0, 0, 0))
    d['body'](lp)
    lp.tri = shifted(d['head_at'])
    d['head'](lp)
    for hip in d['hips']:
        lp.tri = shifted(hip)
        d['leg'](lp)
    del lp.tri                       # back to the normal method
