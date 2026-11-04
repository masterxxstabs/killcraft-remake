# ─────────────────────────────────────────────────────────────────────────────
#  ENEMIES
#  Every enemy is a blocky humanoid. Change colours, size and stats freely, or
#  add a brand-new type and then add it to the wave weights in waves.py.
#
#  Fields:
#    name        shown on the boss bar / kill feed
#    hp          health at wave 1 (it grows every wave)
#    speed       metres per second
#    damage      melee damage per hit
#    attack_rate melee hits per second
#    reach       melee range
#    scale       size multiplier (1 = player sized)
#    coins       (min, max) coins dropped
#    score       points for killing it
#    pose        'reach' (arms forward), 'run' (arms swinging), 'heavy' (arms down)
#    colors      skin / shirt / pants / eyes
#    look        how the skin is painted:
#                  hair   hair colour (None = bald)
#                  top    'shirt', 'tank' (sleeveless), 'vest' (open chest) or 'robe'
#                  shoes  shoe colour
#                  blood  True = blood stains
#                  mouth  'teeth', 'open' or 'drool'
#                  scar   True = stitched scar on the face
#                  belt   True = belt with a buckle
#                  extras list of extra 3D parts: 'shoulder_pads', 'belly', 'crown', 'cape', 'mohawk'
#    ranged      optional dict(range, rate, speed, damage, count, spread, color)
#    boss        True = gets the big health bar
#
#  Special behaviours (added in 1.21, mix and match):
#    crawl       True = no legs to stand on: drags itself along the ground (low and hard to hit)
#    burst       dict(radius, damage, cloud, dps, seconds): pops when it dies, hurting everything near
#                and leaving a toxic cloud that hurts players who stand in it
#    scream      dict(range, every, frenzy, seconds, summons): stops and shrieks when it sees you:
#                zombies within `range` get `frenzy` x speed for `seconds`, and `summons` more climb out
#    armor       0..1: how much body shots (and melee) are reduced. Headshots always do full damage
#    shove_proof True = shoves only make it stumble
#    leap        dict(min, max, every, damage): pounces at you from min..max metres away
#    fireproof   True = can't be set on fire
#    blast_resist  damage from explosions is multiplied by this
#  New 3D extras: 'riot_helmet', 'riot_vest', 'fire_helmet', 'air_tank', 'long_hair', 'boils'
# ─────────────────────────────────────────────────────────────────────────────

