"""What you carry: your pockets plus a grid in every piece of clothing you wear (open it with I).

Items are dicts: uid, id (see data/items.py), n (how many in the pile), x, y (top-left
cell), rot (True = turned 90 degrees), for armor dur (durability left), and for clothing
contents (the piles inside it, so a backpack you drop keeps everything that's in it).

You always have your POCKETS (a small grid). Everything else you wear adds a grid of its
own: a T-shirt a couple of cells, a military backpack 6 x 6. Take a backpack off and its
grid goes with it. Two more slots (HEAD, BODY) hold armor. Everything weighs something,
and weight() adds it all up (what's inside clothing too) to slow you down.

A Grid is one of those rectangles: the same class is used for loot containers.

ResourceView makes the inventory look like the old {resource: amount} dict, so mining,
crafting, repairs and loot keep working: player.resources['iron'] += 5 puts 5 iron ore
in your pockets / clothes, player.resources['iron'] -= 5 takes it out again.
Every player has their own inventory (multiplayer: the host owns it, clients see it).
"""
from collections.abc import MutableMapping
from .data.items import (ARMOR, GEAR_SLOTS, GRID_ORDER, ITEMS, MAX_PROTECTION, POCKETS, STARTING_CLOTHES,
                         default_weight)
from .net import new_id

RESOURCE_IDS = [k for k, d in ITEMS.items() if d['kind'] == 'resource']


def new_pile(item_id, n=1, dur=None):
    it = dict(uid=new_id(), id=item_id, n=n, x=0, y=0, rot=False)
    if item_id in ARMOR:
        it['dur'] = ARMOR[item_id]['durability'] if dur is None else dur
    if ITEMS[item_id]['kind'] == 'clothing':
        it['contents'] = []
    return it


def pile_weight(it):
    """How much a pile weighs, with everything inside it."""
    return default_weight(it['id']) * it['n'] + sum(pile_weight(c) for c in it.get('contents', ()))


def item_size(item_id, rot=False):
    w, h = ITEMS[item_id]['size']
    return (h, w) if rot else (w, h)


class Grid:
    """A rectangle of cells holding piles (pockets, a piece of clothing, a loot crate)."""

    def __init__(self, key, name, cols, rows, items, owner=None):
        self.key, self.name, self.cols, self.rows = key, name, cols, rows
        self.items = items              # the list is shared with whoever owns it (a clothing item's contents)
        self.owner = owner              # the clothing pile this grid belongs to (None for pockets / containers)

    def cells(self, it):
        w, h = item_size(it['id'], it['rot'])
        return [(it['x'] + i, it['y'] + j) for i in range(w) for j in range(h)]

    def can_hold(self, item_id, it=None):
        """Anything fits anywhere it has room (a satchel full of scrap in your backpack), except inside itself."""
        return it is None or it is not self.owner

    def fits(self, item_id, x, y, rot=False, ignore=None):
        w, h = item_size(item_id, rot)
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
        w, h = ITEMS[item_id]['size']
        for rot in (False, True):
            if rot and w == h:
                continue
            for y in range(self.rows):
                for x in range(self.cols):
                    if self.fits(item_id, x, y, rot):
                        return x, y, rot
        return None

    def place(self, it, x, y, rot):
        """Drop a pile at (x, y): onto a matching pile it merges (what's left stays in it), otherwise
        it needs room. Returns True when all of it went in."""
        if not self.can_hold(it['id'], it):
            return False
        target = self.item_at(x, y)
        stack = ITEMS[it['id']]['stack']
        if target is not None and target is not it and target['id'] == it['id'] and stack > 1 and target['n'] < stack:
            k = min(it['n'], stack - target['n'])
            target['n'] += k
            it['n'] -= k
            if it['n'] <= 0:
                return True
        if self.fits(it['id'], x, y, rot):
            it.update(x=x, y=y, rot=rot)
            self.items.append(it)
            return True
        return False

    def add(self, item_id, n=1, dur=None):
        """Top up piles, then make new ones where there's room. Returns how many didn't fit."""
        stack = ITEMS[item_id]['stack']
        if stack > 1:
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
            it = new_pile(item_id, k, dur)
            it.update(x=spot[0], y=spot[1], rot=spot[2])
            self.items.append(it)
            n -= k
        return n

    def put(self, it):
        """Put a whole pile anywhere it fits (topping up piles first). Returns True if all of it went in."""
        if not self.can_hold(it['id'], it):
            return False
        stack = ITEMS[it['id']]['stack']
        if stack > 1 and 'dur' not in it and 'contents' not in it:
            it['n'] = self.add(it['id'], it['n'])
            return it['n'] <= 0
        spot = self.free_spot(it['id'])
        if spot is None:
            return False
        it.update(x=spot[0], y=spot[1], rot=spot[2])
        self.items.append(it)
        return True

    def count(self, item_id):
        return sum(it['n'] for it in self.items if it['id'] == item_id)


