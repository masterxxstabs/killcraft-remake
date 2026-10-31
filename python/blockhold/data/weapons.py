# ─────────────────────────────────────────────────────────────────────────────
#  WEAPONS
#  Add a new gun by copying one of the entries below and changing the numbers.
#  It shows up in the shop automatically, with its own upgrades.
#
#  Basic fields:
#    id          unique name used in code (no spaces)
#    category    which shop tab it's in (see CATEGORIES below)
#    name        what the player sees
#    desc        shop description
#    price       coins to buy (0 = you start with it)
#    damage      damage per hit / per pellet
#    rate        shots (or swings) per second
#    auto        True = hold the mouse button to keep firing
#    mag         bullets per magazine (reserve ammo is unlimited)
#    reload      seconds to reload
#    pellets     bullets per shot (shotguns use more than 1)
#    spread      how inaccurate each bullet is (0 = laser accurate)
#    range       how far bullets / swings reach (metres)
#    knockback   how hard hits push enemies back
#    headshot    damage multiplier for head hits (default 2)
#    sound       which shot sound to use (see sounds.py)
#    tracer      bullet trail colour
#    length      how long the gun is, in metres (used to size downloaded 3D models)
#    hold        optional (x, y, z) where the gun sits on screen, e.g. (0.2, -0.2, 0.45)
#
#  Special fields (mix and match!):
#    melee       True = close-range swing, no ammo
#    cleave      melee only: how many enemies one swing can hit
#    pierce      True = bullets go through every enemy (not walls), or a number = how many
#    projectile  dict(speed, radius, damage) = fires an exploding rocket
#    cone        dict(angle, range) = sprays everything in front of you (flamethrower)
#    burn        dict(dps, seconds) = sets enemies on fire
#    slow        dict(mult, seconds) = freezes enemies (mult 0.5 = half speed)
#    chain       dict(count, range, falloff) = hits jump to nearby enemies
#    spinup      seconds to reach full fire rate (miniguns)
#    move_mult   your movement speed while holding it
#    scope       True = right-click zooms in a long way (sniper scope)
#    hidden      True = not sold in the shop (secret weapons)
#    lifesteal   health you get back for every hit
#
#  The 3D model is a list of boxes:  (material, (width, height, length), (x, y, z))
#    x = right, y = up, z = forward. The hand holds the gun at (0, 0, 0).
#    material is one of the WEAPON_TILES in textures.py:
#      steel dark polymer black wood grip brass rust orange red camo chrome
#      blade tape frost gold tan glow_cyan glow_green glow_orange glow_purple
#    Add 'spin' as a 4th value to make a part spin while firing.
#  muzzle = where bullets come out of the model.
#
#  Want a real 3D model instead? See tools/sketchfab_guns.py - downloaded models
#  in models/<weapon id>/ replace the box model automatically.
# ─────────────────────────────────────────────────────────────────────────────

