# ─────────────────────────────────────────────────────────────────────────────
#  ITEMS  (everything you carry: open your inventory with I)
#
#  What you can carry depends on what you WEAR: your pockets are a small grid, and every
#  piece of clothing (top, trousers, rig, backpack) adds a grid of its own. Each item
#  takes up `size` cells (width, height) and can be turned 90° while you drag it (R).
#  Items with `stack` > 1 pile up in one spot. Everything weighs something: carry too
#  much and you slow down (see WEIGHT below).
#
#    name       shown in the backpack
#    size       (w, h) in grid cells
#    stack      how many fit in one pile
#    colour     the item's tile colour (and its little icon)
#    kind       'resource'  mined / chopped / smelted, spent at workbenches
#               'armor'     worn in the HEAD or BODY slot (see ARMOR below)
#               'food'      right-click it in the backpack to eat it: gives back `heal` health
#               'medical'   bandages and kits: H (or right-click in the backpack) to use; `heal` health
#                           (999 = all of it) after `use_time` seconds. You walk slowly and can't shoot
#                           while you use it; shooting or switching weapons stops it (nothing is used up)
#               'trade'     only good for trading with NPCs
#               'component' scrap parts from barrels and crates (springs, pipes, gears...): crafting
#               'clothing'  worn in TOP, LEGS, RIG or BACKPACK (`slot`); `grid` = (cols, rows) of room it gives
#    weight     kg for one (defaults by kind, see default_weight)
#    icon       how the tile is drawn: 'ore', 'ingot', 'log', 'coal', 'stone', 'crystal',
#               'helmet', 'vest', 'bandage', 'medkit', 'meat', 'feather', 'gem', 'coin', 'note',
#               'scrap', 'spring', 'pipe', 'gears', 'rope', 'cloth', 'plate', 'chip', 'tape', 'body',
#               'powder', 'can', 'shirt', 'pants', 'rig', 'pack'
# ─────────────────────────────────────────────────────────────────────────────

