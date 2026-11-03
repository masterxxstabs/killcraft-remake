"""Ties everything together: main loop, input, waves, shop, saving."""
import json
import math
import random
import time as pytime
from pathlib import Path
from ursina import Entity, Vec3, application, camera, color as ucolor, held_keys, invoke, mouse, scene, time as utime, window

from .data.abilities import ABILITIES
from .data.upgrades import UPGRADES
from .data.waves import BOSS, INTERMISSION, build_wave
from .data.atmosphere import ATMOSPHERES, DEFAULT_ATMOSPHERE, TORCH_COLOUR
from .lighting import Lighting
from .sky import Sky
from .data.weapons import WEAPONS
from .effects import Effects
from .net import Events, PlayerInput
from .enemies import RAGDOLLS, EnemyManager
from .ragdoll import Ragdolls
from .pickups import Pickups
from .powerups import PowerUps
from .mining import Mining
from .barricades import Barricades
from .drops import WeaponDrops
from .animals import Animals
from .npcs import Npcs
from .healing import Healing
from .data.barricades import BARRICADES, MAX_CARRIED, PLACE_RANGE
from .player import Player, REVIVE_TIME
from .projectiles import Projectiles
from .render import col, hex_rgb, node, set_fog
from .sounds import Sounds
from .updater import Updater, restart
from .ui import UI, apply_style, apply_theme
from .data.items import HAND_SLOTS
from .data.themes import DEFAULT_STYLE, DEFAULT_THEME, STYLES, THEMES, default_hud
from .weapons import Weapons
from .world import MAX_SIZE, MIN_SIZE, World
from . import maps

from .paths import USER_DIR as SAVE_DIR
SAVE_FILE = SAVE_DIR / 'save.json'
SETTINGS_FILE = SAVE_DIR / 'settings.json'


def merge_hud(saved):
    """Saved HUD settings on top of the defaults (so new HUD parts show up after an update)."""
    hud = default_hud()
    if isinstance(saved, dict):
        for key in ('panel', 'accent', 'health', 'crosshair', 'opacity'):
            if key in saved:
                hud[key] = saved[key]
        for key, pl in (saved.get('parts') or {}).items():
            if key in hud['parts'] and isinstance(pl, dict):
                hud['parts'][key].update({k: pl[k] for k in ('x', 'y', 'on') if k in pl})
    return hud


def load_json(path, default):
    try:
        return {**default, **json.loads(path.read_text())}
    except Exception:
        return dict(default)


def write_json(path, data):
    try:
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
    except Exception as e:
        print('could not save', e)


