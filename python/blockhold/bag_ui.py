"""The inventory screen (I), the furnace screen (E at a furnace) and searching loot (E at a container).

Left: what you're wearing (HEAD and BODY armor; TOP, LEGS, RIG and BACKPACK clothing) and
the 3 weapons in your hands (TOOL, HANDGUN, RIFLE: keys 1, 2, 3), how much you carry, or
at a furnace its three slots (ORE, FUEL, INGOTS), or the grid of the container you're
searching. Right: your pockets and a grid for each piece of clothing you wear.

Drag items to move them (R turns them while you drag), drop them on a slot to wear /
hold / smelt them, or outside the window to put them on the ground. Right-click is a
shortcut: wear, hold, load into the furnace, move to / from a container, or eat.
"""
import math
from ursina import Entity, camera, mouse
from . import ui as U
from .data.items import (ARMOR, CLOTHING_SLOTS, FUEL, HAND_SLOTS, HEAVY, ITEMS, LIGHT, OVERLOADED, SLOTS, SMELT,
                         hand_slot)
from .inventory import item_size
from .net import new_id
from .render import destroy

WIN_W, WIN_H, WIN_TOP = 1.6, 0.92, 0.44
CELL = 0.055                 # one grid cell
LABEL_H = 0.03               # the name above each grid
GRID_X = 0.64                # your grids start this far from the window's left edge
GRIDS_H = 0.59               # ...and flow into a new column below this
# slot boxes (dx, dy, w, h) from the top-left of the left-hand area
GEAR_BOXES = {'head': (0.0, 0.0, 0.12, 0.11), 'body': (0.0, 0.13, 0.12, 0.16),
              'top': (0.14, 0.0, 0.13, 0.13), 'legs': (0.14, 0.15, 0.13, 0.14),
              'rig': (0.29, 0.0, 0.13, 0.13), 'backpack': (0.29, 0.15, 0.15, 0.14),
              'tool': (0.0, 0.34, 0.08, 0.12), 'handgun': (0.1, 0.34, 0.14, 0.08), 'primary': (0.26, 0.34, 0.24, 0.08)}
HANDS_DY, STATS_DY = 0.34, 0.48
FURNACE_BOXES = {'inp': (0.08, 0.04, 0.12, 0.12), 'fuel': (0.08, 0.28, 0.12, 0.12), 'out': (0.36, 0.13, 0.15, 0.15)}
WEAR = [k for k, _ in SLOTS + CLOTHING_SLOTS]
HANDS = [k for k, _ in HAND_SLOTS]
SLOT_LABELS = dict(SLOTS + CLOTHING_SLOTS + [(s, f'{i + 1}  {n}') for i, (s, n) in enumerate(HAND_SLOTS)] +
                   [('inp', 'ORE'), ('fuel', 'FUEL'), ('out', 'INGOTS')])


def quad(parent, cx, cy, w, h, colour, rot=0, z=-0.02, alpha=1.0):
    """A rectangle centred on (cx, cy), turned rot degrees."""
    return Entity(parent=parent, model='quad', position=(cx, cy, z), scale=(w, h), rotation_z=rot,
                  color=U.C(colour, alpha))