WEAPONS = [
    dict(
        id='wrench', category='melee', name='Rusty Wrench', desc='Close-range bonk. Never needs reloading.',
        price=0, melee=True, damage=40, rate=2.2, range=2.6, knockback=6, length=0.5,
        model=[
            ('rust', (0.035, 0.05, 0.40), (0, 0, 0.16)),
            ('grip', (0.045, 0.06, 0.13), (0, 0, -0.02)),
            ('rust', (0.12, 0.05, 0.06), (0, 0, 0.38)),
            ('rust', (0.035, 0.05, 0.09), (-0.045, 0, 0.44)),
            ('rust', (0.035, 0.05, 0.06), (0.045, 0, 0.43)),
            ('steel', (0.02, 0.054, 0.025), (0, 0, 0.34)),
        ],
        muzzle=(0, 0, 0.45),
    ),
    dict(
        id='pistol', category='pistol', name='Pebble Pistol', desc='Reliable sidearm. Click fast!',
        price=0, damage=26, rate=5, mag=12, reload=1.1, spread=0.008, range=80, knockback=1.5,
        sound='pistol', length=0.26,
        model=[
            ('dark', (0.045, 0.07, 0.26), (0, 0.02, 0.10)),
            ('steel', (0.047, 0.02, 0.22), (0, 0.06, 0.10)),
            ('polymer', (0.04, 0.05, 0.20), (0, -0.025, 0.08)),
            ('grip', (0.042, 0.13, 0.07), (0, -0.09, -0.01)),
            ('steel', (0.03, 0.035, 0.05), (0, -0.05, 0.07)),
            ('black', (0.022, 0.022, 0.01), (0, 0.03, 0.233)),
            ('brass', (0.012, 0.016, 0.012), (0, 0.078, 0.2)),
        ],
        muzzle=(0, 0.03, 0.24),
    ),
    dict(
        id='revolver', category='pistol', name='Six-Shooter', desc='Huge damage, six shots. Headshots hit extra hard.',
        price=150, damage=72, rate=2.2, mag=6, reload=2.0, spread=0.004, range=90, knockback=3,
        headshot=2.5, sound='heavy_pistol', length=0.34,
        model=[
            ('steel', (0.032, 0.032, 0.22), (0, 0.03, 0.17)),
            ('steel', (0.024, 0.016, 0.2), (0, 0.054, 0.17)),
            ('dark', (0.075, 0.075, 0.08), (0, 0.01, 0.03)),
            ('brass', (0.078, 0.02, 0.06), (0, 0.01, 0.03)),
            ('dark', (0.05, 0.06, 0.09), (0, 0.0, -0.035)),
            ('wood', (0.046, 0.13, 0.06), (0, -0.09, -0.06)),
            ('steel', (0.02, 0.03, 0.03), (0, 0.05, -0.075)),
            ('brass', (0.01, 0.02, 0.012), (0, 0.068, 0.27)),
        ],
        muzzle=(0, 0.03, 0.29),
    ),
    dict(
        id='nailgun', category='smg', name='Nail Gun', desc='Hold to spray nails. Big magazine.',
        price=180, damage=17, rate=11, auto=True, mag=45, reload=1.8, spread=0.03, range=70,
        knockback=0.8, sound='nailgun', length=0.4,
        model=[
            ('orange', (0.09, 0.12, 0.30), (0, 0.02, 0.12)),
            ('polymer', (0.07, 0.04, 0.22), (0, 0.10, 0.10)),
            ('steel', (0.045, 0.045, 0.12), (0, 0.0, 0.31)),
            ('black', (0.02, 0.02, 0.01), (0, 0.0, 0.373)),
            ('grip', (0.06, 0.14, 0.07), (0, -0.10, 0.0)),
            ('steel', (0.03, 0.16, 0.04), (0, -0.06, 0.2)),
            ('orange', (0.08, 0.035, 0.09), (0, -0.18, 0.0)),
            ('tape', (0.094, 0.124, 0.05), (0, 0.02, 0.05)),
        ],
        muzzle=(0, 0, 0.38),
    ),
    dict(
        id='smg', category='smg', name='Buzz SMG', desc='Tiny bullets, insane fire rate.',
        price=260, damage=14, rate=15, auto=True, mag=36, reload=1.6, spread=0.04, range=60,
        knockback=0.5, sound='smg', length=0.5,
        model=[
            ('dark', (0.06, 0.08, 0.32), (0, 0.02, 0.12)),
            ('steel', (0.03, 0.03, 0.12), (0, 0.03, 0.33)),
            ('black', (0.042, 0.042, 0.06), (0, 0.03, 0.4)),
            ('polymer', (0.045, 0.17, 0.05), (0, -0.1, 0.16)),
            ('grip', (0.05, 0.12, 0.06), (0, -0.08, 0.0)),
            ('polymer', (0.04, 0.04, 0.14), (0, 0.0, -0.1)),
            ('steel', (0.02, 0.03, 0.04), (0, 0.075, 0.05)),
            ('glow_green', (0.014, 0.014, 0.014), (0, 0.095, 0.05)),
        ],
        muzzle=(0, 0.03, 0.43),
    ),
    dict(
        id='scatter', category='shotgun', name='Scattercannon', desc='Nine pellets per blast. Devastating up close.',
        price=320, damage=14, rate=1.4, mag=6, reload=2.1, pellets=9, spread=0.085, range=35,
        knockback=3, sound='scatter', length=0.7,
        model=[
            ('steel', (0.05, 0.05, 0.5), (0, 0.04, 0.25)),
            ('dark', (0.04, 0.04, 0.4), (0, -0.01, 0.22)),
            ('wood', (0.07, 0.065, 0.14), (0, -0.01, 0.3)),
            ('dark', (0.07, 0.09, 0.2), (0, 0.01, 0.0)),
            ('wood', (0.06, 0.13, 0.07), (0, -0.09, -0.06)),
            ('wood', (0.06, 0.09, 0.2), (0, -0.04, -0.2)),
            ('black', (0.03, 0.03, 0.01), (0, 0.04, 0.503)),
            ('brass', (0.012, 0.012, 0.012), (0, 0.072, 0.48)),
        ],
        muzzle=(0, 0.04, 0.52),
    ),
    dict(
        id='axe', category='melee', name='Fire Axe', desc='Heavy swing that cleaves through up to 3 enemies.',
        price=350, melee=True, damage=120, rate=1.1, range=3.0, cleave=3, knockback=9, gather=1.5, length=0.7,
        model=[
            ('wood', (0.04, 0.04, 0.6), (0, 0, 0.22)),
            ('grip', (0.048, 0.048, 0.13), (0, 0, -0.03)),
            ('red', (0.034, 0.09, 0.16), (0, 0.05, 0.48)),
            ('blade', (0.036, 0.05, 0.2), (0, 0.11, 0.48)),
            ('steel', (0.03, 0.06, 0.05), (0, -0.03, 0.48)),
        ],
        muzzle=(0, 0.1, 0.55),
    ),
    dict(
        id='pickaxe', category='melee', name='Pickaxe', desc='Mines ore 2.5x faster than other melee weapons.',
        price=120, melee=True, damage=55, rate=1.5, range=2.7, knockback=5, gather=2.5, length=0.6,
        craft={'stone': 25},
        model=[
            ('wood', (0.04, 0.04, 0.58), (0, 0, 0.2)),
            ('grip', (0.048, 0.048, 0.13), (0, 0, -0.04)),
            ('steel', (0.045, 0.07, 0.06), (0, 0, 0.47)),
            ('steel', (0.034, 0.3, 0.045), (0, 0.0, 0.47)),
            ('blade', (0.026, 0.07, 0.035), (0, 0.18, 0.455)),
            ('blade', (0.026, 0.07, 0.035), (0, -0.18, 0.455)),
        ],
        muzzle=(0, 0.1, 0.5),
    ),
    dict(
        id='rifle', category='rifle', name='Ranger Rifle', desc='Accurate automatic rifle. A great all-rounder.',
        price=480, damage=34, rate=8, auto=True, mag=30, reload=1.9, spread=0.012, range=100,
        knockback=1.2, sound='rifle', length=0.85,
        model=[
            ('dark', (0.06, 0.09, 0.36), (0, 0.02, 0.12)),
            ('polymer', (0.07, 0.07, 0.22), (0, 0.02, 0.38)),
            ('camo', (0.074, 0.074, 0.1), (0, 0.02, 0.4)),
            ('steel', (0.025, 0.025, 0.16), (0, 0.03, 0.56)),
            ('black', (0.04, 0.04, 0.05), (0, 0.03, 0.65)),
            ('dark', (0.045, 0.16, 0.07), (0, -0.11, 0.15)),
            ('grip', (0.05, 0.12, 0.06), (0, -0.08, -0.01)),
            ('polymer', (0.05, 0.08, 0.22), (0, 0.0, -0.15)),
            ('dark', (0.035, 0.05, 0.12), (0, 0.1, 0.08)),
            ('glow_orange', (0.022, 0.022, 0.01), (0, 0.11, 0.02)),
        ],
        muzzle=(0, 0.03, 0.68),
    ),
    dict(
        id='torch', category='special', name='Torch', desc='Flamethrower. Sets everything in front of you on fire.',
        price=550, damage=5, rate=20, auto=True, mag=120, reload=2.5, range=9, knockback=0.2,
        cone=dict(angle=16, range=9), burn=dict(dps=16, seconds=3), sound='spit', length=0.6,
        model=[
            ('red', (0.13, 0.13, 0.24), (0, -0.04, -0.05)),
            ('steel', (0.14, 0.02, 0.02), (0, -0.04, -0.1)),
            ('steel', (0.14, 0.02, 0.02), (0, -0.04, 0.02)),
            ('steel', (0.05, 0.05, 0.4), (0, 0.06, 0.2)),
            ('brass', (0.075, 0.075, 0.06), (0, 0.06, 0.42)),
            ('black', (0.03, 0.03, 0.01), (0, 0.06, 0.453)),
            ('glow_orange', (0.025, 0.025, 0.035), (0, 0.015, 0.44)),
            ('grip', (0.05, 0.12, 0.06), (0, -0.09, 0.14)),
        ],
        muzzle=(0, 0.06, 0.47),
    ),
    dict(
        id='railspike', category='sniper', name='Railspike', desc='Pierces every enemy in a line. Triple headshot damage.',
        price=600, damage=240, rate=0.9, mag=4, reload=2.4, spread=0, range=150, pierce=True, scope=True,
        headshot=3, knockback=4, sound='railspike', tracer='#7fe7ff', length=0.9,
        model=[
            ('dark', (0.07, 0.1, 0.4), (0, 0.02, 0.12)),
            ('chrome', (0.02, 0.025, 0.5), (-0.028, 0.05, 0.45)),
            ('chrome', (0.02, 0.025, 0.5), (0.028, 0.05, 0.45)),
            ('glow_cyan', (0.02, 0.02, 0.44), (0, 0.05, 0.42)),
            ('steel', (0.09, 0.035, 0.05), (0, 0.05, 0.27)),
            ('steel', (0.09, 0.035, 0.05), (0, 0.05, 0.45)),
            ('steel', (0.09, 0.035, 0.05), (0, 0.05, 0.63)),
            ('grip', (0.05, 0.12, 0.06), (0, -0.09, 0.0)),
            ('polymer', (0.05, 0.08, 0.2), (0, 0.0, -0.18)),
            ('glow_cyan', (0.06, 0.06, 0.06), (0, -0.06, 0.2)),
        ],
        muzzle=(0, 0.05, 0.72),
    ),
    dict(
        id='frostbite', category='special', name='Frostbite', desc='Freeze ray. Slows enemies to a crawl and pierces.',
        price=700, damage=9, rate=12, auto=True, mag=80, reload=2.2, spread=0.006, range=30,
        pierce=True, slow=dict(mult=0.4, seconds=2), knockback=0.1, sound='blink', tracer='#9fdcff',
        length=0.5,
        model=[
            ('chrome', (0.08, 0.1, 0.28), (0, 0.02, 0.1)),
            ('frost', (0.105, 0.105, 0.05), (0, 0.02, 0.18)),
            ('frost', (0.105, 0.105, 0.05), (0, 0.02, 0.28)),
            ('steel', (0.04, 0.04, 0.12), (0, 0.02, 0.36)),
            ('glow_cyan', (0.065, 0.065, 0.03), (0, 0.02, 0.43)),
            ('frost', (0.05, 0.1, 0.05), (0, 0.11, 0.05)),
            ('grip', (0.05, 0.12, 0.06), (0, -0.09, 0.0)),
        ],
        muzzle=(0, 0.02, 0.45),
    ),
    dict(
        id='arc', category='special', name='Arc Caster', desc='Lightning jumps between up to 4 enemies.',
        price=850, damage=55, rate=2.5, mag=16, reload=2.0, spread=0.004, range=50,
        chain=dict(count=4, range=7, falloff=0.75), knockback=1, sound='railspike', tracer='#c07bff',
        length=0.5,
        model=[
            ('dark', (0.07, 0.09, 0.26), (0, 0.02, 0.08)),
            ('brass', (0.032, 0.032, 0.22), (0, 0.02, 0.3)),
            ('brass', (0.095, 0.095, 0.025), (0, 0.02, 0.24)),
            ('brass', (0.095, 0.095, 0.025), (0, 0.02, 0.3)),
            ('brass', (0.095, 0.095, 0.025), (0, 0.02, 0.36)),
            ('glow_purple', (0.045, 0.045, 0.045), (0, 0.02, 0.43)),
            ('glow_purple', (0.05, 0.05, 0.08), (0, 0.09, 0.02)),
            ('grip', (0.05, 0.12, 0.06), (0, -0.09, 0.0)),
        ],
        muzzle=(0, 0.02, 0.45),
    ),
    dict(
        id='firework', category='heavy', name='Firework Launcher', desc='Explosive rockets. Hits everything nearby.',
        price=950, damage=0, rate=1.1, mag=3, reload=2.6, spread=0.004, range=120, knockback=10,
        projectile=dict(speed=32, radius=5, damage=220), sound='firework', length=0.75,
        model=[
            ('red', (0.14, 0.14, 0.6), (0, 0.04, 0.18)),
            ('brass', (0.155, 0.155, 0.04), (0, 0.04, 0.47)),
            ('black', (0.1, 0.1, 0.01), (0, 0.04, 0.493)),
            ('brass', (0.155, 0.155, 0.04), (0, 0.04, -0.1)),
            ('grip', (0.05, 0.12, 0.06), (0, -0.09, 0.12)),
            ('polymer', (0.04, 0.06, 0.08), (0, 0.14, 0.2)),
            ('glow_orange', (0.022, 0.022, 0.01), (0, 0.15, 0.158)),
        ],
        muzzle=(0, 0.04, 0.5),
    ),
    dict(
        id='shredder', category='heavy', name='Shredder', desc='Minigun. Spins up, then never stops. Slows you down.',
        price=1400, damage=16, rate=24, auto=True, mag=200, reload=3.5, spread=0.045, range=70,
        spinup=0.9, move_mult=0.8, knockback=0.6, sound='smg', length=0.75,
        model=[
            ('dark', (0.15, 0.15, 0.22), (0, 0.0, 0.0)),
            ('steel', (0.03, 0.03, 0.45), (0, 0.04, 0.33), 'spin'),
            ('steel', (0.03, 0.03, 0.45), (0, -0.04, 0.33), 'spin'),
            ('steel', (0.03, 0.03, 0.45), (0.035, 0.02, 0.33), 'spin'),
            ('steel', (0.03, 0.03, 0.45), (-0.035, 0.02, 0.33), 'spin'),
            ('steel', (0.03, 0.03, 0.45), (0.035, -0.02, 0.33), 'spin'),
            ('steel', (0.03, 0.03, 0.45), (-0.035, -0.02, 0.33), 'spin'),
            ('dark', (0.12, 0.12, 0.03), (0, 0.0, 0.3), 'spin'),
            ('dark', (0.12, 0.12, 0.03), (0, 0.0, 0.52), 'spin'),
            ('brass', (0.06, 0.1, 0.12), (0.1, -0.05, 0.0)),
            ('grip', (0.05, 0.12, 0.06), (0, -0.13, -0.05)),
            ('steel', (0.04, 0.04, 0.14), (0, 0.1, -0.02)),
        ],
        muzzle=(0, 0, 0.56),
    ),
    # ── real-world guns ──────────────────────────────────────────────────────
    dict(
        id='glock', category='pistol', name='Glock 17', desc='Light, fast-firing 9mm with a big magazine.',
        price=90, damage=24, rate=7, mag=17, reload=1.1, spread=0.01, range=80, knockback=1.2,
        sound='pistol', length=0.21,
        model=[
            ('polymer', (0.042, 0.05, 0.2), (0, 0.03, 0.085)),
            ('polymer', (0.04, 0.035, 0.17), (0, -0.005, 0.07)),
            ('grip', (0.04, 0.12, 0.06), (0, -0.08, -0.005)),
            ('polymer', (0.03, 0.03, 0.04), (0, -0.04, 0.06)),
            ('steel', (0.03, 0.01, 0.1), (0, 0.056, 0.09)),
            ('black', (0.018, 0.018, 0.01), (0, 0.03, 0.186)),
            ('glow_green', (0.008, 0.008, 0.008), (0, 0.06, 0.17)),
        ],
        muzzle=(0, 0.03, 0.19),
    ),
    dict(
        id='m1911', category='pistol', name='M1911', desc='Classic .45 pistol. Hard-hitting and reliable.',
        price=120, damage=40, rate=4, mag=8, reload=1.3, spread=0.006, range=85, knockback=2,
        sound='heavy_pistol', length=0.22,
        model=[
            ('steel', (0.04, 0.05, 0.22), (0, 0.03, 0.09)),
            ('dark', (0.038, 0.035, 0.17), (0, -0.005, 0.07)),
            ('wood', (0.042, 0.12, 0.06), (0, -0.08, -0.01)),
            ('steel', (0.03, 0.03, 0.045), (0, -0.04, 0.06)),
            ('dark', (0.02, 0.025, 0.02), (0, 0.065, -0.015)),
            ('black', (0.02, 0.02, 0.01), (0, 0.03, 0.201)),
            ('dark', (0.01, 0.012, 0.01), (0, 0.06, 0.18)),
        ],
        muzzle=(0, 0.03, 0.21),
    ),
    dict(
        id='deagle', category='pistol', name='Desert Eagle', desc='Hand cannon. Enormous damage, heavy kick.',
        price=400, damage=110, rate=1.8, mag=7, reload=1.8, spread=0.006, range=90, knockback=4,
        headshot=2.5, sound='heavy_pistol', length=0.27,
        model=[
            ('chrome', (0.05, 0.06, 0.28), (0, 0.035, 0.11)),
            ('chrome', (0.03, 0.02, 0.24), (0, 0.072, 0.12)),
            ('chrome', (0.046, 0.04, 0.2), (0, -0.01, 0.08)),
            ('polymer', (0.045, 0.13, 0.07), (0, -0.09, -0.01)),
            ('chrome', (0.032, 0.032, 0.05), (0, -0.045, 0.07)),
            ('black', (0.024, 0.024, 0.01), (0, 0.035, 0.251)),
        ],
        muzzle=(0, 0.035, 0.26),
    ),
    dict(
        id='uzi', category='smg', name='Uzi', desc='Compact bullet hose. Not very accurate.',
        price=220, damage=15, rate=16, auto=True, mag=32, reload=1.6, spread=0.05, range=55,
        knockback=0.5, sound='smg', length=0.42,
        model=[
            ('dark', (0.06, 0.08, 0.3), (0, 0.02, 0.1)),
            ('steel', (0.025, 0.025, 0.06), (0, 0.01, 0.28)),
            ('grip', (0.045, 0.17, 0.06), (0, -0.11, 0.06)),
            ('dark', (0.035, 0.05, 0.04), (0, -0.21, 0.06)),
            ('dark', (0.015, 0.015, 0.18), (0, -0.02, -0.12)),
            ('dark', (0.02, 0.04, 0.02), (0, 0.075, 0.2)),
        ],
        muzzle=(0, 0.01, 0.31),
    ),
    dict(
        id='mp5', category='smg', name='MP5', desc='Smooth, accurate submachine gun.',
        price=300, damage=18, rate=13, auto=True, mag=30, reload=1.7, spread=0.02, range=70,
        knockback=0.7, sound='smg', length=0.55,
        model=[
            ('dark', (0.055, 0.07, 0.3), (0, 0.02, 0.12)),
            ('polymer', (0.065, 0.06, 0.13), (0, 0.0, 0.3)),
            ('steel', (0.025, 0.025, 0.06), (0, 0.02, 0.39)),
            ('dark', (0.03, 0.02, 0.2), (0, 0.065, 0.15)),
            ('dark', (0.035, 0.17, 0.045), (0, -0.11, 0.17)),
            ('polymer', (0.045, 0.12, 0.06), (0, -0.08, -0.01)),
            ('polymer', (0.045, 0.07, 0.18), (0, 0.01, -0.13)),
            ('dark', (0.02, 0.04, 0.02), (0, 0.09, 0.03)),
            ('dark', (0.02, 0.035, 0.02), (0, 0.085, 0.3)),
        ],
        muzzle=(0, 0.02, 0.42),
    ),
    dict(
        id='ar15', category='rifle', name='AR-15', desc='Precise semi-auto rifle with a red dot. Rewards headshots.',
        price=500, damage=46, rate=7, mag=30, reload=1.9, spread=0.005, range=110, knockback=1.4,
        headshot=2.5, sound='rifle', length=0.85,
        model=[
            ('dark', (0.055, 0.08, 0.3), (0, 0.02, 0.1)),
            ('dark', (0.02, 0.03, 0.24), (0, 0.075, 0.1)),
            ('polymer', (0.065, 0.065, 0.24), (0, 0.02, 0.36)),
            ('steel', (0.022, 0.022, 0.14), (0, 0.025, 0.54)),
            ('black', (0.03, 0.03, 0.04), (0, 0.025, 0.62)),
            ('dark', (0.02, 0.06, 0.02), (0, 0.075, 0.47)),
            ('dark', (0.04, 0.15, 0.06), (0, -0.1, 0.12)),
            ('grip', (0.045, 0.11, 0.055), (0, -0.075, -0.02)),
            ('dark', (0.02, 0.02, 0.1), (0, 0.03, -0.08)),
            ('polymer', (0.05, 0.09, 0.13), (0, 0.0, -0.18)),
            ('dark', (0.035, 0.04, 0.06), (0, 0.105, 0.08)),
            ('glow_green', (0.02, 0.022, 0.01), (0, 0.108, 0.048)),
        ],
        muzzle=(0, 0.025, 0.64),
    ),
    dict(
        id='ak47', category='rifle', name='AK-47', desc='Hits hard and never jams. Kicks like a mule.',
        price=520, damage=40, rate=9.5, auto=True, mag=30, reload=2.2, spread=0.025, range=95,
        knockback=1.6, sound='battle_rifle', length=0.88,
        model=[
            ('dark', (0.055, 0.08, 0.34), (0, 0.02, 0.1)),
            ('dark', (0.045, 0.02, 0.3), (0, 0.07, 0.1)),
            ('wood', (0.06, 0.06, 0.18), (0, 0.0, 0.33)),
            ('wood', (0.045, 0.03, 0.14), (0, 0.05, 0.32)),
            ('dark', (0.025, 0.025, 0.24), (0, 0.03, 0.52)),
            ('dark', (0.02, 0.02, 0.18), (0, 0.065, 0.45)),
            ('black', (0.035, 0.035, 0.05), (0, 0.03, 0.66)),
            ('dark', (0.02, 0.05, 0.02), (0, 0.065, 0.62)),
            ('dark', (0.04, 0.16, 0.06), (0, -0.1, 0.14)),
            ('dark', (0.04, 0.06, 0.06), (0, -0.2, 0.18)),
            ('wood', (0.045, 0.12, 0.06), (0, -0.08, -0.03)),
            ('wood', (0.05, 0.09, 0.26), (0, -0.02, -0.2)),
        ],
        muzzle=(0, 0.03, 0.69),
    ),
    dict(
        id='asval', category='rifle', name='AS Val', desc='Built-in silencer. Quiet, fast and deadly accurate.',
        price=680, damage=36, rate=11, auto=True, mag=20, reload=2.0, spread=0.01, range=80,
        headshot=2.5, knockback=1, sound='suppressed', length=0.8,
        model=[
            ('dark', (0.05, 0.075, 0.28), (0, 0.02, 0.08)),
            ('dark', (0.062, 0.062, 0.3), (0, 0.025, 0.36)),
            ('black', (0.04, 0.04, 0.01), (0, 0.025, 0.511)),
            ('polymer', (0.07, 0.065, 0.1), (0, 0.0, 0.24)),
            ('dark', (0.04, 0.11, 0.06), (0, -0.085, 0.12)),
            ('grip', (0.045, 0.11, 0.055), (0, -0.075, -0.02)),
            ('steel', (0.015, 0.015, 0.24), (0, 0.04, -0.15)),
            ('steel', (0.015, 0.015, 0.2), (0, -0.04, -0.14)),
            ('steel', (0.015, 0.1, 0.015), (0, 0.0, -0.26)),
            ('dark', (0.02, 0.04, 0.02), (0, 0.08, 0.05)),
        ],
        muzzle=(0, 0.025, 0.52),
    ),
    dict(
        id='scarh', category='rifle', name='SCAR-H', desc='Battle rifle with big bullets. Punches through 2 enemies.',
        price=750, damage=58, rate=7, auto=True, mag=20, reload=2.3, spread=0.014, range=120,
        pierce=2, knockback=2.5, sound='battle_rifle', length=0.9,
        model=[
            ('tan', (0.06, 0.09, 0.36), (0, 0.02, 0.12)),
            ('dark', (0.025, 0.03, 0.38), (0, 0.08, 0.15)),
            ('tan', (0.065, 0.07, 0.16), (0, 0.02, 0.38)),
            ('steel', (0.025, 0.025, 0.12), (0, 0.025, 0.52)),
            ('black', (0.04, 0.04, 0.05), (0, 0.025, 0.6)),
            ('tan', (0.045, 0.13, 0.07), (0, -0.1, 0.16)),
            ('grip', (0.045, 0.11, 0.055), (0, -0.075, -0.02)),
            ('tan', (0.055, 0.1, 0.22), (0, 0.0, -0.18)),
            ('dark', (0.04, 0.05, 0.08), (0, 0.12, 0.08)),
            ('glow_orange', (0.025, 0.025, 0.01), (0, 0.125, 0.035)),
        ],
        muzzle=(0, 0.025, 0.63),
    ),
    dict(
        id='remington', category='shotgun', name='Remington 870', desc='Pump shotgun. Eight pellets, big stopping power.',
        price=260, damage=17, rate=1.2, mag=6, reload=2.4, pellets=8, spread=0.07, range=35,
        knockback=3.5, sound='shotgun', length=0.9,
        model=[
            ('dark', (0.045, 0.045, 0.48), (0, 0.04, 0.28)),
            ('dark', (0.04, 0.035, 0.38), (0, 0.0, 0.24)),
            ('wood', (0.06, 0.06, 0.14), (0, 0.0, 0.27)),
            ('dark', (0.06, 0.085, 0.2), (0, 0.015, 0.0)),
            ('wood', (0.055, 0.12, 0.06), (0, -0.08, -0.08)),
            ('wood', (0.06, 0.1, 0.24), (0, -0.03, -0.22)),
            ('black', (0.03, 0.03, 0.01), (0, 0.04, 0.521)),
            ('brass', (0.012, 0.012, 0.012), (0, 0.07, 0.5)),
        ],
        muzzle=(0, 0.04, 0.53),
    ),
    dict(
        id='barrett', category='sniper', name='Barrett M82', desc='.50 cal anti-materiel rifle. Goes through everything.',
        price=1250, damage=450, rate=0.8, mag=10, reload=3.0, spread=0, range=200, pierce=True,
        headshot=3, knockback=8, sound='sniper', scope=True, move_mult=0.9, tracer='#ffe9a8', length=1.2,
        model=[
            ('dark', (0.07, 0.1, 0.42), (0, 0.02, 0.12)),
            ('dark', (0.035, 0.035, 0.4), (0, 0.03, 0.52)),
            ('steel', (0.08, 0.06, 0.08), (0, 0.03, 0.74)),
            ('dark', (0.06, 0.04, 0.16), (0, 0.03, 0.38)),
            ('dark', (0.045, 0.15, 0.08), (0, -0.11, 0.12)),
            ('grip', (0.045, 0.11, 0.055), (0, -0.075, -0.06)),
            ('polymer', (0.05, 0.11, 0.2), (0, -0.01, -0.2)),
            ('dark', (0.05, 0.06, 0.24), (0, 0.12, 0.1)),
            ('dark', (0.065, 0.07, 0.04), (0, 0.12, 0.24)),
            ('glow_cyan', (0.04, 0.04, 0.01), (0, 0.12, -0.025)),
        ],
        muzzle=(0, 0.03, 0.78),
    ),
    dict(
        id='m249', category='heavy', name='M249 SAW', desc='Belt-fed machine gun. 100 rounds before you reload.',
        price=1100, damage=26, rate=13, auto=True, mag=100, reload=4.0, spread=0.035, range=90,
        move_mult=0.85, knockback=1.2, sound='battle_rifle', length=0.95,
        model=[
            ('dark', (0.08, 0.1, 0.34), (0, 0.02, 0.1)),
            ('dark', (0.03, 0.03, 0.28), (0, 0.03, 0.4)),
            ('black', (0.04, 0.04, 0.05), (0, 0.03, 0.56)),
            ('dark', (0.06, 0.06, 0.12), (0, 0.0, 0.3)),
            ('dark', (0.02, 0.05, 0.08), (0, 0.08, 0.38)),
            ('camo', (0.1, 0.12, 0.1), (-0.07, -0.09, 0.12)),
            ('grip', (0.045, 0.11, 0.055), (0, -0.075, -0.03)),
            ('polymer', (0.05, 0.1, 0.22), (0, 0.0, -0.18)),
            ('dark', (0.06, 0.03, 0.18), (0, 0.08, 0.06)),
        ],
        muzzle=(0, 0.03, 0.58),
    ),
]

