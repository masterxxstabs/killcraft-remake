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
#    ranged      optional dict(range, rate, speed, damage, count, spread, color)
#    boss        True = gets the big health bar and a crown
# ─────────────────────────────────────────────────────────────────────────────

ENEMIES = {
    'shambler': dict(
        name='Shambler', hp=60, speed=2.3, damage=9, attack_rate=1, reach=1.7, scale=1,
        coins=(4, 7), score=10, pose='reach',
        colors=dict(skin='#6aa84f', shirt='#2f6f9f', pants='#2c2f5a', eyes='#111111'),
    ),
    'sprinter': dict(
        name='Sprinter', hp=34, speed=5.2, damage=6, attack_rate=1.6, reach=1.5, scale=0.82,
        coins=(5, 8), score=14, pose='run',
        colors=dict(skin='#b7c95a', shirt='#a8322d', pants='#3d2b1f', eyes='#ffef5a'),
    ),
    'brute': dict(
        name='Brute', hp=320, speed=1.7, damage=26, attack_rate=0.6, reach=2.4, scale=1.6,
        coins=(15, 24), score=40, pose='heavy',
        colors=dict(skin='#4b7a3a', shirt='#4a4a4a', pants='#26262b', eyes='#ff3b3b'),
    ),
    'spitter': dict(
        name='Spitter', hp=48, speed=2.0, damage=6, attack_rate=1, reach=1.6, scale=0.95,
        coins=(7, 11), score=18, pose='reach',
        colors=dict(skin='#8e5fb5', shirt='#3b8f5a', pants='#2a2a2a', eyes='#c3ff4d'),
        ranged=dict(range=20, rate=0.45, speed=13, damage=9, count=1, spread=0, color='#9cff3a'),
    ),
    'hollow_king': dict(
        name='The Hollow King', hp=2600, speed=2.1, damage=35, attack_rate=0.7, reach=3.6, scale=2.6,
        coins=(120, 160), score=500, pose='heavy', boss=True,
        colors=dict(skin='#2c2c34', shirt='#5e1a7a', pants='#1a1a22', eyes='#ff8c1a'),
        ranged=dict(range=30, rate=0.35, speed=15, damage=14, count=5, spread=0.22, color='#ff8c1a'),
    ),
}
