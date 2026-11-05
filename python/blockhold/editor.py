"""The map editor.

Controls
  Left click / drag     place the selected thing (drag paints paths, draws fences, scatters trees)
  Right click / drag    erase
  R                     turn buildings and props 90°
  Z / X                 turn 15° (hold Shift: 1°)      T / G  tilt      Y / H  roll
  Ctrl+click            pick a placed thing to turn it (Delete removes it, Esc lets go)
  [  ]                  brush size (paths, blocks, eraser): 1, 3, 5, 9 or 15 cells
  1 - 4                 block height
  W A S D / arrows      move the camera     Q / E  turn it     mouse wheel  zoom
  Ctrl+Z                undo
  Esc                   leave the editor
"""
import math
import random
import time as pytime
from panda3d.core import Point2, Point3, TransparencyAttrib
from ursina import Entity, InputField, Mesh, Vec3, application, camera, color as ucolor, held_keys, mouse, scene, window
from . import maps
from .data.assets import ASSETS, ASSET_CATEGORIES, BLOCKS, PATHS
from .render import WORLD_SHADER, col, node, set_fog, destroy
from .ui import (AMBER, BTN_H, EDGE, GREEN, FlatSlider, INK, LINE, MUTED, NAVY, PAPER, RED, SLATE, TEAL, C, FlatButton, Window, box,
                 frame, glyph, text)
from .world import MAX_SIZE, MIN_SIZE, World, prototype, rotate_cell, set_prop_turn

SCATTER_SPACING = {'trees': 2.6, 'shrubs': 1.1, 'props': 1.2}
UNDO_LIMIT = 40
BRUSHES = [1, 3, 5, 9, 15]
TOOLS = ('paths', 'blocks', 'caves')        # palette tabs that are tools rather than assets
CAVE_LIMITS = dict(depth=(8, 120, 4), width=(2, 7, 1), height=(3, 7, 1), branches=(0, 5, 1))
ROW = 0.044                    # palette row height


