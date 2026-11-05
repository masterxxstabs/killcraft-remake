"""The talk window: opens when you press E next to an NPC.

The NPC says their greeting; the buttons under it are TALK (their next line),
TRADE (traders: swap items and coins), JOB (quest givers: take a job, check on it,
hand it in) and BYE. E or Esc closes it too.
"""
from ursina import Entity, camera
from . import ui as U
from .data.items import ITEMS
from .data.npcs import quest_goal_text
from .render import destroy

W, H, TOP = 1.06, 0.8, 0.4
MAX_TRADES = 6


def item_label(item, n):
    if item == 'coins':
        return f'{n} coins'
    d = ITEMS.get(item)
    return f"{n} x {d['name']}" if d else f'{n} x {item}'


class TalkScreen:
    def __init__(self, ui):
        self.ui, self.game = ui, ui.game
        self.root = Entity(parent=camera.ui, z=-1, enabled=False)
        U.backdrop(self.root, 0.35)
        self.win = U.Window(self.root, '', w=W, h=H, top=TOP)
        self.npc = None
        self.mode = 'talk'          # talk, trade, job
        self.said = ''
        self.line = 0
        self.body = None

    @property
    def active(self):
        return self.npc is not None

    def open(self, npc):
        self.npc = npc
        self.mode = 'talk'
        self.line = 0
        self.said = npc.data.get('greeting', 'Hello.')
        self.root.enabled = True
        self.game.npcs.talking = npc
        self.game.sounds.play('equip', volume=0.5, pitch=0.8)
        self.game.events.emit('npc_talk', npc=npc.uid, player=self.game.player)
        self.refresh()

    def close(self):
        if self.npc is not None and self.npc.data.get('farewell'):
            self.ui.kill_feed(f"{self.npc.name}: {self.npc.data['farewell']}")
        self.npc = None
        self.game.npcs.talking = None
        self.root.enabled = False
        if self.body is not None:
            destroy(self.body)
            self.body = None

    # ── buttons ──────────────────────────────────────────────────────────────
    def talk(self):
        lines = self.npc.data.get('lines') or ['...']
        self.said = lines[self.line % len(lines)]
        self.line += 1
        self.mode = 'talk'
        self.refresh()

    def show(self, mode):
        self.mode = mode
        n, p = self.npc, self.game.player
        if mode == 'job':
            q = n.data.get('quest')
            st = self.game.npcs.quest_state(n, p)
            if not q:
                self.said = "I've got nothing for you right now."
            elif st is None:
                self.said = q.get('offer', 'I could use a hand.')
            elif st['state'] == 'done':
                self.said = 'You already did me a good turn. Thank you.'
            elif self.game.npcs.can_finish(n, p):
                self.said = 'You did it? Let me see.'
            else:
                self.said = q.get('progress', 'Still waiting.')
        elif mode == 'trade':
            self.said = 'Take a look.'
        self.refresh()

    def accept(self):
        self.game.npcs.take_quest(self.npc, self.game.player)
        self.said = 'Good. Come back when it\'s done.'
        self.refresh()

    def hand_in(self):
        n = self.npc
        if self.game.npcs.finish_quest(n, self.game.player):
            self.said = n.data['quest'].get('done', 'Thank you!')
        else:
            self.game.sounds.play('deny')
        self.refresh()

    def do_trade(self, t):
        if self.game.npcs.trade(self.npc, self.game.player, t):
            self.said = 'Pleasure doing business.'
        else:
            self.said = "You don't have enough for that."
        self.refresh()

    # ── drawing ──────────────────────────────────────────────────────────────
    def refresh(self):
        if self.npc is None:
            return
        if self.body is not None:
            destroy(self.body)
        b = self.body = Entity(parent=self.win.body)
        g, n, win = self.game, self.npc, self.win
        d = n.data
        role = dict(trader='TRADER', quest='QUEST GIVER', talker='', banker='BANKER', merchant='MERCHANT',
                    gunsmith='GUNSMITH').get(d.get('role'), '')
        if d.get('role') == 'banker':
            role = f'{g.coins} coins in your account'
        win.title.text = n.name
        win.right.text = f'{g.coins} coins' if self.mode == 'trade' else role
        x0, y = win.left, win.top
        inner = W - 0.12
        # what they're saying
        U.frame(b, x0, y + 0.01, inner, 0.13, 'NAVY', 'LINE')
        U.text(b, f'"{self.said}"', x0 + 0.025, y - 0.01, 0.95, 'PAPER', wordwrap=52)
        y -= 0.16
        # the buttons
        tabs = [('TALK', self.talk)]
        if d.get('role') == 'trader' and d.get('trades'):
            tabs.append(('TRADE', lambda: self.show('trade')))
        if d.get('role') == 'quest' and d.get('quest'):
            tabs.append(('JOB', lambda: self.show('job')))
        if d.get('role') == 'banker':
            tabs.append(('BANK', g.open_bank))
        if d.get('role') == 'merchant':
            tabs.append(('TRADE', lambda: g.open_trader(n)))
        if d.get('role') == 'gunsmith':
            tabs.append(('GUNS', lambda: g.open_shop(gunsmith=True)))
        tabs.append(('BYE  (E)', g.close_shop))
        bw = (inner - 0.015 * (len(tabs) - 1)) / len(tabs)
        for i, (label, fn) in enumerate(tabs):
            on = label.lower() == self.mode
            U.FlatButton(b, label, x0 + i * (bw + 0.015), y, bw, 0.055, fn, fill='TEAL' if on else 'SLATE',
                         edge='INK', size=0.9)
        y -= 0.085
        if self.mode == 'trade':
            self.draw_trades(b, x0, y, inner)
        elif self.mode == 'job':
            self.draw_job(b, x0, y, inner)

    def draw_trades(self, b, x0, y, inner):
        g, n, p = self.game, self.npc, self.game.player
        U.text(b, 'YOU GIVE', x0, y, 0.75, 'MUTED')
        U.text(b, 'YOU GET', x0 + 0.42, y, 0.75, 'MUTED')
        y -= 0.035
        for t in n.data.get("trades", [])[:MAX_TRADES]:
            ok = g.npcs.can_trade(p, t)
            have = g.coins if t['give'] == 'coins' else p.inventory.count(t['give'])
            U.box(b, x0, y, inner, 0.05, 'NAVY' if ok else 'LINE', z=0.002)
            U.text(b, item_label(t['give'], t['give_n']), x0 + 0.015, y - 0.025, 0.82, 'PAPER', origin=(-0.5, 0))
            U.text(b, f'(have {have})', x0 + 0.3, y - 0.025, 0.65, 'PAPER', origin=(-0.5, 0))
            U.text(b, item_label(t['get'], t['get_n']), x0 + 0.42, y - 0.025, 0.82, 'PAPER', origin=(-0.5, 0))
            U.FlatButton(b, 'TRADE', x0 + inner - 0.14, y - 0.006, 0.13, 0.038, lambda t=t: self.do_trade(t),
                         fill='GREEN' if ok else 'SLATE', edge='INK', size=0.75)
            y -= 0.058

    def draw_job(self, b, x0, y, inner):
        g, n, p = self.game, self.npc, self.game.player
        q = n.data.get('quest')
        if not q:
            return
        st = g.npcs.quest_state(n, p)
        U.text(b, 'JOB', x0, y, 0.75, 'MUTED')
        U.text(b, quest_goal_text(q), x0, y - 0.03, 1.2, 'INK')
        reward = []
        if q.get('reward_coins'):
            reward.append(f"{q['reward_coins']} coins")
        if q.get('reward_item') and q.get('reward_n', 0) > 0:
            reward.append(item_label(q['reward_item'], q['reward_n']))
        U.text(b, 'Reward: ' + (', '.join(reward) or 'their thanks'), x0, y - 0.085, 0.85, 'MUTED')
        y -= 0.13
        if st is None:
            U.FlatButton(b, 'ACCEPT JOB', x0, y, 0.26, 0.055, self.accept, fill='GREEN', edge='INK', size=0.9)
        elif st['state'] == 'done':
            U.text(b, 'Finished.', x0, y - 0.01, 1.0, 'GREEN')
        else:
            have, need = g.npcs.progress(n, p)
            U.bar(b, x0, y, 0.5, 0.03, have / max(1, need))
            U.text(b, f'{have} / {need}', x0 + 0.52, y + 0.004, 0.85, 'INK')
            ok = g.npcs.can_finish(n, p)
            U.FlatButton(b, 'HAND IN', x0, y - 0.05, 0.26, 0.055, self.hand_in, fill='GREEN' if ok else 'SLATE',
                         edge='INK', size=0.9)
