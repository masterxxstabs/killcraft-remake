# ─────────────────────────────────────────────────────────────────────────────
#  WAVES
#  build_wave(n) decides which enemies show up in wave n. Tweak the weights to
#  change how often each enemy appears.
# ─────────────────────────────────────────────────────────────────────────────
import random

BOSS = 'hollow_king'
BOSS_EVERY = 5        # a boss shows up every Nth wave
MODIFIER_EVERY = 4    # a special modifier every Nth wave
INTERMISSION = 25     # seconds of shopping time between waves

NORMAL_SKY = dict(sky='#8ec9f0', fog='#a9d6f2', fog_near=30, fog_far=110)

# Special wave modifiers. Add your own! Anything left out uses the normal value.
MODIFIERS = [
    dict(id='bloodmoon', name='BLOOD MOON', desc='Enemies are 35% faster.',
         speed_mult=1.35, sky='#3b0707', fog='#3b0707', fog_near=10, fog_far=70),
    dict(id='fog', name='THE FOG', desc='You can barely see past your nose.',
         sky='#a9b2b6', fog='#a9b2b6', fog_near=1, fog_far=17),
    dict(id='swarm', name='SWARM', desc='Twice as many enemies, but they are fragile.',
         count_mult=2, hp_mult=0.5, sky='#4b3a6b', fog='#4b3a6b', fog_near=20, fog_far=90),
    dict(id='goldrush', name='GOLD RUSH', desc='Enemies drop triple coins.',
         coin_mult=3, sky='#f2c14e', fog='#e8b84a', fog_near=25, fog_far=100),
]


def weights(n):
    return {
        'shambler': 10,
        'sprinter': 2 + n * 0.45 if n >= 3 else 0,
        'brute': 0.7 + n * 0.15 if n >= 4 else 0,
        'spitter': 1.5 + n * 0.2 if n >= 6 else 0,
    }


def build_wave(n):
    modifier = MODIFIERS[(n // MODIFIER_EVERY - 1) % len(MODIFIERS)] if n % MODIFIER_EVERY == 0 else None
    mod = modifier or {}
    total = round((6 + n * 2.6) * mod.get('count_mult', 1))
    w = weights(n)
    kinds = [k for k in w if w[k] > 0]
    enemies = random.choices(kinds, weights=[w[k] for k in kinds], k=total)
    if n % BOSS_EVERY == 0:
        enemies.insert(min(3, len(enemies)), BOSS)
    return dict(
        number=n,
        enemies=enemies,
        modifier=modifier,
        max_alive=min(12 + n * 2, 45),
        spawn_interval=max(0.3, 1.3 - n * 0.06),
        hp_mult=(1 + 0.16 * (n - 1)) * mod.get('hp_mult', 1),
        damage_mult=1 + 0.06 * (n - 1),
        speed_mult=mod.get('speed_mult', 1),
        coin_mult=mod.get('coin_mult', 1),
        clear_bonus=30 + n * 12,
    )
