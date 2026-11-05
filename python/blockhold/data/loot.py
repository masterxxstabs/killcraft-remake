# ─────────────────────────────────────────────────────────────────────────────
#  LOOT  (Rust-style scavenging: break barrels, open crates, take the parts home)
#
#  Two sorts of loot spot:
#    breakable   barrels and supply crates: hit or shoot them until they break, and what was
#                inside is left in a sack on the ground (E to open it). They're ore nodes
#                (resources.py) with a `loot` table.
#    container   toolboxes, medical boxes, military crates, clothes racks: E opens them
#                and you drag what you want into your pockets and clothes.
#  An emptied spot fills up again after RESPAWN seconds, but only while nobody is within
#  RESPAWN_CLEAR metres of it (so you never see it happen).
#
#  CONTAINERS fields:
#    name     shown when you look at it
#    grid     (cols, rows) of the loot grid
#    rolls    (min, max) piles rolled each time it fills
#    table    which TABLES entry it rolls from
#    asset    the map piece it's drawn as (data/assets.py)
#
#  TABLES: [(item id, chance weight, (min, max) amount)]. Rolls pick by weight; the same item
#  can come up twice (it piles up).
# ─────────────────────────────────────────────────────────────────────────────
import random

TABLES = {
    'barrel': [('scrap', 10, (3, 8)), ('metal_frags', 6, (5, 15)), ('spring', 3, (1, 1)), ('pipe', 3, (1, 1)),
               ('gears', 3, (1, 2)), ('rope', 3, (1, 2)), ('cloth', 4, (2, 5)), ('screws', 4, (4, 12)),
               ('tarp', 1, (1, 1)), ('sheet_metal', 1, (1, 1)), ('duct_tape', 1, (1, 1)),
               ('canned_food', 2, (1, 1))],
    'supply': [('wood', 6, (6, 14)), ('stone', 4, (4, 10)), ('coal', 3, (3, 8)), ('iron', 3, (3, 9)),
               ('copper', 2, (3, 8)), ('iron_ingot', 2, (1, 3)), ('copper_ingot', 1, (1, 3)), ('crystal', 0.6, (1, 2)),
               ('scrap', 5, (4, 10)), ('metal_frags', 3, (5, 12)), ('cloth', 2, (2, 5))],
    'toolbox': [('scrap', 6, (5, 12)), ('screws', 6, (8, 20)), ('gears', 5, (1, 3)), ('spring', 5, (1, 2)),
                ('pipe', 3, (1, 2)), ('duct_tape', 4, (1, 2)), ('tech_trash', 2, (1, 1)), ('metal_frags', 3, (8, 20)),
                ('gunpowder', 2, (10, 25))],
    'medical': [('bandage', 8, (1, 3)), ('medkit', 3, (1, 1)), ('surgery_kit', 0.5, (1, 1)), ('cloth', 4, (2, 4)),
                ('canned_food', 3, (1, 2)), ('duct_tape', 2, (1, 1))],
    'military': [('spring', 5, (1, 3)), ('pipe', 4, (1, 2)), ('gunpowder', 5, (20, 50)), ('smg_body', 2, (1, 1)),
                 ('rifle_body', 1.2, (1, 1)), ('tech_trash', 3, (1, 2)), ('sheet_metal', 2, (1, 1)),
                 ('combat_helmet', 0.7, (1, 1)), ('kevlar_vest', 0.5, (1, 1)), ('chest_rig', 1, (1, 1)),
                 ('medkit', 1.5, (1, 1)), ('canned_food', 1.5, (1, 2))],
    'clothes': [('tshirt', 3, (1, 1)), ('hoodie', 4, (1, 1)), ('field_jacket', 2, (1, 1)), ('jeans', 3, (1, 1)),
                ('cargo_pants', 3, (1, 1)), ('chest_rig', 1.5, (1, 1)), ('satchel', 3, (1, 1)),
                ('backpack', 2, (1, 1)), ('hiking_pack', 0.8, (1, 1)), ('military_pack', 0.3, (1, 1)),
                ('cloth', 4, (2, 6)), ('rope', 2, (1, 2))],
}

CONTAINERS = {
    'toolbox': dict(name='Toolbox', grid=(4, 2), rolls=(2, 4), table='toolbox', asset='loot_toolbox'),
    'medical': dict(name='Medical box', grid=(4, 3), rolls=(1, 3), table='medical', asset='loot_medical'),
    'military': dict(name='Military crate', grid=(6, 4), rolls=(2, 4), table='military', asset='loot_military'),
    'clothes': dict(name='Clothes rack', grid=(8, 5), rolls=(1, 3), table='clothes', asset='loot_clothes'),
    'sack': dict(name='Loot', grid=(5, 4), rolls=(0, 0), table='barrel'),     # what a broken barrel leaves behind
}

SACK_ROLLS = {'barrel': (2, 4), 'supply': (3, 5)}       # piles a broken barrel / supply crate leaves
SACK_TTL = 180.0              # seconds a sack lies there before it rots away
RESPAWN = (120.0, 240.0)      # seconds before an emptied container fills up again
RESPAWN_CLEAR = 15.0          # ...if no player is this close
OPEN_RANGE = 2.2              # how close you have to be to open one
RANDOM_CONTAINERS = 10        # containers scattered on a classic-size random arena (more on bigger maps)


def roll(table, rolls, rng=random):
    """[(item id, amount)] for one filling of a container."""
    rows = TABLES[table]
    out = []
    for _ in range(rng.randint(*rolls)):
        item, _, (lo, hi) = rng.choices(rows, weights=[r[1] for r in rows])[0]
        out.append((item, rng.randint(lo, hi)))
    return out
