"""HUD, main menu, pause screen, shop and game-over screen.

Flat design: off-white panels with thick dark outlines, tabs along the top, a
header bar, label / value rows, teal progress bars and slate-blue buttons.
Change the colours in the PALETTE section to restyle everything at once.
"""
import math
import time as pytime
from ursina import Button, Entity, Mesh, Text, Texture, Vec2, Vec3, camera, color as ucolor, held_keys, mouse, window
from . import maps
from .data.attachments import ATTACHMENTS, SLOT_NAMES
from .data.gun_models import MODELS as GUN_MODELS
from .gunsmith import CAMOS
from .data.abilities import ABILITIES
from .data.upgrades import UPGRADES
from .data.weapons import CATEGORIES, WEAPONS
from .data.resources import RESOURCES
from .data.atmosphere import ATMOSPHERES
from .render import col, destroy, hex_rgb
from .data.themes import HUD_PARTS
from .textures import icon, scope_texture, vignette_texture

# ── PALETTE ──────────────────────────────────────────────────────────────────
PAPER = '#f5f4f2'       # panel background
INK = '#12121c'         # outlines, active tabs, main text
SLATE = '#404968'       # buttons
SLATE_EDGE = '#1e2537'  # button outlines
NAVY = '#1f2636'        # empty part of bars, small square buttons
TEAL = '#1197b0'        # bar fill, highlights
LINE = '#414a67'        # divider lines
MUTED = '#6b7189'       # secondary text
RED = '#d64541'
AMBER = '#d9912b'
GREEN = '#2e9e6a'
EDGE = 0.008            # thickness of the outlines (set by the style)
STYLE = dict(radius=0.0, segments=0, pill=False, edge=0.008, glass=1.0, font='OpenSans-Regular.ttf')

# window layout (screen height = 1)
WIN_W, WIN_H, WIN_TOP = 1.36, 0.78, 0.33
HEADER_H = 0.095
BTN_H = 0.065


PALETTE_NAMES = ('PAPER', 'INK', 'SLATE', 'SLATE_EDGE', 'NAVY', 'TEAL', 'LINE', 'MUTED', 'RED', 'AMBER', 'GREEN')


def C(c, a=1.0):
    """A colour from '#rrggbb', a palette name like 'PAPER' (looked up now, so themes apply), or a Color."""
    if isinstance(c, str) and c in PALETTE_NAMES:
        c = globals()[c]
    return col(c, a) if isinstance(c, str) else c


# ── building blocks ──────────────────────────────────────────────────────────
#  Everything is placed by its TOP-LEFT corner, like in a drawing program.

def contrast(c):
    """Near-white or near-black: whichever reads better on colour c."""
    if isinstance(c, str) and c in PALETTE_NAMES:
        c = globals()[c]
    r, g, b = hex_rgb(c) if isinstance(c, str) else (c[0], c[1], c[2])
    return '#12121c' if 0.299 * r + 0.587 * g + 0.114 * b > 0.5 else '#f5f4f2'


def _lum(c):
    if isinstance(c, str) and c in PALETTE_NAMES:
        c = globals()[c]
    r, g, b = hex_rgb(c) if isinstance(c, str) else (c[0], c[1], c[2])
    return 0.299 * r + 0.587 * g + 0.114 * b


def readable(fg, bg):
    """Is text in colour fg easy to read on bg?"""
    return abs(_lum(fg) - _lum(bg)) > 0.32


_corners = {}


def round_rect(w, h, r, segments):
    """A w x h rectangle mesh (-0.5..0.5 like a quad, scaled to w, h) with corners of radius r.
    segments = 1 cuts the corners off straight; more makes them round."""
    r = max(0.0, min(r, w / 2 - 1e-4, h / 2 - 1e-4))
    rx, ry = r / w, r / h
    key = (round(rx, 4), round(ry, 4), segments)
    verts = _corners.get(key)
    if verts is None:
        pts = []
        for cx, cy, a0 in ((0.5 - rx, 0.5 - ry, 0), (-0.5 + rx, 0.5 - ry, 90), (-0.5 + rx, -0.5 + ry, 180),
                           (0.5 - rx, -0.5 + ry, 270)):
            for k in range(segments + 1):
                a = math.radians(a0 + 90 * k / segments)
                pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
        verts = _corners[key] = pts
    vs = [Vec3(0, 0, 0)] + [Vec3(px, py, 0) for px, py in verts]
    n = len(verts)
    tris = []
    for i in range(n):
        tris += [0, 1 + i, 1 + (i + 1) % n]          # counter-clockwise, like Ursina's quad (faces the camera)
    return Mesh(vertices=vs, triangles=tris, uvs=[Vec2(v.x + 0.5, v.y + 0.5) for v in vs])


def box(parent, x, y, w, h, color, z=0.0, round=True, radius=None, **kw):
    """A filled rectangle, top-left corner at (x, y). Corners follow the style (round=False keeps it square)."""
    r = STYLE['radius'] if radius is None else radius
    model = 'quad'
    if round and r > 0 and STYLE['segments'] > 0 and min(w, h) > 0.006:
        model = round_rect(w, h, r, STYLE['segments'])
    return Entity(parent=parent, model=model, color=C(color), origin=(-0.5, 0.5),
                  position=(x, y, z), scale=(w, h), **kw)


def frame(parent, x, y, w, h, fill='PAPER', edge='INK', t=None, z=0.0):
    """A filled box with an outline (thickness and corners from the style). Returns the inner fill."""
    t = EDGE if t is None else t
    if t > 0 and STYLE['glass'] >= 1:
        box(parent, x, y, w, h, edge, z=z + 0.002)
    glass = STYLE['glass'] if fill == 'PAPER' or fill == PAPER else 1.0
    return box(parent, x + t, y - t, w - 2 * t, h - 2 * t, C(fill, glass), z=z + 0.001,
               radius=max(0.0, STYLE['radius'] - t * 0.6))


def text(parent, s, x, y, size=1.0, color='INK', origin=(-0.5, 0.5), z=-0.01, **kw):
    if 'wordwrap' in kw and not s:
        s = ' '        # Ursina can't word-wrap an empty string
    if 'Mono' in STYLE.get('font', ''):
        size *= 0.86   # the typewriter font is wider: keep text inside its boxes
    return Text(s, parent=parent, position=(x, y, z), scale=size, color=C(color), origin=origin, **kw)


def glyph(parent, name, x, y, size, color='PAPER', z=-0.012):
    """An icon centred on (x, y)."""
    return Entity(parent=parent, model='quad', texture=icon(name), color=C(color), position=(x, y, z), scale=size)


def hline(parent, x, y, w, color='LINE', t=0.004):
    return box(parent, x, y, w, t, color)


def clamp01(v):
    return max(0.0, min(1.0, v))


class FlatButton:
    """A solid button with an outline. (x, y) is the top-left corner."""

    def __init__(self, parent, label, x, y, w, h, on_click, fill='SLATE', edge='SLATE_EDGE', fg='AUTO',
                 size=1.15, icon_name=None, align='center', right='', z=-0.02, hover=0.12):
        t = EDGE * 0.8
        if fg == 'AUTO' or not readable(fg, fill):       # text that would vanish on this fill: use black or white
            fg = contrast(fill)
        r = h / 2 if STYLE['pill'] else min(STYLE['radius'], h * 0.35)
        self.parts = [box(parent, x, y, w, h, edge, z=z + 0.002, radius=r)] if t > 0 else []
        f = C(fill)
        face = 'quad'
        if r > 0 and STYLE['segments'] > 0:
            face = round_rect(w - 2 * t, h - 2 * t, max(0.0, r - t * 0.6), STYLE['segments'])
        self.button = Button(parent=parent, model=face, text='', color=f, position=(x + w / 2, y - h / 2, z),
                             scale=(w - 2 * t, h - 2 * t), highlight_color=f.tint(hover), pressed_color=f.tint(-0.1),
                             on_click=on_click)
        self.parts.append(self.button)
        cy = y - h / 2
        if icon_name and not label:
            self.parts.append(glyph(parent, icon_name, x + w / 2, cy, h * 0.55, fg, z=z - 0.01))
        elif icon_name:
            self.parts.append(glyph(parent, icon_name, x + h * 0.55, cy, h * 0.45, fg, z=z - 0.01))
            self.parts.append(text(parent, label, x + h * 0.95, cy, size, fg, origin=(-0.5, 0), z=z - 0.01))
        elif align == 'left':
            self.parts.append(text(parent, label, x + 0.02, cy, size, fg, origin=(-0.5, 0), z=z - 0.01))
        else:
            self.parts.append(text(parent, label, x + w / 2, cy, size, fg, origin=(0, 0), z=z - 0.01))
        if right:
            self.parts.append(text(parent, right, x + w - 0.02, cy, size * 0.9, fg, origin=(0.5, 0), z=z - 0.01))

    def set_enabled(self, on):
        for p in self.parts:
            p.enabled = on


def tab_strip(parent, x, y, items, active, on_pick, w_each=0.2, h=0.05):
    """The row of tabs sitting on top of a window (active tab is dark)."""
    n = len(items)
    box(parent, x, y, n * w_each + (n + 1) * EDGE, h + 2 * EDGE, INK, z=0.004)
    for i, (key, label) in enumerate(items):
        on = key == active
        FlatButton(parent, label, x + EDGE + i * (w_each + EDGE), y - EDGE, w_each, h, lambda k=key: on_pick(k),
                   fill=INK if on else PAPER, edge=INK, fg=PAPER if on else INK, size=1.05,
                   hover=0.15 if on else -0.06, z=-0.005)


def bar(parent, x, y, w, h, frac, fill='TEAL', back='NAVY'):
    box(parent, x, y, w, h, back, z=0.001)
    return box(parent, x, y, w * clamp01(frac), h, fill)


def stat_row(parent, x, y, w, label, frac, value, fill='TEAL'):
    """Label on top, a bar underneath and the value to the right (the mock-up's right column)."""
    text(parent, label, x, y, 0.95, INK)
    bar(parent, x, y - 0.032, w, 0.02, frac, fill)
    text(parent, value, x + w + 0.018, y - 0.042, 1.05, INK, origin=(-0.5, 0))


def pair(parent, x, y, label, value, gap=0.3, size=1.1):
    """Label / value row (the mock-up's left column)."""
    text(parent, label, x, y, size, INK)
    text(parent, str(value), x + gap, y + 0.003, size * 1.15, INK)


