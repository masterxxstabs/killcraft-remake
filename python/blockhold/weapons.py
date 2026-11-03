"""Shooting, reloading, weapon upgrades and the gun you hold.
The held gun lives in its own little scene drawn on top of the world, so it
never pokes through walls."""
import math
import random
from panda3d.core import AmbientLight, Camera as PandaCamera, DirectionalLight, NodePath, PerspectiveLens
from ursina import Vec3, application, camera, invoke, window
from . import custom_models
from .data.attachments import ATTACHMENTS
from .data.items import HAND_SLOTS, hand_slot
from .data.gun_models import MODELS
from .data.weapons import PRICE_GROWTH, WEAPON_UPGRADES, WEAPONS, weapon_upgrade_price
from .gunsmith import Smith
from .render import block, col, node, set_fog, init_light_inputs, set_glow, destroy
from .textures import weapon_atlas

UPGRADES_BY_ID = {u['id']: u for u in WEAPON_UPGRADES}
MOUNT_FOR_SLOT = {'optic': 'optic', 'muzzle': 'muzzle', 'under': 'under'}
_slot_cache = {}


HOLD_SHORT = (0.15, -0.12, 0.38)    # where pistols are held (camera space)
HOLD_LONG = (0.14, -0.135, 0.42)    # and everything longer
VM_SCALE = 0.5                      # size of the gun in your hands
TWO_HANDED = {'rifle', 'smg', 'shotgun', 'sniper', 'heavy', 'special'}
SKIN, SLEEVE = '#c48a5c', '#2a2d35'
_arm_tex = {}


