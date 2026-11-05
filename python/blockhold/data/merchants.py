# ─────────────────────────────────────────────────────────────────────────────
#  MERCHANTS AND THE BANK  (the hideout's economy)
#
#  Coins are kept in your bank account: you never carry them, so you can't lose them
#  in a raid. The BANK also holds items (a big grid you open at the banker or at any
#  stash box). Every merchant in the hideout works with the bank: what you buy goes in
#  your inventory, or straight into the bank when you're out of room, and you can sell
#  from your inventory or from the bank.
#
#  VALUES   what an item is worth in coins (merchants sell at this price and buy at
#           BUY_BACK of it). Anything missing is worth DEFAULT_VALUE.
#  MERCHANTS (the `shop` setting of a merchant NPC):
#    name     shown on their screen
#    sells    item ids they stock (as many as you like)
#    buys     item kinds they buy (data/items.py `kind`), or item ids
# ─────────────────────────────────────────────────────────────────────────────

VALUES = {
    # resources
    'stone': 1, 'wood': 1, 'coal': 2, 'iron': 3, 'copper': 3, 'crystal': 40, 'iron_ingot': 8, 'copper_ingot': 8,
    # food and medical
    'raw_meat': 6, 'cooked_meat': 15, 'canned_food': 20, 'bandage': 25, 'medkit': 90, 'surgery_kit': 260,
    # trade goods
    'feather': 4, 'hide': 40, 'gold_coin': 60, 'letter': 30,
    # scrap parts
    'scrap': 1, 'metal_frags': 1, 'spring': 18, 'pipe': 22, 'gears': 14, 'screws': 1, 'rope': 10, 'cloth': 4,
    'tarp': 30, 'sheet_metal': 40, 'tech_trash': 35, 'duct_tape': 20, 'gunpowder': 2, 'smg_body': 140,
    'rifle_body': 220,
    # clothing
    'tshirt': 10, 'hoodie': 45, 'field_jacket': 140, 'jeans': 30, 'cargo_pants': 120, 'chest_rig': 150,
    'tactical_rig': 320, 'satchel': 90, 'backpack': 200, 'hiking_pack': 380, 'military_pack': 600,
    # armor
    'cap_helmet': 60, 'combat_helmet': 220, 'riot_helmet': 480, 'padded_vest': 120, 'kevlar_vest': 380,
    'plate_carrier': 800,
}
DEFAULT_VALUE = 10
BUY_BACK = 0.4               # merchants pay this much of an item's value

MERCHANTS = {
    'scrapper': dict(name='Scrap dealer', sells=['spring', 'pipe', 'gears', 'screws', 'rope', 'cloth', 'tarp',
                                                 'duct_tape', 'sheet_metal', 'tech_trash', 'gunpowder', 'smg_body',
                                                 'rifle_body', 'iron_ingot', 'copper_ingot', 'coal'],
                     buys=['component', 'resource', 'trade']),
    'tailor': dict(name='Tailor', sells=['hoodie', 'field_jacket', 'jeans', 'cargo_pants', 'chest_rig', 'satchel',
                                         'backpack', 'hiking_pack'],
                   buys=['clothing', 'cloth', 'tarp', 'rope', 'hide', 'feather']),
    'medic': dict(name='Medic', sells=['bandage', 'medkit', 'surgery_kit', 'canned_food', 'cooked_meat'],
                  buys=['medical', 'food']),
    'armorer': dict(name='Armorer', sells=['cap_helmet', 'combat_helmet', 'padded_vest', 'kevlar_vest'],
                    buys=['armor', 'sheet_metal']),
}

BANK_GRID = (10, 8)          # cells in your bank


def value(item_id):
    return VALUES.get(item_id, DEFAULT_VALUE)


def sell_price(item_id, n=1):
    """What a merchant pays you for n of item_id."""
    return max(1, int(value(item_id) * n * BUY_BACK))


def buys(merchant, item_id):
    from .items import ITEMS
    d = ITEMS.get(item_id)
    if d is None or d['kind'] == 'weapon':
        return False
    m = MERCHANTS.get(merchant, {})
    return item_id in m.get('buys', ()) or d['kind'] in m.get('buys', ())