class FlatSlider(Entity):
    """A teal bar you can click or drag to set a value."""

    def __init__(self, parent, x, y, w, label, lo, hi, value, fmt, on_change):
        super().__init__(parent=parent)
        self.x0, self.w, self.lo, self.hi, self.fmt, self.on_change = x, w, lo, hi, fmt, on_change
        self.value = value
        self.dragging = False
        text(self, label, x, y, 0.95, INK)
        h = 0.022
        self.track = Button(parent=self, model='quad', text='', color=C(NAVY), highlight_color=C(NAVY).tint(0.1),
                            pressed_color=C(NAVY), position=(x + w / 2, y - 0.032 - h / 2, -0.005), scale=(w, h * 1.8))
        self.fill = box(self, x, y - 0.032, w, h, TEAL, z=-0.01)
        self.knob = box(self, x, y - 0.026, 0.008, h + 0.012, INK, z=-0.012)
        self.label = text(self, '', x + w + 0.018, y - 0.043, 1.05, INK, origin=(-0.5, 0))
        self.refresh()

    def refresh(self):
        f = clamp01((self.value - self.lo) / (self.hi - self.lo))
        self.fill.scale_x = max(0.0001, self.w * f)
        self.knob.x = self.x0 + self.w * f - 0.004
        self.label.text = self.fmt(self.value)

    def update(self):
        if self.track.hovered and held_keys['left mouse']:
            self.dragging = True
        if not held_keys['left mouse']:
            self.dragging = False
        if self.dragging:
            f = clamp01((mouse.x - self.x0) / self.w)
            v = round(self.lo + (self.hi - self.lo) * f)
            if v != self.value:
                self.value = v
                self.refresh()
                self.on_change(v)


class Window:
    """The framed panel from the mock-up: optional tabs on top, a header with a
    big title on the left and small text on the right, then a body."""

    def __init__(self, parent, title='', right='', w=WIN_W, h=WIN_H, top=WIN_TOP):
        self.x, self.y, self.w, self.h = -w / 2, top, w, h
        self.root = Entity(parent=parent)
        solid = STYLE['glass'] >= 1 and EDGE > 0
        if solid:                                        # (see-through styles skip the outline)
            box(self.root, self.x, self.y, w, h, INK, z=0.01)
        box(self.root, self.x + EDGE * 1.5, self.y - EDGE * 1.5, w - EDGE * 3, h - EDGE * 3, C(PAPER, STYLE['glass']),
            z=0.009, radius=max(0.0, STYLE['radius'] * 1.6 - EDGE))
        box(self.root, self.x + 0.03, self.y - HEADER_H, w - 0.06, max(0.003, EDGE * 1.5), INK if solid else LINE,
            z=0.008)
        self.title = text(self.root, title, self.x + 0.04, self.y - 0.047, 2.6, INK, origin=(-0.5, 0))
        self.right = text(self.root, right, self.x + w - 0.045, self.y - 0.047, 1.5, INK, origin=(0.5, 0))
        self.tabs = Entity(parent=self.root)
        self.body = Entity(parent=self.root)
        # handy layout numbers
        self.top = self.y - HEADER_H - 0.04            # first line of the body
        self.left = self.x + 0.06                      # left column
        self.right_col = self.x + w * 0.53             # right column
        self.btn_y = self.y - h + 0.035 + BTN_H        # bottom row of buttons

    def set_tabs(self, items, active, on_pick):
        for c in list(self.tabs.children):
            destroy(c)
        tab_strip(self.tabs, self.x + self.w * 0.075, self.y + 0.05 + 2 * EDGE, items, active, on_pick)

    def clear(self):
        for c in list(self.body.children):
            destroy(c)

    def bottom_left(self, label, on_click, icon_name, on_icon):
        FlatButton(self.body, label, self.left, self.btn_y, 0.26, BTN_H, on_click)
        FlatButton(self.body, '', self.left + 0.272, self.btn_y, BTN_H * 1.2, BTN_H, on_icon, fill=NAVY,
                   edge=LINE, icon_name=icon_name)

    def bottom_right(self, label, on_click, icon_name=None, on_icon=None, fill='SLATE', w=0.26):
        x = self.x + self.w - 0.06 - w
        FlatButton(self.body, label, x, self.btn_y, w, BTN_H, on_click, fill=fill)
        if icon_name:
            FlatButton(self.body, '', x - 0.012 - BTN_H * 1.2, self.btn_y, BTN_H * 1.2, BTN_H, on_icon, fill=NAVY,
                       edge=LINE, icon_name=icon_name)


def backdrop(parent, alpha):
    return box(parent, -2, 0.5, 4, 1, C(INK, alpha), z=0.05)


def milestones(save):
    """Long-term goals shown as progress bars."""
    return [
        ('Reach wave 10', save['best_wave'] / 10, f"{min(save['best_wave'], 10)}/10"),
        ('Reach wave 25', save['best_wave'] / 25, f"{min(save['best_wave'], 25)}/25"),
        ('Score 10,000 in one game', save['best_score'] / 10000, f"{round(clamp01(save['best_score'] / 10000) * 100)}%"),
        ('Defeat 1,000 zombies', save['total_kills'] / 1000, f"{round(clamp01(save['total_kills'] / 1000) * 100)}%"),
        ('Defeat 10,000 zombies', save['total_kills'] / 10000, f"{round(clamp01(save['total_kills'] / 10000) * 100)}%"),
        ('Play 25 games', save['games'] / 25, f"{min(save['games'], 25)}/25"),
        ('???' if not save.get('lance') else 'Claim the Hollow Lance', 1 if save.get('lance') else 0,
         'found!' if save.get('lance') else '?'),
    ]


# ─────────────────────────────────────────────────────────────────────────────
def set_style_temp(st):
    """Draw the next thing in another style (style picker buttons show their own shape)."""
    import sys
    me = sys.modules[__name__]
    me.STYLE = dict(st)
    me.EDGE = st['edge']


def apply_style(sid):
    """Switch the UI's shape: corners, outlines, see-through panels and font."""
    import sys
    from .data.themes import STYLES
    st = STYLES.get(sid) or STYLES['flat']
    me = sys.modules[__name__]
    me.STYLE = dict(st)
    for mod in (me, sys.modules.get('blockhold.editor')):
        if mod is not None and hasattr(mod, 'EDGE'):
            mod.EDGE = st['edge']
    Text.default_font = st['font']


def apply_theme(tid):
    """Switch the palette (every screen reads these when it is built)."""
    import sys
    from .data.themes import THEMES
    pal = THEMES.get(tid) or THEMES['classic']
    for mod in (sys.modules[__name__], sys.modules.get('blockhold.editor')):
        if mod is None:
            continue
        for name in PALETTE_NAMES:
            if hasattr(mod, name):
                setattr(mod, name, pal[name])