class Inventory:
    def __init__(self, on_change=None, clothes=STARTING_CLOTHES):
        self.pockets = []
        self.equipped = {slot: None for slot, _ in GEAR_SLOTS}
        self.on_change = on_change
        self.dress(clothes)

    def dress(self, clothes):
        for cid in clothes:
            self.equipped[ITEMS[cid]['slot']] = new_pile(cid)

    def changed(self):
        if self.on_change:
            self.on_change()

    # ── grids ────────────────────────────────────────────────────────────────
    size = staticmethod(item_size)

    def grids(self):
        """Pockets, then a grid for every worn piece of clothing that has room in it."""
        out = [Grid('pockets', 'POCKETS', POCKETS[0], POCKETS[1], self.pockets)]
        for key in GRID_ORDER[1:]:
            it = self.equipped.get(key)
            if it is not None and ITEMS[it['id']].get('grid'):
                cols, rows = ITEMS[it['id']]['grid']
                out.append(Grid(key, ITEMS[it['id']]['name'].upper(), cols, rows, it.setdefault('contents', []), it))
        return out

    def grid(self, key):
        return next((g for g in self.grids() if g.key == key), None)

    @property
    def items(self):
        """Every pile you carry in a grid (not what you wear)."""
        return [it for g in self.grids() for it in g.items]

    def grid_of(self, it):
        return next((g for g in self.grids() if any(o is it for o in g.items)), None)

    def room(self):
        """Cells you have in total (pockets + clothing)."""
        return sum(g.cols * g.rows for g in self.grids())

    def weight(self):
        """kg you carry: everything in your grids and everything you wear (with what's in it)."""
        return sum(pile_weight(it) for it in self.equipped.values() if it is not None) + \
            sum(pile_weight(it) for it in self.pockets)

    # ── adding and taking ────────────────────────────────────────────────────
    def count(self, item_id):
        return sum(it['n'] for it in self.items if it['id'] == item_id)

    def free_spot(self, item_id):
        """(grid key, x, y, rot) of the first place item_id fits, or None."""
        for g in self.grids():
            spot = g.free_spot(item_id)
            if spot is not None:
                return (g.key,) + spot
        return None

    def add(self, item_id, n=1, dur=None):
        """Put n of item_id in your grids (topping up piles first). Returns how many didn't fit."""
        grids = self.grids()
        stack = ITEMS[item_id]['stack']
        if stack > 1:
            for g in grids:
                for it in g.items:
                    if n <= 0:
                        break
                    if it['id'] == item_id and it['n'] < stack:
                        k = min(n, stack - it['n'])
                        it['n'] += k
                        n -= k
        for g in grids:
            if n <= 0:
                break
            n = g.add(item_id, n, dur)
        self.changed()
        return n

    def remove(self, item_id, n=1):
        """Take up to n of item_id out (smallest piles first). Returns how many were taken."""
        taken = 0
        for g in self.grids():
            for it in sorted([i for i in g.items if i['id'] == item_id], key=lambda i: i['n']):
                if taken >= n:
                    break
                k = min(it['n'], n - taken)
                it['n'] -= k
                taken += k
                if it['n'] <= 0:
                    g.items.remove(it)
        self.changed()
        return taken

    def has_room_for(self, item_id):
        """Room for one new item_id: an empty slot to wear it in, or a spot in a grid."""
        slot = self.slot_for(item_id)
        return (slot is not None and self.equipped.get(slot) is None) or self.free_spot(item_id) is not None

    def give(self, item_id):
        """One new item_id: worn straight away if it's clothing / armor and that slot is free, else in a grid.
        Returns True if it found room."""
        slot = self.slot_for(item_id)
        if slot is not None and self.equipped.get(slot) is None:
            self.equipped[slot] = new_pile(item_id)
            self.changed()
            return True
        return self.add(item_id, 1) == 0

    def lift(self, it):
        """Take a whole pile out of whichever grid it's in (you're dragging it)."""
        g = self.grid_of(it)
        if g is not None:
            g.items.remove(it)
            it['_g'] = g.key
        self.changed()
        return it

    def item_at(self, key, cx, cy):
        g = self.grid(key)
        return g.item_at(cx, cy) if g else None

    def fits(self, item_id, key, x, y, rot=False, ignore=None):
        g = self.grid(key)
        return g is not None and g.can_hold(item_id, ignore) and g.fits(item_id, x, y, rot, ignore)

    def place(self, it, key, x, y, rot):
        g = self.grid(key)
        ok = g is not None and g.place(it, x, y, rot)
        if ok:
            it.pop('_g', None)
        self.changed()
        return ok

    def put_back(self, it):
        """Return a pile to where it was if there's room, otherwise anywhere. False if there's no room."""
        home = it.pop('_g', None)
        if home is not None and self.place(it, home, it['x'], it['y'], it['rot']):
            return True
        if it['n'] <= 0:
            return True
        for g in self.grids():
            if g.put(it):
                self.changed()
                return True
        self.changed()
        return False

    def clear(self):
        self.pockets = []
        self.equipped = {slot: None for slot, _ in GEAR_SLOTS}
        self.dress(STARTING_CLOTHES)
        self.changed()

    # ── wearing things ───────────────────────────────────────────────────────
    @staticmethod
    def slot_for(item_id):
        if item_id in ARMOR:
            return ARMOR[item_id]['slot']
        return ITEMS[item_id].get('slot') if ITEMS[item_id]['kind'] == 'clothing' else None

    def equip(self, it):
        """Wear it (already lifted out of a grid). What was in the slot goes in your grids;
        if there's no room for it the swap is undone."""
        slot = self.slot_for(it['id'])
        if slot is None:
            return False
        old = self.equipped[slot]
        self.equipped[slot] = it
        it.pop('_g', None)
        if old is not None and not self.put_back(old):
            self.equipped[slot] = old
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
                   if it is not None and it['id'] in ARMOR and it.get('dur', 0) > 0)

    def wear(self, damage):
        """Worn armor soaks up damage and loses durability. Returns the names of pieces that broke."""
        broke = []
        for it in self.equipped.values():
            if it is None or it['id'] not in ARMOR or it.get('dur', 0) <= 0:
                continue
            it['dur'] = max(0.0, it['dur'] - damage * ARMOR[it['id']]['protect'] * 2.5)
            if it['dur'] <= 0:
                broke.append(ITEMS[it['id']]['name'])
        if broke:
            self.changed()
        return broke


class ResourceView(MutableMapping):
    """player.resources: the resources you carry as {id: amount}. Writing to it adds or
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
