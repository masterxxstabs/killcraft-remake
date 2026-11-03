"""The backpack screen (I) and the furnace screen (E at a furnace).

Left: the armor you're wearing (HEAD and BODY) and, at a furnace, its controls.
Right: the backpack grid. Drag items to move them, press R while dragging to turn them,
drop armor on HEAD / BODY to wear it, drop anything outside the window to put it on the
ground. Right-click wears armor or takes it off.
"""
import math
from ursina import Entity, camera, mouse
from . import ui as U
from .data.items import ARMOR, BACKPACK, ITEMS, SLOTS, SMELTING
from .render import destroy

CELL = 0.062
SLOT_BOX = {'head': (0.0, 0.0, 0.17, 0.17), 'body': (0.2, 0.0, 0.19, 0.26)}    # relative to the slot area


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


class BagScreen:
    def __init__(self, ui):
        self.ui, self.game = ui, ui.game
        self.root = Entity(parent=camera.ui, z=-1, enabled=False)
        U.backdrop(self.root, 0.5)
        self.win = U.Window(self.root, 'BACKPACK')
        self.active = False
        self.furnace = None
        self.drag = None           # dict(it, src, home, grab, ghost)
        self.tiles = None
        self.fur_panel = None
        self.fur_t = 0.0
        self.updater = Entity(parent=self.root, update=self.update)
        w = self.win
        self.gx, self.gy = w.x + 0.64, w.top - 0.035              # top-left of the grid
        self.sx, self.sy = w.left, w.top - 0.04                   # top-left of the armor slots

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
    def cell_at(self, x, y):
        cx, cy = math.floor((x - self.gx) / CELL), math.floor((self.gy - y) / CELL)
        return (cx, cy) if 0 <= cx < BACKPACK[0] and 0 <= cy < BACKPACK[1] else None

    def slot_at(self, x, y):
        for slot, (dx, dy, w, h) in SLOT_BOX.items():
            sx, sy = self.sx + dx, self.sy - dy
            if sx <= x <= sx + w and sy - h <= y <= sy:
                return slot
        return None

    def inside_window(self, x, y):
        w = self.win
        return w.x <= x <= w.x + w.w and w.y - w.h <= y <= w.y

    # ── drawing ──────────────────────────────────────────────────────────────
    def tile(self, parent, it, x, y, w, h, z=-0.01):
        d = ITEMS[it['id']]
        broken = 'dur' in it and it['dur'] <= 0
        U.box(parent, x, y, w, h, U.INK, z=z + 0.002)
        U.box(parent, x + 0.003, y - 0.003, w - 0.006, h - 0.006, U.C(d['colour'], 0.55 if broken else 0.9), z=z + 0.001)
        draw_icon(parent, d['icon'], x + w / 2, y - h / 2 + 0.004, min(w, h) * 0.78, d['colour'] if not broken else '#555555')
        fg = U.contrast(d['colour'])
        U.text(parent, d['name'] if w > 0.1 else d['name'].split()[0], x + 0.006, y - 0.004, 0.5, fg, z=z - 0.02)
        if it['n'] > 1:
            U.text(parent, str(it['n']), x + w - 0.006, y - h + 0.016, 0.75, fg, origin=(0.5, 0), z=z - 0.02)
        if 'dur' in it:                                  # durability bar
            k = it['dur'] / ARMOR[it['id']]['durability']
            U.box(parent, x + 0.006, y - h + 0.012, w - 0.012, 0.006, '#000000', z=z - 0.02)
            U.box(parent, x + 0.006, y - h + 0.012, (w - 0.012) * k, 0.006, U.GREEN if k > 0.3 else U.RED,
                  z=z - 0.021, round=False)

    def refresh(self):
        if not self.active:
            return
        p = self.game.player
        inv = p.inventory
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
        if self.furnace is not None:          # at a furnace: its controls take the place of the armor
            self.refresh_furnace()
            U.FlatButton(t, 'CLOSE  (E)', self.win.left, self.win.btn_y, 0.26, U.BTN_H, self.game.close_shop)
            return
        # armor slots
        U.text(t, 'WEARING', self.sx, self.sy + 0.035, 0.85, U.MUTED)
        for slot, label in SLOTS:
            dx, dy, w, h = SLOT_BOX[slot]
            x, y = self.sx + dx, self.sy - dy
            U.frame(t, x, y, w, h, U.NAVY, U.INK)
            it = inv.equipped[slot]
            if it is None:
                U.text(t, label, x + w / 2, y - h / 2, 0.8, U.contrast(U.NAVY), origin=(0, 0), z=-0.02)
            else:
                self.tile(t, it, x + 0.008, y - 0.008, w - 0.016, h - 0.016, z=-0.02)
        y = self.sy - 0.29
        base, gear = p.base_armor, inv.protection()
        U.text(t, f'Damage taken  -{round(p.armor * 100)}%', self.sx, y, 1.0, U.INK)
        U.text(t, f'armor {round(gear * 100)}%  +  Plating upgrades {round(base * 100)}%', self.sx, y - 0.035,
               0.72, U.MUTED)
        U.text(t, 'Drag to move.  R turns it while you drag.\nDrop armor on HEAD or BODY to wear it '
                  '(or right-click it).\nDrop something outside this window to put it on the ground.',
               self.sx, y - 0.08, 0.72, U.MUTED)
        U.FlatButton(t, 'CLOSE  (I)', self.win.left, self.win.btn_y, 0.26, U.BTN_H, self.game.close_shop)

    def refresh_furnace(self):
        if self.fur_panel is not None:
            destroy(self.fur_panel)
            self.fur_panel = None
        b = self.furnace
        if not self.active or b is None:
            return
        bars = self.game.barricades
        if b not in bars.list:                          # it got smashed
            self.furnace = None
            return
        f = self.fur_panel = Entity(parent=self.win.body)
        p = self.game.player
        x, y = self.sx, self.sy + 0.035
        coal = p.inventory.count('coal')
        U.text(f, f'SMELT   (you have {coal} coal)', x, y, 0.85, U.MUTED)
        y -= 0.04
        for ore, ingot, need_ore, need_coal, secs in SMELTING:
            have = p.inventory.count(ore)
            most = min(have // need_ore, coal // need_coal)
            U.text(f, f"{ITEMS[ingot]['name']}", x, y - 0.004, 0.85, U.INK)
            U.text(f, f'{need_ore} ore + {need_coal} coal  ({have} ore)', x, y - 0.03, 0.62, U.MUTED)
            for i, (label, n) in enumerate((('1', 1), ('5', 5), ('ALL', 999))):
                ok = most >= (1 if n == 999 else n)
                U.FlatButton(f, label, x + 0.23 + i * 0.075, y, 0.068, 0.04,
                             lambda o=ore, n=n: self.smelt(o, n), fill=U.TEAL if ok else U.NAVY, edge=U.INK,
                             size=0.75)
            y -= 0.058
        ingot, k = bars.furnace_progress(b)
        queued = sum(j[1] for j in b['jobs'])
        if ingot:
            U.text(f, f"Smelting {ITEMS[ingot]['name'].lower()}...  {queued} to go", x, y, 0.72, U.INK)
            U.bar(f, x, y - 0.03, 0.45, 0.012, k)
        else:
            U.text(f, 'Idle. Load some ore.', x, y, 0.72, U.MUTED)
        ready = sum(b['out'].values())
        if ready:
            txt = ', '.join(f"{n} {ITEMS[i]['name'].lower()}" for i, n in b['out'].items())
            U.text(f, f'Ready: {txt}', x, y - 0.075, 0.8, U.INK)
            U.FlatButton(f, 'TAKE INGOTS', x, y - 0.1, 0.26, 0.055, self.take, fill=U.GREEN, edge=U.INK, size=0.9)
        U.text(f, 'The furnace keeps smelting while you\'re away.\nCome back and take the ingots.', x, y - 0.19,
               0.7, U.MUTED)

    # ── furnace buttons ──────────────────────────────────────────────────────
    def smelt(self, ore, n):
        if self.furnace is None:
            return
        made = self.game.barricades.smelt(self.furnace, self.game.player, ore, n)
        self.game.sounds.play('craft' if made else 'deny', volume=0.6)
        self.refresh()

    def take(self):
        if self.furnace is None:
            return
        got = self.game.barricades.collect(self.furnace, self.game.player)
        self.game.sounds.play('coin' if got else 'deny')
        self.refresh()

    # ── dragging ─────────────────────────────────────────────────────────────
    def input(self, key):
        """Returns True if the key was used here."""
        if not self.active:
            return False
        inv = self.game.player.inventory
        mx, my = mouse.x, mouse.y
        if key == 'left mouse down' and self.drag is None:
            c = self.cell_at(mx, my)
            if c is not None:
                it = inv.item_at(*c)
                if it is not None:
                    self.start_drag(inv.lift(it), ('grid', (it['x'], it['y'], it['rot'])), (c[0] - it['x'], c[1] - it['y']))
                    return True
            s = self.slot_at(mx, my)
            if s is not None and inv.equipped[s] is not None:
                self.start_drag(inv.unequip(s), ('slot', s), (0, 0))
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
            c = self.cell_at(mx, my)
            it = inv.item_at(*c) if c else None
            if it is not None and it['id'] in ARMOR:
                home = (it['x'], it['y'], it['rot'])
                inv.lift(it)
                if not inv.equip(it):
                    it.update(x=home[0], y=home[1], rot=home[2])
                    inv.put_back(it)
                self.game.sounds.play('equip', volume=0.7)
                return True
            s = self.slot_at(mx, my)
            if s is not None and inv.equipped[s] is not None:
                it = inv.unequip(s)
                if not inv.put_back(it):
                    inv.equipped[s] = it
                    self.game.ui.banner('BACKPACK FULL', '#d9912b', 1.2, 'No room to take it off')
                self.refresh()
                return True
        return False

    def start_drag(self, it, src, grab):
        self.drag = dict(it=it, src=src, grab=grab, ghost=None)
        self.build_ghost()
        self.game.sounds.play('equip', volume=0.4, pitch=1.3)

    def build_ghost(self):
        if self.drag['ghost'] is not None:
            destroy(self.drag['ghost'])
        it = self.drag['it']
        w, h = self.game.player.inventory.size(it['id'], it['rot'])
        g = self.drag['ghost'] = Entity(parent=self.win.body, z=-0.3)
        self.tile(g, it, 0, 0, w * CELL - 0.004, h * CELL - 0.004, z=-0.3)
        self.drag['outline'] = U.box(g, -0.004, 0.004, w * CELL + 0.004, h * CELL + 0.004, U.TEAL, z=-0.29)

    def update(self):
        if not self.active:
            return
        self.fur_t -= 1 / 30
        if self.furnace is not None and self.drag is None and self.fur_t <= 0:
            self.fur_t = 0.3
            self.refresh_furnace()
        if self.drag is None:
            return
        gx, gy = self.drag['grab']
        g = self.drag['ghost']
        g.position = (mouse.x - (gx + 0.5) * CELL, mouse.y + (gy + 0.5) * CELL, -0.3)
        ok = self.drop_ok(mouse.x, mouse.y)
        self.drag['outline'].color = U.C(U.GREEN if ok else U.RED, 0.85)

    def target(self, mx, my):
        """Where the dragged item would go: ('grid', x, y) / ('slot', s) / ('ground',) / None."""
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
        it, inv = self.drag['it'], self.game.player.inventory
        if t is None:
            return False
        if t[0] == 'slot':
            return ARMOR.get(it['id'], {}).get('slot') == t[1]
        if t[0] == 'grid':
            other = inv.item_at(t[1], t[2])
            if other is not None and other['id'] == it['id'] and ITEMS[it['id']]['stack'] > 1:
                return True
            return inv.fits(it['id'], t[1], t[2], it['rot'])
        return True

    def finish_drag(self, mx, my):
        d, inv = self.drag, self.game.player.inventory
        it = d['it']
        t = self.target(mx, my) if self.drop_ok(mx, my) else None
        done = False
        if t is not None and t[0] == 'grid':
            done = inv.place(it, t[1], t[2], it['rot'])
            if not done and it['n'] > 0:                 # merged part of a pile: the rest goes back
                done = inv.put_back(it)
        elif t is not None and t[0] == 'slot':
            done = inv.equip(it)
        elif t is not None and t[0] == 'ground':
            self.game.drops.drop_item(self.game.player, it)
            done = True
        destroy(d['ghost'])
        self.drag = None
        if not done:
            self.return_home(d)
        self.game.sounds.play('equip', volume=0.4)
        self.refresh()

    def return_home(self, d):
        inv, it = self.game.player.inventory, d['it']
        if d['src'][0] == 'slot':
            inv.equipped[d['src'][1]] = it
            inv.changed()
            return
        x, y, rot = d['src'][1]
        it.update(x=x, y=y, rot=rot)
        if not inv.place(it, x, y, rot) and not inv.put_back(it):
            self.game.drops.drop_item(self.game.player, it)

    def cancel_drag(self):
        if self.drag is not None:
            d = self.drag
            destroy(d['ghost'])
            self.drag = None
            self.return_home(d)