# The secret reward of the Hollow Lance quest (quests.py). Not sold in the shop.
WEAPONS.append(dict(
    id='hollow_lance', category='special', name='The Hollow Lance', hidden=True,
    desc='Forged from the Herald. Pierces, chains, and heals you on every hit.',
    price=0, damage=150, rate=3, mag=12, reload=1.6, spread=0, range=120, pierce=True, headshot=2,
    chain=dict(count=3, range=8, falloff=0.7), lifesteal=3, knockback=4, sound='railspike', tracer='#d6a3ff',
    length=0.8,
    model=[
        ('black', (0.06, 0.09, 0.42), (0, 0.02, 0.14)),
        ('glow_purple', (0.03, 0.03, 0.62), (0, 0.06, 0.38)),
        ('gold', (0.1, 0.1, 0.04), (0, 0.04, 0.22)),
        ('gold', (0.1, 0.1, 0.04), (0, 0.04, 0.42)),
        ('gold', (0.08, 0.08, 0.04), (0, 0.04, 0.6)),
        ('glow_purple', (0.07, 0.07, 0.07), (0, 0.06, 0.72)),
        ('black', (0.05, 0.13, 0.06), (0, -0.09, 0.0)),
        ('gold', (0.02, 0.16, 0.02), (0, 0.12, 0.72)),
        ('gold', (0.16, 0.02, 0.02), (0, 0.06, 0.72)),
    ],
    muzzle=(0, 0.06, 0.76),
))

