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
#    icon       how the tile is drawn: 'ore', 'ingot', 'log', 'coal', 'stone', 'crystal',
#               'helmet', 'vest'
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

BACKPACK = (10, 7)           # backpack size in cells (columns, rows)

# smelting in a furnace: (ore, ingot it makes, ore needed, coal needed, seconds per ingot)
SMELTING = [('iron', 'iron_ingot', 2, 1, 3.0), ('copper', 'copper_ingot', 2, 1, 3.0)]
