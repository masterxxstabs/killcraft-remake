"""The backpack screen (I) and the furnace screen (E at a furnace).

Left: what you're wearing (HEAD, BODY) and the 3 weapons in your hands (TOOL, HANDGUN,
RIFLE: keys 1, 2, 3), or at a furnace its three slots (ORE, FUEL, INGOTS) like Minecraft.
Right: the backpack grid.

Drag items to move them (R turns them while you drag), drop them on a slot to wear /
hold / smelt them, or outside the window to put them on the ground. Right-click is a
shortcut: wear, hold, load into the furnace, or put back in the backpack.
"""
import math
from ursina import Entity, camera, mouse
from . import ui as U
from .data.items import ARMOR, BACKPACK, FUEL, HAND_SLOTS, ITEMS, SLOTS, SMELT, hand_slot
from .net import new_id
from .render import destroy

CELL = 0.062
# slot boxes (dx, dy, w, h) from the top-left of the left-hand area
GEAR_BOXES = {'head': (0.0, 0.0, 0.17, 0.17), 'body': (0.2, 0.0, 0.19, 0.26),
              'tool': (0.0, 0.32, 0.1, 0.15), 'handgun': (0.12, 0.32, 0.16, 0.1), 'primary': (0.3, 0.32, 0.26, 0.1)}
