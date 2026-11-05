# ─────────────────────────────────────────────────────────────────────────────
#  CRAFTING (at workbenches)
#  Every weapon you can buy can also be crafted instead of bought with coins. Guns need
#  scrap parts (Rust-style, from barrels and loot containers): springs, pipes, and an SMG or
#  rifle body for the bigger ones, plus a few ingots. Its cost is worked out from its price
#  and category (weapon_cost below). To set a weapon's cost by hand, give it a `craft` field
#  in weapons.py, e.g. craft={'iron_ingot': 15, 'spring': 2}
#  Workbenches use ingots (smelted in a furnace), not raw ore.
#
#  ITEMS are other things you can craft. kind:
#    'weapon'   gives the weapon `weapon`
#    'heal'     heals `amount` straight away (nothing uses this now: medical items go in the backpack)
#    'item'     puts `item` (data/items.py) in your inventory: medical items, clothing and armor
#               (wear them from the inventory screen, I)
#  Barricades (data/barricades.py) are added to the recipes automatically.
# ─────────────────────────────────────────────────────────────────────────────

ITEMS = [
    dict(id='bandage', kind='item', item='bandage', name='Bandage', cost={'cloth': 4},
         desc='+30 health. Takes 2.5 s to put on (press H).'),
    dict(id='medkit', kind='item', item='medkit', name='Medkit', cost={'cloth': 4, 'duct_tape': 1, 'copper_ingot': 2},
         desc='+70 health. Takes 5 s to use (press H).'),
    dict(id='surgery_kit', kind='item', item='surgery_kit', name='Surgical kit',
         cost={'cloth': 6, 'tech_trash': 1, 'copper_ingot': 4, 'crystal': 1},
         desc='Heals you completely. Takes 8 s to use (press H).'),
]

# clothing: what you can carry depends on what you wear (each piece adds a grid, see items.py)
CLOTHING_RECIPES = [
    ('hoodie', {'cloth': 12}, 'Warm, with a big front pocket.'),
    ('field_jacket', {'cloth': 16, 'tarp': 1, 'rope': 2}, 'Lots of pockets.'),
    ('cargo_pants', {'cloth': 14, 'rope': 1}, 'Pockets down both legs.'),
    ('chest_rig', {'cloth': 8, 'rope': 3, 'duct_tape': 1}, 'Pouches strapped to your chest.'),
    ('tactical_rig', {'cloth': 10, 'tarp': 1, 'rope': 4, 'screws': 10}, 'A proper load-bearing rig.'),
    ('satchel', {'cloth': 8, 'rope': 2}, 'A small bag over the shoulder.'),
    ('backpack', {'cloth': 10, 'tarp': 1, 'rope': 3}, 'A school-sized backpack.'),
    ('hiking_pack', {'cloth': 10, 'tarp': 2, 'rope': 4, 'metal_frags': 15}, 'A big framed pack.'),
    ('military_pack', {'cloth': 12, 'tarp': 3, 'rope': 6, 'duct_tape': 2}, 'The biggest pack there is.'),
]

# armor you wear (data/items.py has how much it protects): goes in your backpack, put it on with I
ARMOR_RECIPES = [
    ('cap_helmet', {'metal_frags': 20, 'cloth': 4}, 'A dented pot with padding. Better than nothing.'),
    ('combat_helmet', {'sheet_metal': 1, 'iron_ingot': 6, 'cloth': 4}, 'A proper steel helmet.'),
    ('riot_helmet', {'sheet_metal': 2, 'iron_ingot': 10, 'copper_ingot': 4, 'crystal': 1},
     'Heavy helmet with a face shield.'),
    ('padded_vest', {'cloth': 16, 'metal_frags': 20}, 'Thick padding with a few metal plates sewn in.'),
    ('kevlar_vest', {'cloth': 20, 'tarp': 2, 'iron_ingot': 6}, 'Soft body armor that stops most bites.'),
    ('plate_carrier', {'sheet_metal': 4, 'iron_ingot': 12, 'tarp': 2, 'crystal': 2},
     'Steel plates front and back. The best there is.'),
]

# the scrap parts each kind of gun needs (on top of ingots and scrap worked out from its price)
GUN_PARTS = {
    'pistol': {'spring': 1, 'pipe': 1},
    'smg': {'smg_body': 1, 'spring': 2, 'pipe': 1},
    'rifle': {'rifle_body': 1, 'spring': 2, 'pipe': 1},
    'shotgun': {'rifle_body': 1, 'spring': 1, 'pipe': 2},
    'sniper': {'rifle_body': 1, 'spring': 2, 'pipe': 2, 'gears': 1},
    'heavy': {'sheet_metal': 2, 'pipe': 2, 'gears': 2},
    'special': {'tech_trash': 1, 'gears': 1, 'spring': 1},
}

CRYSTAL_WEAPONS = {'torch', 'frostbite', 'arc', 'railspike', 'shredder', 'firework'}


def _r5(v):
    return max(5, int(round(v / 5.0)) * 5)


def _half(v):
    """Ingots: half as many as the ore it used to cost (each ingot takes 2 ore to smelt)."""
    return max(2, int(round(_r5(v) / 2)))


def weapon_cost(d):
    """What it takes to craft weapon d (worked out from its coin price and category)."""
    if d.get('craft'):
        return dict(d['craft'])
    pts = d['price'] / 10
    if d.get('melee'):
        cost = {'stone': _r5(pts * 0.6), 'iron_ingot': _half(pts * 0.5)}
        if d['price'] >= 300:
            cost['duct_tape'] = 1
        return cost
    cost = {'iron_ingot': _half(pts * 0.3), 'scrap': _r5(pts * 0.6)}
    for part, n in GUN_PARTS.get(d.get('category', 'special'), GUN_PARTS['special']).items():
        cost[part] = n
    if d['price'] >= 600:
        cost['gears'] = cost.get('gears', 0) + 1
    if d['price'] >= 250:
        cost['copper_ingot'] = _half(pts * 0.2)
    if d['id'] in CRYSTAL_WEAPONS or d['price'] >= 1000:
        cost['crystal'] = max(1, round(pts / 35))
    return cost


def all_recipes():
    """Everything a workbench can make: [dict(id, name, kind, cost, desc, category, weapon?)]"""
    from .weapons import WEAPONS
    from .barricades import BARRICADES
    from .items import ARMOR, ITEMS as BAG_ITEMS
    out = [dict(r, category='items') for r in ITEMS]
    for item_id, cost, desc in CLOTHING_RECIPES:
        c, r = BAG_ITEMS[item_id]['grid']
        out.append(dict(id='c_' + item_id, kind='item', item=item_id, name=BAG_ITEMS[item_id]['name'], cost=cost,
                        category='clothing', desc=f"{desc} Gives you a {c} x {r} grid ({BAG_ITEMS[item_id]['slot']})."))
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