def draw_icon(parent, icon, cx, cy, s, colour):
    """A tiny picture of the item, about s wide, centred on (cx, cy)."""
    if icon == 'ingot':
        quad(parent, cx, cy - s * 0.05, s * 0.9, s * 0.38, U.contrast(colour), z=-0.019)
        quad(parent, cx, cy - s * 0.05, s * 0.84, s * 0.32, colour, z=-0.02)
        quad(parent, cx, cy + s * 0.04, s * 0.6, s * 0.12, '#ffffff', z=-0.021, alpha=0.35)
    elif icon == 'ore':
        quad(parent, cx, cy, s * 0.62, s * 0.5, '#6f6e6a', rot=10)
        for dx, dy, r in ((-0.12, 0.06, 20), (0.1, -0.05, -15), (0.04, 0.12, 40)):
            quad(parent, cx + dx * s, cy + dy * s, s * 0.2, s * 0.2, colour, rot=r, z=-0.021)
    elif icon == 'coal':
        for dx, dy, r, k in ((-0.1, -0.05, 15, 0.42), (0.12, 0.06, -20, 0.34), (0.0, 0.14, 40, 0.24)):
            quad(parent, cx + dx * s, cy + dy * s, s * k, s * k, '#1c1c20', rot=r)
    elif icon == 'log':
        quad(parent, cx, cy, s * 0.8, s * 0.32, '#6e5233', rot=-20)
        quad(parent, cx + s * 0.34, cy + s * 0.13, s * 0.16, s * 0.28, '#d8bd92', rot=-20, z=-0.021)
    elif icon == 'stone':
        quad(parent, cx, cy, s * 0.55, s * 0.45, colour, rot=12)
        quad(parent, cx + s * 0.18, cy - s * 0.12, s * 0.3, s * 0.25, '#8a8a86', rot=-8, z=-0.021)
    elif icon == 'crystal':
        quad(parent, cx, cy, s * 0.36, s * 0.36, colour, rot=45)
        quad(parent, cx - s * 0.05, cy + s * 0.05, s * 0.12, s * 0.12, '#ffffff', rot=45, z=-0.021, alpha=0.5)
    elif icon == 'helmet':
        U.box(parent, cx - s * 0.36, cy + s * 0.26, s * 0.72, s * 0.5, colour, z=-0.02, radius=s * 0.3)
        quad(parent, cx, cy - s * 0.24, s * 0.9, s * 0.1, U.contrast(colour), z=-0.021, alpha=0.4)
    elif icon == 'vest':
        quad(parent, cx, cy - s * 0.05, s * 0.66, s * 0.8, colour)
        quad(parent, cx, cy + s * 0.38, s * 0.26, s * 0.14, '#000000', z=-0.021, alpha=0.35)
        quad(parent, cx, cy - s * 0.05, s * 0.4, s * 0.3, U.contrast(colour), z=-0.021, alpha=0.18)
    elif icon == 'bandage':
        quad(parent, cx, cy, s * 0.7, s * 0.32, colour, rot=-35)
        quad(parent, cx, cy, s * 0.2, s * 0.26, '#d64541', rot=-35, z=-0.021, alpha=0.7)
    elif icon == 'medkit':
        quad(parent, cx, cy - s * 0.02, s * 0.8, s * 0.56, colour)
        quad(parent, cx, cy + s * 0.3, s * 0.3, s * 0.08, U.contrast(colour), z=-0.021, alpha=0.5)   # handle
        quad(parent, cx, cy - s * 0.02, s * 0.36, s * 0.12, '#ffffff', z=-0.021)                      # cross
        quad(parent, cx, cy - s * 0.02, s * 0.12, s * 0.36, '#ffffff', z=-0.021)
    elif icon == 'meat':
        quad(parent, cx + s * 0.22, cy - s * 0.2, s * 0.32, s * 0.08, '#f2ead8', rot=40, z=-0.019)    # bone
        quad(parent, cx - s * 0.04, cy + s * 0.04, s * 0.52, s * 0.42, colour, rot=40)
        quad(parent, cx - s * 0.08, cy + s * 0.08, s * 0.26, s * 0.14, '#ffffff', rot=40, z=-0.021, alpha=0.25)
    elif icon == 'feather':
        quad(parent, cx, cy, s * 0.2, s * 0.75, colour, rot=-30)
        quad(parent, cx, cy, s * 0.03, s * 0.8, '#8a8580', rot=-30, z=-0.021)
    elif icon == 'hide':
        quad(parent, cx, cy, s * 0.7, s * 0.55, colour, rot=8)
        for dx, dy in ((-0.35, 0.25), (0.35, 0.25), (-0.35, -0.25), (0.35, -0.25)):
            quad(parent, cx + dx * s, cy + dy * s, s * 0.16, s * 0.16, colour, rot=45)
    elif icon == 'coin':
        U.box(parent, cx - s * 0.28, cy + s * 0.28, s * 0.56, s * 0.56, colour, z=-0.02, radius=s * 0.28)
        quad(parent, cx, cy, s * 0.2, s * 0.2, U.contrast(colour), z=-0.021, alpha=0.3)
    elif icon == 'note':
        quad(parent, cx, cy, s * 0.72, s * 0.48, colour)
        quad(parent, cx, cy, s * 0.12, s * 0.12, '#b0302a', z=-0.021)
    elif icon == 'scrap':
        for dx, dy, r, k, c in ((-0.12, -0.06, 20, 0.34, colour), (0.12, 0.04, -30, 0.3, '#8a8f96'),
                                (0.0, 0.16, 50, 0.2, '#c8a878')):
            quad(parent, cx + dx * s, cy + dy * s, s * k, s * k * 0.6, c, rot=r)
    elif icon == 'spring':
        for k in range(5):
            quad(parent, cx, cy - s * 0.28 + k * s * 0.14, s * 0.46, s * 0.05, colour, rot=12)
        quad(parent, cx - s * 0.2, cy, s * 0.04, s * 0.6, '#8a8f96', z=-0.019)
    elif icon == 'pipe':
        quad(parent, cx, cy, s * 0.22, s * 0.9, colour)
        quad(parent, cx - s * 0.05, cy, s * 0.05, s * 0.86, '#ffffff', z=-0.021, alpha=0.3)
        for y in (-0.45, 0.45):
            quad(parent, cx, cy + y * s, s * 0.28, s * 0.06, U.contrast(colour), z=-0.021, alpha=0.4)
    elif icon == 'gears':
        for dx, dy, k in ((-0.1, -0.06, 0.42), (0.16, 0.14, 0.28)):
            for r in (0, 45):
                quad(parent, cx + dx * s, cy + dy * s, s * k, s * k, colour, rot=r)
            quad(parent, cx + dx * s, cy + dy * s, s * k * 0.3, s * k * 0.3, '#2a2c30', z=-0.021)
    elif icon == 'rope':
        for k, r in enumerate((0, 60, 120)):
            quad(parent, cx, cy, s * (0.66 - k * 0.12), s * 0.08, colour, rot=r)
        quad(parent, cx, cy, s * 0.22, s * 0.22, '#8a6a3a', rot=45, z=-0.021)
    elif icon == 'cloth':
        quad(parent, cx, cy, s * 0.7, s * 0.5, colour, rot=-8)
        quad(parent, cx + s * 0.08, cy + s * 0.06, s * 0.6, s * 0.06, '#000000', rot=-8, z=-0.021, alpha=0.15)
        quad(parent, cx - s * 0.05, cy - s * 0.1, s * 0.6, s * 0.06, '#000000', rot=-8, z=-0.021, alpha=0.15)
    elif icon == 'plate':
        quad(parent, cx, cy, s * 0.72, s * 0.62, colour, rot=6)
        for dx, dy in ((-0.28, 0.22), (0.28, 0.22), (-0.28, -0.22), (0.28, -0.22)):
            quad(parent, cx + dx * s, cy + dy * s, s * 0.06, s * 0.06, '#2a2c30', z=-0.021)
    elif icon == 'chip':
        quad(parent, cx, cy, s * 0.7, s * 0.5, colour)
        quad(parent, cx - s * 0.1, cy, s * 0.22, s * 0.22, '#1c1c20', z=-0.021)
        for k in range(3):
            quad(parent, cx + s * 0.2, cy - s * 0.15 + k * s * 0.15, s * 0.16, s * 0.04, '#d9c98a', z=-0.021)
    elif icon == 'tape':
        U.box(parent, cx - s * 0.3, cy + s * 0.3, s * 0.6, s * 0.6, colour, z=-0.02, radius=s * 0.3)
        U.box(parent, cx - s * 0.12, cy + s * 0.12, s * 0.24, s * 0.24, '#d8d0c0', z=-0.021, radius=s * 0.12)
    elif icon == 'body':
        quad(parent, cx, cy + s * 0.05, s * 0.8, s * 0.24, colour)
        quad(parent, cx - s * 0.1, cy - s * 0.15, s * 0.12, s * 0.26, colour, rot=-12)
        quad(parent, cx + s * 0.18, cy - s * 0.12, s * 0.1, s * 0.2, U.contrast(colour), alpha=0.25, z=-0.021)
    elif icon == 'powder':
        quad(parent, cx, cy - s * 0.05, s * 0.44, s * 0.56, colour)
        quad(parent, cx, cy + s * 0.27, s * 0.26, s * 0.1, '#6a6f78', z=-0.021)
        quad(parent, cx, cy - s * 0.05, s * 0.3, s * 0.16, '#d64541', z=-0.021)
    elif icon == 'can':
        quad(parent, cx, cy, s * 0.46, s * 0.6, '#9aa0a8')
        quad(parent, cx, cy, s * 0.46, s * 0.34, colour, z=-0.021)
    elif icon == 'shirt':
        quad(parent, cx, cy - s * 0.06, s * 0.46, s * 0.6, colour)
        quad(parent, cx - s * 0.3, cy + s * 0.12, s * 0.2, s * 0.3, colour, rot=30)
        quad(parent, cx + s * 0.3, cy + s * 0.12, s * 0.2, s * 0.3, colour, rot=-30)
        quad(parent, cx, cy + s * 0.22, s * 0.14, s * 0.08, '#000000', z=-0.021, alpha=0.3)
    elif icon == 'pants':
        quad(parent, cx, cy + s * 0.26, s * 0.46, s * 0.12, colour)
        quad(parent, cx - s * 0.12, cy - s * 0.08, s * 0.2, s * 0.6, colour, rot=-4)
        quad(parent, cx + s * 0.12, cy - s * 0.08, s * 0.2, s * 0.6, colour, rot=4)
    elif icon == 'rig':
        quad(parent, cx, cy, s * 0.56, s * 0.66, colour)
        for k in range(3):
            quad(parent, cx - s * 0.18 + k * s * 0.18, cy - s * 0.08, s * 0.15, s * 0.22, U.contrast(colour),
                 z=-0.021, alpha=0.25)
    elif icon == 'pack':
        U.box(parent, cx - s * 0.3, cy + s * 0.36, s * 0.6, s * 0.74, colour, z=-0.02, radius=s * 0.12)
        quad(parent, cx, cy - s * 0.16, s * 0.44, s * 0.24, U.contrast(colour), z=-0.021, alpha=0.2)
        quad(parent, cx, cy + s * 0.42, s * 0.2, s * 0.08, '#2a2c30', z=-0.021)


