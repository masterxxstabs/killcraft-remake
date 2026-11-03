# ─────────────────────────────────────────────────────────────────────────────
#  CRAFTING (at workbenches)
#  Every weapon you can buy can also be crafted from resources instead of coins.
#  Its cost is worked out from its price (weapon_cost below). To set a weapon's
#  cost by hand, give it a `craft` field in weapons.py, e.g. craft={'iron_ingot': 15, 'stone': 10}
#  Workbenches use ingots (smelted in a furnace), not raw ore.
#
#  ITEMS are other things you can craft. kind:
#    'weapon'   gives the weapon `weapon`
#    'heal'     heals `amount` straight away (nothing uses this now: medical items go in the backpack)
#    'item'     puts `item` (data/items.py) in your backpack: armor you wear from the backpack (I)
#  Barricades (data/barricades.py) are added to the recipes automatically.
# ─────────────────────────────────────────────────────────────────────────────

ITEMS = [
    dict(id='bandage', kind='item', item='bandage', name='Bandage', cost={'wood': 6, 'copper_ingot': 1},
         desc='+30 health. Takes 2.5 s to put on (press H). Goes in your backpack.'),
    dict(id='medkit', kind='item', item='medkit', name='Medkit', cost={'copper_ingot': 4, 'iron_ingot': 2},
         desc='+70 health. Takes 5 s to use (press H). Goes in your backpack.'),
    dict(id='surgery_kit', kind='item', item='surgery_kit', name='Surgical kit',
         cost={'copper_ingot': 6, 'iron_ingot': 2, 'crystal': 1},
         desc='Heals you completely. Takes 8 s to use (press H). Goes in your backpack.'),
]

# armor you wear (data/items.py has how much it protects): goes in your backpack, put it on with I
ARMOR_RECIPES = [
    ('cap_helmet', {'iron_ingot': 4, 'wood': 10}, 'A dented pot with padding. Better than nothing.'),
    ('combat_helmet', {'iron_ingot': 12, 'copper_ingot': 4}, 'A proper steel helmet.'),
    ('riot_helmet', {'iron_ingot': 20, 'copper_ingot': 8, 'crystal': 1}, 'Heavy helmet with a face shield.'),
    ('padded_vest', {'wood': 20, 'iron_ingot': 4}, 'Thick padding with a few metal plates sewn in.'),
    ('kevlar_vest', {'iron_ingot': 14, 'copper_ingot': 8}, 'Soft body armor that stops most bites.'),
    ('plate_carrier', {'iron_ingot': 28, 'copper_ingot': 10, 'crystal': 2}, 'Steel plates front and back. The best there is.'),
]

CRYSTAL_WEAPONS = {'torch', 'frostbite', 'arc', 'railspike', 'shredder', 'firework'}


def _r5(v):
    return max(5, int(round(v / 5.0)) * 5)


def _half(v):
    """Ingots: half as many as the ore it used to cost (each ingot takes 2 ore to smelt)."""
    return max(2, int(round(_r5(v) / 2)))


def weapon_cost(d):
    """Resources needed to craft weapon d (worked out from its coin price)."""
    if d.get('craft'):
        return dict(d['craft'])
    pts = d['price'] / 10
    if d.get('melee'):
        return {'stone': _r5(pts * 0.6), 'iron_ingot': _half(pts * 0.5)}
    cost = {'iron_ingot': _half(pts * 0.5), 'stone': _r5(pts * 0.3)}
    if d['price'] >= 250:
        cost['copper_ingot'] = _half(pts * 0.3)
    if d['id'] in CRYSTAL_WEAPONS or d['price'] >= 1000:
        cost['crystal'] = max(1, round(pts / 35))
    return cost


def all_recipes():
    """Everything a workbench can make: [dict(id, name, kind, cost, desc, category, weapon?)]"""
    from .weapons import WEAPONS
    from .barricades import BARRICADES
    from .items import ARMOR, ITEMS as BAG_ITEMS
    out = [dict(r, category='items') for r in ITEMS]
    for item_id, cost, desc in ARMOR_RECIPES:
        a = ARMOR[item_id]
        out.append(dict(id='a_' + item_id, kind='item', item=item_id, name=BAG_ITEMS[item_id]['name'], cost=cost,
                        category='armor', desc=f"{desc} {round(a['protect'] * 100)}% less damage "
                                               f"({a['slot']}), lasts for {a['durability']} damage."))
    for key, b in BARRICADES.items():               # barricades can only be crafted, never bought
        out.append(dict(id='b_' + key, kind='placeable', placeable=key, name=b['name'], cost=b['cost'],
                        desc=b['desc'], category='build'))
    for d in WEAPONS:
        if d.get('hidden'):
            continue
        out.append(dict(id='w_' + d['id'], kind='weapon', weapon=d['id'], name=d['name'], cost=weapon_cost(d),
                        desc=d['desc'], category=d.get('category', 'special')))
    return out


def recipe(rid):
    return next((r for r in all_recipes() if r['id'] == rid), None)
