"""Barricades: crafted at a workbench, then placed in build mode (G).

Each barricade belongs to the player who placed it (its kills earn that player
coins), has a network id, and is solid on the map grid (except landmines).
Zombies walk around barricades when they can and smash through when they can't
(see FlowField in enemies.py). Spikes hurt zombies that push against them,
landmines blow up under zombies, and sentry turrets shoot by themselves.
Events: barricade_placed, barricade_hit, barricade_destroyed, mine_exploded.
"""
import math
import random
from panda3d.core import NodePath, TransparencyAttrib
from ursina import Vec3
from .data.barricades import BARRICADES, MAX_PLACED, REPAIR_COST, REPAIR_RATE
from .data.items import FUEL, ITEMS, SMELT
from .lowpoly import LowPoly
from .net import new_id
from .render import destroy, node, set_glow
from .world import rotate_cell

_holders = {}


def model(kind, part='build'):
    """The shared mesh of a barricade (copy it with copyTo)."""
    key = (kind, part)
    if key not in _holders:
        lp = LowPoly(seed=sum(map(ord, kind)) + (17 if part != 'build' else 0))
        BARRICADES[kind][part](lp)
        holder = NodePath(f'barricade_{kind}_{part}')
        lp.mesh().reparentTo(holder)
        glow = lp.glow_mesh()
        if glow is not None:
            glow.reparentTo(holder)
            set_glow(glow, 1.0)
        _holders[key] = holder
    return _holders[key]


