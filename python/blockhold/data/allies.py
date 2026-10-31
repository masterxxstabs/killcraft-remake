# ─────────────────────────────────────────────────────────────────────────────
#  FRIENDLY SURVIVORS  (hired in the shop: ALLIES tab)
#    hp, speed       health and walking speed
#    gun             which detailed gun model they hold (see gun_models.py)
#    damage, rate, spread, range, sound    how they shoot
#    heal            health per second they give their boss when close (medics)
#    colors / look   how they're painted (same options as enemies, plus human=True,
#                    beard, goggles, helmet)
# ─────────────────────────────────────────────────────────────────────────────

ALLY_TYPES = {
    'rookie': dict(
        name='Rookie', price=300, desc='Cheap and cheerful. Pistol.', hp=90, speed=5.2,
        gun='glock', damage=20, rate=2.5, spread=0.05, range=40, sound='pistol',
        colors=dict(skin='#e0b08a', shirt='#4f7fb8', pants='#3b3b46', eyes='#3a2a1a'),
        look=dict(human=True, hair='#6b4a2b', top='shirt', blood=False),
    ),
    'gunner': dict(
        name='Gunner', price=750, desc='Steady with a rifle.', hp=140, speed=5.0,
        gun='ar15', damage=30, rate=5, spread=0.025, range=70, sound='rifle',
        colors=dict(skin='#c68f63', shirt='#556043', pants='#3e4530', eyes='#1d1e22'),
        look=dict(human=True, hair='#1d1e22', top='shirt', blood=False, helmet='#4f5a3a', belt=True),
    ),
    'medic': dict(
        name='Medic', price=650, desc='Heals you 5 HP/s when close. SMG.', hp=110, speed=5.4, heal=5,
        gun='mp5', damage=16, rate=7, spread=0.04, range=45, sound='smg',
        colors=dict(skin='#f0c8a0', shirt='#e8e8e4', pants='#4a4f5a', eyes='#2a5a8a'),
        look=dict(human=True, hair='#c9a050', top='shirt', blood=False, cross=True),
    ),
    'heavy': dict(
        name='Heavy', price=1300, desc='Machine gun and a lot of health.', hp=300, speed=4.2,
        gun='m249', damage=24, rate=9, spread=0.05, range=60, sound='battle_rifle',
        colors=dict(skin='#8a5a3a', shirt='#3a3d42', pants='#2a2c30', eyes='#1d1e22'),
        look=dict(human=True, hair='#1d1e22', top='vest', blood=False, beard=True, belt=True, goggles=True),
    ),
}
MAX_ALLIES = 3
