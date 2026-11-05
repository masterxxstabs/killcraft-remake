"""The map editor's settings panel for markers that have settings (zones, zombie graves...).

Which settings a marker has comes from its asset's `fields` (see data/zones.py), so any
new marker with fields gets this panel for free. Numbers have - / + buttons (Shift+click
for 10 steps), choices are buttons (or PREV / NEXT when there are many), text is a box.
"""
import copy
from ursina import Entity, InputField, camera, held_keys
from . import ui as U
from .data.assets import ASSETS
from .data.zones import ZONE_COLOURS, choices
from .render import destroy

W, H, TOP = 0.8, 0.7, 0.33


class PropPanel:
    def __init__(self, editor, prop):
        self.editor, self.prop = editor, prop
        self.a = ASSETS[prop['id']]
        self.data = prop['data']
        self.before = copy.deepcopy(self.data)
        self.fields = {}
        self.root = Entity(parent=camera.ui, z=-0.8)
        Entity(parent=self.root, model='quad', color=U.C('INK', 0.45), scale=(4, 1), z=0.05, collider='box')
        self.win = U.Window(self.root, self.a['name'].upper(), w=W, h=H, top=TOP)
        self.win.root.x = -0.25                       # (so you can see the zone's ring on the right)
        self.body = None
        self.draw()

    def typing(self):
        return any(f.active for f in self.fields.values())

    def read_fields(self):
        for key, f in self.fields.items():
            self.data[key] = f.text.strip()[:40]

    def set(self, key, value):
        self.read_fields()
        self.data[key] = value
        f = next((f for f in self.a['fields'] if f['key'] == key), None)
        if f and key in ('min_level', 'max_level', 'group_min', 'group_max'):     # keep ranges the right way round
            lo_key, hi_key = ('min_level', 'max_level') if 'level' in key else ('group_min', 'group_max')
            if self.data[lo_key] > self.data[hi_key]:
                other = hi_key if key == lo_key else lo_key
                self.data[other] = value
        self.editor.refresh_prop_visual(self.prop)
        self.draw()

    def draw(self):
        if self.body is not None:
            destroy(self.body)
        self.fields = {}
        b = self.body = Entity(parent=self.win.body)
        win = self.win
        colour = ZONE_COLOURS.get(self.a.get('zone'), 'TEAL')
        U.box(b, win.x + 0.03, win.y - 0.095, W - 0.06, 0.006, colour, z=-0.01, round=False)
        x, y = win.left, win.top + 0.01
        for f in self.a['fields']:
            key, val = f['key'], self.data.get(f['key'], f['default'])
            U.text(b, f['label'], x, y - 0.012, 0.85, 'INK')
            cx = x + 0.27
            if f['kind'] == 'int':
                def bump(d, f=f, key=key):
                    step = f['step'] * (10 if held_keys['shift'] else 1)
                    self.set(key, max(f['lo'], min(f['hi'], self.data.get(key, f['default']) + d * step)))
                U.FlatButton(b, '-', cx, y, 0.04, 0.036, lambda d=-1, bump=bump: bump(d), fill='SLATE', edge='INK', size=0.9)
                U.box(b, cx + 0.044, y, 0.1, 0.036, 'NAVY', z=-0.01)
                U.text(b, str(val), cx + 0.094, y - 0.018, 0.9, 'PAPER', origin=(0, 0), z=-0.02)
                U.FlatButton(b, '+', cx + 0.148, y, 0.04, 0.036, lambda d=1, bump=bump: bump(d), fill='SLATE', edge='INK',
                             size=0.9)
                U.text(b, f"{f['lo']} - {f['hi']}", cx + 0.2, y - 0.012, 0.65, 'MUTED')
            elif f['kind'] == 'choice':
                opts = choices(f)
                names = dict(opts)
                if len(opts) <= 4:
                    for i, (v, name) in enumerate(opts):
                        on = v == val
                        U.FlatButton(b, name, cx + i * 0.105, y, 0.1, 0.036, lambda v=v, key=key: self.set(key, v),
                                     fill='TEAL' if on else 'SLATE', edge='INK', size=0.72)
                else:                                     # many options: step through them
                    keys = [v for v, _ in opts]
                    i = keys.index(val) if val in keys else 0
                    U.FlatButton(b, 'PREV', cx, y, 0.07, 0.036, lambda i=i, key=key, keys=keys: self.set(key, keys[(i - 1) % len(keys)]),
                                 fill='SLATE', edge='INK', size=0.7)
                    U.box(b, cx + 0.074, y, 0.16, 0.036, 'NAVY', z=-0.01)
                    U.text(b, names.get(val, str(val)), cx + 0.154, y - 0.018, 0.8, 'PAPER', origin=(0, 0), z=-0.02)
                    U.FlatButton(b, 'NEXT', cx + 0.238, y, 0.07, 0.036, lambda i=i, key=key, keys=keys: self.set(key, keys[(i + 1) % len(keys)]),
                                 fill='SLATE', edge='INK', size=0.7)
            else:
                fld = InputField(default_value=str(val), text=str(val), parent=b, position=(cx + 0.15, y - 0.018, -0.02),
                                 scale=(0.3, 0.036), character_limit=f.get('limit', 24), color=U.C('PAPER'))
                fld.text_color = U.C('INK')
                fld.text_field.scale *= 0.7
                fld.text_field.x, fld.text_field.y = -0.47, 0.2
                self.fields[key] = fld
            y -= 0.05
            if f.get('help'):
                U.text(b, f['help'], x + 0.02, y + 0.008, 0.62, 'MUTED', wordwrap=70)
                y -= 0.03
        U.text(b, 'Shift+click - / + for bigger steps.', x, win.btn_y + 0.035, 0.62, 'MUTED')
        U.FlatButton(b, 'CANCEL', win.left, win.btn_y, 0.18, U.BTN_H, self.cancel, fill='SLATE', edge='INK')
        U.FlatButton(b, 'DONE', win.x + W - 0.06 - 0.2, win.btn_y, 0.2, U.BTN_H, self.done, fill='GREEN', edge='INK')

    def done(self):
        self.read_fields()
        self.editor.refresh_prop_visual(self.prop)
        self.editor.close_npc_panel()
        self.editor.toast(f"Saved the {self.a['name'].lower()}. Save the map to keep it.")

    def cancel(self):
        self.data.clear()
        self.data.update(self.before)
        self.editor.refresh_prop_visual(self.prop)
        self.editor.close_npc_panel()

    def destroy(self):
        destroy(self.root)