ITEMS = {
    # raw resources (from nodes, log piles and loot crates)
    'stone': dict(name='Stone', size=(1, 1), stack=100, colour='#a3a39f', kind='resource', icon='stone'),
    'wood': dict(name='Wood', size=(1, 1), stack=100, colour='#b98a52', kind='resource', icon='log'),
    'coal': dict(name='Coal', size=(1, 1), stack=60, colour='#3b3b40', kind='resource', icon='coal'),
    'iron': dict(name='Iron ore', size=(1, 1), stack=60, colour='#c3cfdb', kind='resource', icon='ore'),
    'copper': dict(name='Copper ore', size=(1, 1), stack=60, colour='#e0813a', kind='resource', icon='ore'),
    'crystal': dict(name='Crystal', size=(1, 1), stack=20, colour='#c07bff', kind='resource', icon='crystal'),
    # smelted in a furnace (2 ore + 1 coal -> 1 ingot); workbenches use these instead of ore
    'iron_ingot': dict(name='Iron ingot', size=(2, 1), stack=30, colour='#d7dee6', kind='resource', icon='ingot'),
    'copper_ingot': dict(name='Copper ingot', size=(2, 1), stack=30, colour='#e8955a', kind='resource',
                         icon='ingot'),
    # food: hunt animals for raw meat, cook it in a furnace, right-click it in the backpack to eat
    'raw_meat': dict(name='Raw meat', size=(1, 1), stack=20, colour='#d9606a', kind='food', icon='meat', heal=5,
                     use_time=1.5),
    'cooked_meat': dict(name='Cooked meat', size=(1, 1), stack=20, colour='#9a5a32', kind='food', icon='meat',
                        heal=35, use_time=2.0),
    # medical (crafted at a workbench, or a Medkit from the shop): H uses the best one for how hurt you are
    'bandage': dict(name='Bandage', size=(1, 1), stack=5, colour='#e8e4da', kind='medical', icon='bandage',
                    heal=30, use_time=2.5),
    'medkit': dict(name='Medkit', size=(2, 1), stack=3, colour='#d64541', kind='medical', icon='medkit',
                   heal=70, use_time=5.0),
    'surgery_kit': dict(name='Surgical kit', size=(2, 2), stack=1, colour='#2e9e6a', kind='medical',
                        icon='medkit', heal=999, use_time=8.0),
    # trade goods (animals and loot; NPC traders want them)
    'feather': dict(name='Feathers', size=(1, 1), stack=50, colour='#f2efe6', kind='trade', icon='feather'),
    'hide': dict(name='Deer hide', size=(2, 2), stack=10, colour='#9a6a3f', kind='trade', icon='hide'),
    'gold_coin': dict(name='Old gold coin', size=(1, 1), stack=50, colour='#e8c040', kind='trade', icon='coin'),
    'letter': dict(name='Sealed letter', size=(1, 1), stack=5, colour='#e8dcc0', kind='trade', icon='note'),
    # ── scrap components (Rust-style: break barrels and loot crates for them) ──
    'scrap': dict(name='Scrap', size=(1, 1), stack=500, colour='#b0a090', kind='component', icon='scrap', weight=0.02),
    'metal_frags': dict(name='Metal fragments', size=(1, 1), stack=200, colour='#8a8f96', kind='component',
                        icon='scrap', weight=0.04),
    'spring': dict(name='Spring', size=(1, 1), stack=20, colour='#c8cdd2', kind='component', icon='spring', weight=0.2),
    'pipe': dict(name='Metal pipe', size=(1, 2), stack=10, colour='#6a6f78', kind='component', icon='pipe', weight=0.8),
    'gears': dict(name='Gears', size=(1, 1), stack=20, colour='#a8906a', kind='component', icon='gears', weight=0.3),
    'screws': dict(name='Screws', size=(1, 1), stack=100, colour='#9aa0a8', kind='component', icon='scrap',
                   weight=0.01),
    'rope': dict(name='Rope', size=(1, 1), stack=20, colour='#c8a878', kind='component', icon='rope', weight=0.2),
    'cloth': dict(name='Cloth', size=(1, 1), stack=50, colour='#d8d0c0', kind='component', icon='cloth', weight=0.05),
    'tarp': dict(name='Tarp', size=(2, 2), stack=10, colour='#4f6a8a', kind='component', icon='cloth', weight=0.6),
    'sheet_metal': dict(name='Sheet metal', size=(2, 2), stack=10, colour='#7a8088', kind='component', icon='plate',
                        weight=1.5),
    'tech_trash': dict(name='Tech trash', size=(1, 1), stack=20, colour='#3a6a4a', kind='component', icon='chip',
                       weight=0.3),
    'duct_tape': dict(name='Duct tape', size=(1, 1), stack=10, colour='#8a8f96', kind='component', icon='tape',
                      weight=0.15),
    'gunpowder': dict(name='Gunpowder', size=(1, 1), stack=200, colour='#3a3a3e', kind='component', icon='powder',
                      weight=0.01),
    'smg_body': dict(name='SMG body', size=(2, 1), stack=5, colour='#3a3d42', kind='component', icon='body', weight=1.2),
    'rifle_body': dict(name='Rifle body', size=(3, 1), stack=5, colour='#4a4038', kind='component', icon='body',
                       weight=2.0),
    'canned_food': dict(name='Canned food', size=(1, 1), stack=10, colour='#c8a028', kind='food', icon='can', heal=15,
                        use_time=1.5, weight=0.4),
    # ── clothing: where you carry things (grid = cols x rows of room it gives) ──
    'tshirt': dict(name='T-shirt', size=(2, 2), stack=1, colour='#6a8ab0', kind='clothing', icon='shirt', slot='top',
                   grid=(2, 1), weight=0.2),
    'hoodie': dict(name='Hoodie', size=(2, 2), stack=1, colour='#5a5a62', kind='clothing', icon='shirt', slot='top',
                   grid=(2, 2), weight=0.6),
    'field_jacket': dict(name='Field jacket', size=(2, 2), stack=1, colour='#556043', kind='clothing', icon='shirt',
                         slot='top', grid=(4, 2), weight=1.2),
    'jeans': dict(name='Jeans', size=(2, 2), stack=1, colour='#3a4a6a', kind='clothing', icon='pants', slot='legs',
                  grid=(2, 2), weight=0.7),
    'cargo_pants': dict(name='Cargo pants', size=(2, 2), stack=1, colour='#6b6a48', kind='clothing', icon='pants',
                        slot='legs', grid=(4, 2), weight=0.9),
    'chest_rig': dict(name='Chest rig', size=(2, 2), stack=1, colour='#4f5a3a', kind='clothing', icon='rig', slot='rig',
                      grid=(4, 2), weight=1.0),
    'tactical_rig': dict(name='Tactical rig', size=(3, 2), stack=1, colour='#2a2c30', kind='clothing', icon='rig',
                         slot='rig', grid=(4, 3), weight=1.6),
    'satchel': dict(name='Satchel', size=(2, 2), stack=1, colour='#8a6a3a', kind='clothing', icon='pack',
                    slot='backpack', grid=(3, 3), weight=0.6),
    'backpack': dict(name='Backpack', size=(3, 3), stack=1, colour='#4a5a6a', kind='clothing', icon='pack',
                     slot='backpack', grid=(4, 4), weight=1.2),
    'hiking_pack': dict(name='Hiking pack', size=(3, 4), stack=1, colour='#a8322d', kind='clothing', icon='pack',
                        slot='backpack', grid=(5, 5), weight=1.8),
    'military_pack': dict(name='Military pack', size=(4, 4), stack=1, colour='#4f5a3a', kind='clothing', icon='pack',
                          slot='backpack', grid=(6, 6), weight=2.6),
    # armor (crafted at a workbench, worn from the inventory screen)
    'cap_helmet': dict(name='Scrap helmet', size=(2, 2), stack=1, colour='#7a6a52', kind='armor', icon='helmet'),
    'combat_helmet': dict(name='Combat helmet', size=(2, 2), stack=1, colour='#4f5a35', kind='armor',
                          icon='helmet'),
    'riot_helmet': dict(name='Riot helmet', size=(2, 2), stack=1, colour='#2a2c33', kind='armor', icon='helmet'),
    'padded_vest': dict(name='Padded vest', size=(2, 3), stack=1, colour='#8a7a52', kind='armor', icon='vest'),
    'kevlar_vest': dict(name='Kevlar vest', size=(2, 3), stack=1, colour='#3f4a5a', kind='armor', icon='vest'),
    'plate_carrier': dict(name='Plate carrier', size=(3, 3), stack=1, colour='#4f5a35', kind='armor',
                          icon='vest'),
}

