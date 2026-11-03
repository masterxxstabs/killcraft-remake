"""The backpack: a grid where every item takes up a few cells (open it with I).

Items are dicts: uid, id (see data/items.py), n (how many in the pile), x, y (top-left
cell), rot (True = turned 90 degrees) and, for armor, dur (durability left).
Two equipment slots (head, body) hold armor.

ResourceView makes the backpack look like the old {resource: amount} dict, so mining,
crafting, repairs and loot keep working: player.resources['iron'] += 5 puts 5 iron ore
in the backpack, player.resources['iron'] -= 5 takes it out again.
Every player has their own inventory (multiplayer: the host owns it, clients see it).
"""
from collections.abc import MutableMapping
from .data.items import ARMOR, BACKPACK, ITEMS, MAX_PROTECTION, SLOTS
from .net import new_id

RESOURCE_IDS = [k for k, d in ITEMS.items() if d['kind'] == 'resource']


class Inventory:
    def __init__(self, cols=BACKPACK[0], rows=BACKPACK[1], on_change=None):
        self.cols, self.rows = cols, rows
        self.items = []
        self.equipped = {slot: None for slot, _ in SLOTS}
        self.on_change = on_change

    def changed(self):
        if self.on_change:
            self.on_change()

    # ── shapes ───────────────────────────────────────────────────────────────
    @staticmethod
    def size(item_id, rot=False):
        w, h = ITEMS[item_id]['size']
        return (h, w) if rot else (w, h)

    def cells(self, it):
        w, h = self.size(it['id'], it['rot'])
        return [(it['x'] + i, it['y'] + j) for i in range(w) for j in range(h)]

    def fits(self, item_id, x, y, rot=False, ignore=None):
        w, h = self.size(item_id, rot)
        if x < 0 or y < 0 or x + w > self.cols or y + h > self.rows:
            return False
        want = {(x + i, y + j) for i in range(w) for j in range(h)}
        for other in self.items:
            if other is not ignore and want & set(self.cells(other)):
                return False
        return True

    def item_at(self, cx, cy):
        for it in self.items:
            if (cx, cy) in self.cells(it):
                return it
        return None

    def free_spot(self, item_id):
        for rot in (False, True):
            if rot and ITEMS[item_id]['size'][0] == ITEMS[item_id]['size'][1]:
                continue
            for y in range(self.rows):
                for x in range(self.cols):
                    if self.fits(item_id, x, y, rot):
                        return x, y, rot
        return None

    # ── adding and taking ────────────────────────────────────────────────────
    def count(self, item_id):
        return sum(it['n'] for it in self.items if it['id'] == item_id)

    def add(self, item_id, n=1, dur=None):
        """Put n of item_id in the backpack (topping up piles first). Returns how many didn't fit."""
        stack = ITEMS[item_id]['stack']
        for it in self.items:
            if n <= 0:
                break
            if it['id'] == item_id and it['n'] < stack:
                k = min(n, stack - it['n'])
                it['n'] += k
                n -= k
        while n > 0:
            spot = self.free_spot(item_id)
            if spot is None:
                break
            k = min(n, stack)
            it = dict(uid=new_id(), id=item_id, n=k, x=spot[0], y=spot[1], rot=spot[2])
            if item_id in ARMOR:
                it['dur'] = ARMOR[item_id]['durability'] if dur is None else dur
            self.items.append(it)
            n -= k
        self.changed()
        return n

    def remove(self, item_id, n=1):
        """Take up to n of item_id out (smallest piles first). Returns how many were taken."""
        taken = 0
        for it in sorted([i for i in self.items if i['id'] == item_id], key=lambda i: i['n']):
            if taken >= n:
                break
            k = min(it['n'], n - taken)
            it['n'] -= k
            taken += k
            if it['n'] <= 0:
                self.items.remove(it)
        self.changed()
        return taken

    def lift(self, it):
        """Take a whole pile out of the grid (you're dragging it)."""
        if it in self.items:
            self.items.remove(it)
        self.changed()
        return it

    def place(self, it, x, y, rot):
        """Drop a lifted pile at (x, y): onto a matching pile it merges, otherwise it needs room."""
        target = self.item_at(x, y)
        stack = ITEMS[it['id']]['stack']
        if target is not None and target['id'] == it['id'] and stack > 1 and target['n'] < stack:
            k = min(it['n'], stack - target['n'])
            target['n'] += k
            it['n'] -= k
            if it['n'] <= 0:
                self.changed()
                return True
        if self.fits(it['id'], x, y, rot):
            it.update(x=x, y=y, rot=rot)
            self.items.append(it)
            self.changed()
            return True
        return False

    def put_back(self, it):
        """Return a lifted pile to any free spot. Returns False if there's no room left."""
        if self.place(it, it['x'], it['y'], it['rot']):
            return True
        spot = self.free_spot(it['id'])
        if spot is None:
            return False
        it.update(x=spot[0], y=spot[1], rot=spot[2])
        self.items.append(it)
        self.changed()
        return True

    def clear(self):
        self.items = []
        self.equipped = {slot: None for slot, _ in SLOTS}
        self.changed()

    # ── armor ────────────────────────────────────────────────────────────────
    def equip(self, it):
        """Wear armor item it (already lifted out of the grid). What was in the slot goes in the backpack."""
        a = ARMOR.get(it['id'])
        if a is None:
            return False
        old = self.equipped[a['slot']]
        self.equipped[a['slot']] = it
        if old is not None and not self.put_back(old):
            self.equipped[a['slot']] = old            # no room for the old one: swap back
            return False
        self.changed()
        return True

    def unequip(self, slot):
        it = self.equipped.get(slot)
        if it is None:
            return None
        self.equipped[slot] = None
        self.changed()
        return it

    def protection(self):
        """How much damage the worn armor takes off (0..1), only from pieces that aren't broken."""
        return sum(ARMOR[it['id']]['protect'] for it in self.equipped.values()
                   if it is not None and it.get('dur', 0) > 0)

    def wear(self, damage):
        """Worn armor soaks up damage and loses durability. Returns the names of pieces that broke."""
        broke = []
        for it in self.equipped.values():
            if it is None or it.get('dur', 0) <= 0:
                continue
            it['dur'] = max(0.0, it['dur'] - damage * ARMOR[it['id']]['protect'] * 2.5)
            if it['dur'] <= 0:
                broke.append(ITEMS[it['id']]['name'])
        if broke:
            self.changed()
        return broke


class ResourceView(MutableMapping):
    """player.resources: the resources in the backpack as {id: amount}. Writing to it adds or
    takes items; what doesn't fit is lost and on_full is called."""

    def __init__(self, inv, on_full=None):
        self.inv = inv
        self.on_full = on_full

    def __getitem__(self, key):
        if key not in ITEMS:
            raise KeyError(key)
        return self.inv.count(key)

    def __setitem__(self, key, value):
        have = self.inv.count(key)
        value = max(0, int(value))
        if value > have:
            left = self.inv.add(key, value - have)
            if left and self.on_full:
                self.on_full(key, left)
        elif value < have:
            self.inv.remove(key, have - value)

    def __delitem__(self, key):
        self[key] = 0

    def __iter__(self):
        return iter(RESOURCE_IDS)

    def __len__(self):
        return len(RESOURCE_IDS)


def total_protection(base, inv):
    return min(MAX_PROTECTION, base + inv.protection())
