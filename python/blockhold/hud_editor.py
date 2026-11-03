"""The HUD editor (Settings → CUSTOMIZE HUD).

Drag any part of the HUD to move it, switch parts on and off, and pick the HUD's
colours. Everything is saved in the settings file (`hud` in settings.json).
Press H to hide the panel, Esc or DONE to leave.
"""
from ursina import Entity, camera, held_keys, mouse, window
from . import ui as U
from .data.themes import (HUD_ACCENTS, HUD_CROSSHAIR, HUD_HEALTH, HUD_OPACITY, HUD_PANEL_COLOURS, HUD_PARTS,
                          default_hud)
from .render import destroy

GRID = 0.005          # parts snap to this when dragged


class HudEditor(Entity):
    def __init__(self, ui, came_from):
        super().__init__(parent=camera.ui)
        self.ui, self.game = ui, ui.game
        self.came_from = came_from              # 'menu' or 'pause'
        self.dragging = None                    # (key, start offset, start mouse)
        self.panel_on = True
        self.handles = []
        for screen in (ui.menu, ui.pause):
            screen.enabled = False
        self.backdrop = Entity(parent=camera.ui, model='quad', scale=(4, 1), z=5, color=U.C('#000000', 0.35))
        self.setup()

    # ── building ─────────────────────────────────────────────────────────────
    def setup(self):
        """(Re)show the HUD with example values and a drag handle on every part, plus the panel."""
        ui = self.ui
        ui.hud.enabled = True
        ui.hud_sample()
        for hd in self.handles:
            destroy(hd)
        self.handles = []
        names = dict(HUD_PARTS)
        for key, anchor in ui.parts.items():
            if key == 'crosshair':
                continue
            x, y, w, h = ui.part_rects[key]
            hd = Entity(parent=anchor, z=-0.2)
            # a see-through grab box with an outline and the part's name
            Entity(parent=hd, model='quad', origin=(-0.5, 0.5), position=(x, y, 0), scale=(w, h),
                   color=U.C(U.TEAL, 0.12), collider='box', name=f'handle:{key}')
            for bx, by, bw, bh in ((x, y, w, 0.004), (x, y - h + 0.004, w, 0.004), (x, y, 0.004, h), (x + w - 0.004, y, 0.004, h)):
                U.box(hd, bx, by, bw, bh, U.TEAL, z=-0.01)
            U.text(hd, names[key], x + 0.006, y - 0.004, 0.62, U.TEAL, z=-0.02)
            self.handles.append(hd)
        self.build_panel()

    def build_panel(self):
        if getattr(self, 'panel', None) is not None:
            destroy(self.panel)
        self.panel = Entity(parent=self, z=-0.5)
        p = self.panel
        hud = self.game.hud_settings
        if not self.panel_on:
            U.FlatButton(p, 'SHOW PANEL  (H)', -0.12, 0.07, 0.24, 0.045, self.toggle_panel, fill=U.TEAL, edge=U.INK,
                         size=0.8)
            return
        w, h, top = 0.98, 0.56, 0.17
        x0 = -w / 2
        U.frame(p, x0, top, w, h, U.PAPER, U.INK)
        U.text(p, 'CUSTOMIZE HUD', x0 + 0.03, top - 0.03, 1.5, U.INK)
        U.text(p, 'Drag the outlined boxes to move them. Click a part to switch it on or off.',
               x0 + 0.03, top - 0.08, 0.72, U.MUTED)
        # parts on / off
        y = top - 0.115
        for i, (key, label) in enumerate(HUD_PARTS):
            on = hud['parts'][key]['on']
            U.FlatButton(p, label, x0 + 0.03 + (i % 2) * 0.205, y - (i // 2) * 0.046, 0.198, 0.04,
                         lambda k=key: self.toggle_part(k), fill=U.TEAL if on else U.NAVY, edge=U.INK,
                         size=0.64, align='left', right='ON' if on else 'OFF')
        # colours
        xr, y = x0 + 0.47, top - 0.115
        rows = (('Panels', 'panel', HUD_PANEL_COLOURS), ('Accent', 'accent', HUD_ACCENTS),
                ('Health bar', 'health', HUD_HEALTH), ('Crosshair', 'crosshair', HUD_CROSSHAIR))
        for label, key, choices in rows:
            U.text(p, label, xr, y - 0.01, 0.8, U.INK)
            for i, c in enumerate(choices):
                on = hud.get(key) == c
                bx = xr + 0.11 + i * 0.042
                if c is None:            # the theme's own colour
                    U.FlatButton(p, 'T', bx, y, 0.036, 0.036, lambda k=key: self.set_colour(k, None),
                                 fill=U.PAPER, edge=U.TEAL if on else U.LINE, fg=U.INK, size=0.7, hover=-0.08)
                else:
                    U.FlatButton(p, '', bx, y, 0.036, 0.036, lambda k=key, v=c: self.set_colour(k, v),
                                 fill=c, edge=U.TEAL if on else U.LINE, hover=0.1)
                if on:
                    U.box(p, bx, y - 0.04, 0.036, 0.005, U.TEAL, z=-0.03)
            y -= 0.058
        U.text(p, 'Opacity', xr, y - 0.01, 0.8, U.INK)
        for i, op in enumerate(HUD_OPACITY):
            on = abs(hud.get('opacity', 1.0) - op) < 0.01
            U.FlatButton(p, f'{round(op * 100)}%', xr + 0.11 + i * 0.075, y, 0.07, 0.036,
                         lambda v=op: self.set_colour('opacity', v), fill=U.TEAL if on else U.NAVY, edge=U.INK,
                         size=0.7)
        # bottom row
        by = top - h + 0.065
        U.FlatButton(p, 'RESET POSITIONS', x0 + 0.03, by, 0.21, 0.045, self.reset_positions, fill=U.SLATE, edge=U.INK,
                     size=0.75)
        U.FlatButton(p, 'RESET ALL', x0 + 0.25, by, 0.14, 0.045, self.reset_all, fill=U.SLATE, edge=U.INK, size=0.75)
        U.FlatButton(p, 'HIDE PANEL  (H)', x0 + 0.4, by, 0.2, 0.045, self.toggle_panel, fill=U.SLATE, edge=U.INK,
                     size=0.75)
        U.FlatButton(p, 'DONE', x0 + w - 0.2, by, 0.17, 0.045, self.close, fill=U.GREEN, edge=U.INK, size=0.9)

    # ── actions ──────────────────────────────────────────────────────────────
    def toggle_part(self, key):
        pl = self.game.hud_settings['parts'][key]
        pl['on'] = not pl['on']
        self.ui.apply_hud_layout()
        self.game.save_hud(rebuild=False)
        self.build_panel()

    def set_colour(self, key, value):
        self.game.hud_settings[key] = value
        self.game.save_hud()                 # rebuilds the HUD in the new colours
        self.setup()

    def reset_positions(self):
        for pl in self.game.hud_settings['parts'].values():
            pl['x'] = pl['y'] = 0.0
        self.ui.apply_hud_layout()
        self.game.save_hud(rebuild=False)

    def reset_all(self):
        self.game.hud_settings = default_hud()
        self.game.save_hud()
        self.setup()

    def toggle_panel(self):
        self.panel_on = not self.panel_on
        self.build_panel()

    def close(self):
        g, ui = self.game, self.ui
        g.save_hud()                          # also clears the example values
        for hd in self.handles:
            destroy(hd)
        destroy(self.backdrop)
        destroy(self.panel)
        ui.hud_editor = None
        if self.came_from == 'pause':
            ui.show_pause()
        else:
            ui.hud.enabled = False
            ui.menu.enabled = True
            ui.refresh_menu()
        destroy(self)

    # ── dragging ─────────────────────────────────────────────────────────────
    def input(self, key):
        if key == 'h':
            self.toggle_panel()
        elif key == 'escape':
            self.close()

    def update(self):
        hud = self.game.hud_settings
        if held_keys['left mouse']:
            if self.dragging is None:
                e = mouse.hovered_entity
                name = getattr(e, 'name', '') or ''
                if name.startswith('handle:'):
                    key = name.split(':', 1)[1]
                    pl = hud['parts'][key]
                    self.dragging = (key, (pl['x'], pl['y']), (mouse.x, mouse.y))
            else:
                key, (sx, sy), (mx, my) = self.dragging
                nx, ny = sx + mouse.x - mx, sy + mouse.y - my
                x, y, w, h = self.ui.part_rects[key]          # keep the part on the screen
                a = window.aspect_ratio
                nx = max(-a / 2 - x, min(a / 2 - (x + w), nx))
                ny = max(-0.5 - (y - h), min(0.5 - y, ny))
                nx, ny = round(nx / GRID) * GRID, round(ny / GRID) * GRID
                hud['parts'][key]['x'], hud['parts'][key]['y'] = nx, ny
                self.ui.parts[key].position = (nx, ny, 0)
        elif self.dragging is not None:
            self.dragging = None
            self.game.save_hud(rebuild=False)