# armor: which slot it goes in, how much damage it takes off while it lasts, and how much
# damage it can soak up before it breaks (it then does nothing until you craft a new one)
ARMOR = {
    'cap_helmet': dict(slot='head', protect=0.08, durability=150),
    'combat_helmet': dict(slot='head', protect=0.14, durability=300),
    'riot_helmet': dict(slot='head', protect=0.2, durability=500),
    'padded_vest': dict(slot='body', protect=0.12, durability=250),
    'kevlar_vest': dict(slot='body', protect=0.22, durability=450),
    'plate_carrier': dict(slot='body', protect=0.32, durability=800),
}
SLOTS = [('head', 'HEAD'), ('body', 'BODY')]                     # armor
CLOTHING_SLOTS = [('top', 'TOP'), ('legs', 'LEGS'), ('rig', 'RIG'), ('backpack', 'BACKPACK')]
GEAR_SLOTS = SLOTS + CLOTHING_SLOTS
POCKETS = (4, 1)             # the grid you always have, whatever you wear
STARTING_CLOTHES = ['tshirt', 'jeans']
GRID_ORDER = ['pockets', 'top', 'legs', 'rig', 'backpack']      # where new things go first

# ── weight ───────────────────────────────────────────────────────────────────
# You carry up to LIGHT kg at full speed. Past that you slow down, down to HEAVY_SPEED at HEAVY
# kg (can't sprint past that), and to OVERLOADED_SPEED at OVERLOADED kg and beyond.
LIGHT, HEAVY, OVERLOADED = 25.0, 40.0, 55.0
HEAVY_SPEED, OVERLOADED_SPEED = 0.78, 0.45
WEAPON_WEIGHT = {'melee': 1.5, 'pistol': 1.0, 'smg': 2.6, 'rifle': 3.6, 'shotgun': 3.5, 'sniper': 6.0, 'heavy': 9.0,
                 'special': 3.0}
