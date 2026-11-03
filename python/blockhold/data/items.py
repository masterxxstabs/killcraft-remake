# ─────────────────────────────────────────────────────────────────────────────
#  ITEMS  (everything that goes in your backpack: open it with I)
#
#  The backpack is a grid. Each item takes up `size` cells (width, height) and can
#  be turned 90° while you drag it (R). Items with `stack` > 1 pile up in one spot.
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
#    icon       how the tile is drawn: 'ore', 'ingot', 'log', 'coal', 'stone', 'crystal',
#               'helmet', 'vest', 'bandage', 'medkit', 'meat', 'feather', 'gem', 'coin', 'note'
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
    # armor (crafted at a workbench, worn from the backpack screen)
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
SLOTS = [('head', 'HEAD'), ('body', 'BODY')]
MAX_PROTECTION = 0.75        # armor from gear + the shop's Plating upgrade never goes past this

USE_MOVE_MULT = 0.5          # how fast you walk while bandaging / eating

BACKPACK = (10, 7)           # backpack size in cells (columns, rows)

# ── weapons ──────────────────────────────────────────────────────────────────
# You hold 3 weapons: a TOOL (melee), a HANDGUN and a RIFLE (any long gun). The rest go in
# the backpack as items this size (by shop category):
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