def arm_texture(kind):
    """Blocky pixel textures for the hands and sleeves."""
    if kind not in _arm_tex:
        from ursina import Texture
        from .textures import pixel_image

        def seam(px, rnd, s, sh):            # a darker stitch line down the sleeve
            for y in range(s):
                px[s // 2, y] = sh('#1c1e24')
        img = pixel_image(SKIN, 0.07, 401) if kind == 'skin' else pixel_image(SLEEVE, 0.12, 403, draw=seam)
        _arm_tex[kind] = Texture(img)
    return _arm_tex[kind]


_flash = None


def _flash_mesh():
    """Eight spikes around a hot centre, seen face-on down the barrel."""
    global _flash
    if _flash is None:
        from .lowpoly import LowPoly
        lp = LowPoly(seed=3, variation=0.0, sun=(0, 0, -1))
        for i in range(8):
            a = i / 8 * math.tau
            length = 0.06 if i % 2 == 0 else 0.035
            tip = (math.cos(a) * length, math.sin(a) * length, 0)
            for side in (1, -1):
                b = a + side * math.tau / 18
                base = (math.cos(b) * 0.014, math.sin(b) * 0.014, 0)
                for facing in ((0, 0, 1), (0, 0, -1)):
                    lp.tri((0, 0, 0), base, tip, '#ffd27a' if i % 2 else '#fff1c4', facing)
        _flash = lp.mesh()
    return _flash

class Weapons:
    def __init__(self, game, owner=None):
        self.game = game
        self.owner = owner or game.player       # whose weapons these are
        self.defs = WEAPONS
        base = application.base
        self.vm_root = NodePath('viewmodel')
        set_fog(self.vm_root, (0, 0, 0), 1000, 1001)      # no fog on the gun
        init_light_inputs(self.vm_root)                   # the gun has its own light level (see Game.blend_sky)
        self.lens = PerspectiveLens()
        self.lens.setFov(70)
        self.lens.setNearFar(0.01, 10)
        self.vm_cam = self.vm_root.attachNewNode(PandaCamera('viewmodel_cam', self.lens))
        self.region = base.win.makeDisplayRegion()
        self.region.setSort(10)                 # after the world (0), before the UI (20)
        self.region.setClearDepthActive(True)
        self.region.setCamera(self.vm_cam)
        # lights, only used by downloaded 3D models (block models are pre-shaded)
        amb = AmbientLight('vm_ambient')
        amb.setColor((0.55, 0.55, 0.6, 1))
        sun = DirectionalLight('vm_sun')
        sun.setColor((0.9, 0.88, 0.8, 1))
        self.lights = [self.vm_root.attachNewNode(amb), self.vm_root.attachNewNode(sun)]
        self.lights[1].setHpr(-30, -40, 0)
        self.holder = node(self.vm_root)
        self.holder.scale = VM_SCALE
        self.model = None
        self.spinner = None
        self.flash = node(self.holder, enabled=False)            # a star-shaped muzzle flash
        _flash_mesh().copyTo(self.flash)
        set_glow(self.flash, 1.0)
        self.reset()

    def set_visible(self, on):
        self.region.setActive(on)

    @property
    def owned(self):
        """The weapons in your hands (tool, handgun, rifle), in that order. The rest are in the backpack."""
        return [self.slots[s] for s, _ in HAND_SLOTS if self.slots.get(s) is not None]

    def reset(self):
        self.slots = {s: None for s, _ in HAND_SLOTS}
        self.state = {}             # weapon id -> ammo etc. (every weapon you own, in hand or in the backpack)
        self.levels = {}            # weapon id -> {upgrade id: level}
        self.attach = {}            # weapon id -> {slot: attachment id}
        self.owned_att = {}         # weapon id -> set of attachment ids bought for it
        self.camo = {}              # weapon id -> camo id
        self.owned_camos = {'factory'}
        self.held = None
        self.cooldown = 0
        self.reloading = 0
        self.reload_total = 1
        self.swing = 0
        self.kick = 0
        self.switch_anim = 0
        self.flash_t = 0
        self.spin = 0
        self.spin_angle = 0
        self.trigger_down = False
        self.trigger_pressed = False
        for d in self.defs:                              # the free starting weapons
            if d['price'] == 0 and not d.get('hidden'):
                self.give(d['id'], equip=False)
        self.equip(min(1, len(self.owned) - 1))

    # ── owning, upgrading ────────────────────────────────────────────────────
    def owns(self, wid):
        """In your hands or in your backpack."""
        return wid in self.state

    def in_hands(self, wid):
        return any(d['id'] == wid for d in self.owned)

    @property
    def bag(self):
        return self.owner.inventory

    def get_def(self, wid):
        return next((w for w in self.defs if w['id'] == wid), None)

    def give(self, wid, equip=True):
        """A new weapon: into its hand slot if that's free, otherwise into the backpack
        (and if that's full too, it's left on the ground at your feet)."""
        d = self.get_def(wid)
        if not d or self.owns(wid):
            return
        self.levels.setdefault(wid, {})
        self.state[wid] = dict(ammo=self.stat(d, 'mag'))
        slot = hand_slot(d)
        if self.slots[slot] is None:
            self.slots[slot] = d
            if equip or self.held is None:
                self.equip(self.owned.index(d))
            else:
                self.game.ui.update_weapon()
            return
        if self.bag.add('w_' + wid) == 0:
            if self.owner.is_local:
                self.game.ui.kill_feed(f"{d['name']} went in your backpack (I)")
            return
        pack = self.take_out(d)                       # no room anywhere: on the ground it goes
        self.game.drops.spawn(pack, Vec3(self.owner.position.x, 0, self.owner.position.z), 0, self.owner)
        if self.owner.is_local:
            self.game.ui.banner('BACKPACK FULL', '#d9912b', 1.6, f"{d['name']} is on the ground at your feet")

    # ── hands and backpack ───────────────────────────────────────────────────
    def unslot(self, slot):
        """Take the weapon out of a hand slot (to drag it somewhere). Never leaves your hands empty."""
        d = self.slots.get(slot)
        if d is None or len(self.owned) <= 1:
            return None
        self.slots[slot] = None
        if self.held is d:
            self.held = None
            self.equip(0)
        self.game.ui.update_weapon()
        return d

    def slot_in(self, d, slot=None):
        """Put weapon d in its hand slot (which must be empty)."""
        slot = slot or hand_slot(d)
        self.slots[slot] = d
        if self.held is None:
            self.equip(self.owned.index(d))
        self.game.ui.update_weapon()

    def ready(self, d):
        """Hold weapon d, taking it out of the backpack if needed (what was in its slot goes in instead)."""
        if d in self.owned:
            self.equip(self.owned.index(d))
            return True
        bag, slot = self.bag, hand_slot(d)
        it = next((i for i in bag.items if i['id'] == 'w_' + d['id']), None)
        if it is None:
            return False
        bag.lift(it)
        old = self.slots[slot]
        if old is not None:
            back = dict(id='w_' + old['id'], n=1, x=it['x'], y=it['y'], rot=it['rot'], uid=it['uid'])
            if not bag.put_back(back):
                bag.put_back(it)
                return False
            if self.held is old:
                self.held = None
        self.slots[slot] = d
        self.equip(self.owned.index(d), force=True)
        return True

    def equip_slot(self, slot):
        d = self.slots.get(slot)
        if d is not None:
            self.equip(self.owned.index(d))

    def upgrades_for(self, d):
        key = 'for_melee' if d.get('melee') else 'for_guns'
        return [u for u in WEAPON_UPGRADES if u[key]]

    def level(self, d, uid):
        return self.levels.get(d['id'], {}).get(uid, 0)

    def total_level(self, d):
        return sum(self.levels.get(d['id'], {}).values())

    def max_total(self, d):
        return sum(u['max'] for u in self.upgrades_for(d))

    def upgrade_price(self, d, uid):
        return round(weapon_upgrade_price(d) * PRICE_GROWTH ** self.level(d, uid))

    def upgrade(self, d, uid):
        lv = self.levels.setdefault(d['id'], {})
        lv[uid] = lv.get(uid, 0) + 1
        if uid == 'mag':        # bigger magazine comes pre-filled
            self.state[d['id']]['ammo'] = self.stat(d, 'mag')
        self.game.ui.update_weapon()

    def stat(self, d, key):
        """A weapon stat with its upgrades applied."""
        lv = self.level(d, key)
        bonus = UPGRADES_BY_ID[key]['bonus'] if key in UPGRADES_BY_ID else 0
        if key == 'damage':
            return d['damage'] * (1 + bonus * lv)
        if key == 'rate':
            return d['rate'] * (1 + bonus * lv)
        if key == 'mag':
            return round(d.get('mag', 0) * (1 + bonus * lv) * self.mod(d, 'mag'))
        if key == 'reload':
            return d.get('reload', 1) * (1 - bonus) ** lv * self.mod(d, 'reload')
        if key == 'range':
            return d['range'] * (1 + bonus * lv) * self.mod(d, 'range')
        raise KeyError(key)

    # ── attachments & camos ──────────────────────────────────────────────────
    def fitted(self, d):
        """The attachments on weapon d."""
        return [ATTACHMENTS[a] for a in self.attach.get(d['id'], {}).values() if a in ATTACHMENTS]

    def mod(self, d, key):
        m = 1.0
        for a in self.fitted(d):
            m *= a.get(key, 1.0)
        return m

    def has_scope(self, d):
        return bool(d.get('scope') or any(a.get('scope') for a in self.fitted(d)))

    def shot_sound(self, d):
        return next((a['sound'] for a in self.fitted(d) if a.get('sound')), d.get('sound', 'pistol'))

    def slots_for(self, d):
        """Which attachment slots weapon d has (from the mount points on its model)."""
        if d['id'] not in _slot_cache:
            slots = []
            if d['id'] in MODELS:
                s = Smith()
                MODELS[d['id']](s)
                slots = [slot for slot, m in MOUNT_FOR_SLOT.items() if m in s.mounts]
                if d.get('projectile') or d.get('cone'):
                    slots = [x for x in slots if x == 'optic']
            if d.get('mag') and not d.get('melee') and not d.get('projectile'):
                slots.append('mag')
            _slot_cache[d['id']] = slots
        return _slot_cache[d['id']]

    def fit(self, d, slot, aid):
        """Put attachment aid (or None) in a slot. The magazine is refilled."""
        self.attach.setdefault(d['id'], {})[slot] = aid
        self.state[d['id']]['ammo'] = self.stat(d, 'mag')
        if self.held is d:
            self.equip(self.current, force=True)
        self.game.ui.update_weapon()

    def set_camo(self, d, camo):
        self.camo[d['id']] = camo
        if self.held is d:
            self.equip(self.current, force=True)

    def gun_smith(self, d):
        """Build the detailed model of d with its camo and attachments."""
        s = Smith(camo=self.camo.get(d['id'], 'factory'))
        MODELS[d['id']](s)
        for slot, aid in self.attach.get(d['id'], {}).items():
            a = ATTACHMENTS.get(aid)
            mount = s.mounts.get(MOUNT_FOR_SLOT.get(slot))
            if a and a['build'] and mount is not None:
                a['build'](s, mount)
                if slot == 'muzzle' and aid == 'suppressor':
                    s.mounts['muzzle_end'] = (mount[0], mount[1], mount[2] + 0.16)
        return s

    def dmg_mult(self, d):
        """Damage multiplier from this weapon's upgrades and the player's Power upgrade."""
        return (1 + UPGRADES_BY_ID['damage']['bonus'] * self.level(d, 'damage')) * self.owner.damage_mult

    # ── holding ──────────────────────────────────────────────────────────────
    @property
    def d(self):
        return self.held

    @property
    def current(self):
        return self.owned.index(self.held) if self.held else 0

    def equip(self, i, force=False):
        if i < 0 or i >= len(self.owned):
            return
        if self.owned[i] is self.held and self.model and not force:
            return
        self.held = self.owned[i]
        self.reloading = 0
        self.spin = 0
        self.cooldown = max(self.cooldown, 0.25)
        if self.model:
            destroy(self.model)
        self.model = self.build_model(self.held)
        self.switch_anim = 0.25
        self.game.sounds.play('equip', volume=0.8)
        self.game.ui.update_weapon()

    def cycle(self, direction):
        n = len(self.owned)
        if n == 0:
            return
        self.equip((self.current + direction) % n)

    def build_model(self, d):
        self.grip_at = self.support_at = None
        self.sight_h = 0.06              # how high the sights are above the grip (for aiming)
        g = self._build_gun(d)
        if self.custom is None:
            self.build_arms(d, g)
        return g

    def _build_gun(self, d):
        g = node(self.holder)
        self.spinner = None
        self.custom = None
        custom = custom_models.load(d, g, self.lights)
        if custom is not None:
            self.custom = custom
            self.muzzle = Vec3(0, 0, d.get('length', 0.5) * 0.95)
            return g
        if d['id'] in MODELS:
            s = self.gun_smith(d)
            node(g, model=s.build())
            self.grip_at = s.mounts.get('grip')
            optic = s.mounts.get('optic')
            if optic is not None and self.attach.get(d['id'], {}).get('optic'):
                self.sight_h = optic[0] + 0.035      # looking through the red dot / scope
            elif 'sight' in s.mounts:
                self.sight_h = s.mounts['sight']
            elif optic is not None:
                self.sight_h = optic[0] + 0.015
            under = s.mounts.get('under')
            if under is not None:
                drop = 0.07 if any(a.get('name', '').lower().startswith('foregrip') for a in self.fitted(d)) else 0.0
                self.support_at = (under[0] - drop, under[1])
            m = s.mounts.get('muzzle_end') or s.mounts.get('muzzle') or (0, 0, d.get('length', 0.4))
            self.muzzle = Vec3(*m)
            return g
        atlas = weapon_atlas()
        spin_parts = []
        for part in d.get('model') or [('dark', (0.08, 0.1, d.get('length', 0.4)), (0, 0, d.get('length', 0.4) / 2))]:
            material, size, center = part[0], part[1], part[2]
            if len(part) > 3 and part[3] == 'spin':
                spin_parts.append(part)
                continue
            block(g, size=size, center=center, texture=atlas.texture, uv_rects=atlas.all_faces(material))
        if spin_parts:
            self.spinner = node(g)
            for material, size, center, _ in spin_parts:
                block(self.spinner, size=size, center=center, texture=atlas.texture, uv_rects=atlas.all_faces(material))
        if d.get('melee'):
            g.rotation_x = -30
        self.muzzle = Vec3(*d.get('muzzle', (0, 0, d.get('length', 0.4))))
        return g

    def ground_model(self, d, parent):
        """The gun as an object in the world (a dropped gun): same model, real size."""
        if d['id'] in MODELS:
            node(parent, model=self.gun_smith(d).build())
            return
        atlas = weapon_atlas()
        for part in d.get('model') or [('dark', (0.08, 0.1, d.get('length', 0.4)), (0, 0, d.get('length', 0.4) / 2))]:
            block(parent, size=part[1], center=part[2], texture=atlas.texture, uv_rects=atlas.all_faces(part[0]))

    # ── dropping and picking up ──────────────────────────────────────────────
    def take_out(self, d):
        """Remove weapon d and return everything about it (ammo, upgrades, attachments, camo)."""
        wid = d['id']
        pack = dict(wid=wid, state=dict(self.state.get(wid, {})), levels=dict(self.levels.get(wid, {})),
                    attach=dict(self.attach.get(wid, {})), owned_att=set(self.owned_att.get(wid, set())),
                    camo=self.camo.get(wid, 'factory'))
        was = self.current
        for slot, w in self.slots.items():
            if w is d:
                self.slots[slot] = None
        for it in [i for i in self.bag.items if i['id'] == 'w_' + wid]:
            self.bag.lift(it)
        for table in (self.state, self.levels, self.attach, self.owned_att, self.camo):
            table.pop(wid, None)
        if self.held is d:
            self.held = None
            self.equip(min(was, len(self.owned) - 1))
        self.game.ui.update_weapon()
        return pack

    def put_back(self, pack, equip=True):
        """Give back a weapon taken out with take_out, exactly as it was."""
        wid = pack['wid']
        self.give(wid, equip=False)
        self.state[wid] = dict(pack['state']) or self.state[wid]
        self.levels[wid] = dict(pack['levels'])
        self.attach[wid] = dict(pack['attach'])
        self.owned_att[wid] = set(pack['owned_att'])
        self.camo[wid] = pack['camo']
        if equip and self.in_hands(wid):
            self.equip(self.owned.index(self.get_def(wid)), force=True)

    # ── the arms holding the gun ─────────────────────────────────────────────
    def hold_pos(self, d):
        return d.get('hold') or (HOLD_SHORT if d.get('length', 0.5) < 0.35 else HOLD_LONG)

    def build_arms(self, d, g):
        """Blocky arms like the original: a hand on the grip, a dark sleeve running off the
        bottom of the screen, and a second hand under the barrel for two-handed guns."""
        hx, hy, hz = self.hold_pos(d)
        k = self.holder.scale_x

        def from_camera(x, y, z):            # a point in front of the camera -> gun space
            return Vec3((x - hx) / k, (y - hy) / k, (z - hz) / k)

        melee = d.get('melee')
        arms = node(self.holder if melee else g)
        skin, sleeve = arm_texture('skin'), arm_texture('sleeve')
        if melee:
            gy, gz = -0.01, 0.02
        else:
            gy, gz = self.grip_at or (-0.015, -0.02)
        hand = Vec3(0.0, gy - 0.045, gz - 0.012)
        block(arms, size=(0.052, 0.078, 0.066), center=hand, texture=skin)                            # fist
        block(arms, size=(0.016, 0.022, 0.05), center=hand + Vec3(-0.027, 0.03, 0.02), texture=skin)  # thumb
        if not melee:
            block(arms, size=(0.014, 0.016, 0.03), center=hand + Vec3(-0.02, 0.036, 0.052), texture=skin)  # trigger finger
        self._sleeve(arms, hand + Vec3(0.004, -0.03, -0.03), from_camera(0.36, -0.44, 0.1), sleeve)
        two_handed = d.get('category') in TWO_HANDED and not melee
        if two_handed:
            sy, sz = self.support_at or (-0.035, max(0.16, d.get('length', 0.6) * 0.45))
            hand2 = Vec3(0.0, sy - 0.035, sz)
            block(arms, size=(0.05, 0.06, 0.08), center=hand2, texture=skin)
            block(arms, size=(0.016, 0.03, 0.06), center=hand2 + Vec3(-0.026, 0.035, 0.0), texture=skin)  # fingers up the side
            self._sleeve(arms, hand2 + Vec3(-0.004, -0.028, -0.035), from_camera(-0.1, -0.48, 0.12), sleeve)

    @staticmethod
    def _sleeve(parent, start, end, tex):
        from panda3d.core import Point3
        pivot = node(parent, position=start)
        pivot.lookAt(parent, Point3(end.x, end.y, end.z))
        length = (end - start).length()
        block(pivot, size=(0.078, 0.078, length), center=(0, 0, length / 2), texture=tex)
        block(pivot, size=(0.086, 0.086, 0.035), center=(0, 0, 0.02), color='#55595f')       # cuff

    def rotate_custom(self, axis):
        """F8 / F9: turn a downloaded model that's facing the wrong way (saved to its model.json)."""
        if self.custom is not None:
            custom_models.rotate(self.held, axis)
            self.equip(self.current, force=True)
            self.game.ui.banner('MODEL TURNED', '#7dff8a', 1, 'Saved. F8 = turn sideways, F9 = roll')

    # ── firing ───────────────────────────────────────────────────────────────
    def trigger(self, down):
        if down and not self.trigger_down:
            self.trigger_pressed = True
        self.trigger_down = down

    def start_reload(self):
        d, st = self.held, self.state[self.held['id']]
        if d.get('melee') or self.reloading > 0 or st['ammo'] >= self.stat(d, 'mag'):
            return
        self.reloading = self.reload_total = self.stat(d, 'reload') * self.owner.reload_mult
        self.reload_steps = ['reload_out', 'reload_in', 'pump' if d.get('pellets', 1) > 1 else 'reload_rack']
        self.game.sounds.play(self.reload_steps.pop(0))
        self.game.events.emit('reload', player=self.owner, weapon=d['id'])

    def rate_mult(self):
        p = self.owner
        return p.fire_rate_mult * (2 if p.buffs.get('adrenaline', 0) > 0 else 1)

    def update(self, dt):
        g, d = self.game, self.held
        st = self.state[d['id']]
        self.cooldown -= dt
        if self.reloading > 0:
            self.reloading -= dt
            done = 1 - self.reloading / self.reload_total
            steps = getattr(self, 'reload_steps', [])
            if steps and done >= (0.5 if len(steps) == 2 else 0.85):   # mag in halfway, rack near the end
                g.sounds.play(steps.pop(0), volume=0.9)
            if self.reloading <= 0:
                st['ammo'] = self.stat(d, 'mag')
                self.reloading = 0
                g.ui.update_weapon()

        if d.get('spinup'):
            spinning = self.trigger_down and g.can_act() and self.reloading <= 0
            self.spin = max(0, min(1, self.spin + (dt / d['spinup'] if spinning else -dt / d['spinup'] * 0.7)))
        wants = self.trigger_down if (d.get('auto') or d.get('melee')) else self.trigger_pressed
        if d.get('spinup') and self.spin < 0.3:
            wants = False
        if wants and self.cooldown <= 0 and g.can_act():
            self.fire()
        self.trigger_pressed = False

        # animate the held weapon
        self.kick = max(0, self.kick - dt * 8)
        self.swing = max(0, self.swing - dt * 4)
        self.switch_anim = max(0, self.switch_anim - dt)
        self.flash_t -= dt
        self.flash.enabled = self.flash_t > 0 and not d.get('cone')
        if self.spinner:
            self.spin_angle += dt * 1500 * self.spin
            self.spinner.rotation_z = self.spin_angle
        p = self.owner
        bob_x = math.sin(p.bob) * 0.015 if p.moving else 0
        bob_y = abs(math.cos(p.bob)) * 0.012 if p.moving else 0
        rl = math.sin((1 - self.reloading / self.reload_total) * math.pi) if self.reloading > 0 else 0
        aim = 1 if (g.aiming and not d.get('melee') and self.reloading <= 0) else 0
        self.aim_t = getattr(self, 'aim_t', 0) + (aim - getattr(self, 'aim_t', 0)) * min(1, dt * 12)
        a = self.aim_t
        hx, hy, hz = self.hold_pos(d)
        aim_y = -getattr(self, 'sight_h', 0.06) * self.holder.scale_x     # sights on the crosshair when aiming
        self.holder.position = (hx * (1 - a) + bob_x * (1 - a), hy * (1 - a) + aim_y * a + bob_y - self.switch_anim * 0.8 - rl * 0.1,
                                hz - self.kick * 0.06)
        sw = math.sin(self.swing * math.pi) if d.get('melee') else 0
        self.holder.rotation = (-self.kick * 14 + rl * 35 + sw * 80, -sw * 35, -rl * 17)
        self.flash.position = self.muzzle * 1.0
        self.lens.setAspectRatio(window.aspect_ratio)

    def muzzle_world(self):
        return camera.world_position + camera.forward * 1.0 + camera.right * 0.2 - camera.up * 0.16

    def fire(self):
        g, d, p = self.game, self.held, self.owner
        st = self.state[d['id']]
        eye = Vec3(camera.world_position)
        fwd = Vec3(camera.forward)
        rate = self.stat(d, 'rate') * self.rate_mult() * (max(0.3, self.spin) if d.get('spinup') else 1)
        self.cooldown = 1 / rate
        dm = self.dmg_mult(d)

        if d.get('melee'):
            self.melee(d, eye, fwd, dm)
            return

        if self.reloading > 0:
            return
        if st['ammo'] <= 0:
            g.sounds.play('empty')
            self.start_reload()
            return
        if not g.powerups.active('overdrive'):       # Overdrive power-up: bottomless magazine
            st['ammo'] -= 1
        self.kick = 0.4 if d.get('cone') else 1
        self.flash_t = 0.05
        self.flash.rotation_z = random.random() * 360
        self.flash.scale = 0.75 + random.random() * 0.6
        if not d.get('cone'):
            g.lighting.flash(eye + fwd * 1.2, (1.0, 0.82, 0.55), 9, 1.6, life=0.06)
        p.recoil += (2.3 if d.get('projectile') else min(3, d['damage'] * d.get('pellets', 1) / 70 + 0.3)) \
            * self.mod(d, 'recoil') * (0.7 if g.aiming else 1)
        if not d.get('cone') or random.random() < 0.3:
            g.sounds.shoot(d, self.shot_sound(d))
            if not d.get('projectile') and d.get('sound') not in ('blink', 'spit', 'railspike', 'nailgun') \
                    and random.random() < 0.35:
                invoke(g.sounds.play, 'casing', volume=0.5, pitch=0.9 + random.random() * 0.2, delay=0.25)
        muzzle = self.muzzle_world()

        if d.get('projectile'):
            pr = d['projectile']
            g.projectiles.spawn_rocket(eye + fwd * 0.6, fwd * pr['speed'], pr['radius'],
                                       pr['damage'] * dm / p.damage_mult, d['knockback'])
        elif d.get('cone'):
            self.spray(d, eye, fwd, muzzle, dm)
        else:
            self.shoot_bullets(d, eye, fwd, muzzle, dm)
        if st['ammo'] <= 0:
            self.start_reload()
        g.ui.update_weapon()

    def on_hit(self, d, e, dm):
        """Status effects after a hit."""
        if d.get('lifesteal') and not self.owner.downed:
            o = self.owner
            o.health = min(o.max_health, o.health + d['lifesteal'])
        if e.dead:
            return
        if d.get('burn'):
            e.ignite(d['burn']['dps'] * dm, d['burn']['seconds'])
        if d.get('slow'):
            e.chill(d['slow']['mult'], d['slow']['seconds'])

    def melee(self, d, eye, fwd, dm):
        g = self.game
        self.swing = 1
        g.sounds.play('swing')
        reach = self.stat(d, 'range')
        targets = []
        for e in g.enemies.alive():
            if e.rise > 0.3:
                continue
            to = e.chest_pos() - eye
            dist = max(0, to.length() - e.radius)
            if dist <= reach and to.normalized().dot(fwd) >= 0.55:
                targets.append((dist, e))
        targets.sort(key=lambda t: t[0])
        flat = Vec3(fwd.x, 0, fwd.z).normalized()
        for _, e in targets[:d.get('cleave', 1)]:
            e.hurt(d['damage'] * dm, False, flat * d['knockback'])
            self.on_hit(d, e, dm)
        if targets:
            g.sounds.play('thud')
            g.ui.hitmarker(False)
        elif getattr(g, 'mining', None) is not None:      # nothing to hit: mine the ore node in front of you
            n = g.mining.find(eye, fwd, reach)
            if n is not None:
                dist = (n['pos'] + Vec3(0, 0.45, 0) - eye).length()
                power = d.get('chop', 1) if n['d'].get('wood') else d.get('gather', 1)   # axes chop, picks mine
                g.mining.mine(n, self.owner, power, eye + fwd * max(0.3, dist - 0.4))

    def spray(self, d, eye, fwd, muzzle, dm):
        """Flamethrower-style cone: hits everything in front of you."""
        g = self.game
        cone = d['cone']
        cos_a = math.cos(math.radians(cone['angle']))
        hit = False
        for e in g.enemies.alive():
            if e.rise > 0.3:
                continue
            to = e.chest_pos() - eye
            dist = to.length()
            if dist - e.radius > cone['range'] or dist < 1e-3:
                continue
            if to.normalized().dot(fwd) < cos_a and dist > e.radius + 0.5:
                continue
            if not g.world.line_of_sight(eye, e.chest_pos()):
                continue
            e.hurt(d['damage'] * dm, False, Vec3(fwd.x, 0, fwd.z) * d['knockback'])
            self.on_hit(d, e, dm)
            hit = True
        g.effects.spray(muzzle, fwd, ('#ff8c2a', '#ffcf3a', '#ff4a1a'), count=3,
                        speed=cone['range'] * 1.6, spread=math.radians(cone['angle']) * 0.8, life=0.5)
        if hit:
            g.ui.hitmarker(False)

    def shoot_bullets(self, d, eye, fwd, muzzle, dm):
        g = self.game
        any_hit = any_head = False
        tracer = d.get('tracer', '#fff2a8')
        thick = 'tracer' in d
        for _ in range(d.get('pellets', 1)):
            direction = Vec3(fwd)
            if d.get('spread'):
                s = d['spread'] * (0.45 * self.mod(d, 'aim_spread') if g.aiming else self.mod(d, 'spread'))
                direction += Vec3((random.random() - 0.5) * 2 * s, (random.random() - 0.5) * 2 * s, (random.random() - 0.5) * 2 * s)
                direction = direction.normalized()
            rng = self.stat(d, 'range')
            wall = g.world.raycast(eye, direction, rng)
            if getattr(g, 'quest', None):
                g.quest.on_shot(eye, direction, wall)
            end = eye + direction * wall
            stopped = False
            first = None
            pierce = d.get('pierce')
            can_hit = math.inf if pierce is True else (pierce or 1)
            for dist, e, head in g.enemies.raycast(eye, direction, wall):
                mult = d.get('headshot', 2) if head else 1
                flat = Vec3(direction.x, 0, direction.z)
                e.hurt(d['damage'] * dm * mult, head, flat * d['knockback'])
                self.on_hit(d, e, dm)
                any_hit, any_head = True, any_head or head
                first = first or e
                can_hit -= 1
                if can_hit <= 0:
                    end = eye + direction * dist
                    stopped = True
                    break
            if not stopped and wall < rng:
                g.effects.burst(end, '#8a8a8a', 3, speed=2, size=0.08, life=0.4)
                crate = g.mining.at_point(eye + direction * (wall + 0.05)) if getattr(g, 'mining', None) else None
                if crate is not None:                       # shot a supply crate: bullets break it open too
                    g.mining.mine(crate, self.owner, d['damage'] * dm / 40, end)
            if d.get('chain'):
                g.effects.lightning(muzzle, end, tracer)
                if first:
                    self.chain(d, first, dm)
            else:
                g.effects.tracer(muzzle, end, tracer, 0.05 if thick else 0.02, 0.2 if thick else 0.06)
        if any_hit:
            g.ui.hitmarker(any_head)
            g.sounds.play('headshot' if any_head else 'hit')

    def chain(self, d, first, dm):
        """Lightning jumps from enemy to enemy."""
        g, c = self.game, d['chain']
        hit = {first}
        current, dmg = first, d['damage'] * dm
        for _ in range(c['count']):
            dmg *= c['falloff']
            options = [e for e in g.enemies.alive() if e not in hit and e.rise <= 0.3
                       and (e.chest_pos() - current.chest_pos()).length() <= c['range']]
            options = [e for e in options if g.world.line_of_sight(current.chest_pos(), e.chest_pos())]
            if not options:
                break
            nxt = min(options, key=lambda e: (e.chest_pos() - current.chest_pos()).length())
            g.effects.lightning(current.chest_pos(), nxt.chest_pos(), d.get('tracer', '#c07bff'))
            nxt.hurt(dmg, False, None)
            self.on_hit(d, nxt, dm)
            hit.add(nxt)
            current = nxt