_KIND_WEIGHT = {'resource': 0.1, 'armor': 3.0, 'food': 0.3, 'medical': 0.3, 'trade': 0.2, 'component': 0.2,
                'clothing': 1.0, 'weapon': 3.0}


def default_weight(item_id):
    d = ITEMS[item_id]
    return d.get('weight', _KIND_WEIGHT.get(d['kind'], 0.2))


def speed_for_weight(kg):
    """How fast you move carrying kg (1 = full speed)."""
    if kg <= LIGHT:
        return 1.0
    if kg <= HEAVY:
        return 1 - (1 - HEAVY_SPEED) * (kg - LIGHT) / (HEAVY - LIGHT)
    if kg <= OVERLOADED:
        return HEAVY_SPEED - (HEAVY_SPEED - OVERLOADED_SPEED) * (kg - HEAVY) / (OVERLOADED - HEAVY)
    return OVERLOADED_SPEED


MAX_PROTECTION = 0.75        # armor from gear + the shop's Plating upgrade never goes past this

USE_MOVE_MULT = 0.5          # how fast you walk while bandaging / eating

# ── weapons ──────────────────────────────────────────────────────────────────
# You hold 3 weapons: a TOOL (melee), a HANDGUN and a RIFLE (any long gun). The rest go in
# your inventory as items this size (by shop category):
WEAPON_SIZES = {'melee': (1, 3), 'pistol': (2, 1), 'smg': (3, 2), 'rifle': (4, 2), 'shotgun': (4, 2),
                'sniper': (5, 2), 'heavy': (5, 2), 'special': (3, 2)}
HAND_SLOTS = [('tool', 'TOOL'), ('handgun', 'HANDGUN'), ('primary', 'RIFLE')]     # keys 1, 2, 3


def hand_slot(d):
    """Which hand slot a weapon goes in."""
    if d.get('melee'):
        return 'tool'
    return 'handgun' if d.get('category') == 'pistol' else 'primary'


def _weapon_items():
    from .weapons import WEAPONS
    for d in WEAPONS:
        cat = 'melee' if d.get('melee') else d.get('category', 'special')
        ITEMS['w_' + d['id']] = dict(name=d['name'], size=WEAPON_SIZES.get(cat, (3, 2)), stack=1,
                                     weight=d.get('weight', WEAPON_WEIGHT.get(cat, 3.0)),
                                     colour='#6b4a2b' if d.get('melee') else '#3a3d42', kind='weapon',
                                     icon='melee' if d.get('melee') else 'gun', weapon=d['id'])


_weapon_items()

# ── furnace (works like Minecraft) ───────────────────────────────────────────
# Put ore in the top slot and fuel in the bottom one. Burning fuel smelts one ore into one
# ingot every SMELT seconds; each piece of fuel burns for FUEL seconds (coal = 8 ingots).
# It only smelts while it has fuel burning and room in the output slot.
SMELT = {'iron': ('iron_ingot', 4.0), 'copper': ('copper_ingot', 4.0),         # ore: (ingot, seconds)
         'raw_meat': ('cooked_meat', 5.0)}                                  # and it cooks food
FUEL = {'coal': 32.0, 'wood': 6.0}                                          # fuel: seconds it burns