# ─────────────────────────────────────────────────────────────────────────────
#  WEAPON UPGRADES  (bought per weapon in the shop)
#    bonus      how much each level adds (0.15 = +15%)
#    max        highest level
#    for_melee  True if melee weapons can have it, for_guns for guns
#  Price of a level = weapon_upgrade_price(weapon) * PRICE_GROWTH ^ level
# ─────────────────────────────────────────────────────────────────────────────

WEAPON_UPGRADES = [
    dict(id='damage', name='Damage', desc='+15% damage', bonus=0.15, max=5, for_melee=True, for_guns=True),
    dict(id='rate', name='Fire rate', desc='+10% fire / swing speed', bonus=0.10, max=5, for_melee=True, for_guns=True),
    dict(id='mag', name='Magazine', desc='+25% magazine size', bonus=0.25, max=5, for_melee=False, for_guns=True),
    dict(id='reload', name='Reload', desc='-12% reload time', bonus=0.12, max=5, for_melee=False, for_guns=True),
    dict(id='range', name='Reach', desc='+12% swing reach', bonus=0.12, max=3, for_melee=True, for_guns=False),
]
PRICE_GROWTH = 1.6


def weapon_upgrade_price(weapon):
    """Starting price for one weapon's upgrades. Cheap guns have cheap upgrades."""
    return round(40 + weapon['price'] * 0.3)


# ─────────────────────────────────────────────────────────────────────────────
#  SHOP CATEGORIES  (id, tab name). Weapons are listed by category, then price.
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIES = [
    ('melee', 'Melee'), ('pistol', 'Pistols'), ('smg', 'SMGs'), ('rifle', 'Rifles'),
    ('shotgun', 'Shotguns'), ('sniper', 'Snipers'), ('heavy', 'Heavy'), ('special', 'Special'),
]
_order = [c for c, _ in CATEGORIES]
WEAPONS.sort(key=lambda w: (_order.index(w.get('category', 'special')), w['price']))
