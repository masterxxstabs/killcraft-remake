"""Shooting, reloading and the blocky gun you hold.
The held gun lives in its own little scene drawn on top of the world, so it
never pokes through walls."""
import math
import random
from panda3d.core import Camera as PandaCamera, NodePath, PerspectiveLens
from ursina import Vec3, application, camera, destroy, window
from .data.weapons import WEAPONS
from .render import block, col, node, set_fog


class Weapons:
    def __init__(self, game):
        self.game = game
        self.defs = WEAPONS
        base = application.base
        self.vm_root = NodePath('viewmodel')
        set_fog(self.vm_root, (0, 0, 0), 1000, 1001)      # no fog on the gun
        self.lens = PerspectiveLens()
        self.lens.setFov(70)
        self.lens.setNearFar(0.01, 10)
        self.vm_cam = self.vm_root.attachNewNode(PandaCamera('viewmodel_cam', self.lens))
        self.region = base.win.makeDisplayRegion()
        self.region.setSort(10)                 # after the world (0), before the UI (20)
        self.region.setClearDepthActive(True)
        self.region.setCamera(self.vm_cam)
        self.holder = node(self.vm_root)
        self.holder.scale = 0.7
        self.model = None
        self.flash = block(self.holder, size=(0.12, 0.12, 0.02), color='#ffe08a', enabled=False)
        self.reset()

    def set_visible(self, on):
        self.region.setActive(on)

    def reset(self):
        self.owned = []
        self.state = {}
        self.held = None
        for d in self.defs:
            if d['price'] == 0:
                self.give(d['id'], equip=False)
        self.cooldown = 0
        self.reloading = 0
        self.reload_total = 1
        self.swing = 0
        self.kick = 0
        self.switch_anim = 0
        self.flash_t = 0
        self.trigger_down = False
        self.trigger_pressed = False
        self.equip(min(1, len(self.owned) - 1))

    def owns(self, wid):
        return any(d['id'] == wid for d in self.owned)

    def give(self, wid, equip=True):
        d = next((w for w in self.defs if w['id'] == wid), None)
        if not d or self.owns(wid):
            return
        self.owned.append(d)
        self.owned.sort(key=self.defs.index)
        self.state[wid] = dict(ammo=d.get('mag', 0))
        if equip:
            self.equip(self.owned.index(d))
        else:
            self.game.ui.update_weapon()

    @property
    def d(self):
        return self.held

    @property
    def current(self):
        return self.owned.index(self.held) if self.held else 0

    def equip(self, i):
        if i < 0 or i >= len(self.owned):
            return
        if self.owned[i] is self.held and self.model:
            return
        self.held = self.owned[i]
        self.reloading = 0
        self.cooldown = max(self.cooldown, 0.25)
        if self.model:
            destroy(self.model)
        self.model = self.build_model(self.held)
        self.switch_anim = 0.25
        self.game.ui.update_weapon()

    def cycle(self, direction):
        n = len(self.owned)
        self.equip((self.current + direction) % n)

    def build_model(self, d):
        m = d['model']
        g = node(self.holder)
        body, accent = m['body'], m['accent']
        if d.get('melee'):
            L = m['length']
            block(g, size=(0.05, 0.05, L), center=(0, 0, L / 2), color=accent)
            block(g, size=(0.16, 0.06, 0.08), center=(0, 0, L), color=body)
            block(g, size=(0.05, 0.06, 0.12), center=(-0.06, 0, L + 0.08), color=body)
            block(g, size=(0.05, 0.06, 0.12), center=(0.06, 0, L + 0.08), color=body)
            g.rotation_x = -30
            self.muzzle = Vec3(0, 0, L)
        else:
            L, W = m['length'], m['width']
            block(g, size=(W, W * 1.2, L), center=(0, 0, L / 2), color=body)
            block(g, size=(W * 0.5, W * 0.5, L * 0.35), center=(0, W * 0.25, L + L * 0.12), color=accent)
            block(g, size=(W * 1.02, W * 0.3, L * 0.3), center=(0, W * 0.5, L * 0.45), color=accent)
            grip = node(g, position=(0, -W * 1.3, W * 0.6), rotation_x=15)
            block(grip, size=(W * 0.8, W * 2, W * 0.9), color=body)
            if d.get('mag', 0) > 10:
                block(g, size=(W * 0.6, W * 1.8, W * 0.7), center=(0, -W * 1.2, L * 0.55), color=accent)
            self.muzzle = Vec3(0, 0.02, L * 1.3)
        return g

    def trigger(self, down):
        if down and not self.trigger_down:
            self.trigger_pressed = True
        self.trigger_down = down

    def start_reload(self):
        d, st = self.held, self.state[self.held['id']]
        if d.get('melee') or self.reloading > 0 or st['ammo'] >= d['mag']:
            return
        self.reloading = self.reload_total = d['reload'] * self.game.player.reload_mult
        self.game.sounds.play('reload')

    def rate_mult(self):
        p = self.game.player
        return p.fire_rate_mult * (2 if p.buffs.get('adrenaline', 0) > 0 else 1)

    def update(self, dt):
        g, d = self.game, self.held
        st = self.state[d['id']]
        self.cooldown -= dt
        if self.reloading > 0:
            self.reloading -= dt
            if self.reloading <= 0:
                st['ammo'] = d['mag']
                self.reloading = 0
                g.ui.update_weapon()

        wants = self.trigger_down if (d.get('auto') or d.get('melee')) else self.trigger_pressed
        if wants and self.cooldown <= 0 and g.can_act():
            self.fire()
        self.trigger_pressed = False

        # animate the held weapon
        self.kick = max(0, self.kick - dt * 8)
        self.swing = max(0, self.swing - dt * 4)
        self.switch_anim = max(0, self.switch_anim - dt)
        self.flash_t -= dt
        self.flash.enabled = self.flash_t > 0
        p = g.player
        bob_x = math.sin(p.bob) * 0.015 if p.moving else 0
        bob_y = abs(math.cos(p.bob)) * 0.012 if p.moving else 0
        rl = math.sin((1 - self.reloading / self.reload_total) * math.pi) if self.reloading > 0 else 0
        self.holder.position = (0.2 + bob_x, -0.2 + bob_y - self.switch_anim * 0.8 - rl * 0.1, 0.4 - self.kick * 0.06)
        sw = math.sin(self.swing * math.pi) if d.get('melee') else 0
        self.holder.rotation = (-self.kick * 14 + rl * 35 + sw * 80, -sw * 35, -rl * 17)
        self.flash.position = self.muzzle * 1.0
        self.lens.setAspectRatio(window.aspect_ratio)

    def muzzle_world(self):
        return camera.world_position + camera.forward * 0.6 + camera.right * 0.18 - camera.up * 0.14

    def fire(self):
        g, d, p = self.game, self.held, self.game.player
        st = self.state[d['id']]
        eye = Vec3(camera.world_position)
        fwd = Vec3(camera.forward)
        self.cooldown = 1 / (d['rate'] * self.rate_mult())

        if d.get('melee'):
            self.swing = 1
            g.sounds.play('swing')
            best, best_d = None, math.inf
            for e in g.enemies.alive():
                if e.rise > 0.3:
                    continue
                to = e.chest_pos() - eye
                dist = max(0, to.length() - e.radius)
                if dist > d['range'] or to.normalized().dot(fwd) < 0.55:
                    continue
                if dist < best_d:
                    best, best_d = e, dist
            if best:
                flat = Vec3(fwd.x, 0, fwd.z).normalized()
                best.hurt(d['damage'] * p.damage_mult, False, flat * d['knockback'])
                g.sounds.play('thud')
                g.ui.hitmarker(False)
            return

        if self.reloading > 0:
            return
        if st['ammo'] <= 0:
            g.sounds.play('empty')
            self.start_reload()
            return
        st['ammo'] -= 1
        self.kick = 1
        self.flash_t = 0.05
        p.recoil += 2.3 if d.get('projectile') else min(3, d['damage'] * d.get('pellets', 1) / 70 + 0.45)
        g.sounds.shoot(d)
        muzzle = self.muzzle_world()

        if d.get('projectile'):
            pr = d['projectile']
            g.projectiles.spawn_rocket(eye + fwd * 0.6, fwd * pr['speed'], pr['radius'], pr['damage'], d['knockback'])
        else:
            any_hit = any_head = False
            for _ in range(d.get('pellets', 1)):
                direction = Vec3(fwd)
                if d.get('spread'):
                    s = d['spread']
                    direction += Vec3((random.random() - 0.5) * 2 * s, (random.random() - 0.5) * 2 * s, (random.random() - 0.5) * 2 * s)
                    direction = direction.normalized()
                wall = g.world.raycast(eye, direction, d['range'])
                end = eye + direction * wall
                stopped = False
                for dist, e, head in g.enemies.raycast(eye, direction, wall):
                    mult = d.get('headshot', 2) if head else 1
                    flat = Vec3(direction.x, 0, direction.z)
                    e.hurt(d['damage'] * p.damage_mult * mult, head, flat * d['knockback'])
                    any_hit, any_head = True, any_head or head
                    if not d.get('pierce'):
                        end = eye + direction * dist
                        stopped = True
                        break
                if not stopped and wall < d['range']:
                    g.effects.burst(end, '#8a8a8a', 3, speed=2, size=0.08, life=0.4)
                rail = 'tracer' in d
                g.effects.tracer(muzzle, end, d.get('tracer', '#fff2a8'), 0.06 if rail else 0.02, 0.25 if rail else 0.06)
            if any_hit:
                g.ui.hitmarker(any_head)
                g.sounds.play('headshot' if any_head else 'hit')
        if st['ammo'] <= 0:
            self.start_reload()
        g.ui.update_weapon()
