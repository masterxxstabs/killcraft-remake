# ─────────────────────────────────────────────────────────────────────────────
#  SHOP UPGRADES
#  Each upgrade can be bought many times; the price goes up every level
#  (price * growth ^ level). apply(player) runs once per purchase.
# ─────────────────────────────────────────────────────────────────────────────


def _vitality(p):
    p.max_health += 25
    p.health += 25


def _power(p):
    p.damage_mult += 0.12


def _swift(p):
    p.speed_mult += 0.07


def _regen(p):
    p.regen += 0.6


def _hands(p):
    p.reload_mult *= 0.88
    p.fire_rate_mult += 0.06


def _armor(p):
    p.armor = min(0.6, p.armor + 0.06)


def _magnet(p):
    p.magnet += 2


def _medkit(p):
    p.health = p.max_health


UPGRADES = [
    dict(id='vitality', name='Vitality', desc='+25 max health (and heals that much).', price=60, growth=1.45, max=20, apply=_vitality),
    dict(id='power', name='Power', desc='+12% damage with every weapon.', price=80, growth=1.5, max=25, apply=_power),
    dict(id='swift', name='Swift Boots', desc='+7% movement speed.', price=50, growth=1.6, max=8, apply=_swift),
    dict(id='regen', name='Regeneration', desc='+0.6 health per second.', price=70, growth=1.55, max=15, apply=_regen),
    dict(id='hands', name='Quick Hands', desc='-12% reload time, +6% fire rate.', price=65, growth=1.55, max=6, apply=_hands),
    dict(id='armor', name='Plating', desc='Take 6% less damage.', price=90, growth=1.6, max=8, apply=_armor),
    dict(id='magnet', name='Coin Magnet', desc='Pick up coins from further away.', price=40, growth=1.5, max=6, apply=_magnet),
    dict(id='medkit', name='Medkit', desc='Instantly restore all health.', price=45, growth=1.0, max=999, consumable=True, apply=_medkit),
]