def draw_weapon(parent, it, x, y, w, h):
    """A weapon's silhouette, lying along the long side of its tile."""
    d = ITEMS[it['id']]
    cx, cy = x + w / 2, y - h / 2
    along = max(w, h) * 0.8
    turned = h > w
    piv = Entity(parent=parent, position=(cx, cy, -0.02), rotation_z=90 if turned else 0)
    if d['icon'] == 'melee':           # a handle with a head on the end, drawn lying down
        quad(piv, 0, 0, along, along * 0.08, '#8a6038', z=0)
        quad(piv, along * 0.42, 0, along * 0.16, along * 0.3, '#9aa0a8', z=-0.001)
        return
    thick = min(w, h) * 0.22
    quad(piv, 0.0, thick * 0.3, along * 0.62, thick, '#26282d', z=0)                 # body
    quad(piv, along * 0.36, thick * 0.45, along * 0.3, thick * 0.35, '#3a3d42', z=0)  # barrel
    quad(piv, -along * 0.06, -thick * 0.55, thick * 0.55, thick * 1.2, '#26282d', z=0, rot=-12)   # grip
    if along > 0.2:
        quad(piv, -along * 0.38, thick * 0.1, along * 0.2, thick * 0.9, '#5e3b1f', z=0)    # stock


class BagScreen:
    def __init__(self, ui):
        self.ui, self.game = ui, ui.game
        self.root = Entity(parent=camera.ui, z=-1, enabled=False)
        U.backdrop(self.root, 0.5)
        self.win = U.Window(self.root, 'INVENTORY', w=WIN_W, h=WIN_H, top=WIN_TOP)
        self.active = False
        self.furnace = None
        self.container = None      # a loot container being searched (loot.py)
        self.drag = None           # dict(it, src, grab, ghost, outline)
        self.tiles = None
        self.fur_panel = None
        self.fur_t = 0.0
        self.panels = []           # [(grid, x, y)]: every grid on screen and its top-left corner
        self.updater = Entity(parent=self.root, update=self.update)
        w = self.win
        self.sx, self.sy = w.left, w.top - 0.04                   # top-left of the slots / container area
        self.gx, self.gy = w.x + GRID_X, w.top - 0.035            # top-left of your own grids

    @property
    def player(self):
        return self.game.player

    @property
    def inv(self):
        return self.game.player.inventory

    # ── open / close ─────────────────────────────────────────────────────────
    def open(self, furnace=None, container=None):
        self.furnace, self.container = furnace, container
        self.active = True
        self.root.enabled = True
        self.win.title.text = 'FURNACE' if furnace else (container['d']['name'].upper() if container else 'INVENTORY')
        self.refresh()

    def close(self):
        if not self.active:
            return
        self.cancel_drag()
        self.active = False
        self.root.enabled = False
        self.furnace = self.container = None
        if self.fur_panel is not None:
            destroy(self.fur_panel)
            self.fur_panel = None

    # ── geometry ─────────────────────────────────────────────────────────────
    def boxes(self):
        if self.container is not None:
            return {}
        return FURNACE_BOXES if self.furnace is not None else GEAR_BOXES

    def loot_grid(self):
        return self.game.loot.grid(self.container) if self.container is not None else None

    def grid(self, key):
        return self.loot_grid() if key == 'loot' else self.inv.grid(key)

    def layout(self):
        """Where every grid goes: yours flow down in columns, the container's sits on the left."""
        out = []
        x, y, col_w = self.gx, self.gy, 0.0
        for g in self.inv.grids():
            h = g.rows * CELL + LABEL_H
            if y - h < self.gy - GRIDS_H and y < self.gy:          # full: start the next column
                x, y, col_w = x + col_w + 0.035, self.gy, 0.0
            out.append((g, x, y - LABEL_H))
            y -= h
            col_w = max(col_w, g.cols * CELL)
        lg = self.loot_grid()
        if lg is not None:
            out.append((lg, self.sx, self.sy - LABEL_H))
        return out

    def cell_at(self, x, y):
        """(grid, cx, cy) under the mouse, or None."""
        for g, gx, gy in self.panels:
            cx, cy = math.floor((x - gx) / CELL), math.floor((gy - y) / CELL)
            if 0 <= cx < g.cols and 0 <= cy < g.rows:
                return g, cx, cy
        return None

    def slot_at(self, x, y):
        for key, (dx, dy, w, h) in self.boxes().items():
            sx, sy = self.sx + dx, self.sy - dy
            if sx <= x <= sx + w and sy - h <= y <= sy:
                return key
        return None

    def inside_window(self, x, y):
        w = self.win
        return w.x <= x <= w.x + w.w and w.y - w.h <= y <= w.y

    # ── slots: what you wear, weapons in hand, furnace ───────────────────────
    @staticmethod
    def pile(item_id, n=1):
        return dict(uid=new_id(), id=item_id, n=n, x=0, y=0, rot=False)

    def slot_item(self, key):
        if key in WEAR:
            return self.inv.equipped.get(key)
        if key in HANDS:
            d = self.game.weapons.slots.get(key)
            return self.pile('w_' + d['id']) if d else None
        return self.furnace[key] if self.furnace else None

    def accepts(self, key, it):
        d = ITEMS[it['id']]
        if key in WEAR:
            return self.inv.slot_for(it['id']) == key
        if key in HANDS:
            return d['kind'] == 'weapon' and hand_slot(self.game.weapons.get_def(d['weapon'])) == key
        return self.game.barricades.furnace_accepts(key, it['id'])

    def slot_take(self, key):
        """Lift the item out of a slot. Returns it (a pile dict) or None."""
        if key in WEAR:
            return self.inv.unequip(key)
        if key in HANDS:
            d = self.game.weapons.unslot(key)
            if d is None and self.game.weapons.slots.get(key) is not None:
                self.ui.banner('KEEP ONE', '#d9912b', 1.2, "You can't empty your hands completely")
            return self.pile('w_' + d['id']) if d else None
        it = self.furnace[key]
        self.furnace[key] = None
        if it is not None:
            it = dict(it, uid=new_id(), x=0, y=0, rot=False)
        return it

    def slot_put(self, key, it):
        """Put a pile in a slot. Returns whatever comes back out (what was there, or what didn't fit)."""
        if key in WEAR:
            old = self.inv.equipped.get(key)
            self.inv.equipped[key] = it
            it.pop('_g', None)
            self.inv.changed()
            return old
        if key in HANDS:
            w = self.game.weapons
            d = w.get_def(ITEMS[it['id']]['weapon'])
            old = w.slots.get(key)
            if old is not None:
                w.slots[key] = None
                if w.held is old:
                    w.held = None
            w.slot_in(d, key)
            return self.pile('w_' + old['id']) if old else None
        b = self.furnace
        cur, stack = b[key], ITEMS[it['id']]['stack']
        if cur is None:
            k = min(it['n'], stack)
            b[key] = dict(id=it['id'], n=k)
            return dict(it, n=it['n'] - k) if it['n'] > k else None
        if cur['id'] == it['id']:
            k = min(it['n'], stack - cur['n'])
            cur['n'] += k
            return dict(it, n=it['n'] - k) if it['n'] > k else None
        b[key] = dict(id=it['id'], n=it['n'])
        return dict(cur, uid=new_id(), x=0, y=0, rot=False)

    def slot_restore(self, key, it):
        if key in WEAR:
            self.inv.equipped[key] = it
            self.inv.changed()
        elif key in HANDS:
            self.game.weapons.slot_in(self.game.weapons.get_def(ITEMS[it['id']]['weapon']), key)
        elif self.furnace is not None:
            left = self.slot_put(key, it)
            if left:
                self.to_bag(left)

    def to_bag(self, it, near=None):
        """Put a pile in your grids (at `near` = (grid key, x, y, rot) if there's room there); the ground if it's full."""
        if near is not None:
            g = self.grid(near[0])
            if g is not None and g.place(it, *near[1:]):
                self.inv.changed()
                return
        if it['n'] > 0 and not self.inv.put_back(it):
            self.to_ground(it)

    def to_ground(self, it):
        it.pop('_g', None)
        if ITEMS[it['id']]['kind'] == 'weapon':           # weapons keep their upgrades on the ground
            w = self.game.weapons
            pack = w.take_out(w.get_def(ITEMS[it['id']]['weapon']))
            p = self.player
            fwd = p.forward()
            self.game.drops.spawn(pack, p.position + U.Vec3(fwd.x, 0, fwd.z) * 1.1, p.yaw + 70, p)
        else:
            self.game.drops.drop_item(self.player, it)

    # ── drawing ──────────────────────────────────────────────────────────────
    def tile(self, parent, it, x, y, w, h, z=-0.01):
        d = ITEMS[it['id']]
        broken = 'dur' in it and it['dur'] <= 0
        held = d['kind'] == 'weapon' and self.game.weapons.held is not None and \
            self.game.weapons.held['id'] == d['weapon'] and self.game.weapons.in_hands(d['weapon'])
        U.box(parent, x, y, w, h, U.TEAL if held else U.INK, z=z + 0.002)
        U.box(parent, x + 0.003, y - 0.003, w - 0.006, h - 0.006, U.C(d['colour'], 0.55 if broken else 0.9), z=z + 0.001)
        if d['kind'] == 'weapon':
            draw_weapon(parent, it, x, y, w, h)
        else:
            draw_icon(parent, d['icon'], x + w / 2, y - h / 2 + 0.004, min(w, h) * 0.78,
                      d['colour'] if not broken else '#555555')
        fg = U.contrast(d['colour'])
        U.text(parent, d['name'] if w > 0.1 else d['name'].split()[0], x + 0.005, y - 0.003, 0.45, fg, z=z - 0.02)
        if it['n'] > 1:
            U.text(parent, str(it['n']), x + w - 0.005, y - h + 0.014, 0.68, fg, origin=(0.5, 0), z=z - 0.02)
        if d['kind'] == 'clothing':                       # how much room it gives, and if there's stuff in it
            inside = len(it.get('contents', ()))
            c, r = d['grid']
            U.text(parent, f'{c}x{r}' + (f'  +{inside}' if inside else ''), x + w - 0.005, y - h + 0.014, 0.55, fg,
                   origin=(0.5, 0), z=z - 0.02)
        if 'dur' in it:                                  # durability bar
            k = it['dur'] / ARMOR[it['id']]['durability']
            U.box(parent, x + 0.006, y - h + 0.012, w - 0.012, 0.006, '#000000', z=z - 0.02)
            U.box(parent, x + 0.006, y - h + 0.012, (w - 0.012) * k, 0.006, U.GREEN if k > 0.3 else U.RED,
                  z=z - 0.021, round=False)

    def slot_box(self, parent, key):
        dx, dy, w, h = self.boxes()[key]
        x, y = self.sx + dx, self.sy - dy
        U.frame(parent, x, y, w, h, U.NAVY, U.INK)
        it = self.slot_item(key)
        if it is None:
            U.text(parent, SLOT_LABELS[key], x + w / 2, y - h / 2, 0.6, U.contrast(U.NAVY), origin=(0, 0), z=-0.02)
        else:
            self.tile(parent, it, x + 0.006, y - 0.006, w - 0.012, h - 0.012, z=-0.02)

    def draw_grid(self, t, g, x, y):
        free = g.cols * g.rows - sum(len(g.cells(it)) for it in g.items)
        U.text(t, f'{g.name}  {g.cols}x{g.rows}', x, y + LABEL_H - 0.006, 0.62, U.MUTED)
        U.box(t, x - 0.004, y + 0.004, g.cols * CELL + 0.008, g.rows * CELL + 0.008, U.INK, z=0.004, round=False)
        for cy in range(g.rows):
            for cx in range(g.cols):
                U.box(t, x + cx * CELL + 0.002, y - cy * CELL - 0.002, CELL - 0.004, CELL - 0.004,
                      U.NAVY, z=0.003, round=False)
        for it in g.items:
            w, h = item_size(it['id'], it['rot'])
            self.tile(t, it, x + it['x'] * CELL + 0.002, y - it['y'] * CELL - 0.002, w * CELL - 0.004, h * CELL - 0.004)
        return free

    def refresh(self):
        if not self.active:
            return
        if self.container is not None and self.container not in self.game.loot.list:     # it rotted away
            self.container = None
        if self.tiles is not None:
            destroy(self.tiles)
        t = self.tiles = Entity(parent=self.win.body)
        self.panels = self.layout()
        for g, x, y in self.panels:
            self.draw_grid(t, g, x, y)
        U.text(t, 'Drag to move, R turns it. Drop on a slot to wear / hold it, outside the window to drop it. '
                  'Right-click: quick move / wear / eat.', self.gx, self.win.btn_y + 0.035, 0.58, U.MUTED, wordwrap=110)
        self.win.right.text = self.weight_text()
        if self.furnace is not None:          # at a furnace: its slots take the place of your gear
            U.FlatButton(t, 'CLOSE  (E)', self.win.left, self.win.btn_y, 0.26, U.BTN_H, self.game.close_shop)
            self.refresh_furnace()
            return
        if self.container is not None:        # searching a container: its grid takes the place of your gear
            n = len(self.container['items'])
            U.text(t, 'Empty: it fills up again a while after you leave.' if not n else
                   'Drag what you want into your pockets and clothes.', self.sx, self.sy - 0.36, 0.6, U.MUTED,
                   wordwrap=50)
            U.FlatButton(t, 'TAKE ALL', self.sx, self.sy - 0.42, 0.2, 0.05, self.take_all, fill='GREEN', edge='INK',
                         size=0.8)
            U.FlatButton(t, 'CLOSE  (E)', self.win.left, self.win.btn_y, 0.26, U.BTN_H, self.game.close_shop)
            return
        U.text(t, 'WEARING', self.sx, self.sy + 0.03, 0.75, U.MUTED)
        for key in GEAR_BOXES:
            self.slot_box(t, key)
        U.text(t, 'IN YOUR HANDS   (1  2  3)', self.sx, self.sy - HANDS_DY + 0.03, 0.75, U.MUTED)
        self.draw_stats(t, self.sx, self.sy - STATS_DY)
        U.FlatButton(t, 'CLOSE  (I)', self.win.left, self.win.btn_y, 0.26, U.BTN_H, self.game.close_shop)

    def weight_text(self):
        kg = self.player.carried_weight()
        return f'{kg:.1f} kg'

    def draw_stats(self, t, x, y):
        """Armor and how much you carry (with where you start slowing down)."""
        p, inv = self.player, self.inv
        kg = p.carried_weight()
        U.text(t, f'DAMAGE TAKEN  -{round(p.armor * 100)}%', x, y, 0.72, U.INK)
        U.text(t, f'armor {round(inv.protection() * 100)}%  ·  plating {round(p.base_armor * 100)}%', x, y - 0.03,
               0.58, U.MUTED)
        y -= 0.075
        col = U.GREEN if kg <= LIGHT else (U.AMBER if kg <= HEAVY else U.RED)
        state = 'full speed' if kg <= LIGHT else ('slower' if kg <= HEAVY else 'too heavy: no sprinting')
        U.text(t, f'WEIGHT  {kg:.1f} kg  ({state})', x, y, 0.72, U.INK)
        bw = 0.5
        U.box(t, x, y - 0.03, bw, 0.016, U.NAVY, z=-0.005, round=False)
        U.box(t, x, y - 0.03, bw * min(1.0, kg / OVERLOADED), 0.016, col, z=-0.006, round=False)
        for mark in (LIGHT, HEAVY):
            U.box(t, x + bw * mark / OVERLOADED - 0.001, y - 0.026, 0.002, 0.024, U.INK, z=-0.007, round=False)
        U.text(t, f'Full speed up to {LIGHT:g} kg, no sprinting past {HEAVY:g} kg.  Room: {inv.room()} cells',
               x, y - 0.055, 0.55, U.MUTED)

    def refresh_furnace(self):
        if self.fur_panel is not None:
            destroy(self.fur_panel)
            self.fur_panel = None
        b = self.furnace
        if not self.active or b is None:
            return
        if b not in self.game.barricades.list:          # it got smashed
            self.furnace = None
            self.refresh()
            return
        f = self.fur_panel = Entity(parent=self.win.body)
        for key in ('inp', 'fuel', 'out'):
            self.slot_box(f, key)
        burn, cook = self.game.barricades.furnace_status(b)
        # the flame between ore and fuel (how long the fuel keeps burning)
        fx, fy = self.sx + 0.11, self.sy - 0.18
        U.box(f, fx, fy, 0.06, 0.08, U.NAVY, z=-0.01)
        if burn > 0:
            U.box(f, fx, fy - 0.08 * (1 - burn), 0.06, 0.08 * burn, '#ff8c2a', z=-0.012, round=False)
            U.box(f, fx + 0.015, fy - 0.08 * (1 - burn * 0.6), 0.03, 0.08 * burn * 0.6, '#ffd84a', z=-0.013,
                  round=False)
        # the arrow towards the ingots (how far the current ore has smelted)
        ax, ay = self.sx + 0.22, self.sy - 0.19
        U.box(f, ax, ay, 0.12, 0.03, U.NAVY, z=-0.01, round=False)
        U.box(f, ax, ay, 0.12 * cook, 0.03, U.TEAL, z=-0.012, round=False)
        U.box(f, ax + 0.12, ay + 0.012, 0.025, 0.054, U.NAVY, z=-0.01, round=False)
        x, y = self.sx, self.sy - 0.43
        fuel = ', '.join(f"{ITEMS[k]['name'].lower()} smelts {v / 4:g}" for k, v in FUEL.items())
        ores = ', '.join(ITEMS[k]['name'].lower() for k in SMELT)
        U.text(f, f'Smelts / cooks: {ores}.\nFuel: {fuel} (one piece burns at a time).\n'
                  'It keeps smelting while you\'re away.', x, y, 0.62, U.MUTED, wordwrap=50)

    # ── input ────────────────────────────────────────────────────────────────
    def input(self, key):
        """Returns True if the key was used here."""
        if not self.active:
            return False
        mx, my = mouse.x, mouse.y
        if key == 'left mouse down' and self.drag is None:
            c = self.cell_at(mx, my)
            if c is not None:
                g, cx, cy = c
                it = g.item_at(cx, cy)
                if it is not None:
                    home = (g.key, it['x'], it['y'], it['rot'])
                    g.items.remove(it)
                    self.start_drag(it, ('grid', home), (cx - it['x'], cy - it['y']))
                    self.inv.changed()
                    return True
            s = self.slot_at(mx, my)
            if s is not None and self.slot_item(s) is not None:
                it = self.slot_take(s)
                if it is not None:
                    self.start_drag(it, ('slot', s), (0, 0))
                return True
        elif key == 'left mouse up' and self.drag is not None:
            self.finish_drag(mx, my)
            return True
        elif key == 'r' and self.drag is not None:
            it = self.drag['it']
            w, h = ITEMS[it['id']]['size']
            if w != h:
                it['rot'] = not it['rot']
                gx, gy = self.drag['grab']
                self.drag['grab'] = (gy, gx)
                self.build_ghost()
            return True
        elif key == 'right mouse down' and self.drag is None:
            self.quick_move(mx, my)
            return True
        return False

    def take_all(self):
        if self.container is None:
            return
        n = self.game.loot.take_all(self.player, self.container)
        if self.container['items']:
            self.ui.banner('NO ROOM', '#d9912b', 1.2, 'Wear something with more pockets')
        if n:
            self.game.sounds.play('equip', volume=0.7)
        self.inv.changed()
        self.refresh()

    def quick_move(self, mx, my):
        """Right-click: your item -> the container / its slot (wear, hold, load) / eat it;
        a container's item -> you (worn straight away if that slot is free); slot -> your grids."""
        inv = self.inv
        c = self.cell_at(mx, my)
        it = c[0].item_at(c[1], c[2]) if c else None
        if it is not None:
            g = c[0]
            home = (g.key, it['x'], it['y'], it['rot'])
            kind = ITEMS[it['id']]['kind']
            if g.key == 'loot':                          # out of the container
                g.items.remove(it)
                slot = inv.slot_for(it['id'])
                if slot is not None and inv.equipped.get(slot) is None:
                    inv.equipped[slot] = it
                    inv.changed()
                elif not inv.put_back(it):
                    g.place(it, *home[1:])
                    self.ui.banner('NO ROOM', '#d9912b', 1.2, 'Wear something with more pockets')
                self.game.sounds.play('equip', volume=0.7)
                self.refresh()
                return
            if self.container is not None:              # into the container
                if kind == 'weapon':
                    return
                g.items.remove(it)
                if not self.loot_grid().put(it):
                    g.place(it, *home[1:])
                inv.changed()
                self.game.sounds.play('equip', volume=0.7)
                self.refresh()
                return
            target = next((k for k in self.boxes() if self.accepts(k, it)), None)
            if target is None:
                if kind in ('food', 'medical'):          # eat it / patch yourself up (takes time)
                    self.eat(it)
                return
            g.items.remove(it)
            back = self.slot_put(target, it)
            if back:
                self.to_bag(back, near=home)
            self.game.sounds.play('equip', volume=0.7)
            self.refresh()
            return
        s = self.slot_at(mx, my)
        if s is not None and self.slot_item(s) is not None:
            if s == 'out':                       # ingots: as many as fit
                out = self.furnace['out']
                out['n'] = inv.add(out['id'], out['n'])
                if out['n'] <= 0:
                    self.furnace['out'] = None
            else:
                taken = self.slot_take(s)
                if taken is not None:
                    if ITEMS[taken['id']]['kind'] in ('weapon', 'armor', 'clothing'):
                        if not inv.put_back(taken):
                            self.slot_restore(s, taken)
                            self.ui.banner('NO ROOM', '#d9912b', 1.2, 'No room for it')
                    else:
                        left = inv.add(taken['id'], taken['n'])
                        if left:
                            self.slot_restore(s, dict(taken, n=left))
            self.game.sounds.play('equip', volume=0.7)
            self.refresh()

    def eat(self, it):
        """Start using food or a medical item; the screen closes so you can see what's coming."""
        if self.game.healing.start(self.player, it['id']):
            self.game.close_shop()

    # ── dragging ─────────────────────────────────────────────────────────────
    def start_drag(self, it, src, grab):
        self.drag = dict(it=it, src=src, grab=grab, ghost=None)
        self.build_ghost()
        self.game.sounds.play('equip', volume=0.4, pitch=1.3)
        self.refresh()

    def build_ghost(self):
        if self.drag['ghost'] is not None:
            destroy(self.drag['ghost'])
        it = self.drag['it']
        w, h = item_size(it['id'], it['rot'])
        g = self.drag['ghost'] = Entity(parent=self.win.body, z=-0.3)
        self.tile(g, it, 0, 0, w * CELL - 0.004, h * CELL - 0.004, z=-0.3)
        self.drag['outline'] = U.box(g, -0.004, 0.004, w * CELL + 0.004, h * CELL + 0.004, U.TEAL, z=-0.29)

    def update(self):
        if not self.active:
            return
        self.fur_t -= 1 / 30
        if self.furnace is not None and self.drag is None and self.fur_t <= 0:
            self.fur_t = 0.25
            self.refresh_furnace()
        if self.container is not None and self.container not in self.game.loot.list:
            self.game.close_shop()
            return
        if self.drag is None:
            return
        gx, gy = self.drag['grab']
        g = self.drag['ghost']
        g.position = (mouse.x - (gx + 0.5) * CELL, mouse.y + (gy + 0.5) * CELL, -0.3)
        self.drag['outline'].color = U.C(U.GREEN if self.drop_ok(mouse.x, mouse.y) else U.RED, 0.85)

    def target(self, mx, my):
        """Where the dragged item would go: ('grid', key, x, y) / ('slot', key) / ('ground',) / None."""
        s = self.slot_at(mx, my)
        if s is not None:
            return ('slot', s)
        c = self.cell_at(mx, my)
        if c is not None:                      # the cell you grabbed it by goes under the mouse
            gx, gy = self.drag['grab']
            return ('grid', c[0].key, c[1] - gx, c[2] - gy)
        if not self.inside_window(mx, my):
            return ('ground',)
        return None

    def drop_ok(self, mx, my):
        t = self.target(mx, my)
        it = self.drag['it']
        if t is None:
            return False
        if t[0] == 'slot':
            return t[1] != 'out' and self.accepts(t[1], it)
        if t[0] == 'grid':
            g = self.grid(t[1])
            if g is None or not g.can_hold(it['id'], it):
                return False
            if t[1] == 'loot' and ITEMS[it['id']]['kind'] == 'weapon':     # guns stay with you (or on the ground)
                return False
            other = g.item_at(t[2], t[3])
            if other is not None and other['id'] == it['id'] and ITEMS[it['id']]['stack'] > 1:
                return True
            return g.fits(it['id'], t[2], t[3], it['rot'])
        return True

    def finish_drag(self, mx, my):
        d = self.drag
        it = d['it']
        t = self.target(mx, my) if self.drop_ok(mx, my) else None
        destroy(d['ghost'])
        self.drag = None
        home = d['src'][1] if d['src'][0] == 'grid' else None
        if t is None:
            self.return_home(d)
        elif t[0] == 'grid':
            if not self.grid(t[1]).place(it, t[2], t[3], it['rot']) and it['n'] > 0:
                self.to_bag(it, near=home)             # merged part of a pile: the rest goes back
            self.inv.changed()
        elif t[0] == 'slot':
            back = self.slot_put(t[1], it)
            if back:
                if d['src'][0] == 'slot' and self.accepts(d['src'][1], back) and self.slot_item(d['src'][1]) is None:
                    self.slot_put(d['src'][1], back)     # swapped between two slots
                else:
                    self.to_bag(back, near=home)
        elif t[0] == 'ground':
            self.to_ground(it)
        self.game.sounds.play('equip', volume=0.4)
        self.refresh()

    def return_home(self, d):
        it = d['it']
        if d['src'][0] == 'slot':
            self.slot_restore(d['src'][1], it)
            return
        key, x, y, rot = d['src'][1]
        it['rot'] = rot
        g = self.grid(key)
        if g is None or not g.place(it, x, y, rot):
            self.to_bag(it)
        self.inv.changed()

    def cancel_drag(self):
        if self.drag is not None:
            d = self.drag
            destroy(d['ghost'])
            self.drag = None
            self.return_home(d)