ENEMIES = {
    'shambler': dict(
        name='Shambler', hp=60, speed=2.3, damage=9, attack_rate=1, reach=1.7, scale=1,
        coins=(4, 7), score=10, pose='reach',
        colors=dict(skin='#6aa84f', shirt='#2f6f9f', pants='#2c2f5a', eyes='#111111'),
        look=dict(hair='#3b2a1a', top='shirt', mouth='open', blood=True),
    ),
    'sprinter': dict(
        name='Sprinter', hp=34, speed=5.2, damage=6, attack_rate=1.6, reach=1.5, scale=0.82,
        coins=(5, 8), score=14, pose='run',
        colors=dict(skin='#b7c95a', shirt='#a8322d', pants='#3d2b1f', eyes='#ffef5a'),
        look=dict(hair='#c9b04a', top='tank', shoes='#d0d0d0', mouth='teeth', extras=['mohawk']),
    ),
    'brute': dict(
        name='Brute', hp=320, speed=1.7, damage=26, attack_rate=0.6, reach=2.4, scale=1.6,
        coins=(15, 24), score=40, pose='heavy',
        colors=dict(skin='#4b7a3a', shirt='#4a4a4a', pants='#26262b', eyes='#ff3b3b'),
        look=dict(hair=None, top='vest', mouth='teeth', scar=True, belt=True, extras=['shoulder_pads']),
    ),
    'spitter': dict(
        name='Spitter', hp=48, speed=2.0, damage=6, attack_rate=1, reach=1.6, scale=0.95,
        coins=(7, 11), score=18, pose='reach',
        colors=dict(skin='#8e5fb5', shirt='#3b8f5a', pants='#2a2a2a', eyes='#c3ff4d'),
        look=dict(hair=None, top='shirt', mouth='drool', blood=False, extras=['belly']),
        ranged=dict(range=20, rate=0.45, speed=13, damage=9, count=1, spread=0, color='#9cff3a'),
    ),
    # ── added in 1.21 ──
    'crawler': dict(
        name='Crawler', hp=45, speed=1.5, damage=8, attack_rate=1.2, reach=1.4, scale=0.95,
        coins=(5, 8), score=12, pose='crawl', crawl=True,
        colors=dict(skin='#7d9a5a', shirt='#5a4a3a', pants='#2a2520', eyes='#ff5a3a'),
        look=dict(hair='#2a1f14', top='shirt', mouth='open', blood=True),
    ),
    'bloater': dict(
        name='Bloater', hp=150, speed=1.55, damage=12, attack_rate=0.8, reach=1.9, scale=1.25,
        coins=(10, 15), score=25, pose='heavy',
        burst=dict(radius=4.5, damage=18, cloud=3.0, dps=4, seconds=5),
        colors=dict(skin='#a8b84a', shirt='#6b7a3a', pants='#3a3a2a', eyes='#ffe14d'),
        look=dict(hair=None, top='tank', mouth='drool', blood=False, extras=['belly', 'boils']),
    ),
    'screamer': dict(
        name='Screamer', hp=70, speed=2.7, damage=7, attack_rate=1.2, reach=1.6, scale=0.9,
        coins=(10, 16), score=30, pose='reach',
        scream=dict(range=15, every=9.0, frenzy=1.45, seconds=5.0, summons=2),
        colors=dict(skin='#d8d4c8', shirt='#e8e4da', pants='#5a5a62', eyes='#ff2b2b'),
        look=dict(hair='#1a1a1e', top='robe', mouth='open', blood=True, extras=['long_hair']),
    ),
    'riot': dict(
        name='Riot Zombie', hp=160, speed=2.1, damage=14, attack_rate=1.0, reach=1.8, scale=1.05,
        coins=(12, 18), score=30, pose='reach', armor=0.7, shove_proof=True,
        colors=dict(skin='#6a8a52', shirt='#1f2a3a', pants='#161c26', eyes='#e8e86a'),
        look=dict(hair=None, top='vest', mouth='teeth', blood=True, belt=True,
                  extras=['riot_helmet', 'riot_vest']),
    ),
    'leaper': dict(
        name='Leaper', hp=55, speed=3.3, damage=10, attack_rate=1.4, reach=1.5, scale=0.85,
        coins=(8, 12), score=22, pose='run',
        leap=dict(min=4.0, max=11.0, every=4.5, damage=18),
        colors=dict(skin='#8aa04a', shirt='#3a3f46', pants='#22252a', eyes='#ff8c1a'),
        look=dict(hair='#3a2a1a', top='tank', mouth='teeth', blood=True, scar=True),
    ),
    'firefighter': dict(
        name='Firefighter', hp=210, speed=2.0, damage=16, attack_rate=0.9, reach=1.9, scale=1.1,
        coins=(14, 20), score=35, pose='heavy', fireproof=True, blast_resist=0.5,
        colors=dict(skin='#7a9a5a', shirt='#c8a028', pants='#2a2a2e', eyes='#ffb43a'),
        look=dict(hair=None, top='shirt', mouth='open', blood=True, belt=True,
                  extras=['fire_helmet', 'air_tank']),
    ),
    'hollow_king': dict(
        name='The Hollow King', hp=2600, speed=2.1, damage=35, attack_rate=0.7, reach=3.6, scale=2.6,
        coins=(120, 160), score=500, pose='heavy', boss=True,
        colors=dict(skin='#2c2c34', shirt='#5e1a7a', pants='#1a1a22', eyes='#ff8c1a'),
        look=dict(hair='#111116', top='robe', mouth='open', blood=False, extras=['crown', 'cape']),
        ranged=dict(range=30, rate=0.35, speed=15, damage=14, count=5, spread=0.22, color='#ff8c1a'),
    ),
    # summoned by the secret altar (see quests.py) - never appears in normal waves
    'hollow_herald': dict(
        name='The Hollow Herald', hp=1700, speed=3.4, damage=28, attack_rate=1.0, reach=2.8, scale=2.1,
        coins=(150, 200), score=800, pose='reach', boss=True,
        colors=dict(skin='#3a2456', shirt='#1b1030', pants='#120a20', eyes='#e0a8ff'),
        look=dict(hair='#0a0612', top='robe', mouth='open', blood=False, extras=['crown', 'cape']),
        ranged=dict(range=28, rate=0.5, speed=17, damage=12, count=3, spread=0.15, color='#c07bff'),
    ),
}
