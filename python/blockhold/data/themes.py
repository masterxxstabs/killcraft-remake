# ─────────────────────────────────────────────────────────────────────────────
#  UI THEMES AND HUD OPTIONS
#
#  A theme recolours every screen (menus, shop, workbench, pause, HUD, editor).
#  Pick one under Settings. Each colour has a job:
#    PAPER       panel background (and text on dark boxes)
#    INK         outlines, active tabs, main text (and dark boxes)
#    SLATE       buttons            SLATE_EDGE  button outlines
#    NAVY        empty part of bars, small square buttons
#    TEAL        highlights and bar fills
#    LINE        divider lines      MUTED       secondary text
#    RED / AMBER / GREEN   warnings, prices, "ready"
#  PAPER and INK are drawn on top of each other, so keep them far apart
#  (one light, one dark). Add a theme by copying one and changing the colours.
# ─────────────────────────────────────────────────────────────────────────────

THEMES = {
    'classic': dict(name='Classic', PAPER='#f5f4f2', INK='#12121c', SLATE='#404968', SLATE_EDGE='#1e2537',
                    NAVY='#1f2636', TEAL='#1197b0', LINE='#414a67', MUTED='#6b7189',
                    RED='#d64541', AMBER='#d9912b', GREEN='#2e9e6a'),
    'midnight': dict(name='Midnight', PAPER='#1b1f2a', INK='#e9ecf4', SLATE='#3a4560', SLATE_EDGE='#0d1018',
                     NAVY='#11141c', TEAL='#4fb3ff', LINE='#3c4660', MUTED='#8a93ad',
                     RED='#ff5d5d', AMBER='#ffb547', GREEN='#3ddc97'),
    'military': dict(name='Military', PAPER='#e4dcc2', INK='#23261a', SLATE='#59613d', SLATE_EDGE='#2b301c',
                     NAVY='#30351f', TEAL='#9aa95a', LINE='#6b7150', MUTED='#6f6c58',
                     RED='#b8442e', AMBER='#d49a2a', GREEN='#6f9a3a'),
    'neon': dict(name='Neon', PAPER='#0e0b16', INK='#f2f0ff', SLATE='#3a1f5c', SLATE_EDGE='#ff2bd6',
                 NAVY='#1a1030', TEAL='#00f0ff', LINE='#5b2e8a', MUTED='#a58fd0',
                 RED='#ff2b6a', AMBER='#ffcc00', GREEN='#39ff88'),
    'blood': dict(name='Blood Moon', PAPER='#1c0f10', INK='#f3e3dc', SLATE='#5e1f22', SLATE_EDGE='#0c0405',
                  NAVY='#140809', TEAL='#e0473c', LINE='#5a2a2a', MUTED='#b08880',
                  RED='#ff4b3e', AMBER='#f0a040', GREEN='#7fbf6a'),
    'arctic': dict(name='Arctic', PAPER='#eef6fb', INK='#15324a', SLATE='#3f7fae', SLATE_EDGE='#1c4566',
                   NAVY='#c6dceb', TEAL='#2bb3d9', LINE='#9cc0d8', MUTED='#5f7f97',
                   RED='#d9534f', AMBER='#e09a2f', GREEN='#2fa67a'),
    'terminal': dict(name='Terminal', PAPER='#050a05', INK='#7dff8a', SLATE='#0f2a12', SLATE_EDGE='#3bd65a',
                     NAVY='#081408', TEAL='#3bd65a', LINE='#1f5a2a', MUTED='#4fa85e',
                     RED='#ff5a4a', AMBER='#ffd24a', GREEN='#7dff8a'),
    'sunset': dict(name='Sunset', PAPER='#fff1e3', INK='#2b1630', SLATE='#c4513e', SLATE_EDGE='#5a2230',
                   NAVY='#f2d2bf', TEAL='#ee7b3a', LINE='#d8a48c', MUTED='#8a6170',
                   RED='#d6334a', AMBER='#e8902a', GREEN='#3a9a6a'),
}
DEFAULT_THEME = 'classic'

