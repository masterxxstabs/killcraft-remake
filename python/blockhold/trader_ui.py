"""Two hideout screens: a merchant's counter, and the raid picker at the exit ladder.

TraderScreen: on the left what the merchant sells (BUY; Shift+click buys 5), on the right
what you have that they'll buy, from your inventory and from your bank (SELL 1, SELL ALL).
Coins come out of and go into your bank account. Things you buy go in your inventory (or
on you, if it's clothing for an empty slot), and into the bank when you're out of room.

RaidMenu: the raids you can go on (data/raids.py, plus your own maps with extraction
points), with what you're taking up the ladder.
"""
from ursina import Entity, camera, held_keys
from . import ui as U
from .data.items import ITEMS, LIGHT
from .data.merchants import MERCHANTS, buys, sell_price, value
from .render import destroy

ROWS = 8


class TraderScreen:
    def __init__(self, ui):
        self.ui, self.game = ui, ui.game
        self.root = Entity(parent=camera.ui, z=-1, enabled=False)
        U.backdrop(self.root, 0.45)
        self.win = U.Window(self.root, 'MERCHANT', w=1.4, h=0.86, top=0.4)
        self.npc = None
        self.body = None
        self.page = [0, 0]
        self.said = ''

    @property
    def active(self):
        return self.npc is not None

    @property
    def shop(self):
        return MERCHANTS.get(self.npc.data.get('shop'), MERCHANTS['scrapper'])

    def open(self, npc):
        self.npc = npc
        self.page = [0, 0]
        self.said = npc.data.get('greeting', '')
        self.root.enabled = True
        self.game.npcs.talking = npc
        self.refresh()

    def close(self):
        if self.npc is None:
            return
        self.npc = None
        self.game.npcs.talking = None
        self.root.enabled = False
        if self.body is not None:
            destroy(self.body)
            self.body = None

    # ── buying and selling ───────────────────────────────────────────────────
    def sellable(self):
        """[(item id, in inventory, in bank)] for what this merchant buys (not worn, not with things inside)."""
        g = self.game
        have = {}
        for it in g.player.inventory.items:
            if not it.get('contents'):
                have.setdefault(it['id'], [0, 0])[0] += it['n']
        for it in g.raids.bank_items:
            if not it.get('contents'):
                have.setdefault(it['id'], [0, 0])[1] += it['n']
        key = self.npc.data.get('shop')
        return [(k, a, b) for k, (a, b) in sorted(have.items(), key=lambda kv: ITEMS[kv[0]]['name'])
                if buys(key, k)]

    def buy(self, item_id):
        g = self.game
        n = 5 if held_keys['shift'] and ITEMS[item_id]['stack'] > 1 else 1
        price = value(item_id) * n
        if g.coins < price:
            g.sounds.play('deny')
            self.said = "You can't afford that."
            return self.refresh()
        inv = g.player.inventory
        got = 0
        to_bank = 0
        for _ in range(n):
            if inv.give(item_id):
                got += 1
            elif g.raids.to_bank(item_id, 1) == 0:
                to_bank += 1
            else:
                break
        if got + to_bank == 0:
            g.sounds.play('deny')
            self.said = 'No room on you and no room in your bank.'
            return self.refresh()
        g.coins -= value(item_id) * (got + to_bank)
        g.sounds.play('buy')
        name = ITEMS[item_id]['name']
        self.said = f'{got + to_bank} x {name}' + (' (sent to your bank)' if to_bank else '') + '. Pleasure.'
        g.events.emit('merchant_buy', npc=self.npc.uid, item=item_id, n=got + to_bank)
        self.refresh()

    def take(self, item_id, n):
        """Take up to n of item_id from your inventory, then the bank (never clothing with things in it)."""
        g = self.game
        taken = 0
        piles = [(gr.items, it) for gr in g.player.inventory.grids() for it in gr.items]
        piles += [(g.raids.bank_items, it) for it in g.raids.bank_items]
        for lst, it in piles:
            if taken >= n:
                break
            if it['id'] != item_id or it.get('contents'):
                continue
            k = min(it['n'], n - taken)
            it['n'] -= k
            taken += k
            if it['n'] <= 0:
                lst.remove(it)
        g.player.inventory.changed()
        return taken

    def sell(self, item_id, all_of_them=False):
        g = self.game
        have = next(((a + b) for k, a, b in self.sellable() if k == item_id), 0)
        n = self.take(item_id, have if all_of_them else 1)
        if n <= 0:
            g.sounds.play('deny')
            return self.refresh()
        pay = sell_price(item_id, n)
        g.coins += pay
        g.sounds.play('buy')
        self.said = f"{n} x {ITEMS[item_id]['name']} for {pay} coins."
        g.events.emit('merchant_sell', npc=self.npc.uid, item=item_id, n=n, coins=pay)
        self.refresh()

    def turn(self, side, d):
        self.page[side] = max(0, self.page[side] + d)
        self.refresh()

    # ── drawing ──────────────────────────────────────────────────────────────
    def row(self, b, x, y, w, item_id, line, right):
        d = ITEMS[item_id]
        U.box(b, x, y, w, 0.046, 'PAPER', z=0.002)
        U.box(b, x + 0.006, y - 0.008, 0.03, 0.03, d['colour'], z=-0.005)
        U.text(b, d['name'], x + 0.045, y - 0.012, 0.82, 'INK')
        U.text(b, line, x + 0.045, y - 0.032, 0.6, 'MUTED')
        U.text(b, right, x + w - 0.2, y - 0.023, 0.8, 'INK', origin=(0.5, 0))

    def pager(self, b, x, y, side, total):
        pages = max(1, (total + ROWS - 1) // ROWS)
        self.page[side] = min(self.page[side], pages - 1)
        if pages > 1:
            U.FlatButton(b, 'PREV', x, y, 0.08, 0.036, lambda: self.turn(side, -1), fill='SLATE', edge='INK', size=0.65)
            U.text(b, f'{self.page[side] + 1} / {pages}', x + 0.12, y - 0.018, 0.7, 'MUTED', origin=(0, 0))
            U.FlatButton(b, 'NEXT', x + 0.16, y, 0.08, 0.036, lambda: self.turn(side, 1), fill='SLATE', edge='INK', size=0.65)

    def refresh(self):
        if self.npc is None:
            return
        if self.body is not None:
            destroy(self.body)
        b = self.body = Entity(parent=self.win.body)
        g, win = self.game, self.win
        win.title.text = self.npc.name
        win.right.text = f'{g.coins} coins'
        x0, xr, y0 = win.left, win.right_col + 0.01, win.top + 0.01
        col_w = 0.6
        U.frame(b, x0, y0, win.w - 0.12, 0.05, 'NAVY', 'LINE')
        U.text(b, f'"{self.said}"' if self.said else '', x0 + 0.02, y0 - 0.025, 0.8, 'PAPER', origin=(-0.5, 0))
        y = y0 - 0.08
        U.text(b, f"{self.shop['name'].upper()} SELLS", x0, y, 0.75, 'MUTED')
        U.text(b, 'WHAT THEY BUY FROM YOU', xr, y, 0.75, 'MUTED')
        y -= 0.03
        stock = self.shop['sells']
        for k, item_id in enumerate(stock[self.page[0] * ROWS:(self.page[0] + 1) * ROWS]):
            yy = y - k * 0.052
            price = value(item_id)
            d = ITEMS[item_id]
            info = f"{d['size'][0]}x{d['size'][1]}" + (f",  gives {d['grid'][0]}x{d['grid'][1]}" if d.get('grid') else '')
            self.row(b, x0, yy, col_w, item_id, info, f'{price}')
            ok = g.coins >= price
            U.FlatButton(b, 'BUY', x0 + col_w - 0.13, yy - 0.006, 0.12, 0.034, lambda i=item_id: self.buy(i),
                         fill='GREEN' if ok else 'SLATE', edge='INK', size=0.7)
        self.pager(b, x0, y - ROWS * 0.052 - 0.005, 0, len(stock))
        mine = self.sellable()
        if not mine:
            U.text(b, "Nothing they want. Bring them something from up top\n(on you or in your bank).", xr, y - 0.01,
                   0.75, 'MUTED')
        for k, (item_id, a, bank) in enumerate(mine[self.page[1] * ROWS:(self.page[1] + 1) * ROWS]):
            yy = y - k * 0.052
            where = (f'{a} on you' if a else '') + ('  ·  ' if a and bank else '') + (f'{bank} in bank' if bank else '')
            self.row(b, xr, yy, col_w, item_id, where, f'{sell_price(item_id)}')
            U.FlatButton(b, 'SELL', xr + col_w - 0.25, yy - 0.006, 0.1, 0.034, lambda i=item_id: self.sell(i),
                         fill='TEAL', edge='INK', size=0.65)
            U.FlatButton(b, 'ALL', xr + col_w - 0.14, yy - 0.006, 0.13, 0.034, lambda i=item_id: self.sell(i, True),
                         fill='SLATE', edge='INK', size=0.65, right=str(sell_price(item_id, a + bank)))
        self.pager(b, xr, y - ROWS * 0.052 - 0.005, 1, len(mine))
        U.text(b, 'Coins go into (and come out of) your bank. Shift+click BUY for 5. Out of room? It goes to the bank.',
               x0, win.btn_y + 0.03, 0.62, 'MUTED')
        U.FlatButton(b, 'BANK', x0 + win.w - 0.12 - 0.5, win.btn_y, 0.22, U.BTN_H, self.game.open_bank,
                     fill='SLATE', edge='INK', size=0.9)
        U.FlatButton(b, 'DONE  (E)', x0 + win.w - 0.12 - 0.26, win.btn_y, 0.26, U.BTN_H, self.game.close_shop,
                     fill='TEAL', edge='INK')


class RaidMenu:
    def __init__(self, ui):
        self.ui, self.game = ui, ui.game
        self.root = Entity(parent=camera.ui, z=-1, enabled=False)
        U.backdrop(self.root, 0.45)
        self.win = U.Window(self.root, 'TO THE SURFACE', w=1.4, h=0.86, top=0.4)
        self.body = None
        self.active = False

    def open(self):
        self.active = True
        self.root.enabled = True
        self.refresh()

    def close(self):
        if not self.active:
            return
        self.active = False
        self.root.enabled = False
        if self.body is not None:
            destroy(self.body)
            self.body = None

    def go(self, option):
        self.game.close_shop()
        self.game.raids.start_raid(option)

    def refresh(self):
        if self.body is not None:
            destroy(self.body)
        b = self.body = Entity(parent=self.win.body)
        g, win = self.game, self.win
        p = g.player
        x0, y = win.left, win.top + 0.01
        win.right.text = f'Level {p.level}'
        options = g.raids.options()
        U.text(b, 'WHERE TO?', x0, y, 0.75, 'MUTED')
        y -= 0.03
        for opt in options[:6]:
            U.frame(b, x0, y, 0.74, 0.088, 'PAPER', 'LINE')
            U.text(b, opt['name'].upper(), x0 + 0.015, y - 0.014, 1.05, 'INK')
            lv = opt.get('levels')
            facts = f"{opt['size'] * 2} x {opt['size'] * 2} m  ·  {opt['exits']} ways out" + \
                (f"  ·  zombies level {lv[0]}-{lv[3]}" if lv else '')
            U.text(b, facts, x0 + 0.015, y - 0.044, 0.62, 'TEAL')
            U.text(b, opt['desc'], x0 + 0.015, y - 0.064, 0.6, 'MUTED', wordwrap=80)
            U.FlatButton(b, 'GO', x0 + 0.74 - 0.13, y - 0.02, 0.11, 0.048, lambda o=opt: self.go(o), fill='GREEN',
                         edge='INK', size=0.9)
            y -= 0.098
        # what you're taking
        xr, y = x0 + 0.8, win.top + 0.01
        U.text(b, 'YOU TAKE', xr, y, 0.75, 'MUTED')
        y -= 0.035
        inv = p.inventory
        kg = p.carried_weight()
        worn = [ITEMS[it['id']]['name'] for it in inv.equipped.values() if it is not None]
        hands = [d['name'] for d in g.weapons.owned]
        lines = [f'Weapons: {", ".join(hands) or "none"}', f'Wearing: {", ".join(worn) or "nothing"}',
                 f'Room: {inv.room()} cells   ·   {len(inv.items)} things carried', f'Weight: {kg:.1f} kg' +
                 ('  (heavy: you\'ll be slower)' if kg > LIGHT else '')]
        for line in lines:
            t = U.text(b, line, xr, y, 0.7, 'INK', wordwrap=46)
            y -= 0.032 * (t.text.count('\n') + 1) + 0.008
        y -= 0.02
        U.text(b, 'Everything you take can be lost. Die up there and it stays where you fell; get to an extraction '
                  'point and stand in it to come home with it all.\n\nAnything in your bank is safe.', xr, y, 0.66,
               'MUTED', wordwrap=48)
        U.FlatButton(b, 'STAY  (E)', x0 + win.w - 0.12 - 0.26, win.btn_y, 0.26, U.BTN_H, g.close_shop, fill='SLATE',
                     edge='INK')