class Game(Entity):
    def __init__(self, check_updates=False):
        super().__init__()
        camera.fov = 90
        camera.clip_plane_near = 0.05
        camera.clip_plane_far = 1000
        self.save = load_json(SAVE_FILE, dict(best_wave=0, best_score=0, total_kills=0, games=0))
        st = load_json(SETTINGS_FILE, dict(sensitivity=40, volume=0.5, ability=ABILITIES[0]['id'],
                                           fov=90, auto_update=True, muted=False, map=None,
                                           atmosphere=DEFAULT_ATMOSPHERE, arena_size=34, theme=DEFAULT_THEME,
                                           style=DEFAULT_STYLE, hud=None, ragdolls=True))
        self.atmosphere_id = st['atmosphere'] if st['atmosphere'] in ATMOSPHERES else DEFAULT_ATMOSPHERE
        self.atmosphere_override = None      # the map editor uses its own bright look
        self.arena_size = max(MIN_SIZE, min(MAX_SIZE, int(st['arena_size'])))   # random arena size (half width)
        self.theme_id = st['theme'] if st['theme'] in THEMES else DEFAULT_THEME
        self.hud_settings = merge_hud(st['hud'])
        self.style_id = st['style'] if st['style'] in STYLES else DEFAULT_STYLE
        apply_theme(self.theme_id)
        apply_style(self.style_id)
        self.sensitivity = st['sensitivity']
        self.fov = st['fov']
        self.auto_update = st['auto_update']
        RAGDOLLS[0] = bool(st['ragdolls'])
        self.map_stem = st['map'] if st['map'] in [m for m, _ in maps.list_maps()] else None
        self.editor = None
        self.from_editor = None      # map data to return to after a play test
        camera.fov = self.fov
        self.ability_id = st['ability']
        self.sounds = Sounds()
        self.sounds.volume = st['volume']
        self.sounds.muted = st['muted']

        self.state = 'menu'
        self.phase = 'intermission'
        self.shop_open = False
        self.god_mode = False
        self.aiming = False
        self.shake_amt = 0
        self.wave_number = self.remaining = 0
        self.time = 0
        self.intermission = 0
        self.events = Events()
        self._pressed = set()        # keys pressed since the last frame (for PlayerInput)
        self.sky = [0.0] * 11                 # sky rgb, fog rgb, fog near, fog far, ambient rgb
        self.sky_target = list(self.sky)
        self.lighting = Lighting(self)
        self.sky_dome = Sky()

        self.world = World()
        from . import fastloop
        fastloop.install(application.base)        # Ursina's frame loop without the per-entity overhead
        self.world_root = node()
        self.player = Player(self)           # the local player
        self.players = [self.player]         # everyone in the game (more once multiplayer exists)
        self.allies = []                     # friendly NPCs
        self.ui = UI(self)
        self.effects = Effects(self)
        self.weapons = Weapons(self)
        self.ragdolls = Ragdolls(self)          # dead zombies go limp
        self.enemies = EnemyManager(self)
        self.projectiles = Projectiles(self)
        self.pickups = Pickups(self)
        self.powerups = PowerUps(self)
        self.mining = Mining(self)
        self.barricades = Barricades(self)
        self.drops = WeaponDrops(self)          # guns dropped with X
        self.animals = Animals(self)            # deer, pigs and chickens
        self.npcs = Npcs(self)                  # traders, quest givers and talkers from the map
        self.healing = Healing(self)            # bandages, medkits and food take time to use
        self.build_kind = None       # build mode: which barricade is being placed (None = not building)
        self.build_rot = 0
        self.build_spot = None
        self.craft_open = False
        self.weapons.set_visible(False)
        self.apply_sky(instant=True)
        self.show_cursor(True)
        self.updater = Updater()
        if check_updates and self.auto_update:
            self.updater.check_async()

    def install_update(self):
        if self.updater.status != 'available':
            return
        self.updater.install_async()

    def finish_update(self):
        """Called once the update is installed: start the new version."""
        restart(self.updater)
        application.quit()

    # ── settings / saving ────────────────────────────────────────────────────
    @property
    def ability(self):
        return next((a for a in ABILITIES if a['id'] == self.ability_id), ABILITIES[0])

    def save_settings(self):
        write_json(SETTINGS_FILE, dict(sensitivity=self.sensitivity, volume=self.sounds.volume, ability=self.ability_id,
                                       fov=self.fov, auto_update=self.auto_update, muted=self.sounds.muted,
                                       map=self.map_stem, atmosphere=self.atmosphere_id, arena_size=self.arena_size,
                                       theme=self.theme_id, style=self.style_id, hud=self.hud_settings,
                                       ragdolls=RAGDOLLS[0]))

    def set_sensitivity(self, v):
        self.sensitivity = v
        self.save_settings()

    def set_fov(self, v):
        self.fov = v
        if not self.aiming:
            camera.fov = v
        self.save_settings()

    def toggle_fullscreen(self):
        window.fullscreen = not window.fullscreen

    def toggle_auto_update(self):
        self.auto_update = not self.auto_update
        self.save_settings()

    def toggle_ragdolls(self):
        RAGDOLLS[0] = not RAGDOLLS[0]
        self.save_settings()

    def toggle_mute(self):
        self.sounds.toggle_mute()
        self.save_settings()

    def set_volume(self, v):
        self.sounds.volume = v
        self.save_settings()

    def show_cursor(self, on):
        mouse.locked = not on
        mouse.visible = on
        # Ursina raycasts for whatever is under the cursor every frame (and loops over every entity when it
        # misses). Nothing needs that while you're aiming with a locked mouse, so it only runs with a cursor.
        mouse.update_step = 1 if on else 10 ** 9
        mouse._i = 0

    def quit(self):
        application.quit()

    # ── flow ─────────────────────────────────────────────────────────────────
    def select_map(self, stem):
        self.map_stem = stem
        self.save_settings()

    def set_theme(self, tid):
        """Recolour every screen with another UI theme."""
        self.theme_id = tid
        apply_theme(tid)
        self.save_settings()
        self.ui.rebuild()

    def set_style(self, sid):
        """Reshape every screen: corners, outlines, see-through panels and font."""
        self.style_id = sid
        apply_style(sid)
        self.save_settings()
        self.ui.rebuild()

    def save_hud(self, rebuild=True):
        self.save_settings()
        if rebuild:
            self.ui.rebuild_hud()

    def set_arena_size(self, half):
        self.arena_size = half
        self.save_settings()

    def start_game(self, map_data=None, from_editor=False):
        """Start a run on map_data, or on the map picked in the menu (None = random arena)."""
        if map_data is None and not from_editor and self.map_stem:
            try:
                map_data = maps.load_map(self.map_stem)
            except Exception as e:
                print('could not load map', self.map_stem, e)
        self.from_editor = map_data if from_editor else None
        self.atmosphere_override = None
        for screen in (self.ui.menu, self.ui.dead, self.ui.pause, self.ui.shop):
            screen.enabled = False
        self.ui.hud.enabled = True
        self.enemies.clear()
        self.projectiles.clear()
        self.pickups.clear()
        self.powerups.clear()
        self.effects.clear()
        self.clear_allies()
        self.exit_build()
        self.barricades.clear()
        self.drops.clear()
        self.mining.clear()
        self.animals.clear()
        self.npcs.clear()
        self.world.destroy()
        self.world = World(map_data=map_data, size=self.arena_size)
        self.sky_dome.set_arena(self.world.half)
        self.lighting.clear()
        self.start_quest()
        self.player.reset()
        self.player.position = Vec3(self.world.player_spawn)
        self.mining.reset()
        self.animals.reset()
        self.npcs.reset()
        self.weapons.reset()
        self.weapons.set_visible(True)
        self.wave_number = self.remaining = 0
        self.time = 0
        self.shop_open = False
        self.god_mode = False
        self.state = 'playing'
        self.begin_intermission(8)
        self.ui.banner('GET READY', '#ffe066', 3, 'Survive as many waves as you can')
        self.show_cursor(False)

    def to_menu(self):
        self.close_shop()
        self.clear_allies()
        self.powerups.clear()
        self.exit_build()
        self.barricades.clear()
        self.drops.clear()
        self.mining.clear()
        self.animals.clear()
        self.npcs.clear()
        self.end_quest()
        if self.from_editor is not None:            # play test: go back to the editor
            data, self.from_editor = self.from_editor, None
            for screen in (self.ui.hud, self.ui.pause, self.ui.dead, self.ui.shop):
                screen.enabled = False
            self.enemies.clear()
            self.projectiles.clear()
            self.pickups.clear()
            self.open_editor(data)
            return
        self.aiming = False
        camera.fov = self.fov
        self.state = 'menu'
        self.shop_open = False
        for screen in (self.ui.hud, self.ui.pause, self.ui.dead, self.ui.shop):
            screen.enabled = False
        self.weapons.set_visible(False)
        self.ui.refresh_menu()
        self.ui.menu.enabled = True
        self.apply_sky()
        self.show_cursor(True)

    # ── map editor ───────────────────────────────────────────────────────────
    def open_editor(self, map_data=None, stem=None):
        from .editor import Editor
        self.ui.menu.enabled = False
        self.weapons.set_visible(False)
        self.state = 'editor'
        self.world.destroy()
        self.atmosphere_override = 'editor'
        self.apply_sky(instant=True)
        self.editor = Editor(self, map_data, stem)
        self.show_cursor(True)

    def close_editor(self):
        if self.editor:
            self.editor.close()
            self.editor = None
        self.atmosphere_override = None
        self.apply_sky(instant=True)
        self.world = World()
        self.to_menu()

    def pause(self):
        self.aiming = False
        camera.fov = self.fov
        self.ui.scope.enabled = False
        self.weapons.set_visible(True)
        self.state = 'paused'
        self.weapons.trigger(False)
        self.ui.hud.enabled = False
        self.ui.show_pause()
        self.show_cursor(True)

    def resume(self):
        self.ui.pause.enabled = False
        self.ui.hud.enabled = True
        self.state = 'playing'
        self.show_cursor(False)

    def can_act(self):
        return self.state == 'playing' and not self.shop_open and not self.player.dead and self.player.using is None

    def begin_intermission(self, seconds=INTERMISSION):
        self.phase = 'intermission'
        self.intermission = seconds
        self.apply_sky()

    def start_wave(self):
        if self.phase != 'intermission':
            return
        self.wave_number += 1
        self.wave = build_wave(self.wave_number)
        self.spawn_queue = list(self.wave['enemies'])
        self.remaining = len(self.spawn_queue)
        self.spawn_t = 1
        self.phase = 'wave'
        mod = self.wave['modifier']
        self.apply_sky(mod)
        self.sounds.play('wave_start')
        self.events.emit('wave_started', wave=self.wave_number)
        n = self.wave_number
        if mod:
            self.ui.banner(f"WAVE {n}: {mod['name']}", '#ff8c5a', 3.5, mod['desc'])
        elif BOSS in self.wave['enemies']:
            self.ui.banner(f'WAVE {n}', '#ff5a5a', 3.5, 'A boss approaches...')
        else:
            self.ui.banner(f'WAVE {n}', '#ffffff', 2.5, f'{self.remaining} enemies incoming')

    def end_wave(self):
        bonus = self.wave['clear_bonus']
        for p in self.players:
            p.coins += bonus
            p.score += self.wave_number * 50
        for p in self.players:
            p.revive(0.5)
        for a in self.allies:                    # everyone gets patched up between waves
            a.revive(1.0)
            a.hp = a.max_hp
        self.events.emit('wave_cleared', wave=self.wave_number)
        self.sounds.play('wave_clear')
        self.ui.banner('WAVE CLEARED', '#7dff8a', 3, f'+{bonus} coins  ·  press B to open the shop')
        self.begin_intermission()

    # ── shop ─────────────────────────────────────────────────────────────────
    def open_shop(self):
        if self.player.downed:
            return
        if self.phase != 'intermission':
            self.ui.banner('SHOP CLOSED', '#ff7070', 1.2, 'The shop opens between waves')
            return
        self.exit_build()
        self.shop_open = True
        self.aiming = False
        camera.fov = self.fov
        self.ui.scope.enabled = False
        self.weapons.trigger(False)
        self.ui.refresh_shop()
        self.ui.hud.enabled = False
        self.ui.shop.enabled = True
        self.show_cursor(True)

    def close_shop(self):
        if not self.shop_open:
            return
        self.ui.bag.close()            # the backpack / furnace screen (drops whatever you were dragging back in)
        self.ui.talk.close()
        self.shop_open = False
        self.craft_open = False
        self.ui.shop.enabled = False
        self.ui.craft.enabled = False
        self.ui.hud.enabled = True
        self.show_cursor(False)

    # ── crafting ─────────────────────────────────────────────────────────────
    def near_bench(self, player=None, reach=2.8):
        p = player or self.player
        return any((Vec3(b.x - p.position.x, 0, b.z - p.position.z)).length() < reach for b in self.world.benches)

    def open_craft(self):
        """The workbench menu. Unlike the shop it works during waves too, so watch your back."""
        if self.player.downed or self.shop_open or not self.near_bench():
            return
        self.exit_build()
        self.shop_open = self.craft_open = True
        self.aiming = False
        camera.fov = self.fov
        self.ui.scope.enabled = False
        self.weapons.trigger(False)
        self.ui.refresh_craft()
        self.ui.hud.enabled = False
        self.ui.craft.enabled = True
        self.show_cursor(True)

    def open_bag(self, furnace=None):
        """The backpack (I), or a furnace's screen (E next to it, the backpack is shown too)."""
        if self.player.downed or self.player.dead or self.shop_open:
            return
        self.exit_build()
        self.shop_open = True
        self.aiming = False
        camera.fov = self.fov
        self.ui.scope.enabled = False
        self.weapons.trigger(False)
        self.ui.hud.enabled = False
        self.ui.bag.open(furnace)
        self.show_cursor(True)

    def open_talk(self, npc):
        """Talk to an NPC (E next to them)."""
        if self.player.downed or self.player.dead or self.shop_open:
            return
        self.exit_build()
        self.shop_open = True
        self.aiming = False
        camera.fov = self.fov
        self.ui.scope.enabled = False
        self.weapons.trigger(False)
        self.ui.hud.enabled = False
        self.ui.talk.open(npc)
        self.show_cursor(True)

    def can_craft(self, r, player=None):
        p = player or self.player
        return all(p.resources.get(res, 0) >= n for res, n in r['cost'].items())

    def craft_blocker(self, r, player=None):
        """Why recipe r can't be crafted right now ('' if it can)."""
        p = player or self.player
        if r['kind'] == 'weapon' and self.weapons.owns(r['weapon']):
            return 'OWNED'
        if r['kind'] == 'heal' and p.health >= p.max_health:
            return 'FULL HEALTH'
        if r['kind'] == 'item' and p.inventory.free_spot(r['item']) is None:
            return 'NO ROOM'
        if r['kind'] == 'placeable' and p.placeables.get(r['placeable'], 0) >= MAX_CARRIED:
            return 'CARRYING MAX'
        if not self.can_craft(r, p):
            return 'NEED MORE'
        return ''

    def craft(self, rid, player=None):
        from .data.crafting import recipe
        p = player or self.player
        r = recipe(rid)
        if r is None or self.craft_blocker(r, p):
            self.sounds.play('deny')
            return False
        for res, n in r['cost'].items():
            p.resources[res] -= n
        if r['kind'] == 'weapon':
            self.weapons.give(r['weapon'])
        elif r['kind'] == 'heal':
            p.heal(r['amount'])
        elif r['kind'] == 'item':
            p.inventory.add(r['item'], 1)
        elif r['kind'] == 'placeable':
            p.placeables[r['placeable']] = p.placeables.get(r['placeable'], 0) + 1
        self.events.emit('crafted', player=p, recipe=rid)
        if p.is_local:
            self.sounds.play('craft')
            self.ui.kill_feed(f"Crafted {r['name']}")
            self.ui.refresh_craft()
        return True

    def shop_start_wave(self):
        self.close_shop()
        self.start_wave()

    def upgrade_price(self, u):
        return round(u['price'] * u['growth'] ** self.upgrade_levels.get(u['id'], 0))

    def buy_weapon(self, wid):
        d = next(w for w in WEAPONS if w['id'] == wid)
        if self.weapons.owns(wid) or self.coins < d['price']:
            self.sounds.play('deny')
            return
        self.coins -= d['price']
        self.weapons.give(wid)
        self.ui.shop_sel = wid
        self.sounds.play('buy')
        self.ui.refresh_shop()

    def buy_weapon_upgrade(self, wid, uid):
        w = self.weapons
        d = w.get_def(wid)
        u = next(x for x in w.upgrades_for(d) if x['id'] == uid)
        price = w.upgrade_price(d, uid)
        if not w.owns(wid) or w.level(d, uid) >= u['max'] or self.coins < price:
            self.sounds.play('deny')
            return
        self.coins -= price
        w.upgrade(d, uid)
        self.sounds.play('buy')
        self.ui.refresh_shop()

    def buy_attachment(self, wid, aid):
        """Buy (if needed) and fit an attachment. aid=None takes the slot's attachment off."""
        w = self.weapons
        d = w.get_def(wid)
        from .data.attachments import ATTACHMENTS
        if aid is None:
            return
        a = ATTACHMENTS[aid]
        owned = w.owned_att.setdefault(wid, set())
        if aid not in owned:
            if self.coins < a['price']:
                self.sounds.play('deny')
                return
            self.coins -= a['price']
            owned.add(aid)
            self.sounds.play('buy')
        else:
            self.sounds.play('equip')
        current = w.attach.get(wid, {}).get(a['slot'])
        w.fit(d, a['slot'], None if current == aid else aid)       # clicking the fitted one takes it off
        self.ui.refresh_shop()

    def buy_camo(self, wid, camo):
        from .gunsmith import CAMOS
        w = self.weapons
        if camo not in w.owned_camos:
            if self.coins < CAMOS[camo]['price']:
                self.sounds.play('deny')
                return
            self.coins -= CAMOS[camo]['price']
            w.owned_camos.add(camo)
            self.sounds.play('buy')
        w.set_camo(w.get_def(wid), camo)
        self.ui.refresh_shop()

    # ── allies ───────────────────────────────────────────────────────────────
    def hire_ally(self, kind):
        from .allies import Ally
        from .data.allies import ALLY_TYPES, MAX_ALLIES
        mine = [a for a in self.allies if a.owner is self.player]
        price = ALLY_TYPES[kind]['price']
        if len(mine) >= MAX_ALLIES or self.coins < price:
            self.sounds.play('deny')
            return
        self.coins -= price
        slot = next(i for i in range(MAX_ALLIES) if i not in [a.slot for a in mine])
        p = self.player
        back = Vec3(-math.sin(math.radians(p.yaw)), 0, -math.cos(math.radians(p.yaw)))
        ally = Ally(self, kind, p, p.position + back * 2 + Vec3((slot - 1) * 1.5, 0, 0), slot)
        self.allies.append(ally)
        self.events.emit('ally_hired', ally=ally, player=p)
        self.sounds.play('buy')
        self.ui.refresh_shop()

    def start_quest(self):
        from .quests import HollowLanceQuest
        self.end_quest()
        self.quest = HollowLanceQuest(self)

    def end_quest(self):
        if getattr(self, 'quest', None):
            self.quest.destroy()
        self.quest = None

    def save_progress(self):
        write_json(SAVE_FILE, self.save)

    def clear_allies(self):
        for a in self.allies:
            a.destroy()
        self.allies = []

    def update_revives(self, dt, inp):
        """Hold E next to a downed ally to get them back up."""
        p = self.player
        if p.downed:
            helper = next((a for a in self.allies if a.reviving), None)
            msg = f'{helper.name} is coming for you' if helper else 'Waiting for an ally'
            self.ui.set_prompt(f'{msg}   {math.ceil(p.bleed)}s', p.revive_progress / REVIVE_TIME if helper else None)
            return
        if p.using is not None:                     # bandaging / eating: show how long it's got left
            self.ui.set_prompt(self.healing.label(p), p.using['t'] / p.using['total'])
            return
        near = None
        for a in self.allies:
            if a.downed and (a.position - p.position).length() < 2.6:
                near = a
                break
        for a in self.allies:
            if a is not near:
                a.revive_progress = 0
        if near is None:
            drop_msg = self.drops.prompt(p)
            if drop_msg:
                self.ui.set_prompt(drop_msg)
                return
            npc_msg = self.npcs.prompt(p)
            if npc_msg:
                self.ui.set_prompt(npc_msg)
                return
            if self.near_bench():
                self.ui.set_prompt('Press E to use the workbench')
                return
            msg, progress = self.barricades.interact(p, inp.use, dt)
            self.ui.set_prompt(msg or '', progress)
            return
        if inp.use:
            near.revive_progress += dt
            if near.revive_progress >= 2.0:
                near.revive(0.5)
                self.sounds.play('heal')
                self.ui.set_prompt('')
                return
            self.ui.set_prompt(f'Reviving {near.name}...', near.revive_progress / 2.0)
        else:
            self.ui.set_prompt(f'Hold E to revive {near.name}')

    def buy_upgrade(self, uid):
        u = next(x for x in UPGRADES if x['id'] == uid)
        lvl = self.upgrade_levels.get(uid, 0)
        price = self.upgrade_price(u)
        p = self.player
        if lvl >= u['max'] or self.coins < price or (uid == 'medkit' and p.inventory.free_spot('medkit') is None):
            self.sounds.play('deny')
            return
        self.coins -= price
        if not u.get('consumable'):
            self.upgrade_levels[uid] = lvl + 1
        u['apply'](p)
        self.sounds.play('buy')
        self.ui.refresh_shop()

    # ── events ───────────────────────────────────────────────────────────────
    def use_ability(self):
        if not self.can_act() or self.player.ability_cd > 0 or self.player.downed:
            return
        self.ability['use'](self)
        self.player.ability_cd = self.ability['cooldown']

    def on_enemy_killed(self, e, headshot, attacker=None):
        attacker = attacker or self.player
        owner = getattr(attacker, 'owner', attacker)       # allies earn for the player who hired them
        self.remaining -= 1
        d = e.d
        if attacker is not owner and hasattr(attacker, 'kills'):
            attacker.kills += 1                             # for the ally's line on the scoreboard
        if hasattr(owner, 'kills'):
            owner.kills += 1
            owner.score += round(d['score'] * (1.5 if headshot else 1) * (1 + self.wave_number * 0.1))
        self.events.emit('enemy_killed', enemy=e, attacker=attacker, headshot=headshot)
        lo, hi = d['coins']
        coins = round((lo + random.random() * (hi - lo)) * e.coin_mult * (1 + self.wave_number * 0.04)
                      * self.powerups.coin_mult())
        self.pickups.drop_coins(e.position, coins)
        self.powerups.on_kill(e)
        if random.random() < (1 if d.get('boss') else 0.07):
            self.pickups.drop(e.position, 'heal', 60 if d.get('boss') else 20)
        self.effects.burst(e.chest_pos(), d['colors']['shirt'], 10, speed=5, size=0.18)
        if d.get('boss'):
            self.ui.banner('BOSS DEFEATED', '#ffd54a', 3)
            self.shake(0.5)
        self.ui.kill_feed(f"{'HEADSHOT ' if headshot else ''}{d['name']} +{coins}")

    def on_player_death(self, player=None):
        if player is not None and not player.is_local:
            return                       # (multiplayer: a team-mate went down)
        self.close_shop()                # the workbench can be open mid-wave
        self.weapons.trigger(False)
        self.aiming = False
        camera.fov = self.fov
        self.state = 'dead'
        self.sounds.play('game_over')
        s = self.save
        stats = dict(wave=self.wave_number, kills=self.kills, score=self.score, time=self.time)
        record = self.score > s['best_score'] or self.wave_number > s['best_wave']
        s['best_wave'] = max(s['best_wave'], self.wave_number)
        s['best_score'] = max(s['best_score'], self.score)
        s['total_kills'] += self.kills
        s['games'] += 1
        write_json(SAVE_FILE, s)

        def show():
            if self.state != 'dead':
                return
            self.ui.hud.enabled = False
            self.weapons.set_visible(False)
            self.ui.show_dead(stats, record)
            self.show_cursor(True)
        invoke(show, delay=1.2)

    def is_scoped(self):
        return self.aiming and self.weapons.has_scope(self.weapons.d) and camera.fov < 45

    def update_aim(self, dt):
        d = self.weapons.d
        can_aim = self.aiming and not d.get('melee') and self.can_act() and self.weapons.reloading <= 0
        scope = self.weapons.has_scope(d)
        target = (28 if scope else self.fov * 0.68 / self.weapons.mod(d, 'zoom')) if can_aim else self.fov
        camera.fov += (target - camera.fov) * min(1, dt * 12)
        scoped = can_aim and scope and camera.fov < 45
        self.ui.scope.enabled = bool(scoped)
        self.weapons.set_visible(not scoped and self.build_kind is None)   # building: hands are busy

    def shake(self, n):
        self.shake_amt = min(0.6, self.shake_amt + n)

    # ── sky & fog per wave modifier ──────────────────────────────────────────
    def atmosphere(self):
        return ATMOSPHERES[self.atmosphere_override or self.atmosphere_id]

    def set_atmosphere(self, aid):
        self.atmosphere_id = aid
        self.save_settings()
        in_wave = self.state in ('playing', 'paused') and self.phase == 'wave' and getattr(self, 'wave', None)
        self.apply_sky(self.wave.get('modifier') if in_wave else None, instant=True)

    def apply_sky(self, mod=None, instant=False):
        """Sky, fog and light level: the chosen atmosphere, tinted by a wave modifier (Blood Moon...)."""
        a = self.atmosphere()
        sky, fog, near, far = hex_rgb(a['sky']), hex_rgb(a['fog']), a['fog_near'], a['fog_far']
        if self.atmosphere_override == 'editor':          # big maps: see further while editing
            k = max(1.0, self.world.half / 60)
            near, far = near * k, far * k
        if mod and 'sky' in mod:
            k = a['mod_dim']
            sky = tuple(c * k for c in hex_rgb(mod['sky']))
            fog = tuple(c * k for c in hex_rgb(mod.get('fog', mod['sky'])))
            near, far = min(near, mod.get('fog_near', near)), min(far, mod.get('fog_far', far))
        self.sky_target = list(sky + fog + (near, far) + tuple(a['ambient']))
        self.lighting.set_atmosphere(a)
        self.sky_dome.set_style(a)
        if instant:
            self.sky = list(self.sky_target)
            self.blend_sky(0)

    def blend_sky(self, k):
        self.sky = [a + (b - a) * k for a, b in zip(self.sky, self.sky_target)]
        s = self.sky
        window.color = ucolor.Color(s[3], s[4], s[5], 1)
        set_fog(scene, s[3:6], s[6], s[7])
        self.sky_dome.set_colours(s[0:3], s[3:6], s[7], 0.85 if s[8] > 0.9 else 0.55)
        amb = s[8:11]
        self.lighting.set_ambient(amb)
        # the gun in your hands is lit by your torch
        t = self.lighting.torch * 0.45
        vm = tuple(min(1.0, amb[i] + t * TORCH_COLOUR[i]) for i in range(3))
        from panda3d.core import LVecBase3f
        self.weapons.vm_root.setShaderInput('ambient', LVecBase3f(*vm))

    # ── build mode (G): placing crafted barricades ─────────────────────────────
    def owned_placeables(self):
        p = self.player
        return [k for k in BARRICADES if p.placeables.get(k, 0) > 0]

    def toggle_build(self, step=1, wrap=False):
        """G: start building, or switch to the next barricade you have (past the last one: stop)."""
        p = self.player
        if p.downed or p.dead or self.shop_open:
            return
        owned = self.owned_placeables()
        if not owned:
            self.exit_build()
            self.ui.banner('NOTHING TO BUILD', '#d9912b', 1.6, 'Craft barricades at a workbench first')
            self.sounds.play('deny')
            return
        if self.build_kind not in owned:
            self.build_kind = owned[0]
        else:
            i = owned.index(self.build_kind) + step
            if not wrap and i >= len(owned):
                self.exit_build()
                return
            self.build_kind = owned[i % len(owned)]
        self.weapons.trigger(False)
        self.aiming = False
        self.weapons.set_visible(False)

    def exit_build(self):
        if getattr(self, 'build_kind', None) is None:
            return
        self.build_kind = None
        self.build_spot = None
        self.barricades.hide_ghost()
        self.ui.set_build_hint('')
        if self.state == 'playing':
            self.weapons.set_visible(True)

    def update_build(self):
        """Move the see-through preview to where you're looking."""
        kind = self.build_kind
        if kind is None:
            return
        p = self.player
        if p.downed or p.dead or self.shop_open:
            self.exit_build()
            return
        if p.placeables.get(kind, 0) <= 0:
            owned = self.owned_placeables()
            if not owned:
                self.exit_build()
                return
            kind = self.build_kind = owned[0]
        eye, fwd = p.eye(), p.forward()
        flat = Vec3(fwd.x, 0, fwd.z).normalized()
        reach = PLACE_RANGE
        if fwd.y < -0.05:
            reach = min(reach, eye.y / -fwd.y * Vec3(fwd.x, 0, fwd.z).length())
        reach = max(1.8, reach)
        spot = Vec3(p.position.x, 0, p.position.z) + flat * reach
        rot = (round(p.yaw / 90) * 90 + self.build_rot) % 360    # long side faces you
        why = self.barricades.can_place(kind, spot.x, spot.z, rot, p)
        self.build_spot = (spot.x, spot.z, rot, why)
        self.barricades.show_ghost(kind, spot.x, spot.z, rot, not why)
        d = BARRICADES[kind]
        self.ui.set_build_hint(f"{d['name'].upper()}   x{p.placeables.get(kind, 0)}", why)

    def try_place(self):
        if self.build_kind is None or self.build_spot is None:
            return
        x, z, rot, why = self.build_spot
        if why:
            self.sounds.play('deny')
            return
        self.barricades.place(self.player, self.build_kind, x, z, rot)

    # ── input ────────────────────────────────────────────────────────────────
    def input(self, key):
        if self.ui.hud_editor is not None:          # the HUD editor has the keyboard and mouse
            return
        self._pressed.add(key)
        if key == 'f11':
            window.fullscreen = not window.fullscreen
        if self.state == 'editor' and self.editor.typing():     # typing a name: keys are letters, not shortcuts
            self.editor.input(key)
            return
        if key == 'm':
            self.toggle_mute()
        if self.state == 'editor':
            self.editor.input(key)
            return
        if self.state == 'paused':
            if key == 'escape':
                self.resume()
            return
        if self.state != 'playing':
            return
        if self.shop_open:
            if self.ui.bag.active and self.ui.bag.input(key):
                return
            if key in ('b', 'escape') or (key == 'e' and self.craft_open) or \
                    (key in ('i', 'e', 'tab') and self.ui.bag.active) or (key == 'e' and self.ui.talk.active):
                self.close_shop()
            return
        if self.player.using is not None and key in ('left mouse down', '1', '2', '3', 'r', 'scroll up',
                                                     'scroll down', 'g', 'q'):
            self.healing.cancel(self.player, '')        # shooting, reloading or switching stops it
            return
        if key == 'h' and not self.player.downed and self.build_kind is None:
            self.healing.quick(self.player)
            return
        if key == 'x' and self.build_kind is None:
            self.drops.drop(self.player)
            return
        if key == 'e' and self.drops.nearest(self.player.position) is not None and not self.player.downed:
            self.drops.pick_up(self.player)
            return
        if key == 'i' and not self.player.downed:
            self.open_bag()
            return
        npc = self.npcs.nearest(self.player.position)
        if key == 'e' and npc is not None and not self.player.downed:
            self.open_talk(npc)
            return
        fur = self.barricades.nearest(self.player.position, 2.2, kinds=('furnace',))[0]
        if key == 'e' and fur is not None and not self.player.downed:
            self.open_bag(fur)
            return
        if key == 'e' and self.near_bench() and not self.player.downed:
            self.open_craft()
            return
        if key == 'g':
            self.toggle_build()
            return
        if self.build_kind is not None:
            if key == 'left mouse down':
                if not mouse.locked:
                    self.show_cursor(False)
                self.try_place()
                return
            if key in ('right mouse down', 'escape'):
                self.exit_build()
                return
            if key == 'r':
                self.build_rot = (self.build_rot + 90) % 360
                return
            if key in ('scroll up', 'scroll down'):
                self.toggle_build(step=-1 if key == 'scroll up' else 1, wrap=True)
                return
            if key in ('left mouse up', 'right mouse up'):
                return
            if (key in '123456789' and len(key) == 1) or key == 'b':
                self.exit_build()            # picking a weapon or opening the shop ends build mode
        if key == 'escape':
            self.pause()
        elif key == 'left mouse down':
            if not mouse.locked:
                self.show_cursor(False)
            self.weapons.trigger(True)
        elif key == 'left mouse up':
            self.weapons.trigger(False)
        elif key == 'right mouse down':
            self.aiming = True
        elif key == 'right mouse up':
            self.aiming = False
        elif key in ('1', '2', '3'):              # tool, handgun, rifle
            self.weapons.equip_slot(HAND_SLOTS[int(key) - 1][0])
        elif key == 'scroll down':
            self.weapons.cycle(1)
        elif key == 'scroll up':
            self.weapons.cycle(-1)
        elif key == 'r':
            self.weapons.start_reload()
        elif key == 'f8':
            self.weapons.rotate_custom('yaw')
        elif key == 'f9':
            self.weapons.rotate_custom('roll')
        elif key == 'q':
            self.use_ability()
        elif key == 'b':
            self.open_shop()
        elif key in ('n', 'enter') and self.phase == 'intermission':
            self.start_wave()

    def local_input(self):
        """This frame's PlayerInput from the keyboard (a remote player's comes from the network)."""
        k = held_keys
        crouch = bool(k['c'] or k['left control'] or k['control'])
        inp = PlayerInput(
            move_x=max(k['d'], k['right arrow']) - max(k['a'], k['left arrow']),
            move_z=max(k['w'], k['up arrow']) - max(k['s'], k['down arrow']),
            jump=bool(k['space']), jump_pressed='space' in self._pressed,
            sprint=bool(k['left shift'] or k['right shift'] or k['shift']),
            crouch=crouch, crouch_pressed=bool({'c', 'left control', 'control'} & self._pressed),
            use=bool(k['e']),
        )
        self._pressed.clear()
        return inp

    # ── who is where (players and friendly NPCs) ─────────────────────────────
    def targets(self):
        """Everything zombies can attack: living players and allies."""
        return [p for p in self.players if not p.dead and not p.downed] + [a for a in self.allies if not a.dead]

    def can_go_down(self, player):
        """A player only goes down (instead of dying) while one of their allies is still standing."""
        return any(a.owner is player and not a.downed for a in self.allies)

    def nearest_target(self, pos):
        best, best_d = None, math.inf
        for t in self.targets():
            d = (t.position.x - pos.x) ** 2 + (t.position.z - pos.z) ** 2
            if d < best_d:
                best, best_d = t, d
        return best

    def nearest_player(self, pos):
        alive = [p for p in self.players if not p.dead] or self.players
        return min(alive, key=lambda p: (p.position.x - pos.x) ** 2 + (p.position.z - pos.z) ** 2)

    # ── each player's economy; these read / write the local player's ──────────
    coins = property(lambda self: self.player.coins, lambda self, v: setattr(self.player, 'coins', v))
    score = property(lambda self: self.player.score, lambda self, v: setattr(self.player, 'score', v))
    kills = property(lambda self: self.player.kills, lambda self, v: setattr(self.player, 'kills', v))
    upgrade_levels = property(lambda self: self.player.upgrade_levels,
                              lambda self, v: setattr(self.player, 'upgrade_levels', v))

    # ── main loop ────────────────────────────────────────────────────────────
    def update(self):
        self.step(min(0.05, utime.dt))

    def step(self, dt):
        self.blend_sky(min(1, dt * 1.5))
        self.sky_dome.update(dt)
        self.lighting.update(dt)
        if self.state != 'editor':
            self.world.update_view(camera.world_position, self.sky[7] + 10, dt)   # hide regions lost in the fog
        if self.state in ('playing', 'dead'):
            self.simulate(dt)
        elif self.state == 'editor':
            self.editor.update(dt)
        elif self.state == 'menu':
            self.ui.update_menu()
            if self.updater.status == 'installed' and not getattr(self, '_restarting', False):
                self._restarting = True
                invoke(self.finish_update, delay=1.5)
            t = pytime.time() * 0.08
            x, z = math.cos(t) * 26, math.sin(t) * 26
            camera.position = (x, 14, z)
            camera.rotation = (math.degrees(math.atan2(14, 26)), math.degrees(math.atan2(-x, -z)), 0)
        self.shake_amt = max(0, self.shake_amt - dt * 1.5)
        self.effects.update(dt)

    def simulate(self, dt):
        p = self.player
        if self.state == 'playing' and not p.dead:
            self.time += dt
            self.update_aim(dt)
            if mouse.locked and not self.shop_open:
                v = mouse.velocity
                sens = self.sensitivity * camera.fov / self.fov     # slower aiming when zoomed in
                p.look(v[0] * sens, v[1] * sens)
            inp = PlayerInput() if self.shop_open else self.local_input()
            self.update_revives(dt, inp)
            if self.quest:
                self.quest.update(dt, inp.use)
            p.update(dt, inp)
            p.apply_camera(dt)
            self.weapons.update(dt)
            self.update_build()

            if self.phase == 'intermission' and not self.shop_open:
                self.intermission -= dt
                if self.intermission <= 0:
                    self.start_wave()
            if self.phase == 'wave':
                self.spawn_t -= dt
                if self.spawn_queue and self.spawn_t <= 0 and self.enemies.alive_count() < self.wave['max_alive']:
                    self.spawn_t = self.wave['spawn_interval'] * (0.6 + random.random() * 0.8)
                    kind = self.spawn_queue.pop(0)
                    near = random.choice([q for q in self.players if not q.dead] or self.players)
                    self.enemies.spawn(kind, self.wave, self.world.random_spawn(near.position))
                    if kind == BOSS:
                        self.sounds.play('boss_roar')
                        self.shake(0.4)
                if not self.spawn_queue and self.remaining <= 0:
                    self.end_wave()
        self.enemies.update(dt)
        for a in self.allies:
            a.update(dt)
        self.projectiles.update(dt)
        self.pickups.update(dt)
        if self.state == 'playing':
            self.powerups.update(dt)
            self.mining.update(dt)
            self.barricades.update(dt)
            self.animals.update(dt)
            self.npcs.update(dt)
            self.healing.update(dt)
        self.drops.update(dt)
        self.ui.update(dt)