# ── STYLES ───────────────────────────────────────────────────────────────────
# The shape of the UI, separate from its colours (any style works with any theme):
#    radius     how round panel and button corners are (screen height = 1; 0 = square)
#    segments   how the corners are drawn: 6+ = round, 1 = cut off at 45° (chamfered)
#    pill       buttons are fully round at the ends
#    edge       outline thickness (0 = no outlines)
#    glass      how solid the panels are (1 = solid, lower = see-through)
#    font       OpenSans-Regular.ttf or VeraMono.ttf (a typewriter-style font)
STYLES = {
    'flat': dict(name='Flat', radius=0.0, segments=0, pill=False, edge=0.008, glass=1.0,
                 font='OpenSans-Regular.ttf'),
    'rounded': dict(name='Rounded', radius=0.016, segments=6, pill=False, edge=0.005, glass=1.0,
                    font='OpenSans-Regular.ttf'),
    'soft': dict(name='Soft', radius=0.03, segments=8, pill=True, edge=0.003, glass=1.0,
                 font='OpenSans-Regular.ttf'),
    'tactical': dict(name='Tactical', radius=0.016, segments=1, pill=False, edge=0.004, glass=0.94,
                     font='VeraMono.ttf'),
    'glass': dict(name='Glass', radius=0.014, segments=6, pill=False, edge=0.0025, glass=0.78,
                  font='OpenSans-Regular.ttf'),
    'minimal': dict(name='Minimal', radius=0.0, segments=0, pill=False, edge=0.0, glass=0.94,
                    font='OpenSans-Regular.ttf'),
    'chunky': dict(name='Chunky', radius=0.008, segments=1, pill=False, edge=0.014, glass=1.0,
                   font='OpenSans-Regular.ttf'),
}
DEFAULT_STYLE = 'flat'

# ── HUD ──────────────────────────────────────────────────────────────────────
# The parts of the HUD you can move and switch off (Settings → CUSTOMIZE HUD).
# Each one has a box (x, y, w, h: top-left corner and size, screen height = 1;
# L / R / B / T are the left, right, bottom and top edges of the screen) that you
# grab to drag it around. Moved parts are saved as an offset from where they start.
HUD_PARTS = [
    ('crosshair', 'Crosshair'),
    ('wave', 'Wave counter'),
    ('quest', 'Quest tracker'),
    ('money', 'Coins and score'),
    ('feed', 'Kill feed'),
    ('health', 'Health bar'),
    ('powers', 'Power-ups'),
    ('ability', 'Ability'),
    ('weapon', 'Weapon / ammo'),
    ('hint', 'Shop hint'),
    ('banner', 'Wave banner'),
    ('boss', 'Boss health'),
]

# colour choices offered in the HUD editor (None = use the theme's colour)
HUD_PANEL_COLOURS = [None, '#12121c', '#1f2636', '#2b1630', '#23261a', '#3a1f5c', '#5e1f22', '#f5f4f2']
HUD_ACCENTS = [None, '#1197b0', '#4fb3ff', '#00f0ff', '#39ff88', '#ffcc00', '#ff8c2a', '#ff2bd6', '#e0473c']
HUD_HEALTH = [None, '#d64541', '#ff2b6a', '#39ff88', '#2e9e6a', '#ffcc00', '#4fb3ff', '#f5f4f2']
HUD_CROSSHAIR = [None, '#f5f4f2', '#39ff88', '#00f0ff', '#ffcc00', '#ff2b6a', '#ff8c2a', '#12121c']
HUD_OPACITY = [1.0, 0.85, 0.65, 0.45]


def default_hud():
    return dict(panel=None, accent=None, health=None, crosshair=None, opacity=1.0,
                parts={k: dict(x=0.0, y=0.0, on=True) for k, _ in HUD_PARTS})