class Editor:
    def __init__(self, game, map_data=None, stem=None):
        self.game = game
        data = map_data or maps.blank_map()
        self.stem = stem
        self.name = data.get('name', 'My map')
        self.loaded_name = self.name
        self.world = None
        self.grid = None
        self.page = 0
        self.dlg = dict(size=34, walls=True, fill='empty')
        self.cave = dict(depth=30, width=3, height=4, branches=1, extras=True)
        self.category, self.asset = 'trees', 'pine'
        self.path_kind, self.block_kind = 'dirt', 'stone'
        self.rot = 0           # how the next thing you place is turned (any angle), tilted and rolled
        self.tilt = 0
        self.roll = 0
        self.selected = None   # a placed prop picked with Ctrl+click, to turn it after placing
        self.rot_panel = None
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
        self.npc_panel = None   # the NPC editor (npc_editor.py) while it's open
        self.pivot = Vec3(0, 0, 0)
        self.yaw, self.pitch, self.dist = 35.0, 52.0, 30.0
        camera.fov = 60
        self.use_world(data)
        sp = self.world.player_spawn
        self.pivot = Vec3(sp.x, 0, sp.z)
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
    def use_world(self, data):
        """Show a map (new, opened, undone or resized): rebuild the world, the grid and the view."""
        if self.world is not None:
            self.world.destroy()
        self.selected = None
        self.world = World(map_data=data, editor=True)
        self.game.world = self.world
        self.build_grid()
        self.game.sky_dome.set_arena(self.world.half)
        self.game.apply_sky(instant=True)          # the fog reaches further on big maps
        h = self.world.half
        self.pivot = Vec3(max(-h, min(h, self.pivot.x)), 0, max(-h, min(h, self.pivot.z)))
        if getattr(self, 'ui', None) is not None:
            self.refresh_rot_panel()

    def max_zoom(self):
        return max(80, self.world.half * 1.7)

    def build_grid(self):
        if self.grid is not None:
            destroy(self.grid)
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
        q = self.world.add_prop(self.asset, x, z, rot, scale, self.tilt, self.roll)
        if q is not None and (ASSETS[self.asset].get('npc') or ASSETS[self.asset].get('fields')) \
                and ASSETS[self.asset].get('spawn') != 'zombie':     # a new NPC or zone: open its settings straight away
            self.painting = False
            self.open_npc_panel(q)
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
        self.use_world(data)
        self.toast('Undone')

    def apply(self, p, first):
        """Left mouse: place / paint at p. Called on click and while dragging."""
        cell = self.world.to_grid(p.x, p.z)
        if self.eraser:
            if first or cell != self.last_cell:
                self.erase(p, everything=True)
                self.last_cell = cell
            return
        if self.category == 'caves':
            if first:
                c = self.cave
                info = self.world.make_cave(p.x, p.z, c['depth'], c['width'], c['height'], c['branches'], c['extras'])
                if info.get('cells'):
                    self.toast(f"Dug a cave: {info['length']} m deep, {info['tunnels']} tunnel(s). "
                               'Ctrl+Z to try again for a different one.')
                else:
                    self.toast('No room for a cave there', RED)
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
            elif first or (cell != self.last_cell and len(a['solid']) <= 1 and not a.get('npc') and not a.get('zone')):
                # small props can be drawn in lines (fences, walls, hedges); big ones need a click each
                self.place_prop(p, random_look=False)
                self.last_cell = cell

    def erase(self, p, everything=False):
        cells = self.brush_cells(p)
        if everything or self.category not in TOOLS:
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
        """Make the map the NEW dialog describes: its size, walls, and empty or a random arena to start from."""
        d = self.dlg
        self.close_dialog()
        self.push_undo()
        self.stem = None
        self.name = self.loaded_name = 'My map'
        self.name_field.text = self.name
        if d['fill'] == 'random':
            self.toast('Building a random arena...')
            tmp = World(editor=True, size=d['size'])
            data = tmp.to_map(self.name)
            tmp.destroy()
            data['props'].append(['player_spawn', 0.5, 0.5, 0, 1])
        else:
            data = maps.blank_map(self.name, d['size'])
        data['walls'] = d['walls']
        self.use_world(data)
        self.pivot = Vec3(0, 0, 0)
        self.toast(f"New map: {maps.size_label(self.world.half)}  (Ctrl+Z brings the old one back)")

    def resize_map(self):
        """Change the size of this map. Everything stays centred; what falls outside is removed."""
        half = self.dlg['size']
        self.close_dialog()
        if half == self.world.half:
            return
        self.push_undo()
        data = self.world.to_map(self.name)
        data['size'] = half
        edge = half - (1 if data.get('walls', True) else 0)
        before = len(data['props'])
        data['props'] = [q for q in data['props'] if abs(q[1]) < edge and abs(q[2]) < edge]
        self.use_world(data)
        lost = before - len(data['props'])
        self.toast(f"Resized to {maps.size_label(half)}" + (f'  ({lost} objects outside were removed)' if lost else ''))

    def open_map(self, stem):
        self.close_dialog()
        self.push_undo()
        data = maps.load_map(stem)
        self.stem, self.name = stem, data.get('name', stem)
        self.loaded_name = self.name
        self.name_field.text = self.name
        self.use_world(data)
        self.dirty = False
        self.toast(f'Opened {self.name}  ({maps.size_label(self.world.half)})')

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
        return self.name_field.active or (self.npc_panel is not None and self.npc_panel.typing())

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
        info = f'{self.world.n} x {self.world.n} m   {len(self.world.props)} props   {len(self.world.paths)} path tiles   ' \
               f'{len(self.world.zombie_spawns)} zombie spawns'
        if self.info_text.text != info:
            self.info_text.text = info

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
        if self.category == 'caves' and not self.eraser:     # where the cave entrance will be
            self.ghost_root.hide()
            self.block_ghost.enabled = False
            self.marker.enabled = True
            self.marker.position = (cx, 0.06, cz)
            self.marker.scale = (self.cave['width'] + 1, self.cave['width'] + 1, 1)
            self.marker.color = C(AMBER, 0.45)
            return
        paint = self.category in TOOLS or self.eraser
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
        self.ghost_root.setHpr(-rot, self.tilt, self.roll)
        self.ghost_root.setColorScale(0.7, 1.3, 0.8, 0.6) if valid else self.ghost_root.setColorScale(1.6, 0.4, 0.4, 0.6)

    def input(self, key):
        if self.npc_panel is not None:
            if key == 'escape' and not self.npc_panel.typing():
                self.npc_panel.done()
            return
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
        if key == 'left mouse down' and not self.over_ui() and ctrl:      # Ctrl+click: pick a placed thing
            p = self.ground_point()
            q = self.world.prop_at(p.x, p.z) if p is not None else None
            self.select(q)
            return
        if key == 'left mouse down' and not self.over_ui():
            p = self.ground_point()
            if p is not None:
                self.select(None)
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
            self.turn(90, 0, 0, snap=True)
        elif key in ('z', 'x', 'shift+z', 'shift+x'):    # turn 15° (Shift: 1°)
            step = 1 if key.startswith('shift') or held_keys['shift'] or held_keys['left shift'] else 15
            self.turn(step if key.endswith('x') else -step, 0, 0)
        elif key in ('t', 'g'):                          # tilt forward / back
            self.turn(0, 15 if key == 't' else -15, 0)
        elif key in ('y', 'h'):                          # roll left / right
            self.turn(0, 0, 15 if key == 'y' else -15)
        elif key == 'n' and self.selected is not None and self.selected.get('data') is not None:
            self.open_npc_panel(self.selected)
        elif key == 'delete' and self.selected is not None:
            self.push_undo()
            self.world.remove_prop(self.selected)
            self.selected = None
            self.refresh_rot_panel()
            self.toast('Deleted')
        elif key == 'scroll up':
            self.dist = max(6, self.dist * 0.88)
        elif key == 'scroll down':
            self.dist = min(self.max_zoom(), self.dist / 0.88)
        elif key in ('[', ']'):
            i = BRUSHES.index(self.brush) + (1 if key == ']' else -1)
            self.brush = BRUSHES[max(0, min(len(BRUSHES) - 1, i))]
            self.refresh_options()
        elif key in ('1', '2', '3', '4'):
            self.block_h = int(key)
            self.refresh_options()
        elif key == 'escape':
            if self.selected is not None:
                self.select(None)
            else:
                self.exit()

    # ── turning (any angle, tilt and roll) ──────────────────────────────────
    def turn_values(self):
        q = self.selected
        if q is not None:
            return q['rot'], q.get('tilt', 0), q.get('roll', 0)
        return self.rot, self.tilt, self.roll

    def set_turn(self, rot, tilt, roll):
        """Set the turn of the picked prop, or of the next thing you place."""
        rot, tilt, roll = rot % 360, max(-90, min(90, tilt)), max(-180, min(180, roll))
        if self.selected is not None:
            set_prop_turn(self.selected, rot, tilt, roll, self.world)
            self.dirty = True
        else:
            self.rot, self.tilt, self.roll = rot, tilt, roll

    def turn(self, d_rot, d_tilt, d_roll, snap=False):
        rot, tilt, roll = self.turn_values()
        if snap:
            rot = (round(rot / 90) * 90 + d_rot) % 360
        else:
            rot += d_rot
        self.set_turn(rot, tilt + d_tilt, roll + d_roll)
        self.refresh_rot_panel()

    def select(self, q):
        if self.selected is not None and self.selected.get('np') is not None:
            self.selected['np'].clearColorScale()
        self.selected = q
        if q is not None:
            self.push_undo()                  # Ctrl+Z puts it back the way it was
            if q.get('np') is not None:
                q['np'].setColorScale(1.25, 1.25, 0.7, 1)
            self.toast(f"Picked {ASSETS[q['id']]['name']}: turn it with the panel, Delete removes it, Esc lets go")
        self.refresh_rot_panel()

    def refresh_rot_panel(self):
        """The ROTATION panel on the right: for the picked prop, or for what you place next."""
        if self.rot_panel is not None:
            destroy(self.rot_panel)
            self.rot_panel = None
        placing = self.category not in TOOLS and not self.eraser
        if self.selected is None and not placing:
            return
        a = window.aspect_ratio
        x0, w, top = a / 2 - 0.38, 0.36, 0.415
        p = self.rot_panel = Entity(parent=self.ui)
        Entity(parent=p, model='quad', color=C(INK), position=(x0 + w / 2, top - 0.17, 0.02), scale=(w, 0.34),
               collider='box')
        box(p, x0 + EDGE, top - EDGE, w - 2 * EDGE, 0.34 - 2 * EDGE, PAPER, z=0.01)
        name = ASSETS[self.selected['id']]['name'] if self.selected is not None else ASSETS[self.asset]['name']
        text(p, 'ROTATION', x0 + 0.02, top - 0.02, 0.9, MUTED)
        text(p, ('Picked: ' if self.selected is not None else 'Next: ') + name, x0 + 0.02, top - 0.05, 0.75,
             TEAL if self.selected is not None else INK)
        rot, tilt, roll = self.turn_values()
        sw = 0.2
        FlatSlider(p, x0 + 0.02, top - 0.085, sw, 'Turn', 0, 359, round(rot), lambda v: f'{v}°',
                   lambda v: self.set_turn(v, *self.turn_values()[1:]))
        FlatSlider(p, x0 + 0.02, top - 0.155, sw, 'Tilt', -90, 90, round(tilt), lambda v: f'{v}°',
                   lambda v: self.set_turn(self.turn_values()[0], v, self.turn_values()[2]))
        FlatSlider(p, x0 + 0.02, top - 0.225, sw, 'Roll', -180, 180, round(roll), lambda v: f'{v}°',
                   lambda v: self.set_turn(*self.turn_values()[:2], v))
        by = top - 0.29
        for i, (label, fn) in enumerate((('-15°', lambda: self.turn(-15, 0, 0)), ('+15°', lambda: self.turn(15, 0, 0)),
                                         ('90°', lambda: self.turn(90, 0, 0, snap=True)),
                                         ('RESET', lambda: (self.set_turn(0, 0, 0), self.refresh_rot_panel())))):
            FlatButton(p, label, x0 + 0.02 + i * 0.082, by, 0.076, 0.036, fn, fill=SLATE, edge=INK, size=0.72)
        if self.selected is not None and self.selected.get('data') is not None:
            q = self.selected
            label = f"EDIT NPC  (N):  {q['data']['name']}" if ASSETS[q['id']].get('npc') else 'EDIT SETTINGS  (N)'
            FlatButton(p, label, x0, top - 0.35, w, 0.05, lambda: self.open_npc_panel(q), fill=GREEN, edge=INK, size=0.8)

    # ── NPCs ─────────────────────────────────────────────────────────────────
    def open_npc_panel(self, q):
        """The settings panel for a placed thing: the NPC editor, or the settings of a zone / grave."""
        self.close_npc_panel()
        self.push_undo()
        if not ASSETS[q['id']].get('npc'):
            from .prop_editor import PropPanel
            self.npc_panel = PropPanel(self, q)
            self.dialog = self.npc_panel.root
            if self.rot_panel is not None:
                destroy(self.rot_panel)
                self.rot_panel = None
            r = q['data'].get('radius', 6)                    # step back far enough to see the whole zone
            self.pivot = Vec3(q['x'] - r * 0.5, 0, q['z'])
            self.dist = max(self.dist, min(self.max_zoom(), r * 2.6 + 8))
            return
        from .npc_editor import NpcEditor
        self.npc_panel = NpcEditor(self, q)
        self.dialog = self.npc_panel.root
        # look at the NPC's face, with them on the right of the screen (the panel covers the left)
        self.yaw = (q['rot'] + 180) % 360
        self.pitch, self.dist = 8.0, 10.0
        yr = math.radians(self.yaw)
        right = Vec3(math.cos(yr), 0, -math.sin(yr))
        fwd = Vec3(math.sin(yr), 0, math.cos(yr))
        self.pivot = Vec3(q['x'], 0, q['z']) - right * 3.2 + fwd * 1.0
        if self.rot_panel is not None:                  # (it's back when the NPC panel closes)
            destroy(self.rot_panel)
            self.rot_panel = None

    def close_npc_panel(self):
        if self.npc_panel is not None:
            self.npc_panel.destroy()
            self.npc_panel = None
            self.dialog = None
            self.dirty = True
            self.refresh_rot_panel()

    def refresh_prop_visual(self, q):
        """Redraw a placed thing after its settings changed (an NPC's look, a zone's ring)."""
        if ASSETS[q['id']].get('npc'):
            self.refresh_npc_model(q)
        elif ASSETS[q['id']].get('zone'):
            self.world.draw_ring(q)
        self.dirty = True

    def refresh_npc_model(self, q):
        """Show an NPC in the map the way their settings say."""
        from .npcs import npc_model
        if q.get('np') is None:
            return
        for child in q['np'].getChildren():
            child.removeNode()
        npc_model(q['data']).reparentTo(q['np'])

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
                                   ('SIZE', lambda: self.size_dialog('resize'), SLATE, 0.12),
                                   ('NEW', lambda: self.size_dialog('new'), SLATE, 0.12)):
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
        text(u, 'LMB place   RMB erase   R 90°  Z X turn  T G tilt  Y H roll   Ctrl+click pick   [ ] brush   1-4 height   '
                'WASD Q E view   wheel zoom   Ctrl+Z undo', L + 0.03, -0.478, 0.72, PAPER, origin=(-0.5, 0))
        self.info_text = text(u, '', R - 0.03, -0.478, 0.78, MUTED, origin=(0.5, 0))
        self.toast_text = text(u, '', 0, 0.405, 1.1, TEAL, origin=(0, 0))
        self.refresh_palette()

    def select_category(self, cat):
        self.category = cat
        self.page = 0
        self.eraser = False
        if cat not in TOOLS:
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
        cats = list(ASSET_CATEGORIES) + [('eraser', 'ERASER')]
        cw = (w - 0.008) / 3
        for i, (cid, cname) in enumerate(cats):
            bx, by = x0 + (i % 3) * (cw + 0.004), y - (i // 3) * 0.045
            if cid == 'eraser':
                FlatButton(p, cname, bx, by, cw, 0.039, self.toggle_eraser, fill=RED if self.eraser else PAPER,
                           edge=INK, fg=PAPER if self.eraser else INK, size=0.72, hover=0.12 if self.eraser else -0.06)
                continue
            on = cid == self.category and not self.eraser
            FlatButton(p, cname, bx, by, cw, 0.039, lambda c=cid: self.select_category(c), fill=INK if on else PAPER,
                       edge=INK, fg=PAPER if on else INK, size=0.72 if len(cname) <= 10 else 0.58,
                       hover=0.15 if on else -0.06)
        y -= ((len(cats) + 2) // 3) * 0.045 + 0.012
        if self.category == 'paths':
            items = [(k, n, self.path_kind == k) for k, n in PATHS.items()]
            pick = self.pick_tile
        elif self.category == 'blocks':
            items = [(k, n, self.block_kind == k) for k, n in BLOCKS.items()]
            pick = self.pick_tile
        elif self.category == 'caves':
            self.cave_settings(p, x0, y, w)
            self.options_y = -0.25 - 0.05
            self.options = Entity(parent=self.palette)
            return
        else:
            items = [(k, a['name'], self.asset == k) for k, a in ASSETS.items() if a['category'] == self.category]
            pick = self.select_asset
        # two columns, and pages when a category has more than fits
        bottom = -0.25
        rows = max(1, int((y - bottom) / ROW))
        per = rows * 2
        pages = max(1, -(-len(items) // per))
        self.page = max(0, min(self.page, pages - 1))
        iw = (w - 0.006) / 2
        for i, (k, name, on) in enumerate(items[self.page * per:(self.page + 1) * per]):
            on = on and not self.eraser
            FlatButton(p, name, x0 + (i % 2) * (iw + 0.006), y - (i // 2) * ROW, iw, 0.039, lambda k=k: pick(k),
                       fill=INK if on else PAPER, edge=INK if on else LINE, fg=PAPER if on else INK, size=0.7,
                       align='left', hover=0.15 if on else -0.06)
        if pages > 1:
            py = bottom - 0.004
            FlatButton(p, 'PREV', x0, py, 0.08, 0.036, lambda: self.turn_page(-1), fill=SLATE, edge=INK, size=0.7)
            text(p, f'page {self.page + 1} / {pages}', x0 + w / 2, py - 0.018, 0.75, MUTED, origin=(0, 0))
            FlatButton(p, 'NEXT', x0 + w - 0.08, py, 0.08, 0.036, lambda: self.turn_page(1), fill=SLATE, edge=INK, size=0.7)
        self.options_y = bottom - 0.05
        self.options = Entity(parent=self.palette)
        self.refresh_options()

    def cave_settings(self, p, x0, y, w):
        """The Caves tab: what the next cave you click will look like."""
        c = self.cave

        def change(key, step):
            lo, hi, _ = CAVE_LIMITS[key]
            c[key] = max(lo, min(hi, c[key] + step))
            self.refresh_palette()
        rows = (('depth', 'Depth', 'm'), ('width', 'Width', 'm'), ('height', 'Rock height', 'm'),
                ('branches', 'Side tunnels', ''))
        for key, label, unit in rows:
            step = CAVE_LIMITS[key][2]
            text(p, label, x0, y - 0.012, 0.85, INK)
            FlatButton(p, '-', x0 + w - 0.2, y, 0.045, 0.036, lambda k=key, s=step: change(k, -s), fill=SLATE, edge=INK)
            text(p, f'{c[key]} {unit}'.strip(), x0 + w - 0.105, y - 0.018, 0.9, TEAL, origin=(0, 0))
            FlatButton(p, '+', x0 + w - 0.045, y, 0.045, 0.036, lambda k=key, s=step: change(k, s), fill=SLATE, edge=INK)
            y -= 0.05
        text(p, 'Lanterns, ore, crate, grave', x0, y - 0.012, 0.75, INK)
        on = c['extras']
        FlatButton(p, 'ON' if on else 'OFF', x0 + w - 0.09, y, 0.09, 0.036,
                   lambda: (c.__setitem__('extras', not c['extras']), self.refresh_palette()),
                   fill=TEAL if on else NAVY, edge=INK, size=0.8)
        y -= 0.065
        text(p, 'Click on the map to dig a cave. The entrance is where you click; the tunnels wind '
                'into a rock hill with a roof you walk under. Ctrl+Z and click again for a different one. '
                'Erase parts of it with the ERASER.', x0, y, 0.72, MUTED, wordwrap=36)

    def turn_page(self, step):
        self.page += step
        self.refresh_palette()

    def refresh_options(self):
        for c in list(self.options.children):
            destroy(c)
        if self.category == 'caves' and not self.eraser:
            return
        o, x0, y = self.options, self.panel_x + 0.02, self.options_y
        w = self.panel_w - 0.04
        box(o, x0, y + 0.006, w, 0.004, LINE)
        y -= 0.02
        if self.eraser or self.category in TOOLS:
            text(o, 'Brush  [ ]', x0, y, 0.85, MUTED)
            for i, s in enumerate(BRUSHES):
                on = self.brush == s
                FlatButton(o, str(s), x0 + 0.11 + i * 0.043, y + 0.008, 0.04, 0.036,
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
        if not self.eraser and self.category not in TOOLS:
            a = ASSETS[self.asset]
            if a['nature']:
                text(o, 'Hold and drag to scatter.\nEach one gets a random turn and size.', x0, y, 0.78, MUTED)
            else:
                text(o, 'Turn it with the ROTATION panel\n(R = 90°, Z / X = 15°).', x0, y, 0.78, MUTED)
                if len(a['solid']) <= 1:
                    text(o, 'Drag to draw a line.', x0, y - 0.035, 0.78, MUTED)
            if a.get('spawn') == 'zombie':
                text(o, 'Zombies climb out of these graves.\nNo graves = they come over the walls.',
                     x0, y - 0.07, 0.75, TEAL)
            elif a.get('spawn') == 'player':
                text(o, 'Where you start. Only one per map.', x0, y - 0.07, 0.75, TEAL)
        self.refresh_rot_panel()

    def size_dialog(self, mode):
        """NEW: pick a size, walls and what to start with. SIZE: change the size of this map."""
        if self.dialog is None and mode == 'resize':      # opening it: start from this map's size
            self.dlg['size'] = self.world.half
        self.close_dialog()
        d = self.dlg
        self.dialog = Entity(parent=camera.ui, z=-0.8)
        Entity(parent=self.dialog, model='quad', color=C(INK, 0.55), scale=(4, 1), z=0.05, collider='box')
        win = Window(self.dialog, 'NEW MAP' if mode == 'new' else 'MAP SIZE', w=0.86, h=0.62, top=0.3)
        b, x, y = win.body, win.left, win.top
        redo = lambda: self.size_dialog(mode)

        def setv(key, value):
            d[key] = value
            redo()
        text(b, 'SIZE', x, y, 0.85, MUTED)
        y -= 0.035
        for i, (label, half) in enumerate(maps.MAP_SIZES):
            on = d['size'] == half
            FlatButton(b, label, x + i * 0.148, y, 0.14, 0.05, lambda h=half: setv('size', h),
                       fill=INK if on else PAPER, edge=INK, fg=PAPER if on else INK, size=0.95, hover=0.15 if on else -0.06)
        y -= 0.075
        FlatButton(b, '-', x, y, 0.06, 0.045, lambda: setv('size', max(MIN_SIZE, d['size'] - 4)), fill=SLATE, edge=INK)
        text(b, f"{d['size'] * 2} x {d['size'] * 2} m", x + 0.17, y - 0.022, 1.3, INK, origin=(0, 0))
        FlatButton(b, '+', x + 0.28, y, 0.06, 0.045, lambda: setv('size', min(MAX_SIZE, d['size'] + 4)), fill=SLATE, edge=INK)
        text(b, f'{MIN_SIZE * 2} to {MAX_SIZE * 2} m across, in 8 m steps', x + 0.37, y - 0.022, 0.8, MUTED, origin=(-0.5, 0))
        y -= 0.08
        if mode == 'new':
            text(b, 'WALLS', x, y, 0.85, MUTED)
            text(b, 'START WITH', x + 0.3, y, 0.85, MUTED)
            y -= 0.035
            for i, (label, val) in enumerate((('On', True), ('Off', False))):
                on = d['walls'] == val
                FlatButton(b, label, x + i * 0.11, y, 0.1, 0.045, lambda v=val: setv('walls', v),
                           fill=INK if on else PAPER, edge=INK, fg=PAPER if on else INK, size=0.9)
            for i, (label, val) in enumerate((('Empty ground', 'empty'), ('Random arena', 'random'))):
                on = d['fill'] == val
                FlatButton(b, label, x + 0.3 + i * 0.2, y, 0.19, 0.045, lambda v=val: setv('fill', v),
                           fill=INK if on else PAPER, edge=INK, fg=PAPER if on else INK, size=0.9)
            y -= 0.07
            note = ('Huge maps take a few seconds to build. Zombies come out of graves near you, '
                    'or out of the ground around you if there are none close.') if d['size'] > 48 else \
                   'A random arena gives you trees, ruins, tracks and workbenches to edit.'
        else:
            note = (f'Now {self.world.n} x {self.world.n} m. Everything stays centred; '
                    'anything outside the new size is removed (Ctrl+Z undoes it).')
        text(b, note, x, y, 0.8, MUTED, wordwrap=80)
        FlatButton(b, 'CANCEL', x, win.btn_y, 0.2, BTN_H, self.close_dialog, fill=SLATE, edge=INK)
        FlatButton(b, 'CREATE' if mode == 'new' else 'RESIZE', win.x + win.w - 0.06 - 0.24, win.btn_y, 0.24, BTN_H,
                   self.new_map if mode == 'new' else self.resize_map, fill=GREEN, edge=INK)

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
        if self.npc_panel is not None:
            self.close_npc_panel()
            return
        if self.dialog:
            destroy(self.dialog)
            self.dialog = None
