# ─────────────────────────────────────────────────────────────────────────────
#  POWER-UPS
#  Rare drops from zombies during a wave. Whoever walks into one triggers it for
#  the whole team.
#    name, desc  shown in the banner when it's picked up
#    color       token, banner and HUD colour
#    time        how long it lasts in seconds (0 = happens once)
#    weight      how often it drops compared to the others
# ─────────────────────────────────────────────────────────────────────────────

POWERUPS = {
    'instakill': dict(name='BONEBREAKER', desc='Every zombie dies in one hit (bosses excepted)',
                      color='#ff5a5a', time=15, weight=3),
    'double': dict(name='GOLD RUSH', desc='Double coins from every kill', color='#f2c230', time=20, weight=3),
    'overdrive': dict(name='OVERDRIVE', desc='Bottomless magazines, no reloading', color='#5ad1ff', time=12, weight=3),
    'blast': dict(name='SHOCK BLAST', desc='Every zombie nearby is blown apart. +150 coins each',
                  color='#ffffff', time=0, weight=1),
}

DROP_CHANCE = 0.03      # chance per kill
DROP_COOLDOWN = 20      # seconds before another one can drop
MAX_ON_GROUND = 2
LIFETIME = 25           # seconds before an untouched token fades away (it blinks for the last 6)
BLAST_RADIUS = 40       # metres from whoever picked it up
