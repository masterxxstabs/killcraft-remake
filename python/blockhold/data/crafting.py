# ─────────────────────────────────────────────────────────────────────────────
#  CRAFTING (at workbenches)
#  Every weapon you can buy can also be crafted from resources instead of coins.
#  Its cost is worked out from its price (weapon_cost below). To set a weapon's
#  cost by hand, give it a `craft` field in weapons.py, e.g. craft={'iron': 30, 'stone': 10}
#
#  ITEMS are other things you can craft. kind:
#    'weapon'   gives the weapon `weapon`
#    'heal'     heals `amount` straight away
#    'armor'    adds `amount` armor (0.05 = 5% less damage), up to `max`
# ─────────────────────────────────────────────────────────────────────────────

ITEMS = [
    dict(id='bandage', kind='heal', amount=40, name='Bandage', cost={'stone': 10, 'copper': 5},
         desc='Heals 40 health right away.'),
    dict(id='medkit', kind='heal', amount=100, name='Medkit', cost={'copper': 15, 'crystal': 1},
         desc='Heals you completely.'),
    dict(id='plating', kind='armor', amount=0.05, max=0.4, name='Armor plating', cost={'iron': 30, 'stone': 20},
         desc='5% less damage from everything, for the rest of the run. Stacks up to 40%.'),
]

CRYSTAL_WEAPONS = {'torch', 'frostbite', 'arc', 'railspike', 'shredder', 'firework'}


def _r5(v):
    return max(5, int(round(v / 5.0)) * 5)


def weapon_cost(d):
    """Resources needed to craft weapon d (worked out from its coin price)."""
    if d.get('craft'):
        return dict(d['craft'])
    pts = d['price'] / 10
    if d.get('melee'):
        return {'stone': _r5(pts * 0.6), 'iron': _r5(pts * 0.5)}
    cost = {'iron': _r5(pts * 0.5), 'stone': _r5(pts * 0.3)}
    if d['price'] >= 250:
        cost['copper'] = _r5(pts * 0.3)
    if d['id'] in CRYSTAL_WEAPONS or d['price'] >= 1000:
        cost['crystal'] = max(1, round(pts / 35))
    return cost


def all_recipes():
    """Everything a workbench can make: [dict(id, name, kind, cost, desc, category, weapon?)]"""
    from .weapons import WEAPONS
    out = [dict(r, category='items') for r in ITEMS]
    for d in WEAPONS:
        if d.get('hidden'):
            continue
        out.append(dict(id='w_' + d['id'], kind='weapon', weapon=d['id'], name=d['name'], cost=weapon_cost(d),
                        desc=d['desc'], category=d.get('category', 'special')))
    return out


def recipe(rid):
    return next((r for r in all_recipes() if r['id'] == rid), None)
