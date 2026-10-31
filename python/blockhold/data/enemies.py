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
