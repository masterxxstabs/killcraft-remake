"""The map editor's NPC panel: who an NPC is, what they say, what they trade and
what job they give out (open it by placing an NPC, or Ctrl+click one and press N).

Tabs:  LOOK      name, role, colours, hat and extras (the NPC in the map updates as you go)
       DIALOGUE  greeting, up to four TALK lines and a goodbye
       TRADES    up to six swaps: what the player gives and what they get
       QUEST     the job: bring items, kill zombies or hunt animals, and the reward
Everything is saved with the map.
"""
import copy
from ursina import Entity, InputField, camera
from . import ui as U
from .data.items import ITEMS
from .data.npcs import quest_goal_text
from .data.npcs import (CLOTH_COLOURS, DEFAULT_QUEST, HAIR_COLOURS, HATS, HUNT_TARGETS, PRESETS, QUEST_KINDS, ROLES,
                        SKIN_COLOURS)
from .render import destroy

TABS = [('look', 'LOOK'), ('dialogue', 'DIALOGUE'), ('trades', 'TRADES'), ('quest', 'QUEST')]
W, H, TOP = 1.16, 0.86, 0.4
SHIFT = -0.3                 # the panel sits left of centre so you can watch the NPC change on the right
MAX_TRADES = 6
MAX_LINES = 4


def tradeable():
    """Everything an NPC can trade: coins first, then items (no weapons on the give side)."""
    items = [k for k, d in ITEMS.items() if d['kind'] != 'weapon']
    guns = [k for k, d in ITEMS.items() if d['kind'] == 'weapon']
    return ['coins'] + items, ['coins'] + items + guns


def auto_offer(q):
    return f"{quest_goal_text(q)} for me and I'll make it worth your while."


def label(item):
    return 'Coins' if item == 'coins' else (ITEMS[item]['name'] if item in ITEMS else 'None')