FURNACE_BOXES = {'inp': (0.08, 0.04, 0.12, 0.12), 'fuel': (0.08, 0.28, 0.12, 0.12), 'out': (0.36, 0.13, 0.15, 0.15)}
SLOT_LABELS = dict(SLOTS + [(s, f'{i + 1}  {n}') for i, (s, n) in enumerate(HAND_SLOTS)] +
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
        self.win = U.Window(self.root, 'BACKPACK')
        self.active = False
        self.furnace = None
        self.drag = None           # dict(it, src, grab, ghost, outline)
        self.tiles = None
        self.fur_panel = None
        self.fur_t = 0.0
        self.updater = Entity(parent=self.root, update=self.update)
        w = self.win
        self.gx, self.gy = w.x + 0.64, w.top - 0.035              # top-left of the grid
        self.sx, self.sy = w.left, w.top - 0.04                   # top-left of the slots area

    @property
    def player(self):
        return self.game.player

    @property
    def inv(self):
        return self.game.player.inventory

    # ── open / close ─────────────────────────────────────────────────────────
    def open(self, furnace=None):
        self.furnace = furnace
        self.active = True
        self.root.enabled = True
        self.win.title.text = 'FURNACE' if furnace else 'BACKPACK'
        self.refresh()

    def close(self):
        if not self.active:
            return
        self.cancel_drag()
        self.active = False
        self.root.enabled = False
        self.furnace = None
        if self.fur_panel is not None:
            destroy(self.fur_panel)
            self.fur_panel = None

    # ── geometry ─────────────────────────────────────────────────────────────
    def boxes(self):
        return FURNACE_BOXES if self.furnace is not None else GEAR_BOXES

    def cell_at(self, x, y):
        cx, cy = math.floor((x - self.gx) / CELL), math.floor((self.gy - y) / CELL)
        return (cx, cy) if 0 <= cx < BACKPACK[0] and 0 <= cy < BACKPACK[1] else None

    def slot_at(self, x, y):
        for key, (dx, dy, w, h) in self.boxes().items():
            sx, sy = self.sx + dx, self.sy - dy
            if sx <= x <= sx + w and sy - h <= y <= sy:
                return key
        return None

    def inside_window(self, x, y):
        w = self.win
        return w.x <= x <= w.x + w.w and w.y - w.h <= y <= w.y

    # ── slots: armor, weapons in hand, furnace ───────────────────────────────
    @staticmethod
    def pile(item_id, n=1):
        return dict(uid=new_id(), id=item_id, n=n, x=0, y=0, rot=False)

    def slot_item(self, key):
        if key in ('head', 'body'):
            return self.inv.equipped.get(key)
        if key in ('tool', 'handgun', 'primary'):
            d = self.game.weapons.slots.get(key)
            return self.pile('w_' + d['id']) if d else None
        return self.furnace[key] if self.furnace else None

    def accepts(self, key, it):
        d = ITEMS[it['id']]
        if key in ('head', 'body'):
            return ARMOR.get(it['id'], {}).get('slot') == key
        if key in ('tool', 'handgun', 'primary'):
            return d['kind'] == 'weapon' and hand_slot(self.game.weapons.get_def(d['weapon'])) == key
        return self.game.barricades.furnace_accepts(key, it['id'])

    def slot_take(self, key):
        """Lift the item out of a slot. Returns it (a pile dict) or None."""
        if key in ('head', 'body'):
            return self.inv.unequip(key)
        if key in ('tool', 'handgun', 'primary'):
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
        if key in ('head', 'body'):
            old = self.inv.equipped.get(key)
            self.inv.equipped[key] = it
            self.inv.changed()
            return old
        if key in ('tool', 'handgun', 'primary'):
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
        if key in ('head', 'body'):
            self.inv.equipped[key] = it
            self.inv.changed()
        elif key in ('tool', 'handgun', 'primary'):
            self.game.weapons.slot_in(self.game.weapons.get_def(ITEMS[it['id']]['weapon']), key)
        elif self.furnace is not None:
            left = self.slot_put(key, it)
            if left:
                self.to_bag(left)

    def to_bag(self, it, near=None):
        """Put a pile in the backpack (at `near` = (x, y, rot) if there's room there); the ground if it's full."""
        if near is not None and self.inv.place(dict(it, x=near[0], y=near[1], rot=near[2]), *near):
            return
        if ITEMS[it['id']]['kind'] == 'weapon' or 'dur' in it:
            if self.inv.put_back(it):
                return
        else:
            it = dict(it, n=self.inv.add(it['id'], it['n']))
            if it['n'] <= 0:
                return
        self.to_ground(it)

    def to_ground(self, it):
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
        U.text(parent, d['name'] if w > 0.1 else d['name'].split()[0], x + 0.006, y - 0.004, 0.5, fg, z=z - 0.02)
        if it['n'] > 1:
            U.text(parent, str(it['n']), x + w - 0.006, y - h + 0.016, 0.75, fg, origin=(0.5, 0), z=z - 0.02)
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
            U.text(parent, SLOT_LABELS[key], x + w / 2, y - h / 2, 0.66, U.contrast(U.NAVY), origin=(0, 0), z=-0.02)
        else:
            self.tile(parent, it, x + 0.008, y - 0.008, w - 0.016, h - 0.016, z=-0.02)

    def refresh(self):
        if not self.active:
            return
        inv = self.inv
        if self.tiles is not None:
            destroy(self.tiles)
        t = self.tiles = Entity(parent=self.win.body)
        # backpack grid
        U.text(t, f'BACKPACK  {BACKPACK[0]} x {BACKPACK[1]}', self.gx, self.gy + 0.03, 0.85, U.MUTED)
        U.box(t, self.gx - 0.006, self.gy + 0.006, BACKPACK[0] * CELL + 0.012, BACKPACK[1] * CELL + 0.012, U.INK,
              z=0.004, round=False)
        for cy in range(BACKPACK[1]):
            for cx in range(BACKPACK[0]):
                U.box(t, self.gx + cx * CELL + 0.002, self.gy - cy * CELL - 0.002, CELL - 0.004, CELL - 0.004,
                      U.NAVY, z=0.003, round=False)
        for it in inv.items:
            w, h = inv.size(it['id'], it['rot'])
            self.tile(t, it, self.gx + it['x'] * CELL + 0.002, self.gy - it['y'] * CELL - 0.002,
                      w * CELL - 0.004, h * CELL - 0.004)
        U.text(t, 'Drag to move, R turns it.  Drop on a slot to wear / hold / smelt it, outside the window '
                  'to drop it.  Right-click: quick move.', self.gx, self.gy - BACKPACK[1] * CELL - 0.02, 0.6, U.MUTED,
               wordwrap=96)
        if self.furnace is not None:          # at a furnace: its slots take the place of your gear
            U.FlatButton(t, 'CLOSE  (E)', self.win.left, self.win.btn_y, 0.26, U.BTN_H, self.game.close_shop)
            self.refresh_furnace()
            return
        # what you're wearing and holding
        U.text(t, 'WEARING', self.sx, self.sy + 0.035, 0.85, U.MUTED)
        for key in ('head', 'body', 'tool', 'handgun', 'primary'):
            self.slot_box(t, key)
        p = self.player
        U.text(t, 'DAMAGE\nTAKEN', self.sx + 0.42, self.sy - 0.01, 0.72, U.MUTED)
        U.text(t, f'-{round(p.armor * 100)}%', self.sx + 0.42, self.sy - 0.075, 1.6, U.INK)
        U.text(t, f'armor {round(inv.protection() * 100)}%\nplating {round(p.base_armor * 100)}%',
               self.sx + 0.42, self.sy - 0.14, 0.62, U.MUTED)
        U.text(t, 'IN YOUR HANDS   (1  2  3)', self.sx, self.sy - 0.285, 0.85, U.MUTED)
        U.FlatButton(t, 'CLOSE  (I)', self.win.left, self.win.btn_y, 0.26, U.BTN_H, self.game.close_shop)

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
        U.text(f, f'Ore: {ores}.\nFuel: {fuel} (one piece burns at a time).\n'
                  'It keeps smelting while you\'re away.', x, y, 0.66, U.MUTED)

    # ── input ────────────────────────────────────────────────────────────────
    def input(self, key):
        """Returns True if the key was used here."""
        if not self.active:
            return False
        inv = self.inv
        mx, my = mouse.x, mouse.y
        if key == 'left mouse down' and self.drag is None:
            c = self.cell_at(mx, my)
            if c is not None:
                it = inv.item_at(*c)
                if it is not None:
                    home = (it['x'], it['y'], it['rot'])
                    self.start_drag(inv.lift(it), ('grid', home), (c[0] - it['x'], c[1] - it['y']))
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

    def quick_move(self, mx, my):
        """Right-click: grid item -> its slot (wear / hold / load); slot -> backpack."""
        inv = self.inv
        c = self.cell_at(mx, my)
        it = inv.item_at(*c) if c else None
        if it is not None:
            home = (it['x'], it['y'], it['rot'])
            target = next((k for k in self.boxes() if self.accepts(k, it)), None)
            if target is None:
                return
            inv.lift(it)
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
                    if ITEMS[taken['id']]['kind'] == 'weapon' or 'dur' in taken:
                        if not inv.put_back(taken):
                            self.slot_restore(s, taken)
                            self.ui.banner('BACKPACK FULL', '#d9912b', 1.2, 'No room for it')
                    else:
                        left = inv.add(taken['id'], taken['n'])
                        if left:
                            self.slot_restore(s, dict(taken, n=left))
            self.game.sounds.play('equip', volume=0.7)
            self.refresh()

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
        w, h = self.inv.size(it['id'], it['rot'])
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
        if self.drag is None:
            return
        gx, gy = self.drag['grab']
        g = self.drag['ghost']
        g.position = (mouse.x - (gx + 0.5) * CELL, mouse.y + (gy + 0.5) * CELL, -0.3)
        self.drag['outline'].color = U.C(U.GREEN if self.drop_ok(mouse.x, mouse.y) else U.RED, 0.85)

    def target(self, mx, my):
        """Where the dragged item would go: ('grid', x, y) / ('slot', key) / ('ground',) / None."""
        s = self.slot_at(mx, my)
        if s is not None:
            return ('slot', s)
        cm = self.cell_at(mx, my)
        if cm is not None:                     # the cell you grabbed it by goes under the mouse
            gx, gy = self.drag['grab']
            return ('grid', cm[0] - gx, cm[1] - gy)
        if not self.inside_window(mx, my):
            return ('ground',)
        return None

    def drop_ok(self, mx, my):
        t = self.target(mx, my)
        it, inv = self.drag['it'], self.inv
        if t is None:
            return False
        if t[0] == 'slot':
            return t[1] != 'out' and self.accepts(t[1], it)
        if t[0] == 'grid':
            other = inv.item_at(t[1], t[2])
            if other is not None and other['id'] == it['id'] and ITEMS[it['id']]['stack'] > 1:
                return True
            return inv.fits(it['id'], t[1], t[2], it['rot'])
        return True

    def finish_drag(self, mx, my):
        d, inv = self.drag, self.inv
        it = d['it']
        t = self.target(mx, my) if self.drop_ok(mx, my) else None
        destroy(d['ghost'])
        self.drag = None
        home = d['src'][1] if d['src'][0] == 'grid' else None
        if t is None:
            self.return_home(d)
        elif t[0] == 'grid':
            if not inv.place(it, t[1], t[2], it['rot']) and it['n'] > 0:
                self.to_bag(it, near=home)             # merged part of a pile: the rest goes back
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
        x, y, rot = d['src'][1]
        it.update(x=x, y=y, rot=rot)
        if not self.inv.place(it, x, y, rot):
            self.to_bag(it)

    def cancel_drag(self):
        if self.drag is not None:
            d = self.drag
            destroy(d['ghost'])
            self.drag = None
            self.return_home(d)