class Barricades:
    def __init__(self, game):
        self.game = game
        self.root = node(game.world_root)
        self.list = []
        self.cells = {}          # (gx, gz) -> barricade that blocks it (zombies have to break it)
        self.taken = set()       # every cell something is placed on (landmines too)
        self.ghost = None
        self.ghost_kind = None
        self.sound_t = 0.0

    # ── placing ──────────────────────────────────────────────────────────────
    def footprint(self, kind, x, z, rot):
        w = self.game.world
        gx, gz = w.to_grid(x, z)
        out = []
        for dx, dz in BARRICADES[kind]['cells']:
            rx, rz = rotate_cell(dx, dz, rot)
            out.append((gx + rx, gz + rz))
        return out

    def can_place(self, kind, x, z, rot, player=None):
        """'' if it fits there, otherwise the reason it doesn't."""
        g, w = self.game, self.game.world
        if player is not None and sum(1 for b in self.list if b['owner'] is player) >= MAX_PLACED:
            return f'You already have {MAX_PLACED} barricades up'
        cells = self.footprint(kind, x, z, rot)
        for c in cells:
            if not w.inside(c[0], c[1], 1):
                return 'Too close to the edge'
            if w.heights[w.gidx(*c)] > 0 or c in w.columns or c in self.taken:
                return 'Something is in the way'
        if BARRICADES[kind]['height'] > 0:
            bodies = [p for p in g.players if not p.dead] + [a for a in g.allies if not a.dead] + list(g.enemies.alive())
            for gx, gz in cells:
                cx, cz = gx - w.half + 0.5, gz - w.half + 0.5
                for b in bodies:
                    if abs(b.position.x - cx) < 0.5 + b.radius and abs(b.position.z - cz) < 0.5 + b.radius:
                        return 'Someone is standing there'
        return ''

    def place(self, player, kind, x, z, rot):
        """Put down one of the player's crafted barricades. Returns it, or None."""
        g, w = self.game, self.game.world
        if player.placeables.get(kind, 0) <= 0 or self.can_place(kind, x, z, rot, player):
            return None
        player.placeables[kind] -= 1
        d = BARRICADES[kind]
        cells = self.footprint(kind, x, z, rot)
        gx, gz = w.to_grid(x, z)
        pos = Vec3(gx - w.half + 0.5, 0, gz - w.half + 0.5)
        e = node(self.root, position=pos, rotation_y=rot)
        body = node(e)
        model(kind).copyTo(body)
        hp = float(d['hp']) * getattr(player, 'barricade_hp_mult', 1.0)      # Engineer skills
        b = dict(id=new_id(), kind=kind, d=d, owner=player, pos=pos, rot=rot, cells=cells, hp=hp,
                 max_hp=hp, e=e, body=body, shake=0.0, flash=0.0, tick=0.0, grow=0.0)
        if d.get('turret'):
            head = node(e, y=d['turret']['head_y'])
            model(kind, 'build_head').copyTo(head)
            b.update(head=head, ammo=d['turret']['ammo'], cooldown=0.0, target=None, retarget=0.0, yaw=0.0,
                     pitch=0.0, shots=0, reload=0.0)
        if d.get('mine'):
            b.update(arm=d['mine']['arm'])
        if d.get('furnace'):                          # like a Minecraft furnace: ore, fuel and output slots
            b.update(inp=None, fuel=None, out=None, burn=0.0, burn_max=1.0, cook=0.0)
        for c in cells:
            self.taken.add(c)
            if d['height'] > 0:
                self.cells[c] = b
                w.set_dynamic_solid(c[0], c[1], d['height'])
        self.list.append(b)
        g.sounds.play('build_place', pitch=0.9 + random.random() * 0.2)
        g.effects.burst(pos + Vec3(0, 0.2, 0), '#8a6a44', 10, speed=3, size=0.12)
        g.events.emit('barricade_placed', id=b['id'], kind=kind, player=player, pos=pos, rot=rot)
        return b

    # ── damage ───────────────────────────────────────────────────────────────
    def hurt(self, b, amount, source=None):
        """Something (a zombie) hits barricade b."""
        if b not in self.list:
            return
        g = self.game
        b['hp'] -= amount
        b['flash'] = 0.12
        b['shake'] = 0.2
        g.effects.burst(b['pos'] + Vec3((random.random() - 0.5) * 1.5, 0.6, 0), '#9a7448', 4, speed=3, size=0.1)
        self.sound_t -= 1
        if self.sound_t <= 0:
            self.sound_t = 2                       # don't play a knock for every single hit
            g.sounds.play('barricade_hit', volume=0.7, pitch=0.85 + random.random() * 0.3)
        thorns = b['d'].get('thorns')
        if thorns and source is not None and hasattr(source, 'hurt') and not source.dead:
            source.hurt(thorns['hit'] * self.wave_scale(), False, None, attacker=b['owner'])
        g.events.emit('barricade_hit', id=b['id'], amount=amount)
        if b['hp'] <= 0:
            self.remove(b, broken=True)

    def remove(self, b, broken=False):
        if b not in self.list:
            return
        g, w = self.game, self.game.world
        self.list.remove(b)
        for c in b['cells']:
            self.taken.discard(c)
            if self.cells.get(c) is b:
                del self.cells[c]
                w.set_dynamic_solid(c[0], c[1], 0)
        if broken:
            g.effects.burst(b['pos'] + Vec3(0, 0.6, 0), '#9a7448', 22, speed=6, size=0.16)
            g.effects.burst(b['pos'] + Vec3(0, 0.4, 0), '#6e5233', 12, speed=5, size=0.2)
            g.sounds.play('barricade_break')
            g.ui.kill_feed(f"{b['d']['name']} destroyed!")
        destroy(b['e'])
        g.events.emit('barricade_destroyed', id=b['id'], kind=b['kind'], broken=broken)

    def clear(self):
        w = self.game.world
        for b in list(self.list):
            for c in b['cells']:
                if self.cells.get(c) is b:
                    w.set_dynamic_solid(c[0], c[1], 0)
            destroy(b['e'])
        self.list = []
        self.cells = {}
        self.taken = set()
        self.hide_ghost()

    # ── what zombies ask ─────────────────────────────────────────────────────
    def at_cell(self, cell):
        return self.cells.get(cell)

    def nearest(self, pos, max_dist, kinds=None):
        best, best_d = None, max_dist
        for b in self.list:
            if kinds and b['kind'] not in kinds:
                continue
            for gx, gz in b['cells']:
                w = self.game.world
                d = math.hypot(gx - w.half + 0.5 - pos.x, gz - w.half + 0.5 - pos.z)
                if d < best_d:
                    best, best_d = b, d
        return best, best_d

    # ── interacting (hold E) ─────────────────────────────────────────────────
    def interact(self, player, use_held, dt):
        """The prompt to show near a barricade, and repairs / turret reloads while E is held."""
        g = self.game
        turret, td = self.nearest(player.position, 2.2, kinds=('turret',))
        if turret is not None:
            t = turret['d']['turret']
            if turret['ammo'] >= t['ammo']:
                turret['reload'] = 0
                return f"Sentry turret: {turret['ammo']}/{t['ammo']} ammo", None
            cost = t['reload_cost']
            have = all(player.resources.get(r, 0) >= n for r, n in cost.items())
            price = ', '.join(f"{n} {ITEMS[r]['name'].lower()}" for r, n in cost.items())
            if not have:
                return f"Turret ammo {turret['ammo']}/{t['ammo']}: reloading needs {price}", None
            if use_held:
                turret['reload'] += dt
                if turret['reload'] >= 1.0:
                    for r, n in cost.items():
                        player.resources[r] -= n
                    turret['ammo'] = t['ammo']
                    turret['reload'] = 0
                    g.sounds.play('reload_rack')
                    return '', None
                return 'Reloading the turret...', turret['reload']
            turret['reload'] = 0
            return f"Turret ammo {turret['ammo']}/{t['ammo']}: hold E to reload ({price})", None
        fur, _ = self.nearest(player.position, 2.2, kinds=('furnace',))
        if fur is not None and fur['hp'] >= fur['max_hp']:
            out = fur['out']
            extra = f"  ({out['n']} {ITEMS[out['id']]['name'].lower()} ready)" if out else ''
            if fur['burn'] > 0 and self.can_smelt(fur):
                return 'Press E to use the furnace: smelting' + extra, self.furnace_status(fur)[1]
            return 'Press E to use the furnace' + extra, None
        b, _ = self.nearest(player.position, 1.9)
        if b is None or b['hp'] >= b['max_hp'] or b['d'].get('mine'):
            return None, None
        wood = player.resources.get('wood', 0)
        if wood <= 0:
            return f"{b['d']['name']} {math.ceil(b['hp'])}/{int(b['max_hp'])}: repairing needs wood", None
        if not use_held:
            return f"{b['d']['name']} {math.ceil(b['hp'])}/{int(b['max_hp'])}: hold E to repair (wood)", None
        amount = min(REPAIR_RATE * dt, b['max_hp'] - b['hp'])
        b['wood_debt'] = b.get('wood_debt', 0.0) + amount / REPAIR_COST
        while b['wood_debt'] >= 1 and player.resources.get('wood', 0) > 0:
            player.resources['wood'] -= 1
            b['wood_debt'] -= 1
        b['hp'] += amount
        if random.random() < dt * 6:
            g.sounds.play('barricade_hit', volume=0.4, pitch=1.3)
        return 'Repairing...', b['hp'] / b['max_hp']

    # ── per frame ────────────────────────────────────────────────────────────
    def update(self, dt):
        for b in list(self.list):
            b['grow'] = min(1.0, b['grow'] + dt * 4)
            b['shake'] = max(0.0, b['shake'] - dt)
            b['flash'] = max(0.0, b['flash'] - dt)
            s = b['shake'] * 0.08
            b['body'].setPos((random.random() - 0.5) * s, 0, (random.random() - 0.5) * s)
            b['body'].setScale(1, 0.4 + 0.6 * b['grow'], 1)
            k = 1 + b['flash'] * 8
            b['body'].setColorScale(k, k * 0.9, k * 0.8, 1)
            d = b['d']
            if 'ttl' in b:                       # a Sentry from the Engineer's ability: gone after a while
                b['ttl'] -= dt
                if b['ttl'] <= 0:
                    self.remove(b)
                    continue
            if d.get('thorns'):
                self.update_thorns(b, dt)
            if d.get('mine'):
                self.update_mine(b, dt)
            if d.get('turret'):
                self.update_turret(b, dt)
            if d.get('furnace'):
                self.update_furnace(b, dt)

    def wave_scale(self):
        """Turrets and spikes hit harder in later waves (5% per wave), so they stay useful."""
        return 1 + 0.05 * max(0, self.game.wave_number - 1)

    # ── furnaces (work like Minecraft) ───────────────────────────────────────
    @staticmethod
    def furnace_accepts(slot, item_id):
        """Can item_id go in furnace slot 'inp' (ore) / 'fuel'? Nothing can be put in 'out'."""
        return (slot == 'inp' and item_id in SMELT) or (slot == 'fuel' and item_id in FUEL)

    def can_smelt(self, b):
        inp, out = b['inp'], b['out']
        if not inp or inp['n'] <= 0 or inp['id'] not in SMELT:
            return False
        ingot = SMELT[inp['id']][0]
        return out is None or (out['id'] == ingot and out['n'] < ITEMS[ingot]['stack'])

    def update_furnace(self, b, dt):
        if b['burn'] > 0:
            b['burn'] = max(0.0, b['burn'] - dt)
        if self.can_smelt(b):
            if b['burn'] <= 0 and b['fuel'] and b['fuel']['n'] > 0:      # light the next piece of fuel
                b['burn'] = b['burn_max'] = FUEL[b['fuel']['id']]
                b['fuel']['n'] -= 1
                if b['fuel']['n'] <= 0:
                    b['fuel'] = None
            if b['burn'] > 0:
                ingot, secs = SMELT[b['inp']['id']]
                b['cook'] += dt
                if b['cook'] >= secs:
                    b['cook'] = 0.0
                    b['inp']['n'] -= 1
                    if b['inp']['n'] <= 0:
                        b['inp'] = None
                    if b['out'] is None:
                        b['out'] = dict(id=ingot, n=0)
                    b['out']['n'] += 1
                    self.game.events.emit('furnace_smelted', id=b['id'], ingot=ingot)
            else:
                b['cook'] = max(0.0, b['cook'] - dt * 2)      # out of fuel: the progress cools off
        else:
            b['cook'] = 0.0

    def furnace_status(self, b):
        """(burning 0..1, cooking 0..1)"""
        cook = 0.0
        if b['inp'] and b['inp']['id'] in SMELT:
            cook = b['cook'] / SMELT[b['inp']['id']][1]
        return b['burn'] / max(0.01, b['burn_max']), cook

    def lights(self):
        """Furnaces glow while they're burning."""
        return [(b['pos'] + Vec3(0, 0.6, 0), (1.0, 0.55, 0.22), 6, 1.2) for b in self.list
                if b['d'].get('furnace') and b['burn'] > 0]

    def update_thorns(self, b, dt):
        b['tick'] -= dt
        if b['tick'] > 0:
            return
        b['tick'] = 0.5
        w = self.game.world
        dps = b['d']['thorns']['dps'] * self.wave_scale()
        for e in self.game.enemies.alive():
            if e.rise > 0:
                continue
            for gx, gz in b['cells']:
                cx, cz = gx - w.half + 0.5, gz - w.half + 0.5
                if abs(e.position.x - cx) < 0.62 + e.radius and abs(e.position.z - cz) < 0.62 + e.radius:
                    e.hurt(dps * 0.5, False, None, attacker=b['owner'])
                    break

    def update_mine(self, b, dt):
        g, m = self.game, b['d']['mine']
        if b['arm'] > 0:
            b['arm'] -= dt
            if b['arm'] <= 0:
                g.sounds.play('empty', volume=0.6, pitch=1.6)      # a little click: armed
            return
        for e in g.enemies.alive():
            if e.rise <= 0 and (Vec3(e.position.x, 0, e.position.z) - b['pos']).length() < m['trigger'] + e.radius:
                self.remove(b)
                g.projectiles.explode(b['pos'] + Vec3(0, 0.3, 0),
                                      dict(radius=m['radius'], damage=m['damage'], knockback=12, shooter=b['owner']))
                g.events.emit('mine_exploded', id=b['id'], player=b['owner'])
                return

    def update_turret(self, b, dt):
        g, t = self.game, b['d']['turret']
        head = b['head']
        eye = b['pos'] + Vec3(0, t['head_y'], 0)
        b['cooldown'] -= dt
        b['retarget'] -= dt
        target = b['target']
        if target is not None and (target.dead or (target.chest_pos() - eye).length() > t['range']):
            target = b['target'] = None
        if b['retarget'] <= 0:
            b['retarget'] = 0.3
            best, best_d = None, t['range']
            for e in g.enemies.alive():
                if e.rise > 0.3:
                    continue
                aim = e.chest_pos() - eye
                dd = aim.length()
                # look from just outside the turret's own (solid) cell
                if dd < best_d and g.world.line_of_sight(eye + aim / max(dd, 0.01) * 0.8, e.chest_pos()):
                    best, best_d = e, dd
            target = b['target'] = best
        if target is None:
            b['yaw'] += dt * 25                         # idle: sweep slowly
            b['pitch'] *= max(0.0, 1 - dt * 3)
        else:
            aim = target.chest_pos() - eye
            want_yaw = math.degrees(math.atan2(aim.x, aim.z)) - b['rot']
            want_pitch = math.degrees(math.atan2(aim.y, math.hypot(aim.x, aim.z)))
            diff = (want_yaw - b['yaw'] + 180) % 360 - 180
            b['yaw'] += diff * min(1.0, dt * 10)
            b['pitch'] += (want_pitch - b['pitch']) * min(1.0, dt * 10)
            if abs(diff) < 12 and b['ammo'] > 0 and b['cooldown'] <= 0:
                self.turret_fire(b, target, eye, aim)
        head.rotation_y = b['yaw']
        head.rotation_x = -b['pitch']

    def turret_fire(self, b, target, eye, aim):
        g, t = self.game, b['d']['turret']
        b['cooldown'] = 1 / t['rate']
        b['ammo'] -= 1
        b['shots'] += 1
        d = aim.normalized()
        spread = 0.025
        d = Vec3(d.x + (random.random() - 0.5) * spread, d.y + (random.random() - 0.5) * spread,
                 d.z + (random.random() - 0.5) * spread).normalized()
        muzzle = eye + d * 0.8
        wall = g.world.raycast(muzzle, d, t['range'])
        end = muzzle + d * wall
        hits = g.enemies.raycast(muzzle, d, wall)
        if hits:
            dist, enemy, head = hits[0]
            end = muzzle + d * dist
            damage = t['damage'] * self.wave_scale() * (1.8 if head else 1)
            enemy.hurt(damage, head, Vec3(d.x, 0, d.z) * 0.8, attacker=b['owner'])
        g.effects.tracer(muzzle, end, '#ffe08a', 0.025, 0.05)
        g.lighting.flash(muzzle, (1.0, 0.82, 0.55), 6, 1.2, life=0.05)
        if b['shots'] % 2 == 0:
            g.sounds.play('shoot_smg', volume=0.35, pitch=1.1 + random.random() * 0.1)

    # ── build-mode ghost (what you're about to place) ────────────────────────
    def show_ghost(self, kind, x, z, rot, ok):
        if self.ghost_kind != kind:
            self.hide_ghost()
            self.ghost = node(self.root)
            model(kind).copyTo(self.ghost)
            if BARRICADES[kind].get('build_head'):
                head = node(self.ghost, y=BARRICADES[kind]['turret']['head_y'])
                model(kind, 'build_head').copyTo(head)
            self.ghost.setTransparency(TransparencyAttrib.M_alpha)
            self.ghost.setDepthWrite(False)
            self.ghost.setShaderInput('glow', 0.6)
            self.ghost_kind = kind
        w = self.game.world
        gx, gz = w.to_grid(x, z)
        self.ghost.position = Vec3(gx - w.half + 0.5, 0.01, gz - w.half + 0.5)
        self.ghost.rotation_y = rot
        self.ghost.setColorScale(0.45, 1.0, 0.5, 0.55) if ok else self.ghost.setColorScale(1.0, 0.3, 0.3, 0.55)

    def hide_ghost(self):
        if self.ghost is not None:
            destroy(self.ghost)
        self.ghost = None
        self.ghost_kind = None