class UI:
    def __init__(self, game):
        self.game = game
        self.banner_t = 0
        self.hit_t = 0
        self.hurt_t = 0
        self.feed = []
        self._cache = {}
        self.menu_tab = 'play'
        self.shop_tab = 'weapons'
        self.shop_view = 'stats'
        self.shop_sel = None
        self._update_status = None
        self.hud_editor = None
        self.build_hud()
        self.build_menu()
        self.build_pause()
        self.build_shop()
        self.build_craft()
        self.build_dead()
        self.build_bag()

    def build_bag(self):
        from .bag_ui import BagScreen
        from .npc_ui import TalkScreen
        self.bag = BagScreen(self)
        self.talk = TalkScreen(self)

    def inventory_changed(self):
        """The local player's backpack changed: redraw whatever shows it."""
        if getattr(self, 'bag', None) is not None and self.bag.active:
            self.bag.refresh()
        if getattr(self, 'craft', None) is not None and self.craft.enabled:
            self.refresh_craft()

    def rebuild_hud(self):
        """Build the HUD again (new colours / layout), keeping whether it was showing."""
        on = self.hud.enabled
        effects = getattr(self.game, 'effects', None)
        keep = [n['t'] for n in effects.numbers] if effects else []     # damage numbers live on the HUD
        for t in keep:
            t.parent = camera.ui
        destroy(self.hud)
        self._cache = {}
        self.build_hud()
        for t in keep:
            t.parent = self.hud
        self.hud.enabled = on
        if getattr(self.game, 'weapons', None) is not None and self.game.weapons.held:
            self.update_weapon()

    def rebuild(self):
        """Build every screen again with the current theme."""
        shown = {n: getattr(self, n).enabled for n in ('menu', 'pause', 'shop', 'craft', 'dead')}
        for n in ('menu', 'pause', 'shop', 'craft', 'dead'):
            destroy(getattr(self, n))
        self.bag.close()
        destroy(self.bag.root)
        self.talk.close()
        destroy(self.talk.root)
        self.rebuild_hud()
        self.build_menu()
        self.build_pause()
        self.build_shop()
        self.build_craft()
        self.build_dead()
        self.build_bag()
        for n, on in shown.items():
            getattr(self, n).enabled = on
        if shown['menu']:
            self.refresh_menu()
        if shown['pause']:
            self.show_pause()

    def set_text(self, t, value):
        """Only rebuild text when it changes (it's slow-ish)."""
        if self._cache.get(id(t)) != value:
            self._cache[id(t)] = value
            t.text = value

    # ── HUD ──────────────────────────────────────────────────────────────────
    def hud_colours(self):
        """The HUD's colours: the theme's, unless changed in the HUD editor."""
        hud = self.game.hud_settings
        panel = hud.get('panel') or INK
        return dict(panel=panel, fg=contrast(panel), op=hud.get('opacity', 1.0),
                    accent=hud.get('accent') or TEAL, health=hud.get('health') or RED,
                    cross=hud.get('crosshair') or PAPER)

    def build_hud(self):
        a = window.aspect_ratio
        L, R, T, B = -a / 2, a / 2, 0.5, -0.5
        k = self.hud_colours()
        P, FG, AC = C(k['panel'], k['op']), k['fg'], k['accent']
        h = self.hud = Entity(parent=camera.ui, enabled=False)
        # every movable part of the HUD hangs off its own anchor (moved / hidden as one)
        self.parts = {key: Entity(parent=h) for key, _ in HUD_PARTS}
        self.part_rects = {
            'crosshair': (-0.04, 0.04, 0.08, 0.08), 'wave': (L + 0.03, T - 0.03, 0.42, 0.095),
            'quest': (L + 0.03, T - 0.135, 0.412, 0.042), 'money': (R - 0.33, T - 0.03, 0.3, 0.095),
            'feed': (R - 0.33, T - 0.135, 0.3, 0.1), 'health': (L + 0.03, B + 0.1, 0.46, 0.07),
            'powers': (L + 0.03, B + 0.152 + 3 * 0.047, 0.3, 0.18), 'ability': (-0.07, B + 0.175, 0.14, 0.145),
            'weapon': (R - 0.33, B + 0.105, 0.3, 0.075),
            'hint': (-0.27, B + 0.205, 0.54, 0.045), 'banner': (-0.46, 0.27, 0.92, 0.13),
            'boss': (-0.36, T - 0.14, 0.72, 0.075)}
        el = self.parts
        self.scope = Entity(parent=h, enabled=False)
        Entity(parent=self.scope, model='quad', texture=scope_texture(), scale=(1, 1), z=0.9)
        box(self.scope, -0.499 - a, 0.5, a, 1, '#000000', z=0.9)
        box(self.scope, 0.499, 0.5, a, 1, '#000000', z=0.9)
        self.vignette = Entity(parent=h, model='quad', texture=vignette_texture(), scale=(a, 1), z=1, color=ucolor.Color(1, 1, 1, 0))
        self.adrenaline = Entity(parent=h, model='quad', texture=vignette_texture((255, 60, 110)), scale=(a, 1), z=1,
                                 color=ucolor.Color(1, 1, 1, 0))

        # crosshair with an outline in the opposite shade
        cross = el['crosshair']
        for sx, sy in ((0.026, 0.0065), (0.0065, 0.026)):
            box(cross, -sx / 2, sy / 2, sx, sy, contrast(k['cross']), z=0.002)
        for sx, sy in ((0.022, 0.0028), (0.0028, 0.022)):
            box(cross, -sx / 2, sy / 2, sx, sy, k['cross'])
        self.hit = Entity(parent=cross, enabled=False)
        for r in (45, -45):
            Entity(parent=self.hit, model='quad', color=C(k['cross']), scale=(0.042, 0.004), rotation_z=r)
        self.reload_back = box(cross, -0.04, -0.04, 0.08, 0.008, P, z=0.001)
        self.reload_fill = box(cross, -0.04, -0.04, 0.08, 0.008, AC, round=False)

        # top left: wave
        w_ = el['wave']
        box(w_, L + 0.03, T - 0.03, 0.12, 0.095, P, z=0.003)
        text(w_, 'WAVE', L + 0.09, T - 0.047, 0.85, FG, origin=(0, 0))
        self.wave = text(w_, '0', L + 0.09, T - 0.088, 2.6, FG, origin=(0, 0))
        frame(w_, L + 0.15 - EDGE, T - 0.03, 0.3, 0.095, PAPER, INK)
        self.remaining = text(w_, '', L + 0.17, T - 0.0775, 1.15, INK, origin=(-0.5, 0))
        self.quest_box = Entity(parent=el['quest'], enabled=False)
        box(self.quest_box, L + 0.03, T - 0.135, 0.412, 0.042, P, z=0.003)
        glyph(self.quest_box, 'skull', L + 0.052, T - 0.156, 0.026, '#d6a3ff')
        self.quest_text = text(self.quest_box, '', L + 0.075, T - 0.156, 0.9, '#d6a3ff', origin=(-0.5, 0))

        # top right: coins, score, kill feed
        m = el['money']
        frame(m, R - 0.33, T - 0.03, 0.3, 0.095, PAPER, INK)
        glyph(m, 'coin', R - 0.29, T - 0.0775, 0.045, AMBER)
        self.coins = text(m, '', R - 0.05, T - 0.066, 2.0, INK, origin=(0.5, 0))
        self.score = text(m, '', R - 0.05, T - 0.103, 0.85, MUTED, origin=(0.5, 0))
        self.feed_box = box(el['feed'], R - 0.33, T - 0.135, 0.3, 0.1, P, z=0.003)
        self.feed_right = R - 0.03
        self.feed_text = text(el['feed'], '', R - 0.045, T - 0.145, 0.85, FG, origin=(0.5, 0.5))

        # banner (wave messages)
        self.banner_root = Entity(parent=el['banner'], enabled=False)
        bw, bh, by = 0.92, 0.13, 0.27
        frame(self.banner_root, -bw / 2, by, bw, bh, PAPER, INK)
        self.banner_accent = box(self.banner_root, -bw / 2, by, bw, 0.016, AC, z=-0.001)
        self.banner_text = text(self.banner_root, '', 0, by - 0.058, 2.6, INK, origin=(0, 0))
        self.banner_sub = text(self.banner_root, '', 0, by - 0.101, 1.0, MUTED, origin=(0, 0))

        # boss health
        self.boss = Entity(parent=el['boss'], enabled=False)
        box(self.boss, -0.36, T - 0.14, 0.72, 0.075, P, z=0.003)
        self.boss_name = text(self.boss, '', 0, T - 0.158, 1.0, FG, origin=(0, 0))
        box(self.boss, -0.345, T - 0.178, 0.69, 0.024, NAVY, z=0.001)
        self.boss_fill = box(self.boss, -0.345, T - 0.178, 0.69, 0.024, RED, round=False)

        # interaction prompt (revive etc.)
        self.prompt = Entity(parent=h, enabled=False)
        self.prompt_box = box(self.prompt, -0.2, -0.13, 0.4, 0.06, P, z=0.003)
        self.prompt_text = text(self.prompt, '', 0, -0.152, 1.0, FG, origin=(0, 0))
        self.prompt_bar = box(self.prompt, -0.19, -0.176, 0.38, 0.008, AC)

        # between-wave hint
        self.hint = Entity(parent=el['hint'])
        box(self.hint, -0.27, B + 0.205, 0.54, 0.045, P, z=0.003)
        text(self.hint, 'B = shop     N = start the next wave', 0, B + 0.1825, 0.95, FG, origin=(0, 0))

        # bottom left: health
        hp = el['health']
        box(hp, L + 0.03, B + 0.1, 0.46, 0.07, P, z=0.003)
        glyph(hp, 'heart', L + 0.065, B + 0.065, 0.032, k['health'])
        box(hp, L + 0.1, B + 0.088, 0.375, 0.046, NAVY, z=0.001)
        self.hp_fill = box(hp, L + 0.1, B + 0.088, 0.375, 0.046, k['health'], round=False)
        self.hp_text = text(hp, '', L + 0.465, B + 0.065, 1.05, contrast(k['health']), origin=(0.5, 0), z=-0.02)
        # scoreboard (hold Tab): every player, then every ally
        self.scoreboard = Entity(parent=h, enabled=False, z=-0.05)
        self.board_rows = Entity(parent=self.scoreboard)
        self.board_t = 0.0
        self.power_rows = []                    # active power-ups, stacked above the health bar
        for i in range(4):
            row = Entity(parent=el['powers'], enabled=False)
            y = B + 0.152 + i * 0.047
            box(row, L + 0.03, y, 0.3, 0.04, P, z=0.003)
            chip = box(row, L + 0.042, y - 0.008, 0.024, 0.024, FG, z=0.001)
            name = text(row, '', L + 0.078, y - 0.02, 0.9, FG, origin=(-0.5, 0))
            secs = text(row, '', L + 0.318, y - 0.02, 0.9, FG, origin=(0.5, 0))
            self.power_rows.append((row, chip, name, secs))

        # bottom middle: ability
        ab = el['ability']
        self.ability_name = text(ab, '', 0, B + 0.142, 0.85, FG, origin=(0, 0), z=-0.02)
        self.ability_name_box = box(ab, -0.07, B + 0.158, 0.14, 0.033, P, z=0.003)
        box(ab, -0.045, B + 0.12, 0.09, 0.09, P, z=0.003)
        box(ab, -0.045 + EDGE, B + 0.12 - EDGE, 0.09 - 2 * EDGE, 0.09 - 2 * EDGE, NAVY, z=0.002)
        self.ability_fill = Entity(parent=ab, model='quad', origin=(0, -0.5), position=(0, B + 0.03 + EDGE, 0.001),
                                   scale=(0.09 - 2 * EDGE, 0.09 - 2 * EDGE), color=C(AC))
        self.ability_cd = text(ab, 'Q', 0, B + 0.075, 1.7, '#f5f4f2', origin=(0, 0), z=-0.02)

        # bottom middle, above the ability: build mode (what you're placing, controls or why it can't go there)
        self.build_box = Entity(parent=h, enabled=False)
        box(self.build_box, -0.3, B + 0.3, 0.6, 0.088, P, z=0.003)
        self.build_accent = box(self.build_box, -0.3, B + 0.3, 0.6, 0.007, AC, z=0.002)
        self.build_title = text(self.build_box, '', 0, B + 0.264, 1.0, FG, origin=(0, 0))
        self.build_sub = text(self.build_box, '', 0, B + 0.23, 0.72, '#aeb3c4', origin=(0, 0))

        # bottom right: a compact weapon box (name, slots, ammo) that stays clear of the gun
        wp = el['weapon']
        frame(wp, R - 0.33, B + 0.105, 0.3, 0.075, PAPER, INK)
        self.weapon_name = text(wp, '', R - 0.318, B + 0.085, 0.72, INK, origin=(-0.5, 0))
        self.slots = text(wp, '', R - 0.318, B + 0.051, 0.58, MUTED, origin=(-0.5, 0))
        box(wp, R - 0.156, B + 0.094, 0.003, 0.053, LINE, z=-0.005)
        self.ammo = text(wp, '', R - 0.093, B + 0.067, 1.5, INK, origin=(0, 0))
        self.apply_hud_layout()

    def open_hud_editor(self):
        from .hud_editor import HudEditor
        self.hud_editor = HudEditor(self, 'pause' if self.game.state == 'paused' else 'menu')

    def hud_sample(self):
        """Fill the HUD with example values and show every part (for the HUD editor)."""
        st = self.set_text
        st(self.wave, '7')
        st(self.remaining, '12 enemies left')
        st(self.coins, '1250')
        st(self.score, 'SCORE 4210')
        self.hp_fill.scale_x = 0.375 * 0.7
        st(self.hp_text, '70 / 100')
        self.quest_box.enabled = True
        st(self.quest_text, 'Light the three braziers (1/3)')
        st(self.feed_text, 'Shambler +5\nBrute +12\nSpike barricade placed')
        self.feed_box.enabled = True
        self.feed_box.scale_y = 0.02 + 0.0245 * 3
        self.boss.enabled = True
        st(self.boss_name, 'THE HOLLOW KING')
        self.boss_fill.scale_x = 0.69 * 0.6
        self.banner_root.enabled = True
        self.banner_text.text, self.banner_sub.text = 'WAVE 7', 'Here they come'
        self.hint.enabled = True
        for i, (row, chip, name, secs) in enumerate(self.power_rows[:2]):
            row.enabled = True
            st(name, ('Gold Rush', 'Overdrive')[i])
            st(secs, ('14s', '6s')[i])
        st(self.weapon_name, 'AK-47')
        st(self.slots, '1  [2]  3')
        st(self.ammo, '24/30')
        st(self.ability_name, 'SHOCKWAVE')
        st(self.ability_cd, 'Q')

    def apply_hud_layout(self):
        """Move and show / hide the HUD parts as saved in the HUD editor."""
        parts = self.game.hud_settings.get('parts', {})
        for key, anchor in self.parts.items():
            pl = parts.get(key, {})
            anchor.position = (pl.get('x', 0.0), pl.get('y', 0.0), 0)
            anchor.enabled = pl.get('on', True)

    def update_weapon(self):
        w = getattr(self.game, 'weapons', None)
        if not w or not w.held:
            return
        d, st = w.d, w.state[w.d['id']]
        lvl = w.total_level(d)
        name = d['name'].upper() + (f'  +{lvl}' if lvl else '')
        self.set_text(self.weapon_name, name)
        self.weapon_name.scale = 0.72 if len(name) <= 13 else max(0.46, 0.72 * 13 / len(name))   # long names shrink to fit
        if d.get('melee'):
            self.set_text(self.ammo, '--')
            self.ammo.scale = 1.5
            self.ammo.color = C(INK)
        else:
            mag = w.stat(d, 'mag')
            label = f"{st['ammo']}/{mag}"
            self.set_text(self.ammo, label)
            self.ammo.scale = 1.5 if len(label) <= 5 else (1.28 if len(label) == 6 else 1.1)
            self.ammo.color = C(RED) if st['ammo'] <= math.ceil(mag * 0.25) else C(INK)
        from .data.items import HAND_SLOTS
        marks = []
        for i, (slot, _) in enumerate(HAND_SLOTS):        # 1 tool  2 handgun  3 rifle
            o = w.slots.get(slot)
            marks.append(f'[{i + 1}]' if o is not None and o is w.held else (str(i + 1) if o is not None else '-'))
        self.set_text(self.slots, '  '.join(marks))

    def build_scoreboard(self):
        g = self.game
        destroy(self.board_rows)
        b = self.board_rows = Entity(parent=self.scoreboard)
        rows = [(p.name + ('  (you)' if p.is_local else ''), p.kills, p.score, p.coins, 'DEAD' if p.dead else '', p.is_local)
                for p in g.players]
        rows += [(f'{a.name}  ({a.owner.name})', a.kills, '-', '-', 'DOWN' if a.downed else '', False) for a in g.allies]
        w, rh = 0.82, 0.052
        h = 0.16 + rh * len(rows)
        x0, y0 = -w / 2, 0.06 + h / 2
        frame(b, x0, y0, w, h, PAPER, INK)
        box(b, x0, y0, w, 0.07, INK, z=-0.001)
        mins, secs = divmod(int(g.time), 60)
        text(b, f'WAVE {g.wave_number}', x0 + 0.03, y0 - 0.035, 1.3, PAPER, origin=(-0.5, 0), z=-0.02)
        text(b, f'{mins:02d}:{secs:02d} survived', x0 + w - 0.03, y0 - 0.035, 1.0, MUTED, origin=(0.5, 0), z=-0.02)
        cols = [(x0 + 0.03, -0.5), (x0 + 0.5, 0.5), (x0 + 0.63, 0.5), (x0 + 0.76, 0.5)]
        y = y0 - 0.1
        for (cx, ox), label in zip(cols, ('NAME', 'KILLS', 'SCORE', 'COINS')):
            text(b, label, cx, y, 0.8, MUTED, origin=(ox, 0), z=-0.02)
        y -= 0.045
        for name, kills, score, coins, status, me in rows:
            if me:
                box(b, x0 + 0.012, y + rh / 2, w - 0.024, rh, '#e6ecf2', z=-0.001)
            colour = RED if status else INK
            for (cx, ox), v in zip(cols, (name + (f'   {status}' if status else ''), kills, score, coins)):
                text(b, str(v), cx, y, 1.0, colour, origin=(ox, 0), z=-0.02)
            y -= rh

    def banner(self, title, color='TEAL', duration=2.5, sub=''):
        self.banner_text.text = title
        self.banner_sub.text = sub
        self.banner_accent.color = C(color)
        self.banner_root.enabled = True
        self.banner_t = duration

    def hitmarker(self, head):
        for c in self.hit.children:
            c.color = C(RED) if head else C(PAPER)
        self.hit.enabled = True
        self.hit_t = 0.12

    def hurt(self, frac):
        self.hurt_t = min(1, self.hurt_t + 0.35 + frac * 2)

    def set_prompt(self, msg, progress=None):
        """A centred hint like 'Hold E to revive' (with an optional progress bar)."""
        self.prompt.enabled = bool(msg)
        if msg:
            if self._cache.get(id(self.prompt_text)) != msg:
                self.set_text(self.prompt_text, msg)
                w = max(0.4, self.prompt_text.width + 0.05)      # long hints get a wider box
                self.prompt_box.x, self.prompt_box.scale_x = -w / 2, w
            self.prompt_bar.enabled = progress is not None
            if progress is not None:
                self.prompt_bar.scale_x = max(0.001, 0.38 * clamp01(progress))

    def set_build_hint(self, title, why=''):
        """Build mode: what you're placing and the controls, or (in red) why it can't go there."""
        self.build_box.enabled = bool(title)
        if not title:
            return
        self.set_text(self.build_title, title)
        self.set_text(self.build_sub, why.upper() if why else 'LMB place     R turn     G / wheel next     RMB done')
        colour = RED if why else TEAL
        if self._cache.get('build_colour') != colour:
            self._cache['build_colour'] = colour
            self.build_accent.color = C(colour)
            self.build_sub.color = C('#ff8a80' if why else '#aeb3c4')

    def kill_feed(self, line):
        self.feed.insert(0, (line, pytime.time()))
        del self.feed[5:]

    def update(self, dt):
        g, p = self.game, self.game.player
        self.hp_fill.scale_x = max(0.0001, 0.375 * clamp01(p.health / p.max_health))
        self.set_text(self.hp_text, 'DOWN' if p.downed else f'{math.ceil(p.health)} / {p.max_health}')
        self.set_text(self.coins, str(g.coins))
        self.set_text(self.score, f'SCORE {g.score}')
        self.set_text(self.wave, str(g.wave_number))
        if g.phase == 'wave':
            self.set_text(self.remaining, f'{g.remaining} enemies left')
        else:
            self.set_text(self.remaining, f'Next wave in {math.ceil(g.intermission)}s')
        self.hint.enabled = g.phase == 'intermission' and not g.shop_open
        tracker = g.quest.tracker() if getattr(g, 'quest', None) else ''
        self.quest_box.enabled = bool(tracker)
        if tracker:
            self.set_text(self.quest_text, tracker)

        show_board = bool(held_keys['tab']) and g.state == 'playing' and not g.shop_open
        if show_board != self.scoreboard.enabled:
            self.scoreboard.enabled = show_board
            self.board_t = 0
        if show_board:
            self.board_t -= dt
            if self.board_t <= 0:
                self.board_t = 0.25
                self.build_scoreboard()
        powers = g.powerups.hud_rows()
        for i, (row, chip, name, secs) in enumerate(self.power_rows):
            row.enabled = i < len(powers)
            if row.enabled:
                label, colour, left = powers[i]
                if self._cache.get(('colour', i)) != colour:
                    self._cache[('colour', i)] = colour
                    chip.color = C(colour)
                    name.color = secs.color = C(colour)
                self.set_text(name, label)
                self.set_text(secs, f'{math.ceil(left)}s')
                chip.enabled = left > 3 or int(left * 4) % 2 == 0     # blink when running out

        now = pytime.time()
        self.feed = [f for f in self.feed if now - f[1] < 3]
        self.set_text(self.feed_text, '\n'.join(f[0] for f in self.feed))
        self.feed_box.enabled = bool(self.feed)
        self.feed_box.scale_y = 0.02 + 0.0245 * len(self.feed)
        if self.feed:                       # widen the box for long messages
            w = max(0.3, 0.0108 * max(len(f[0]) for f in self.feed) + 0.03)
            self.feed_box.scale_x = w
            self.feed_box.x = self.feed_right - w

        a = g.ability
        cd = max(0, p.ability_cd)
        self.ability_fill.color = C(a['color'], 1 if cd <= 0 else 0.45)
        self.ability_fill.scale_y = max(0.0001, (0.09 - 2 * EDGE) * (1 - cd / a['cooldown']))
        self.set_text(self.ability_cd, str(math.ceil(cd)) if cd > 0 else 'Q')
        self.set_text(self.ability_name, a['name'].upper())

        w = g.weapons
        reloading = w.reloading > 0
        self.reload_back.enabled = self.reload_fill.enabled = reloading
        if reloading:
            self.reload_fill.scale_x = max(0.0001, 0.08 * (1 - w.reloading / w.reload_total))

        boss = next((e for e in g.enemies.alive() if e.d.get('boss')), None)
        self.boss.enabled = boss is not None
        if boss:
            self.set_text(self.boss_name, boss.d['name'].upper())
            self.boss_fill.scale_x = max(0.0001, 0.69 * boss.hp / boss.max_hp)

        if self.banner_t > 0:
            self.banner_t -= dt
            if self.banner_t <= 0:
                self.banner_root.enabled = False
        if self.hit_t > 0:
            self.hit_t -= dt
            if self.hit_t <= 0:
                self.hit.enabled = False
        self.hurt_t = max(0, self.hurt_t - dt * 1.5)
        low = 0.35 + math.sin(now * 5) * 0.1 if p.health / p.max_health < 0.3 else 0
        if p.downed:
            low = 0.8 + math.sin(now * 3) * 0.12
        self.vignette.alpha = max(self.hurt_t, low)
        self.adrenaline.alpha = 0.8 if p.buffs.get('adrenaline', 0) > 0 else 0

    # ── main menu ────────────────────────────────────────────────────────────
    MENU_TABS = [('play', 'PLAY'), ('maps', 'MAPS'), ('controls', 'CONTROLS'), ('settings', 'SETTINGS'),
                 ('about', 'ABOUT')]

    def build_menu(self):
        self.menu = Entity(parent=camera.ui, z=-1)
        backdrop(self.menu, 0.35)
        self.menu_win = Window(self.menu, 'BLOCKHOLD')
        self.refresh_menu()

    def set_menu_tab(self, tab):
        self.menu_tab = tab
        self.refresh_menu()

    def refresh_menu(self):
        win, g = self.menu_win, self.game
        win.set_tabs(self.MENU_TABS, self.menu_tab, self.set_menu_tab)
        win.clear()
        getattr(self, f'menu_{self.menu_tab}')(win, g)
        self.update_menu(force=True)

    def menu_play(self, win, g):
        b, y = win.body, win.top
        text(b, 'CHOOSE YOUR ABILITY', win.left, y, 0.85, MUTED)
        y -= 0.035
        for ab in ABILITIES:
            on = g.ability_id == ab['id']
            FlatButton(b, ab['name'].upper(), win.left, y, 0.54, 0.052, lambda a=ab: self.pick_ability(a['id']),
                       fill=INK if on else PAPER, edge=INK, fg=PAPER if on else INK, size=1.05, align='left',
                       right=f"{ab['cooldown']}s", hover=0.15 if on else -0.06)
            y -= 0.062
        text(b, g.ability['desc'], win.left, y - 0.005, 0.85, MUTED, wordwrap=62)
        y -= 0.085
        hline(b, win.left, y, 0.54)
        s = g.save
        y -= 0.03
        pair(b, win.left, y, 'Best wave', s['best_wave'], 0.15, 0.95)
        pair(b, win.left + 0.28, y, 'Best score', s['best_score'], 0.16, 0.95)
        pair(b, win.left, y - 0.05, 'Total kills', s['total_kills'], 0.15, 0.95)
        pair(b, win.left + 0.28, y - 0.05, 'Games', s['games'], 0.16, 0.95)
        hline(b, win.left, y - 0.1, 0.54)
        names = dict(maps.list_maps())
        text(b, 'Map', win.left, y - 0.125, 0.95, INK)
        text(b, names.get(g.map_stem, 'Random arena'), win.left + 0.15, y - 0.122, 1.1, TEAL)
        FlatButton(b, 'CHANGE', win.left + 0.42, y - 0.115, 0.12, 0.04, lambda: self.set_menu_tab('maps'),
                   fill=PAPER, edge=INK, fg=INK, size=0.8, hover=-0.06)

        x, y = win.right_col + 0.03, win.top
        text(b, 'MILESTONES', x, y, 0.85, MUTED)
        y -= 0.04
        for label, frac, value in milestones(s):
            stat_row(b, x, y, 0.38, label, frac, value, GREEN if frac >= 1 else TEAL)
            y -= 0.063
        win.bottom_left('QUIT', g.quit, 'gear', lambda: self.set_menu_tab('settings'))
        win.bottom_right('PLAY', g.start_game, 'keyboard', lambda: self.set_menu_tab('controls'))

    def menu_maps(self, win, g):
        b, x, y = win.body, win.left, win.top
        text(b, 'CHOOSE A MAP', x, y, 0.85, MUTED)
        y -= 0.035
        options = [(None, 'Random arena')] + maps.list_maps()
        for stem, name in options[:9]:
            on = g.map_stem == stem
            FlatButton(b, name, x, y, 0.54, 0.048, lambda s=stem: (g.select_map(s), self.refresh_menu()),
                       fill=INK if on else PAPER, edge=INK if on else LINE, fg=PAPER if on else INK, size=1.0,
                       align='left', right='new every game' if stem is None else '', hover=0.15 if on else -0.06)
            y -= 0.055
        if len(options) > 9:
            text(b, f'+ {len(options) - 9} more in the maps folder', x, y, 0.8, MUTED)

        xr, y = win.right_col + 0.03, win.top
        text(b, 'PREVIEW', xr, y, 0.85, MUTED)
        size = 0.3
        if g.map_stem is None:
            box(b, xr, y - 0.035, size, size, NAVY)
            text(b, '?', xr + size / 2, y - 0.035 - size / 2, 5, PAPER, origin=(0, 0))
            info = ('A new random arena\nevery game, with block\ntrees, crates and ruins.\n\n'
                    f'{maps.size_label(g.arena_size)}')

        else:
            data = maps.load_map(g.map_stem)
            img = maps.preview_image(data)
            box(b, xr - EDGE, y - 0.035 + EDGE, size + 2 * EDGE, size + 2 * EDGE, INK, z=0.001)
            Entity(parent=b, model='quad', texture=Texture(img), origin=(-0.5, 0.5), position=(xr, y - 0.035, -0.001),
                   scale=(size, size))
            graves = sum(1 for p in data.get('props', []) if p[0] == 'zombie_grave')
            info = (f"{maps.size_label(int(data.get('size', 34)))}\n"
                    f"{len(data.get('props', []))} objects\n{len(data.get('paths', []))} path tiles\n"
                    f"{graves} zombie graves\nmaps/{g.map_stem}.json")
        text(b, info, xr + size + 0.03, y - 0.04, 0.85, INK)
        by = y - size - 0.07
        if g.map_stem is not None:
            FlatButton(b, 'EDIT THIS MAP', xr, by, 0.25, 0.055, lambda: g.open_editor(maps.load_map(g.map_stem), g.map_stem),
                       fill=SLATE, edge=SLATE_EDGE, size=1.0)
        FlatButton(b, 'NEW MAP', xr + (0.27 if g.map_stem is not None else 0), by, 0.2, 0.055, lambda: g.open_editor(),
                   fill=TEAL, edge=INK, size=1.0)
        if g.map_stem is None:                   # how big the random arena is
            text(b, 'ARENA SIZE', xr + 0.23, by - 0.012, 0.8, MUTED)
            for i, (label, half) in enumerate(maps.MAP_SIZES):
                on = g.arena_size == half
                FlatButton(b, label, xr + i * 0.112, by - 0.07, 0.106, 0.045,
                           lambda h=half: (g.set_arena_size(h), self.refresh_menu()),
                           fill=INK if on else PAPER, edge=INK, fg=PAPER if on else INK, size=0.85,
                           hover=0.15 if on else -0.06)
        if g.map_stem is not None:
            text(b, 'Build your own maps with trees, buildings, paths and zombie graves.', xr, by - 0.08, 0.8, MUTED,
                 wordwrap=55)
        win.bottom_left('BACK', lambda: self.set_menu_tab('play'), 'home', lambda: self.set_menu_tab('play'))
        win.bottom_right('PLAY', g.start_game)

    CONTROLS = [
        [('Move', 'W A S D'), ('Look', 'Mouse'), ('Shoot', 'Left click'), ('Aim / scope', 'Right click'),
         ('Jump / climb', 'Space'), ('Sprint', 'Shift'), ('Crouch', 'C / Ctrl'), ('Slide', 'Sprint + C'),
         ('Reload', 'R'), ('Ability', 'Q')],
        [('Tool / handgun / rifle', '1 2 3 / wheel'), ('Craft / pick up', 'E'), ('Backpack / drop gun', 'I / X'), ('Build (R turns)', 'G'),
         ('Revive / repair', 'Hold E'), ('Shop', 'B'), ('Scoreboard', 'Hold Tab'),
         ('Next wave', 'N'), ('Pause', 'Esc'), ('Mute / fullscreen', 'M / F11')],
    ]

    def menu_controls(self, win, g):
        b = win.body
        for col_i, rows in enumerate(self.CONTROLS):
            x = win.left if col_i == 0 else win.right_col + 0.03
            y = win.top
            for i, (action, key) in enumerate(rows):
                if i == 4:
                    hline(b, x, y + 0.012, 0.5)
                    y -= 0.022
                text(b, action, x, y, 1.05, INK)
                text(b, key, x + 0.25, y + 0.002, 1.15, TEAL)
                y -= 0.05
        win.bottom_left('BACK', lambda: self.set_menu_tab('play'), 'home', lambda: self.set_menu_tab('play'))
        win.bottom_right('PLAY', g.start_game)

    def menu_settings(self, win, g):
        b = win.body
        self.settings_rows(b, win.right_col + 0.03, win.top, g)
        x, y = win.left, win.top
        text(b, 'OPTIONS', x, y, 0.85, MUTED)
        y -= 0.04
        for label, on, toggle in (('Fullscreen', window.fullscreen, g.toggle_fullscreen),
                                  ('Check for updates on start', g.auto_update, g.toggle_auto_update),
                                  ('Sound', not g.sounds.muted, g.toggle_mute)):
            text(b, label, x, y - 0.012, 1.05, INK)
            FlatButton(b, 'ON' if on else 'OFF', x + 0.42, y, 0.12, 0.045,
                       lambda t=toggle: (t(), self.refresh_menu()), fill=TEAL if on else NAVY,
                       edge=INK, size=0.95)
            y -= 0.07
        hline(b, x, y + 0.01, 0.54)
        self.style_picker(b, x, y - 0.025, g)
        text(b, 'Settings and records are saved in the .blockhold folder in your home folder.',
             x, y - 0.17, 0.75, MUTED, wordwrap=66)
        win.bottom_left('BACK', lambda: self.set_menu_tab('play'), 'home', lambda: self.set_menu_tab('play'))
        win.bottom_right('PLAY', g.start_game)

    def settings_rows(self, parent, x, y, g):
        text(parent, 'SETTINGS', x, y, 0.85, MUTED)
        y -= 0.045
        FlatSlider(parent, x, y, 0.38, 'Mouse sensitivity', 10, 120, round(g.sensitivity), lambda v: f'{v}',
                   g.set_sensitivity)
        FlatSlider(parent, x, y - 0.085, 0.38, 'Volume', 0, 100, round(g.sounds.volume * 100), lambda v: f'{v}%',
                   lambda v: g.set_volume(v / 100))
        FlatSlider(parent, x, y - 0.17, 0.38, 'Field of view', 70, 110, round(g.fov), lambda v: f'{v}°', g.set_fov)
        y -= 0.265
        text(parent, 'Atmosphere', x, y, 0.95, INK)
        choices = [(k, a) for k, a in ATMOSPHERES.items() if not a.get('hidden')]
        for i, (aid, a) in enumerate(choices):
            on = g.atmosphere_id == aid
            FlatButton(parent, a['name'].upper(), x + i * 0.13, y - 0.03, 0.122, 0.045,
                       lambda k=aid: (g.set_atmosphere(k), self.refresh_settings_screen()),
                       fill=TEAL if on else NAVY, edge=INK, size=0.85)
        # UI theme: each button is drawn in that theme's own colours
        from .data.themes import THEMES
        y -= 0.09
        text(parent, 'Theme', x, y, 0.95, INK)
        FlatButton(parent, 'CUSTOMIZE HUD', x + 0.2, y + 0.01, 0.22, 0.04, self.open_hud_editor,
                   fill=TEAL, edge=INK, size=0.8)
        for i, (tid, t) in enumerate(THEMES.items()):
            on = g.theme_id == tid
            FlatButton(parent, t['name'], x + (i % 4) * 0.105, y - 0.035 - (i // 4) * 0.047, 0.1, 0.04,
                       lambda k=tid: g.set_theme(k), fill=t['PAPER'], edge=t['TEAL'] if on else t['INK'],
                       fg=t['INK'], size=0.6, hover=-0.08)
            if on:
                box(parent, x + (i % 4) * 0.105, y - 0.035 - (i // 4) * 0.047 - 0.04, 0.1, 0.006, t['TEAL'], z=-0.03)

    def style_picker(self, parent, x, y, g):
        """STYLE: the shape of the UI. Each button is drawn in its own style."""
        from .data.themes import STYLES
        text(parent, 'STYLE', x, y, 0.85, MUTED)
        text(parent, 'corners, outlines and font', x + 0.09, y, 0.75, MUTED)
        mine = STYLE
        for i, (sid, st) in enumerate(STYLES.items()):
            on = g.style_id == sid
            set_style_temp(st)
            FlatButton(parent, st['name'], x + (i % 4) * 0.137, y - 0.035 - (i // 4) * 0.056, 0.128, 0.046,
                       lambda k=sid: g.set_style(k), fill=TEAL if on else NAVY, edge=INK, size=0.8)
            set_style_temp(mine)

    def refresh_settings_screen(self):
        if self.game.state == 'paused':
            self.show_pause()
        else:
            self.refresh_menu()

    def menu_about(self, win, g):
        b, u = win.body, g.updater
        x, y = win.left, win.top
        text(b, 'VERSION', x, y, 0.85, MUTED)
        pair(b, x, y - 0.045, 'Installed', f'v{u.local}', 0.25, 1.05)
        pair(b, x, y - 0.095, 'Newest on GitHub', f'v{u.remote}' if u.remote else '?', 0.25, 1.05)
        self.about_status = text(b, '', x, y - 0.15, 0.95, TEAL, wordwrap=60)
        if u.status == 'available':
            notes = '\n'.join('- ' + (n if len(n) <= 60 else n[:58] + '...') for n in u.notes[:5])
            text(b, notes, x, y - 0.2, 0.8, INK)
            FlatButton(b, 'UPDATE NOW', x, win.btn_y + BTN_H + 0.03, 0.3, 0.055, g.install_update,
                       fill=TEAL, edge=INK, icon_name='download', size=1.0)
        xr, y = win.right_col + 0.03, win.top
        text(b, '3D MODEL CREDITS', xr, y, 0.85, MUTED)
        from .custom_models import credits
        lines = credits()
        text(b, '\n'.join(lines) if lines else 'No downloaded models yet.\nGet the recommended pack with:\n'
             'python tools/sketchfab_guns.py pack', xr, y - 0.04, 0.85, INK, wordwrap=55)
        hline(b, xr, y - 0.3, 0.5)
        text(b, 'Made with Python and the Ursina engine.\nAll sounds and textures are made by code.',
             xr, y - 0.325, 0.85, MUTED)
        win.bottom_left('BACK', lambda: self.set_menu_tab('play'), 'home', lambda: self.set_menu_tab('play'))
        win.bottom_right('PLAY', g.start_game)

    def update_menu(self, force=False):
        u = getattr(self.game, 'updater', None)
        if u is None:
            return
        status = {
            'idle': '', 'checking': 'Checking GitHub for updates...', 'up_to_date': 'You have the newest version.',
            'offline': 'Could not check for updates.', 'installing': 'Downloading the update...',
            'installed': f'Updated to v{u.local}! Restarting...', 'failed': u.message[:160],
            'available': f'Version {u.remote} is ready to install:',
        }.get(u.status, '')
        right = 'UPDATE AVAILABLE' if u.status == 'available' else f'v{u.local}'
        self.set_text(self.menu_win.right, right)
        self.menu_win.right.color = C(TEAL if u.status == 'available' else INK)
        if self.menu_tab == 'about':
            if u.status != self._update_status and not force:
                self._update_status = u.status
                self.refresh_menu()          # show / hide the update button
                return
            self.set_text(self.about_status, status)
        self._update_status = u.status

    def pick_ability(self, aid):
        self.game.ability_id = aid
        self.game.save_settings()
        self.refresh_menu()

    # ── pause ────────────────────────────────────────────────────────────────
    def build_pause(self):
        self.pause = Entity(parent=camera.ui, z=-1, enabled=False)
        backdrop(self.pause, 0.6)
        self.pause_win = Window(self.pause, 'PAUSED')

    def show_pause(self):
        g, win = self.game, self.pause_win
        win.clear()
        win.right.text = f'WAVE {g.wave_number}'
        b, x, y = win.body, win.left, win.top
        text(b, 'THIS RUN', x, y, 0.85, MUTED)
        t = g.time
        rows = [('Wave', g.wave_number), ('Kills', g.kills), ('Score', g.score), ('Coins', g.coins),
                ('Time', f'{int(t // 60)}:{int(t % 60):02d}'), ('Weapons', len(g.weapons.owned))]
        y -= 0.045
        for i, (label, value) in enumerate(rows):
            if i == 3:
                hline(b, x, y + 0.012, 0.54)
                y -= 0.022
            pair(b, x, y, label, value, 0.25, 1.1)
            y -= 0.058
        self.settings_rows(b, win.right_col + 0.03, win.top, g)
        win.bottom_left('EDITOR' if g.from_editor is not None else 'MAIN MENU', g.to_menu, 'home', g.to_menu)
        win.bottom_right('RESUME', g.resume, fill=TEAL)
        self.pause.enabled = True

    # ── shop ─────────────────────────────────────────────────────────────────
    def build_shop(self):
        self.shop = Entity(parent=camera.ui, z=-1, enabled=False)
        backdrop(self.shop, 0.55)
        self.shop_win = Window(self.shop, 'SHOP')

    # ── workbench (crafting) ─────────────────────────────────────────────────
    def build_craft(self):
        self.craft = Entity(parent=camera.ui, z=-1, enabled=False)
        backdrop(self.craft, 0.45)
        self.craft_win = Window(self.craft, 'WORKBENCH')
        self.craft_cat = 'items'
        self.craft_sel = None

    def select_recipe(self, rid=None, cat=None):
        if cat is not None:
            self.craft_cat = cat
        self.craft_sel = rid
        self.refresh_craft()

    def refresh_craft(self):
        from .data.crafting import all_recipes
        g, win = self.game, self.craft_win
        p, b = g.player, win.body
        win.clear()
        win.right.text = ''
        # header: what you've got
        mats = ('stone', 'wood', 'coal', 'iron_ingot', 'copper_ingot', 'crystal')     # what workbenches use
        x = win.x + win.w - 0.06 - (len(mats) - 1) * 0.11 - 0.07
        for rid, r in ((k, RESOURCES[k]) for k in mats):
            box(b, x, win.y - 0.035, 0.024, 0.024, r['color'], z=-0.01)
            text(b, str(p.resources.get(rid, 0)), x + 0.032, win.y - 0.047, 1.2, INK, origin=(-0.5, 0))
            x += 0.11
        recipes = all_recipes()
        cats = [('items', 'Items'), ('armor', 'Armor'), ('build', 'Build')] + list(CATEGORIES)
        mine = [r for r in recipes if r['category'] == self.craft_cat]
        sel = next((r for r in mine if r['id'] == self.craft_sel), None) or (mine[0] if mine else recipes[0])
        self.craft_sel = sel['id']

        # left: categories + recipe list
        x, y = win.left, win.top + 0.01
        for i, (cid, cname) in enumerate(cats):
            on = cid == self.craft_cat
            FlatButton(b, cname, x + (i % 5) * 0.11, y - (i // 5) * 0.05, 0.104, 0.042,
                       lambda c=cid: self.select_recipe(None, c), fill=INK if on else PAPER, edge=INK,
                       fg=PAPER if on else INK, size=0.8, hover=0.15 if on else -0.06)
        y -= 0.05 * ((len(cats) + 4) // 5) + 0.015
        for r in mine:
            blocker = g.craft_blocker(r)
            is_sel = r is sel
            right = 'READY' if not blocker else ('OWNED' if blocker == 'OWNED' else '')
            fg = PAPER if is_sel else (MUTED if blocker == 'OWNED' else INK)
            FlatButton(b, r['name'], x, y, 0.54, 0.05, lambda rid=r['id']: self.select_recipe(rid),
                       fill=INK if is_sel else PAPER, edge=INK if is_sel else LINE, fg=fg, size=1.0, align='left',
                       right=right, hover=0.15 if is_sel else -0.06)
            y -= 0.058
        tip = {'build': 'Press G to build what you carry. The Furnace turns ore into ingots.',
               'armor': 'Armor goes in your backpack: press I and drag it onto HEAD or BODY.'}.get(
            self.craft_cat, 'Workbenches use ingots: smelt ore and coal in a Furnace (Build tab).')
        text(b, tip, x, win.btn_y + 0.045, 0.8, MUTED)

        # right: the selected recipe
        xr, y = win.right_col + 0.03, win.top + 0.01
        text(b, sel['name'].upper(), xr, y, 1.9, INK)
        text(b, sel['desc'], xr, y - 0.052, 0.85, MUTED, wordwrap=62)
        y -= 0.1
        if sel['kind'] == 'weapon':
            d = g.weapons.get_def(sel['weapon'])
            specials = self.weapon_specials(d, g.weapons)
            if specials:
                text(b, specials, xr, y, 0.8, TEAL, wordwrap=70)
                y -= 0.035
            if d['price']:
                text(b, f"or buy it for {d['price']} coins in the shop between waves", xr, y, 0.8, MUTED)
                y -= 0.035
        elif sel['kind'] == 'placeable':
            from .data.barricades import BARRICADES, MAX_CARRIED
            d = BARRICADES[sel['placeable']]
            t = text(b, self.barricade_specials(d), xr, y, 0.8, TEAL, wordwrap=56)
            y -= 0.035 * (t.text.count('\n') + 1)
            text(b, f"Carrying {p.placeables.get(sel['placeable'], 0)} / {MAX_CARRIED}", xr, y, 0.8, INK)
            y -= 0.035
        y -= 0.02
        text(b, 'COST', xr, y, 0.85, MUTED)
        y -= 0.04
        for rid, need in sel['cost'].items():
            have = p.resources.get(rid, 0)
            r = RESOURCES[rid]
            box(b, xr, y, 0.026, 0.026, r['color'], z=-0.01)
            text(b, r['name'], xr + 0.04, y - 0.013, 1.05, INK, origin=(-0.5, 0))
            bar(b, xr + 0.2, y - 0.006, 0.2, 0.016, clamp01(have / need), GREEN if have >= need else AMBER)
            text(b, f'{have} / {need}', xr + 0.42, y - 0.013, 1.0, GREEN if have >= need else RED, origin=(-0.5, 0))
            y -= 0.055
        blocker = g.craft_blocker(sel)
        if sel['kind'] == 'armor':
            text(b, f'Armor now: {round(p.armor * 100)}%', xr, y - 0.01, 0.85, INK)
        win.bottom_left('CLOSE', g.close_shop, 'cross', g.close_shop)
        label = 'CRAFT' if not blocker else blocker
        win.bottom_right(label, lambda: g.craft(sel['id']), fill=GREEN if not blocker else NAVY, w=0.3)

    @staticmethod
    def barricade_specials(d):
        parts = [f"{d['hp']} HP"]
        if d['height'] >= 3:
            parts.append('too tall to climb')
        elif d['height'] >= 1 and 'turret' not in d:
            parts.append('zombies must break it')
        if 'thorns' in d:
            parts.append(f"{d['thorns']['dps']} damage/s to zombies touching it")
        if 'turret' in d:
            t = d['turret']
            parts.append(f"{t['damage']} damage x {t['rate']}/s  |  {t['range']} m range  |  {t['ammo']} rounds")
        if 'mine' in d:
            parts.append(f"{d['mine']['damage']} blast damage, {d['mine']['radius']} m radius")
        return '  |  '.join(parts)

    def set_tab(self, tab):
        self.shop_tab = tab
        self.refresh_shop()

    def select_weapon(self, wid):
        self.shop_sel = wid
        self.refresh_shop()

    def refresh_shop(self):
        g, win = self.game, self.shop_win
        win.set_tabs([('weapons', 'WEAPONS'), ('player', 'PLAYER'), ('allies', 'ALLIES')], self.shop_tab, self.set_tab)
        win.clear()
        win.right.text = f'{g.coins} coins'
        if self.shop_tab == 'player':
            self.shop_player(win, g)
        elif self.shop_tab == 'allies':
            self.shop_allies(win, g)
        else:
            self.shop_weapons(win, g)
        win.bottom_left('CLOSE', g.close_shop, 'cross', g.close_shop)

    def weapon_specials(self, d, w):
        dm = 1 + 0.15 * w.level(d, 'damage')
        out = []
        if d.get('pellets', 1) > 1:
            out.append(f"{d['pellets']} pellets")
        if d.get('projectile'):
            out.append(f"explodes ({d['projectile']['radius']}m)")
        if d.get('pierce') is True:
            out.append('goes through everything')
        elif d.get('pierce'):
            out.append(f"goes through {d['pierce']}")
        if d.get('cleave'):
            out.append(f"hits {d['cleave']} at once")
        if d.get('headshot'):
            out.append(f"headshots x{d['headshot']}")
        if d.get('scope'):
            out.append('scope')
        if d.get('burn'):
            out.append(f"burns {d['burn']['dps'] * dm:.0f}/s")
        if d.get('slow'):
            out.append(f"freezes {round((1 - d['slow']['mult']) * 100)}%")
        if d.get('chain'):
            out.append(f"chains to {d['chain']['count']}")
        if d.get('spinup'):
            out.append('spins up')
        if d.get('move_mult', 1) != 1:
            out.append(f"{round((1 - d['move_mult']) * 100)}% slower walk")
        return '  /  '.join(out)

    def shop_weapons(self, win, g):
        w, b = g.weapons, win.body
        if self.shop_sel is None or not w.get_def(self.shop_sel) or (w.get_def(self.shop_sel).get('hidden') and not w.owns(self.shop_sel)):
            self.shop_sel = next((d['id'] for d in WEAPONS if not w.owns(d['id']) and not d.get('hidden')), WEAPONS[0]['id'])
        d = w.get_def(self.shop_sel)
        cat = d.get('category', 'special')

        # left: categories + weapon list
        x, y = win.left, win.top + 0.01
        for i, (cid, cname) in enumerate(CATEGORIES):
            on = cid == cat
            FlatButton(b, cname, x + (i % 4) * 0.137, y - (i // 4) * 0.05, 0.128, 0.042,
                       lambda c=cid: self.select_weapon(next(o['id'] for o in WEAPONS if o.get('category') == c)),
                       fill=INK if on else PAPER, edge=INK, fg=PAPER if on else INK, size=0.85,
                       hover=0.15 if on else -0.06)
        y -= 0.115
        for o in WEAPONS:
            if o.get('category') != cat or (o.get('hidden') and not w.owns(o['id'])):
                continue
            owned, sel = w.owns(o['id']), o['id'] == self.shop_sel
            lvl = w.total_level(o)
            price = ('EQUIPPED' if w.held is o else 'OWNED') if owned else f"{o['price']}"
            fg = PAPER if sel else (MUTED if owned else INK)
            FlatButton(b, o['name'] + (f'  +{lvl}' if lvl else ''), x, y, 0.54, 0.05, lambda wid=o['id']: self.select_weapon(wid),
                       fill=INK if sel else PAPER, edge=INK if sel else LINE, fg=fg, size=1.0, align='left',
                       right=price, hover=0.15 if sel else -0.06)
            y -= 0.058
        owned_count = sum(1 for o in WEAPONS if w.owns(o['id']) and not o.get('hidden'))
        total = sum(1 for o in WEAPONS if not o.get('hidden'))
        text(b, f'{owned_count} / {total} weapons owned', x, win.btn_y + 0.045, 0.8, MUTED)

        # right: details, stat bars with their upgrade buttons
        xr, y = win.right_col + 0.03, win.top + 0.01
        text(b, d['name'].upper(), xr, y, 1.9, INK)
        can_customize = w.owns(d['id']) and (w.slots_for(d) or d['id'] in GUN_MODELS)
        if can_customize:
            for i, (view, label) in enumerate((('stats', 'UPGRADES'), ('customize', 'CUSTOMIZE'))):
                on = self.shop_view == view
                FlatButton(b, label, xr + 0.33 + i * 0.125, y + 0.004, 0.12, 0.036,
                           lambda v=view: (setattr(self, 'shop_view', v), self.refresh_shop()),
                           fill=INK if on else PAPER, edge=INK, fg=PAPER if on else INK, size=0.75,
                           hover=0.15 if on else -0.06)
        if can_customize and self.shop_view == 'customize':
            self.weapon_customize(b, g, w, d, xr, y - 0.05)
            self.weapon_buttons(win, g, w, d)
            return
        text(b, d['desc'], xr, y - 0.052, 0.85, MUTED, wordwrap=62)
        specials = self.weapon_specials(d, w)
        if specials:
            text(b, specials, xr, y - 0.085, 0.8, TEAL, wordwrap=70)
        owned = w.owns(d['id'])
        ups = {u['id']: u for u in w.upgrades_for(d)}
        rows = [('damage', 'Damage', *self.dmg_stat(d, w))]
        rows.append(('rate', 'Swing speed' if d.get('melee') else 'Fire rate',
                     clamp01(w.stat(d, 'rate') / 24), f"{w.stat(d, 'rate'):.1f}/s"))
        if d.get('melee'):
            rows.append(('range', 'Reach', clamp01(w.stat(d, 'range') / 4), f"{w.stat(d, 'range'):.1f}m"))
        else:
            rows.append(('mag', 'Magazine', clamp01(w.stat(d, 'mag') / 120), str(w.stat(d, 'mag'))))
            rows.append(('reload', 'Reload', clamp01(1.0 / w.stat(d, 'reload')), f"{w.stat(d, 'reload'):.1f}s"))
            rows.append((None, 'Accuracy', clamp01(1 - d.get('spread', 0) / 0.09), f"{round(clamp01(1 - d.get('spread', 0) / 0.09) * 100)}%"))
        y -= 0.135
        for uid, label, frac, value in rows:
            u = ups.get(uid)
            lv = w.level(d, uid) if u else 0
            text(b, label, xr, y, 0.95, INK)
            if u:
                for k in range(u['max']):     # level pips
                    box(b, xr + 0.15 + k * 0.022, y - 0.004, 0.016, 0.012, TEAL if k < lv else C(LINE, 0.35))
            bar(b, xr, y - 0.03, 0.3, 0.018, frac)
            text(b, value, xr + 0.315, y - 0.039, 0.95, INK, origin=(-0.5, 0))
            if u and owned:
                price = w.upgrade_price(d, uid)
                maxed = lv >= u['max']
                ok = g.coins >= price and not maxed
                FlatButton(b, 'MAX' if maxed else str(price), xr + 0.43, y + 0.002, 0.15, 0.048,
                           lambda i=uid: g.buy_weapon_upgrade(d['id'], i), fill=TEAL if ok else NAVY, edge=INK,
                           icon_name=None if maxed else 'arrow_up', size=0.9)
            y -= 0.068

        self.weapon_buttons(win, g, w, d)

    def weapon_buttons(self, win, g, w, d):
        # bottom right: buy / equip + start wave
        owned = w.owns(d['id'])
        if not owned:
            ok = g.coins >= d['price']
            win.bottom_right(f"BUY  {d['price']}", lambda: g.buy_weapon(d['id']), 'play', g.shop_start_wave,
                             fill=GREEN if ok else NAVY, w=0.3)
        elif w.held is not d:
            win.bottom_right('EQUIP', lambda: (w.ready(d), self.refresh_shop()), 'play',
                             g.shop_start_wave, fill=SLATE, w=0.3)
        else:
            win.bottom_right('START WAVE', g.shop_start_wave, fill=TEAL, w=0.3)

    def weapon_customize(self, b, g, w, d, xr, y):
        """Attachments and camo, with a 3D preview of the gun."""
        # preview
        pw, ph = 0.6, 0.135
        frame(b, xr, y, pw, ph, '#e9e8e4', LINE, t=0.004)
        if d['id'] in GUN_MODELS:
            s = w.gun_smith(d)
            zs = [v[2] for v in s.lp.verts]
            ys = [v[1] for v in s.lp.verts]
            length = max(zs) - min(zs)
            scale = min(0.5 / length, 0.12 / max(0.01, max(ys) - min(ys)))
            gun = Entity(parent=b, model=s.build(), rotation=(4, 90, 0), scale=scale,
                         position=(xr + pw / 2 - (max(zs) + min(zs)) / 2 * scale, y - ph / 2 - (max(ys) + min(ys)) / 2 * scale, -0.2))
            gun.setDepthTest(True)
            gun.setDepthWrite(True)
        else:
            text(b, 'This weapon keeps its classic look.', xr + pw / 2, y - ph / 2, 0.85, MUTED, origin=(0, 0))
        y -= ph + 0.025
        fitted = w.attach.get(d['id'], {})
        owned_att = w.owned_att.get(d['id'], set())
        for slot in w.slots_for(d):
            text(b, SLOT_NAMES[slot].upper(), xr, y - 0.004, 0.8, MUTED)
            options = [k for k, a in ATTACHMENTS.items() if a['slot'] == slot]
            for i, aid in enumerate(options):
                a = ATTACHMENTS[aid]
                on = fitted.get(slot) == aid
                have = aid in owned_att
                label = a['name'] if have else f"{a['name']}  {a['price']}"
                ok = have or g.coins >= a['price']
                FlatButton(b, label, xr + 0.13 + i * 0.148, y + 0.006, 0.142, 0.038,
                           lambda x=aid: g.buy_attachment(d['id'], x),
                           fill=INK if on else (PAPER if ok else '#e2d9d6'), edge=INK if (on or have) else LINE,
                           fg=PAPER if on else (INK if ok else RED), size=0.64, hover=0.15 if on else -0.06)
            y -= 0.05
        if d['id'] in GUN_MODELS:
            text(b, 'CAMO', xr, y - 0.004, 0.8, MUTED)
            current = w.camo.get(d['id'], 'factory')
            for i, (cid, c) in enumerate(CAMOS.items()):
                swatch = c['colours'][0] if c['colours'] else '#383c43'
                on = cid == current
                have = cid in w.owned_camos
                FlatButton(b, '', xr + 0.13 + i * 0.044, y + 0.008, 0.04, 0.036, lambda x=cid: g.buy_camo(d['id'], x),
                           fill=swatch, edge=INK if on else LINE, hover=0.15)
                if on:
                    box(b, xr + 0.13 + i * 0.044, y - 0.032, 0.04, 0.006, INK)
                if not have:
                    text(b, str(c['price']), xr + 0.15 + i * 0.044, y - 0.036, 0.5, MUTED, origin=(0, 0.5))
            c = CAMOS[current]
            text(b, f"{c['name']} camo", xr, y - 0.03, 0.7, INK)

    def shop_allies(self, win, g):
        from .data.allies import ALLY_TYPES, MAX_ALLIES
        b, x, y = win.body, win.left, win.top + 0.01
        mine = [a for a in g.allies if a.owner is g.player]
        text(b, 'HIRE SURVIVORS', x, y, 0.85, MUTED)
        y -= 0.035
        for kind, d in ALLY_TYPES.items():
            frame(b, x, y, 0.56, 0.1, PAPER, LINE, t=0.004, z=0.01)
            text(b, d['name'].upper(), x + 0.015, y - 0.012, 1.15, INK)
            text(b, d['desc'], x + 0.015, y - 0.047, 0.72, MUTED)
            bar(b, x + 0.015, y - 0.075, 0.16, 0.012, d['hp'] / 300, GREEN)
            text(b, f"{d['hp']} hp", x + 0.18, y - 0.081, 0.68, INK, origin=(-0.5, 0))
            dps = d['damage'] * d['rate']
            bar(b, x + 0.25, y - 0.075, 0.12, 0.012, dps / 220, TEAL)
            text(b, f'{dps:.0f} dps', x + 0.375, y - 0.081, 0.68, INK, origin=(-0.5, 0))
            full = len(mine) >= MAX_ALLIES
            ok = g.coins >= d['price'] and not full
            FlatButton(b, 'TEAM FULL' if full else f"HIRE  {d['price']}", x + 0.42, y - 0.012, 0.13, 0.045,
                       lambda k=kind: g.hire_ally(k), fill=GREEN if ok else NAVY, edge=INK, size=0.8)
            y -= 0.112
        xr, y = win.right_col + 0.03, win.top + 0.01
        text(b, f'YOUR TEAM  {len(mine)}/{MAX_ALLIES}', xr, y, 0.85, MUTED)
        y -= 0.045
        if not mine:
            text(b, 'No survivors yet.\nAllies follow you, shoot zombies and earn you coins.\n'
                    'If one goes down, hold E next to them to revive them.\nEveryone gets back up when a wave ends.',
                 xr, y, 0.85, INK)
        for a in mine:
            text(b, a.name, xr, y, 1.1, INK)
            bar(b, xr + 0.2, y - 0.012, 0.25, 0.016, a.hp / a.max_hp, RED if a.downed else GREEN)
            text(b, 'DOWN' if a.downed else f'{math.ceil(a.hp)} hp', xr + 0.47, y - 0.02, 0.8,
                 RED if a.downed else INK, origin=(-0.5, 0))
            y -= 0.06
        win.bottom_right('START WAVE', g.shop_start_wave, fill=TEAL, w=0.3)

    def dmg_stat(self, d, w):
        dm = 1 + 0.15 * w.level(d, 'damage')
        if d.get('projectile'):
            v = d['projectile']['damage'] * dm
            return clamp01(math.sqrt(v / 450)), f'{v:.0f}'
        v = w.stat(d, 'damage') * d.get('pellets', 1)
        label = f"{w.stat(d, 'damage'):.0f}x{d['pellets']}" if d.get('pellets', 1) > 1 else f'{v:.0f}'
        return clamp01(math.sqrt(v / 450)), label

    def shop_player(self, win, g):
        p, b = g.player, win.body
        text(b, (f'Health {math.ceil(p.health)}/{p.max_health}     Damage {round(p.damage_mult * 100)}%     '
                 f'Speed {round(p.speed_mult * 100)}%     Regen {p.regen:.1f}/s     Armor {round(p.armor * 100)}%'),
             win.left, win.top + 0.01, 0.9, MUTED)
        for i, u in enumerate(UPGRADES):
            x = win.left if i % 2 == 0 else win.right_col + 0.03
            y = win.top - 0.04 - (i // 2) * 0.115
            lvl = g.upgrade_levels.get(u['id'], 0)
            price = g.upgrade_price(u)
            maxed = lvl >= u['max']
            useless = u['id'] == 'medkit' and p.health >= p.max_health
            text(b, u['name'], x, y, 1.05, INK)
            text(b, u['desc'], x, y - 0.03, 0.78, MUTED)
            if u.get('consumable'):
                bar(b, x, y - 0.06, 0.34, 0.016, p.health / p.max_health, RED)
                value = f'{math.ceil(p.health)} hp'
            else:
                bar(b, x, y - 0.06, 0.34, 0.016, lvl / u['max'], GREEN if maxed else TEAL)
                value = f"{lvl}/{u['max']}"
            text(b, value, x + 0.355, y - 0.068, 0.9, INK, origin=(-0.5, 0))
            ok = g.coins >= price and not maxed and not useless
            FlatButton(b, 'MAX' if maxed else str(price), x + 0.45, y - 0.005, 0.13, 0.05,
                       lambda uid=u['id']: g.buy_upgrade(uid), fill=TEAL if ok else NAVY, edge=INK,
                       icon_name=None if maxed else 'cart', size=0.9)
        win.bottom_right('START WAVE', g.shop_start_wave, fill=TEAL, w=0.3)

    # ── game over ────────────────────────────────────────────────────────────
    def build_dead(self):
        self.dead = Entity(parent=camera.ui, z=-1, enabled=False)
        backdrop(self.dead, 0.6)
        self.dead_win = Window(self.dead, 'YOU FELL')

    def show_dead(self, stats, record):
        g, win = self.game, self.dead_win
        win.clear()
        win.right.text = f"WAVE {stats['wave']}"
        b, x, y = win.body, win.left, win.top
        text(b, 'THIS RUN', x, y, 0.85, MUTED)
        t = stats['time']
        y -= 0.05
        for label, value in (('Wave reached', stats['wave']), ('Zombies defeated', stats['kills']),
                             ('Score', stats['score']), ('Time survived', f'{int(t // 60)}:{int(t % 60):02d}')):
            pair(b, x, y, label, value, 0.3, 1.15)
            y -= 0.065
        hline(b, x, y + 0.015, 0.54)
        if record:
            glyph(b, 'star', x + 0.02, y - 0.03, 0.04, AMBER)
            text(b, 'NEW PERSONAL BEST!', x + 0.05, y - 0.03, 1.2, AMBER, origin=(-0.5, 0))
        xr, y = win.right_col + 0.03, win.top
        text(b, 'MILESTONES', xr, y, 0.85, MUTED)
        y -= 0.04
        for label, frac, value in milestones(g.save):
            stat_row(b, xr, y, 0.38, label, frac, value, GREEN if frac >= 1 else TEAL)
            y -= 0.063
        win.bottom_left('EDITOR' if g.from_editor is not None else 'MAIN MENU', g.to_menu, 'home', g.to_menu)
        win.bottom_right('PLAY AGAIN', lambda: g.start_game(g.from_editor, from_editor=g.from_editor is not None),
                         fill=TEAL)
        self.dead.enabled = True