class NpcEditor:
    def __init__(self, editor, prop):
        self.editor, self.prop = editor, prop
        self.data = prop['data']
        self.before = copy.deepcopy(self.data)
        self.tab = 'look'
        self.fields = {}             # key -> InputField (read back before redrawing)
        self.picker = None           # (title, choices, on_pick) while the item list is open
        self.root = Entity(parent=camera.ui, z=-0.8)
        Entity(parent=self.root, model='quad', color=U.C('INK', 0.55), scale=(4, 1), z=0.05, collider='box')
        self.win = U.Window(self.root, 'EDIT NPC', w=W, h=H, top=TOP)
        self.win.root.x = SHIFT
        self.body = None
        self.draw()

    # ── helpers ──────────────────────────────────────────────────────────────
    def typing(self):
        return any(f.active for f in self.fields.values())

    def read_fields(self):
        for key, f in self.fields.items():
            value = f.text.strip()
            if key == 'name':
                self.data['name'] = value or 'Stranger'
            elif key.startswith('line'):
                i = int(key[4:])
                lines = self.data.setdefault('lines', [])
                while len(lines) <= i:
                    lines.append('')
                lines[i] = value
            elif key.startswith('q_'):
                if self.data.get('quest'):
                    self.data['quest'][key[2:]] = value
            else:
                self.data[key] = value
        if 'lines' in self.data:
            self.data['lines'] = [ln for ln in self.data['lines'] if ln] or ['...']

    def redraw(self):
        self.read_fields()
        self.draw()

    def set(self, key, value, model=False):
        self.read_fields()
        self.data[key] = value
        if model:
            self.editor.refresh_npc_model(self.prop)
        self.draw()

    def field(self, parent, key, value, x, y, w, limit=90):
        f = InputField(default_value=value, text=value, parent=parent, position=(x + w / 2, y - 0.0225, -0.02),
                       scale=(w, 0.045), character_limit=limit, color=U.C('PAPER'))
        f.text_color = U.C('INK')
        f.highlight_color = U.C('PAPER').tint(-0.06)
        f.text_field.scale *= 0.62                      # Ursina's default text is too big for a long line
        f.text_field.x, f.text_field.y = -0.48, 0.17
        self.fields[key] = f
        return f

    def swatches(self, parent, x, y, choices, current, on_pick, size=0.034):
        for i, c in enumerate(choices):
            on = c == current
            bx = x + i * (size + 0.008)
            if c is None:
                U.FlatButton(parent, '-', bx, y, size, size, lambda v=c: on_pick(v), fill='PAPER',
                             edge='TEAL' if on else 'LINE', fg='INK', size=0.7, hover=-0.08)
            else:
                U.FlatButton(parent, '', bx, y, size, size, lambda v=c: on_pick(v), fill=c,
                             edge='TEAL' if on else 'LINE', hover=0.1)
            if on:
                U.box(parent, bx, y - size - 0.004, size, 0.005, 'TEAL', z=-0.03)

    def choice_row(self, parent, x, y, options, current, on_pick, w=0.15, h=0.04, size=0.75):
        for i, (value, name) in enumerate(options):
            on = value == current
            U.FlatButton(parent, name, x + i * (w + 0.008), y, w, h, lambda v=value: on_pick(v),
                         fill='TEAL' if on else 'SLATE', edge='INK', size=size)

    def stepper(self, parent, x, y, value, on_change, step=1, lo=1, hi=999, w=0.07):
        U.FlatButton(parent, '-', x, y, 0.036, 0.036, lambda: on_change(max(lo, value - step)), fill='SLATE',
                     edge='INK', size=0.9)
        U.box(parent, x + 0.04, y, w, 0.036, 'NAVY', z=-0.01)
        U.text(parent, str(value), x + 0.04 + w / 2, y - 0.018, 0.85, 'PAPER', origin=(0, 0), z=-0.02)
        U.FlatButton(parent, '+', x + 0.044 + w, y, 0.036, 0.036, lambda: on_change(min(hi, value + step)),
                     fill='SLATE', edge='INK', size=0.9)

    def item_button(self, parent, x, y, w, item, title, choices, on_pick):
        def open_picker():
            self.read_fields()
            self.picker = (title, choices, on_pick)
            self.draw()
        U.FlatButton(parent, label(item), x, y, w, 0.036, open_picker, fill='PAPER', edge='LINE', fg='INK',
                     size=0.72, align='left', right='v', hover=-0.06)

    # ── drawing ──────────────────────────────────────────────────────────────
    def draw(self):
        if self.body is not None:
            destroy(self.body)
        self.fields = {}
        b = self.body = Entity(parent=self.win.body)
        win = self.win
        self.win.title.text = f"EDIT NPC:  {self.data['name']}"
        self.win.right.text = dict(ROLES).get(self.data.get('role'), '')
        if self.picker is not None:
            self.draw_picker(b)
            return
        # tabs
        x, y = win.left, win.top
        for i, (key, name) in enumerate(TABS):
            on = key == self.tab
            U.FlatButton(b, name, x + i * 0.19, y, 0.18, 0.045, lambda k=key: self.show_tab(k),
                         fill='TEAL' if on else 'SLATE', edge='INK', size=0.85)
        y -= 0.075
        getattr(self, 'tab_' + self.tab)(b, x, y)
        # bottom buttons
        U.FlatButton(b, 'CANCEL', win.left, win.btn_y, 0.2, U.BTN_H, self.cancel, fill='SLATE', edge='INK')
        U.FlatButton(b, 'DONE', win.x + W - 0.06 - 0.22, win.btn_y, 0.22, U.BTN_H, self.done, fill='GREEN',
                     edge='INK')

    def show_tab(self, key):
        self.read_fields()
        self.tab = key
        self.draw()

    def tab_look(self, b, x, y):
        d = self.data
        U.text(b, 'Name', x, y - 0.012, 0.85, 'MUTED')
        self.field(b, 'name', d['name'], x + 0.13, y + 0.004, 0.42, limit=24)
        y -= 0.06
        U.text(b, 'Role', x, y - 0.012, 0.85, 'MUTED')
        self.choice_row(b, x + 0.13, y + 0.002, ROLES, d.get('role'), self.set_role, w=0.105, size=0.6)
        y -= 0.06
        if d.get('role') == 'merchant':                  # what they deal in (data/merchants.py)
            from .data.merchants import MERCHANTS
            U.text(b, 'Sells', x, y - 0.012, 0.85, 'MUTED')
            self.choice_row(b, x + 0.13, y + 0.002, [(k, m['name'].upper()) for k, m in MERCHANTS.items()],
                            d.get('shop'), lambda v: self.set('shop', v), w=0.105, size=0.55)
            y -= 0.06
        else:
            U.text(b, 'The NPC on the right changes as you pick. In a game, players walk up and press E to talk.',
                   x + 0.6, y - 0.005, 0.72, 'MUTED', wordwrap=30)
        rows = (('Skin', 'skin', SKIN_COLOURS), ('Shirt', 'shirt', CLOTH_COLOURS), ('Trousers', 'pants', CLOTH_COLOURS),
                ('Hair', 'hair', HAIR_COLOURS))
        for name, key, choices in rows:
            U.text(b, name, x, y - 0.012, 0.85, 'MUTED')
            self.swatches(b, x + 0.13, y + 0.004, choices, d.get(key), lambda v, k=key: self.set(k, v, model=True))
            y -= 0.058
        U.text(b, 'Hat', x, y - 0.012, 0.85, 'MUTED')
        self.choice_row(b, x + 0.13, y + 0.002, [(h, (h or 'none').upper()) for h in HATS], d.get('hat'),
                        lambda v: self.set('hat', v, model=True), w=0.1, size=0.65)
        y -= 0.06
        U.text(b, 'Extras', x, y - 0.012, 0.85, 'MUTED')
        for i, (key, name) in enumerate((('beard', 'BEARD'), ('goggles', 'GOGGLES'), ('apron', 'APRON'))):
            on = bool(d.get(key))
            U.FlatButton(b, name, x + 0.13 + i * 0.13, y + 0.002, 0.12, 0.04,
                         lambda k=key, v=on: self.set(k, not v, model=True), fill='TEAL' if on else 'SLATE',
                         edge='INK', size=0.72)
        y -= 0.075
        if d.get('role') == 'merchant':                  # (no room for the ready-made NPCs under the Sells row)
            return
        U.text(b, 'Start over from a ready-made NPC (keeps the name):', x, y, 0.75, 'MUTED')
        y -= 0.03
        for i, (role, name) in enumerate(ROLES):
            U.FlatButton(b, f"{PRESETS[role]['name']}  ({name.lower()})", x + (i % 3) * 0.27, y - (i // 3) * 0.046,
                         0.26, 0.04, lambda r=role: self.use_preset(r), fill='SLATE', edge='INK', size=0.68)


    def tab_dialogue(self, b, x, y):
        d = self.data
        U.text(b, 'What they say. Players see the greeting first, TALK shows the lines one after another.',
               x, y, 0.75, 'MUTED')
        y -= 0.05
        U.text(b, 'Greeting', x, y - 0.012, 0.85, 'MUTED')
        self.field(b, 'greeting', d.get('greeting', ''), x + 0.15, y + 0.004, 0.87)
        y -= 0.065
        lines = list(d.get('lines') or [])
        for i in range(MAX_LINES):
            U.text(b, f'Line {i + 1}', x, y - 0.012, 0.85, 'MUTED')
            self.field(b, f'line{i}', lines[i] if i < len(lines) else '', x + 0.15, y + 0.004, 0.87)
            y -= 0.058
        y -= 0.008
        U.text(b, 'Goodbye', x, y - 0.012, 0.85, 'MUTED')
        self.field(b, 'farewell', d.get('farewell', ''), x + 0.15, y + 0.004, 0.87)

    def tab_trades(self, b, x, y):
        d = self.data
        trades = d.setdefault('trades', [])
        gives, gets = tradeable()
        if d.get('role') != 'trader':
            U.text(b, 'Only traders trade: set the role to Trader on the LOOK tab.', x, y, 0.8, 'AMBER')
            y -= 0.035
        U.text(b, 'PLAYER GIVES', x, y, 0.75, 'MUTED')
        U.text(b, 'PLAYER GETS', x + 0.45, y, 0.75, 'MUTED')
        y -= 0.035
        for i, t in enumerate(trades):
            self.item_button(b, x, y, 0.24, t['give'], 'The player gives', gives,
                             lambda v, t=t: self.set_trade(t, 'give', v))
            self.stepper(b, x + 0.25, y, t['give_n'], lambda v, t=t: self.set_trade(t, 'give_n', v),
                         step=10 if t['give'] == 'coins' else 1)
            U.text(b, '>', x + 0.425, y - 0.018, 1.0, 'INK', origin=(0, 0))
            self.item_button(b, x + 0.45, y, 0.24, t['get'], 'The player gets', gets,
                             lambda v, t=t: self.set_trade(t, 'get', v))
            self.stepper(b, x + 0.70, y, t['get_n'], lambda v, t=t: self.set_trade(t, 'get_n', v),
                         step=10 if t['get'] == 'coins' else 1)
            U.FlatButton(b, 'REMOVE', x + 0.87, y, 0.12, 0.036, lambda t=t: self.remove_trade(t), fill='RED',
                         edge='INK', size=0.68)
            y -= 0.052
        if len(trades) < MAX_TRADES:
            U.FlatButton(b, '+ ADD TRADE', x, y - 0.01, 0.22, 0.042, self.add_trade, fill='GREEN', edge='INK',
                         size=0.8)

    def tab_quest(self, b, x, y):
        d = self.data
        q = d.get('quest')
        if d.get('role') != 'quest':
            U.text(b, 'Only quest givers hand out jobs: set the role to Quest giver on the LOOK tab.', x, y, 0.8,
                   'AMBER')
            y -= 0.035
        if not q:
            U.FlatButton(b, '+ GIVE THEM A JOB', x, y - 0.01, 0.3, 0.045, self.add_quest, fill='GREEN', edge='INK',
                         size=0.85)
            return
        U.text(b, 'Job', x, y - 0.012, 0.85, 'MUTED')
        self.choice_row(b, x + 0.15, y + 0.002, QUEST_KINDS, q['kind'], lambda v: self.set_quest('kind', v), w=0.18)
        U.FlatButton(b, 'NO JOB', x + 0.88, y + 0.002, 0.14, 0.04, self.remove_quest, fill='RED', edge='INK', size=0.7)
        y -= 0.058
        U.text(b, 'How many', x, y - 0.012, 0.85, 'MUTED')
        self.stepper(b, x + 0.15, y, q['n'], lambda v: self.set_quest('n', v))
        if q['kind'] == 'bring':
            U.text(b, 'of', x + 0.32, y - 0.012, 0.85, 'MUTED')
            items = tradeable()[0][1:]
            self.item_button(b, x + 0.36, y, 0.28, q['item'], 'Bring what?', items,
                             lambda v: self.set_quest('item', v))
        elif q['kind'] == 'hunt':
            self.choice_row(b, x + 0.32, y, [(t, t.upper()) for t in HUNT_TARGETS], q.get('animal', 'any'),
                            lambda v: self.set_quest('animal', v), w=0.12, h=0.036, size=0.7)
        y -= 0.058
        U.text(b, 'Reward', x, y - 0.012, 0.85, 'MUTED')
        self.stepper(b, x + 0.15, y, q.get('reward_coins', 0), lambda v: self.set_quest('reward_coins', v), step=50,
                     lo=0, hi=99999)
        U.text(b, 'coins  +', x + 0.32, y - 0.012, 0.85, 'MUTED')
        self.stepper(b, x + 0.42, y, q.get('reward_n', 0), lambda v: self.set_quest('reward_n', v), lo=0)
        self.item_button(b, x + 0.6, y, 0.28, q.get('reward_item') or 'none', 'Reward item', tradeable()[1][1:],
                         lambda v: self.set_quest('reward_item', v))
        rep = bool(q.get('repeat'))
        U.FlatButton(b, 'REPEATS', x + 0.89, y, 0.13, 0.036, lambda: self.set_quest('repeat', not rep),
                     fill='TEAL' if rep else 'SLATE', edge='INK', size=0.7)
        y -= 0.07
        for key, name in (('offer', 'Offer'), ('progress', 'Not done'), ('done', 'Finished')):
            U.text(b, name, x, y - 0.012, 0.85, 'MUTED')
            self.field(b, 'q_' + key, q.get(key, ''), x + 0.15, y + 0.004, 0.87)
            y -= 0.058

    def draw_picker(self, b):
        title, choices, on_pick = self.picker
        x, y = self.win.left, self.win.top
        U.text(b, title, x, y, 1.1, 'INK')
        y -= 0.05
        cols, w, h = 5, 0.2, 0.036
        for i, item in enumerate(choices[:100]):
            cx, cy = x + (i % cols) * (w + 0.006), y - (i // cols) * (h + 0.004)
            fill = ITEMS[item]['colour'] if item in ITEMS else '#e8c040'

            def pick(v=item):
                self.picker = None
                on_pick(v)
            U.FlatButton(b, label(item), cx, cy, w, h, pick, fill='PAPER', edge=fill, fg='INK', size=0.6,
                         align='left', hover=-0.06)
        U.FlatButton(b, 'BACK', self.win.left, self.win.btn_y, 0.2, U.BTN_H, self.close_picker, fill='SLATE',
                     edge='INK')

    def close_picker(self):
        self.picker = None
        self.draw()

    # ── changes ──────────────────────────────────────────────────────────────
    def set_role(self, role):
        self.read_fields()
        self.data['role'] = role
        if role == 'trader' and not self.data.get('trades'):
            self.data['trades'] = copy.deepcopy(PRESETS['trader']['trades'][:2])
        if role == 'quest' and not self.data.get('quest'):
            self.data['quest'] = copy.deepcopy(DEFAULT_QUEST)
        self.editor.refresh_npc_model(self.prop)
        self.draw()

    def use_preset(self, role):
        self.read_fields()
        name, uid = self.data['name'], self.data['uid']
        self.data.clear()
        self.data.update(copy.deepcopy(PRESETS[role]))
        if self.data.get('quest'):
            q = copy.deepcopy(DEFAULT_QUEST)
            q.update(self.data['quest'])
            self.data['quest'] = q
        self.data['name'], self.data['uid'] = name, uid
        self.editor.refresh_npc_model(self.prop)
        self.draw()

    def set_trade(self, t, key, value):
        self.read_fields()
        t[key] = value
        self.draw()

    def add_trade(self):
        self.read_fields()
        self.data.setdefault('trades', []).append(dict(give='raw_meat', give_n=1, get='coins', get_n=20))
        self.draw()

    def remove_trade(self, t):
        self.read_fields()
        self.data['trades'].remove(t)
        self.draw()

    def add_quest(self):
        self.read_fields()
        self.data['quest'] = copy.deepcopy(DEFAULT_QUEST)
        self.draw()

    def remove_quest(self):
        self.read_fields()
        self.data['quest'] = None
        self.draw()

    def set_quest(self, key, value):
        self.read_fields()
        if key == 'reward_item' and value == 'none':
            value = None
        q = self.data['quest']
        auto = auto_offer(q)
        q[key] = value
        if q.get('offer') in (auto, DEFAULT_QUEST['offer']):     # they kept the made-up offer: keep it matching
            q['offer'] = auto_offer(q)
        if key == 'reward_item' and value and not self.data['quest'].get('reward_n'):
            self.data['quest']['reward_n'] = 1
        self.draw()

    # ── closing ──────────────────────────────────────────────────────────────
    def done(self):
        self.read_fields()
        self.editor.refresh_npc_model(self.prop)
        self.editor.close_npc_panel()
        self.editor.toast(f"Saved {self.data['name']}. Save the map to keep it.")

    def cancel(self):
        self.data.clear()
        self.data.update(self.before)
        self.editor.refresh_npc_model(self.prop)
        self.editor.close_npc_panel()

    def destroy(self):
        destroy(self.root)

