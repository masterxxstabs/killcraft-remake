"""The map editor.

Controls
  Left click / drag     place the selected thing (drag paints paths, draws fences, scatters trees)
  Right click / drag    erase
  R                     turn buildings and props
  [  ]                  brush size (paths, blocks, eraser)
  1 - 4                 block height
  W A S D / arrows      move the camera     Q / E  turn it     mouse wheel  zoom
  Ctrl+Z                undo
  Esc                   leave the editor
"""
import math
import random
import time as pytime
from panda3d.core import Point2, Point3, TransparencyAttrib
from ursina import Entity, InputField, Mesh, Vec3, application, camera, color as ucolor, destroy, held_keys, mouse, scene, window
from . import maps
from .data.assets import ASSETS, ASSET_CATEGORIES, BLOCKS, PATHS
from .render import WORLD_SHADER, col, node, set_fog
from .ui import (BTN_H, EDGE, GREEN, INK, LINE, MUTED, NAVY, PAPER, RED, SLATE, TEAL, C, FlatButton, Window, box,
                 frame, glyph, text)
from .world import World, prototype, rotate_cell

SCATTER_SPACING = {'trees': 2.6, 'shrubs': 1.1, 'props': 1.2}
UNDO_LIMIT = 40


class Editor:
    def __init__(self, game, map_data=None, stem=None):
        self.game = game
        data = map_data or maps.blank_map()
        self.stem = stem
        self.name = data.get('name', 'My map')
        self.loaded_name = self.name
        self.world = World(map_data=data, editor=True)
        game.world = self.world
        self.category, self.asset = 'trees', 'pine'
        self.path_kind, self.block_kind = 'dirt', 'stone'
        self.rot = 0
        self.brush = 1
        self.block_h = 2
        self.eraser = False
        self.undo_stack = []
        self.dirty = False
        self.exit_armed = 0
        self.painting = self.erasing = False
        self.last_cell = self.last_scatter = None
        self.toast_t = 0
        self.dialog = None
        sp = self.world.player_spawn
        self.pivot = Vec3(sp.x, 0, sp.z)
        self.yaw, self.pitch, self.dist = 35.0, 52.0, 30.0
        camera.fov = 60
        camera.clip_plane_far = 1000
        window.color = col('#8ec9f0')
        set_fog(scene, (0.66, 0.84, 0.95), 150, 320)
        self.build_grid()
        self.build_cursor()
        self.build_ui()
        self.select_asset('pine')

    def close(self):
        for e in (self.ui, self.grid, self.ghost_root, self.marker, self.block_ghost):
            destroy(e)
        if self.dialog:
            destroy(self.dialog)
        self.world.destroy()
        camera.fov = self.game.fov

    # ── scene helpers ────────────────────────────────────────────────────────
    def build_grid(self):
        h, verts, lines = self.world.half, [], []
        for i in range(-h, h + 1):
            for a, b in (((i, 0.03, -h), (i, 0.03, h)), ((-h, 0.03, i), (h, 0.03, i))):
                lines.append((len(verts), len(verts) + 1))
                verts += [Vec3(*a), Vec3(*b)]
        self.grid = Entity(model=Mesh(vertices=verts, triangles=lines, mode='line', thickness=1),
                           color=ucolor.Color(1, 1, 1, 0.13))

    def build_cursor(self):
        self.ghost_root = node()
        self.ghost_root.setTransparency(TransparencyAttrib.MAlpha)
        self.ghost_model = None
        self.marker = Entity(model='quad', rotation_x=90, color=C(TEAL, 0.35), y=0.06, shader=WORLD_SHADER)
        self.marker.setTransparency(TransparencyAttrib.MAlpha)
        self.block_ghost = Entity(model='cube', color=C(TEAL, 0.35), shader=WORLD_SHADER, enabled=False)
        self.block_ghost.setTransparency(TransparencyAttrib.MAlpha)

    def set_ghost(self, aid):
        if self.ghost_model:
            self.ghost_model.removeNode()
            self.ghost_model = None
        if aid:
            self.ghost_model = prototype(aid, 0).copyTo(self.ghost_root)

    def ground_point(self):
        """Where the mouse ray hits the ground (y = 0)."""
        base = application.base
        lens = base.camLens
        near, far = Point3(), Point3()
        fx, fy = mouse.x / (window.aspect_ratio / 2), mouse.y / 0.5
        if not lens.extrude(Point2(fx, fy), near, far):
            return None
        render = base.render
        a, b = render.getRelativePoint(base.cam, near), render.getRelativePoint(base.cam, far)
        d = b - a
        if d.y >= -1e-6:
            return None
        t = -a.y / d.y
        p = a + d * t
        return Vec3(p.x, 0, p.z)

    def over_ui(self):
        e = mouse.hovered_entity
        return e is not None and (e.has_ancestor(camera.ui) if hasattr(e, 'has_ancestor') else True)

    def interior(self, gx, gz):
        return self.world.inside(gx, gz, 1 if self.world.walls else 0)

    def brush_cells(self, p):
        gx, gz = self.world.to_grid(p.x, p.z)
        r = self.brush // 2
        return [(gx + dx, gz + dz) for dx in range(-r, r + 1) for dz in range(-r, r + 1) if self.interior(gx + dx, gz + dz)]

    # ── placing props ────────────────────────────────────────────────────────
    def placement(self, p, random_look=False):
        """(x, z, rot, scale, valid) for placing the selected asset at point p."""
        a = ASSETS[self.asset]
        if a['nature']:
            x, z = p.x, p.z
            rot = random.random() * 360 if random_look else self.rot
            scale = 0.85 + random.random() * 0.35 if random_look else 1.0
        else:
            x, z = math.floor(p.x) + 0.5, math.floor(p.z) + 0.5
            rot, scale = self.rot, 1.0
        gx0, gz0 = self.world.to_grid(x, z)
        valid = self.interior(gx0, gz0)
        for dx, dz, _ in a['solid']:
            rx, rz = rotate_cell(dx, dz, rot)
            gx, gz = gx0 + rx, gz0 + rz
            if not self.interior(gx, gz) or self.world.heights[self.world.gidx(gx, gz)] > 0:
                valid = False
        return x, z, rot, scale, valid

    def place_prop(self, p, random_look=True):
        x, z, rot, scale, valid = self.placement(p, random_look)
        if not valid:
            return False
        if ASSETS[self.asset].get('spawn') == 'player':       # only one player start
            for old in [q for q in self.world.props if ASSETS[q['id']].get('spawn') == 'player']:
                self.world.remove_prop(old)
        self.world.add_prop(self.asset, x, z, rot, scale)
        return True

    # ── actions ──────────────────────────────────────────────────────────────
    def push_undo(self):
        self.undo_stack.append(self.world.to_map(self.name))
        del self.undo_stack[:-UNDO_LIMIT]
        self.dirty = True

    def undo(self):
        if not self.undo_stack:
            self.toast('Nothing to undo')
            return
        data = self.undo_stack.pop()
        self.world.destroy()
        self.world = World(map_data=data, editor=True)
        self.game.world = self.world
        self.toast('Undone')

    def apply(self, p, first):
        """Left mouse: place / paint at p. Called on click and while dragging."""
        cell = self.world.to_grid(p.x, p.z)
        if self.eraser:
            if first or cell != self.last_cell:
                self.erase(p, everything=True)
                self.last_cell = cell
            return
        if self.category == 'paths':
            for gx, gz in self.brush_cells(p):
                self.world.set_path(gx, gz, self.path_kind)
        elif self.category == 'blocks':
            if first or cell != self.last_cell:
                for gx, gz in self.brush_cells(p):
                    self.world.set_column(gx, gz, self.block_kind, self.block_h)
                self.last_cell = cell
        else:
            a = ASSETS[self.asset]
            if a['nature']:
                spacing = SCATTER_SPACING.get(a['category'], 1.2)
                if first or self.last_scatter is None or (p - self.last_scatter).length() >= spacing:
                    jitter = Vec3((random.random() - 0.5) * 0.6, 0, (random.random() - 0.5) * 0.6)
                    if self.place_prop(p + (jitter if not first else Vec3(0, 0, 0))):
                        self.last_scatter = Vec3(p)
            elif first or (cell != self.last_cell and len(a['solid']) <= 1):
                # small props can be drawn in lines (fences, walls, hedges); big ones need a click each
                self.place_prop(p, random_look=False)
                self.last_cell = cell

    def erase(self, p, everything=False):
        cells = self.brush_cells(p)
        if everything or self.category not in ('paths', 'blocks'):
            gone = set()
            for gx, gz in cells or [self.world.to_grid(p.x, p.z)]:
                q = self.world.prop_at(gx - self.world.half + 0.5, gz - self.world.half + 0.5,
                                       radius=0.8 if self.brush == 1 else 0.5)
                if q and id(q) not in gone:
                    gone.add(id(q))
                    self.world.remove_prop(q)
            if not cells:
                q = self.world.prop_at(p.x, p.z)
                if q:
                    self.world.remove_prop(q)
        if everything or self.category == 'paths':
            for gx, gz in cells:
                self.world.set_path(gx, gz, None)
        if everything or self.category == 'blocks':
            for gx, gz in cells:
                self.world.clear_column(gx, gz)

    def save(self):
        self.name = self.name_field.text.strip() or 'My map'
        if self.stem is None or self.name != self.loaded_name:      # renamed: save as a new file
            self.stem = maps.slug(self.name)
        self.stem = maps.save_map(self.world.to_map(self.name), self.stem)
        self.loaded_name = self.name
        self.game.select_map(self.stem)
        self.dirty = False
        self.toast(f'Saved to maps/{self.stem}.json')

    def new_map(self):
        self.push_undo()
        self.stem = None
        self.name = self.loaded_name = 'My map'
        self.name_field.text = self.name
        self.world.destroy()
        self.world = World(map_data=maps.blank_map(self.name), editor=True)
        self.game.world = self.world
        self.toast('New map (Ctrl+Z brings the old one back)')

    def open_map(self, stem):
        self.close_dialog()
        self.push_undo()
        data = maps.load_map(stem)
        self.stem, self.name = stem, data.get('name', stem)
        self.loaded_name = self.name
        self.name_field.text = self.name
        self.world.destroy()
        self.world = World(map_data=data, editor=True)
        self.game.world = self.world
        self.dirty = False
        self.toast(f'Opened {self.name}')

    def play_test(self):
        self.name = self.name_field.text.strip() or 'My map'
        data = self.world.to_map(self.name)
        game = self.game
        self.close()
        game.editor = None
        game.world = World()           # placeholder; start_game replaces it
        game.start_game(map_data=data, from_editor=True)

    def exit(self):
        if self.dirty and pytime.time() - self.exit_armed > 3:
            self.exit_armed = pytime.time()
            self.toast('Unsaved changes! Press EXIT (or Esc) again to leave without saving.', RED)
            return
        self.game.close_editor()

    # ── per frame ────────────────────────────────────────────────────────────
    def typing(self):
        return self.name_field.active

    def update(self, dt):
        if self.toast_t > 0:
            self.toast_t -= dt
            if self.toast_t <= 0:
                self.toast_text.text = ''
        self.update_camera(dt)
        if self.dialog:
            self.marker.enabled = False
            self.ghost_root.hide()
            return
        p = None if self.over_ui() else self.ground_point()
        self.update_cursor(p)
        if p is not None:
            if self.painting and held_keys['left mouse']:
                self.apply(p, first=False)
            if self.erasing and held_keys['right mouse']:
                cell = self.world.to_grid(p.x, p.z)
                if cell != self.last_cell:
                    self.erase(p)
                    self.last_cell = cell
        if self.world.dirty_blocks or self.world.dirty_paths:
            self.world.flush()
        self.info_text.text = f'{len(self.world.props)} props   {len(self.world.paths)} path tiles   ' \
                              f'{len(self.world.zombie_spawns)} zombie spawns'

    def update_camera(self, dt):
        if not self.typing():
            fwd = Vec3(math.sin(math.radians(self.yaw)), 0, math.cos(math.radians(self.yaw)))
            right = Vec3(fwd.z, 0, -fwd.x)
            move = (fwd * (held_keys['w'] + held_keys['up arrow'] - held_keys['s'] - held_keys['down arrow'])
                    + right * (held_keys['d'] + held_keys['right arrow'] - held_keys['a'] - held_keys['left arrow']))
            self.pivot += move * dt * (8 + self.dist * 0.8)
            h = self.world.half
            self.pivot = Vec3(max(-h, min(h, self.pivot.x)), 0, max(-h, min(h, self.pivot.z)))
            self.yaw += (held_keys['e'] - held_keys['q']) * dt * 90
        pr, yr = math.radians(self.pitch), math.radians(self.yaw)
        f = Vec3(math.sin(yr) * math.cos(pr), -math.sin(pr), math.cos(yr) * math.cos(pr))
        camera.position = self.pivot - f * self.dist
        camera.rotation = (self.pitch, self.yaw, 0)

    def update_cursor(self, p):
        if p is None:
            self.marker.enabled = False
            self.block_ghost.enabled = False
            self.ghost_root.hide()
            return
        gx, gz = self.world.to_grid(p.x, p.z)
        cx, cz = gx - self.world.half + 0.5, gz - self.world.half + 0.5
        paint = self.category in ('paths', 'blocks') or self.eraser
        self.marker.enabled = paint
        if not paint:
            self.block_ghost.enabled = False
        if paint:
            self.ghost_root.hide()
            self.marker.position = (cx, 0.06, cz)
            self.marker.scale = (self.brush, self.brush, 1)
            self.marker.color = C(RED if self.eraser else TEAL, 0.4)
            show_block = self.category == 'blocks' and not self.eraser
            self.block_ghost.enabled = show_block
            if show_block:
                self.block_ghost.position = (cx, self.block_h / 2, cz)
                self.block_ghost.scale = (self.brush, self.block_h, self.brush)
            return
        x, z, rot, scale, valid = self.placement(p)
        self.ghost_root.show()
        self.ghost_root.setPos(x, 0, z)
        self.ghost_root.setH(-rot)
        self.ghost_root.setColorScale(0.7, 1.3, 0.8, 0.6) if valid else self.ghost_root.setColorScale(1.6, 0.4, 0.4, 0.6)

    def input(self, key):
        if self.dialog:
            if key == 'escape':
                self.close_dialog()
            return
        if self.typing():
            if key in ('enter', 'escape'):
                self.name_field.active = False
                self.name = self.name_field.text.strip() or 'My map'
            return
        ctrl = held_keys['control'] or held_keys['left control'] or held_keys['right control']
        if key in ('control+z', 'ctrl+z') or (key == 'z' and ctrl):
            self.undo()
            return
        if key == 'left mouse down' and not self.over_ui():
            p = self.ground_point()
            if p is not None:
                self.push_undo()
                self.painting = True
                self.last_cell = self.last_scatter = None
                self.apply(p, first=True)
        elif key == 'left mouse up':
            self.painting = False
        elif key == 'right mouse down' and not self.over_ui():
            p = self.ground_point()
            if p is not None:
                self.push_undo()
                self.erasing = True
                self.last_cell = self.world.to_grid(p.x, p.z)
                self.erase(p)
        elif key == 'right mouse up':
            self.erasing = False
        elif key == 'r':
            self.rot = (self.rot + 90) % 360
            self.refresh_options()
        elif key == 'scroll up':
            self.dist = max(6, self.dist * 0.88)
        elif key == 'scroll down':
            self.dist = min(80, self.dist / 0.88)
        elif key in ('[', ']'):
            sizes = [1, 3, 5]
            i = sizes.index(self.brush) + (1 if key == ']' else -1)
            self.brush = sizes[max(0, min(2, i))]
            self.refresh_options()
        elif key in ('1', '2', '3', '4'):
            self.block_h = int(key)
            self.refresh_options()
        elif key == 'escape':
            self.exit()

    # ── UI ───────────────────────────────────────────────────────────────────
    def toast(self, msg, colour=TEAL):
        self.toast_text.text = msg
        self.toast_text.color = C(colour)
        self.toast_t = 3.5

    def build_ui(self):
        a = window.aspect_ratio
        L, R = -a / 2, a / 2
        self.ui = Entity(parent=camera.ui, z=-0.5)
        u = self.ui
        # top bar
        Entity(parent=u, model='quad', color=C(INK), position=(0, 0.465, 0.02), scale=(a, 0.07), collider='box')
        text(u, 'MAP EDITOR', L + 0.03, 0.465, 1.4, PAPER, origin=(-0.5, 0))
        text(u, 'Name', L + 0.3, 0.465, 0.9, MUTED, origin=(-0.5, 0))
        self.name_field = InputField(default_value=self.name, text=self.name, parent=u, position=(L + 0.53, 0.465, -0.01),
                                     scale=(0.32, 0.045), character_limit=28, color=C(PAPER))
        self.name_field.text_color = C(INK)          # (Ursina ignores text_color in the constructor)
        self.name_field.highlight_color = C(PAPER).tint(-0.06)
        x = R - 0.03
        for label, fn, fill, w in (('EXIT', self.exit, SLATE, 0.12), ('PLAY TEST', self.play_test, TEAL, 0.18),
                                   ('SAVE', self.save, GREEN, 0.12), ('OPEN', self.open_dialog, SLATE, 0.12),
                                   ('NEW', self.new_map, SLATE, 0.12)):
            x -= w
            FlatButton(u, label, x, 0.49, w, 0.05, fn, fill=fill, edge=INK, size=0.95)
            x -= 0.012
        # palette
        self.panel_x, self.panel_w = L + 0.015, 0.36
        Entity(parent=u, model='quad', color=C(INK), position=(self.panel_x + self.panel_w / 2, 0.005, 0.02),
               scale=(self.panel_w, 0.82), collider='box')
        box(u, self.panel_x + EDGE, 0.415 - EDGE, self.panel_w - 2 * EDGE, 0.82 - 2 * EDGE, PAPER, z=0.01)
        self.palette = Entity(parent=u)
        # bottom bar
        Entity(parent=u, model='quad', color=C(INK), position=(0, -0.478, 0.02), scale=(a, 0.045), collider='box')
        text(u, 'LMB place / drag   RMB erase   R turn   [ ] brush   1-4 block height   WASD move   Q E turn view   '
                'wheel zoom   Ctrl+Z undo', L + 0.03, -0.478, 0.78, PAPER, origin=(-0.5, 0))
        self.info_text = text(u, '', R - 0.03, -0.478, 0.78, MUTED, origin=(0.5, 0))
        self.toast_text = text(u, '', 0, 0.405, 1.1, TEAL, origin=(0, 0))
        self.refresh_palette()

    def select_category(self, cat):
        self.category = cat
        self.eraser = False
        if cat not in ('paths', 'blocks'):
            first = next(k for k, a in ASSETS.items() if a['category'] == cat)
            self.select_asset(first)
        else:
            self.set_ghost(None)
            self.refresh_palette()

    def select_asset(self, aid):
        self.asset = aid
        self.category = ASSETS[aid]['category']
        self.eraser = False
        self.set_ghost(aid)
        self.refresh_palette()

    def pick_tile(self, kind):
        if self.category == 'paths':
            self.path_kind = kind
        else:
            self.block_kind = kind
        self.eraser = False
        self.refresh_palette()

    def toggle_eraser(self):
        self.eraser = not self.eraser
        self.refresh_palette()

    def refresh_palette(self):
        for c in list(self.palette.children):
            destroy(c)
        p, x0 = self.palette, self.panel_x + 0.02
        w = self.panel_w - 0.04
        y = 0.39
        for i, (cid, cname) in enumerate(ASSET_CATEGORIES):
            on = cid == self.category and not self.eraser
            FlatButton(p, cname, x0 + (i % 2) * (w / 2 + 0.004), y - (i // 2) * 0.047, w / 2 - 0.004, 0.04,
                       lambda c=cid: self.select_category(c), fill=INK if on else PAPER, edge=INK,
                       fg=PAPER if on else INK, size=0.85, hover=0.15 if on else -0.06)
        FlatButton(p, 'ERASER', x0 + (w / 2 + 0.004), y - 3 * 0.047, w / 2 - 0.004, 0.04, self.toggle_eraser,
                   fill=RED if self.eraser else PAPER, edge=INK, fg=PAPER if self.eraser else INK, size=0.85,
                   hover=0.12 if self.eraser else -0.06)
        y -= 4 * 0.047 + 0.012
        if self.category == 'paths':
            items = [(k, n, self.path_kind == k) for k, n in PATHS.items()]
            pick = self.pick_tile
        elif self.category == 'blocks':
            items = [(k, n, self.block_kind == k) for k, n in BLOCKS.items()]
            pick = self.pick_tile
        else:
            items = [(k, a['name'], self.asset == k) for k, a in ASSETS.items() if a['category'] == self.category]
            pick = self.select_asset
        for k, name, on in items:
            on = on and not self.eraser
            FlatButton(p, name, x0, y, w, 0.04, lambda k=k: pick(k), fill=INK if on else PAPER,
                       edge=INK if on else LINE, fg=PAPER if on else INK, size=0.88, align='left', hover=0.15 if on else -0.06)
            y -= 0.046
        self.options_y = y - 0.01
        self.options = Entity(parent=self.palette)
        self.refresh_options()

    def refresh_options(self):
        for c in list(self.options.children):
            destroy(c)
        o, x0, y = self.options, self.panel_x + 0.02, self.options_y
        w = self.panel_w - 0.04
        box(o, x0, y + 0.006, w, 0.004, LINE)
        y -= 0.02
        if self.eraser or self.category in ('paths', 'blocks'):
            text(o, 'Brush  ( [ ] )', x0, y, 0.85, MUTED)
            for i, s in enumerate((1, 3, 5)):
                on = self.brush == s
                FlatButton(o, f'{s}x{s}', x0 + 0.15 + i * 0.065, y + 0.008, 0.06, 0.036,
                           lambda s=s: (setattr(self, 'brush', s), self.refresh_options()),
                           fill=INK if on else PAPER, edge=INK, fg=PAPER if on else INK, size=0.75)
            y -= 0.05
        if self.category == 'blocks' and not self.eraser:
            text(o, 'Height  ( 1-4 )', x0, y, 0.85, MUTED)
            for i in range(4):
                on = self.block_h == i + 1
                FlatButton(o, str(i + 1), x0 + 0.15 + i * 0.049, y + 0.008, 0.044, 0.036,
                           lambda h=i + 1: (setattr(self, 'block_h', h), self.refresh_options()),
                           fill=INK if on else PAPER, edge=INK, fg=PAPER if on else INK, size=0.75)
            y -= 0.05
        if not self.eraser and self.category not in ('paths', 'blocks'):
            a = ASSETS[self.asset]
            if a['nature']:
                text(o, 'Hold and drag to scatter.\nEach one gets a random turn and size.', x0, y, 0.78, MUTED)
            else:
                text(o, f'Turn: {self.rot}°   (press R)', x0, y, 0.85, MUTED)
                FlatButton(o, '', x0 + w - 0.05, y + 0.012, 0.05, 0.04, lambda: self.input('r'), fill=SLATE,
                           edge=INK, icon_name='arrow_up')
                if len(a['solid']) <= 1:
                    text(o, 'Drag to draw a line.', x0, y - 0.035, 0.78, MUTED)
            if a.get('spawn') == 'zombie':
                text(o, 'Zombies climb out of these graves.\nNo graves = they come over the walls.',
                     x0, y - 0.07, 0.75, TEAL)
            elif a.get('spawn') == 'player':
                text(o, 'Where you start. Only one per map.', x0, y - 0.07, 0.75, TEAL)

    def open_dialog(self):
        self.dialog = Entity(parent=camera.ui, z=-0.8)
        Entity(parent=self.dialog, model='quad', color=C(INK, 0.55), scale=(4, 1), z=0.05, collider='box')
        win = Window(self.dialog, 'OPEN MAP', w=0.8, h=0.7, top=0.33)
        y = win.top
        found = maps.list_maps()
        if not found:
            text(win.body, 'No saved maps yet. Press SAVE to save this one.', win.left, y, 1.0, MUTED)
        for stem, name in found[:9]:
            FlatButton(win.body, name, win.left, y, 0.68, 0.05, lambda s=stem: self.open_map(s), fill=PAPER, edge=LINE,
                       fg=INK, align='left', right=f'{stem}.json', hover=-0.06, size=1.0)
            y -= 0.058
        win.bottom_right('CANCEL', self.close_dialog, w=0.2)

    def close_dialog(self):
        if self.dialog:
            destroy(self.dialog)
            self.dialog = None
