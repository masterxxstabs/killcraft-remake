"""Ties everything together: main loop, input, waves, shop, saving."""
import json
import math
import random
import time as pytime
from pathlib import Path
from ursina import Entity, application, camera, color as ucolor, held_keys, invoke, mouse, scene, time as utime, window

from .data.abilities import ABILITIES
from .data.upgrades import UPGRADES
from .data.waves import BOSS, INTERMISSION, NORMAL_SKY, build_wave
from .data.weapons import WEAPONS
from .effects import Effects
from .enemies import EnemyManager
from .pickups import Pickups
from .player import Player
from .projectiles import Projectiles
from .render import col, hex_rgb, node, set_fog
from .sounds import Sounds
from .updater import Updater, restart
from .ui import UI
from .weapons import Weapons
from .world import World

SAVE_DIR = Path.home() / '.blockhold'
SAVE_FILE = SAVE_DIR / 'save.json'
SETTINGS_FILE = SAVE_DIR / 'settings.json'


def load_json(path, default):
    try:
        return {**default, **json.loads(path.read_text())}
    except Exception:
        return dict(default)


def write_json(path, data):
    try:
        SAVE_DIR.mkdir(exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
    except Exception as e:
        print('could not save', e)


class Game(Entity):
    def __init__(self, check_updates=False):
        super().__init__()
        camera.fov = 90
        camera.clip_plane_near = 0.05
        self.save = load_json(SAVE_FILE, dict(best_wave=0, best_score=0, total_kills=0, games=0))
        st = load_json(SETTINGS_FILE, dict(sensitivity=40, volume=0.5, ability=ABILITIES[0]['id']))
        self.sensitivity = st['sensitivity']
        self.ability_id = st['ability']
        self.sounds = Sounds()
        self.sounds.volume = st['volume']

        self.state = 'menu'
        self.phase = 'intermission'
        self.shop_open = False
        self.god_mode = False
        self.aiming = False
        self.shake_amt = 0
        self.coins = self.score = self.kills = self.wave_number = self.remaining = 0
        self.time = 0
        self.intermission = 0
        self.upgrade_levels = {}
        self.sky = list(hex_rgb(NORMAL_SKY['sky']) + hex_rgb(NORMAL_SKY['fog']) + (NORMAL_SKY['fog_near'], NORMAL_SKY['fog_far']))
        self.sky_target = list(self.sky)

        self.world = World()
        self.world_root = node()
        self.player = Player(self)
        self.ui = UI(self)
        self.effects = Effects(self)
        self.weapons = Weapons(self)
        self.enemies = EnemyManager(self)
        self.projectiles = Projectiles(self)
        self.pickups = Pickups(self)
        self.weapons.set_visible(False)
        self.apply_sky(NORMAL_SKY, instant=True)
        self.show_cursor(True)
        self.updater = Updater()
        if check_updates:
            self.updater.check_async()

    def install_update(self):
        if self.updater.status != 'available':
            return
        self.updater.install_async()

    def finish_update(self):
        """Called once the update is installed: start the new version."""
        restart()
        application.quit()

    # ── settings / saving ────────────────────────────────────────────────────
    @property
    def ability(self):
        return next((a for a in ABILITIES if a['id'] == self.ability_id), ABILITIES[0])

    def save_settings(self):
        write_json(SETTINGS_FILE, dict(sensitivity=self.sensitivity, volume=self.sounds.volume, ability=self.ability_id))

    def set_sensitivity(self, v):
        self.sensitivity = v
        self.save_settings()

    def set_volume(self, v):
        self.sounds.volume = v
        self.save_settings()

    def show_cursor(self, on):
        mouse.locked = not on
        mouse.visible = on

    def quit(self):
        application.quit()

    # ── flow ─────────────────────────────────────────────────────────────────
    def start_game(self):
        for screen in (self.ui.menu, self.ui.dead, self.ui.pause, self.ui.shop):
            screen.enabled = False
        self.ui.hud.enabled = True
        self.enemies.clear()
        self.projectiles.clear()
        self.pickups.clear()
        self.effects.clear()
        self.world.destroy()
        self.world = World()
        self.player.reset()
        self.weapons.reset()
        self.weapons.set_visible(True)
        self.coins = self.score = self.kills = self.wave_number = self.remaining = 0
        self.time = 0
        self.upgrade_levels = {}
        self.shop_open = False
        self.god_mode = False
        self.state = 'playing'
        self.begin_intermission(8)
        self.ui.banner('GET READY', '#ffe066', 3, 'Survive as many waves as you can')
        self.show_cursor(False)

    def to_menu(self):
        self.aiming = False
        camera.fov = 90
        self.state = 'menu'
        self.shop_open = False
        for screen in (self.ui.hud, self.ui.pause, self.ui.dead, self.ui.shop):
            screen.enabled = False
        self.weapons.set_visible(False)
        self.ui.refresh_menu()
        self.ui.menu.enabled = True
        self.apply_sky(NORMAL_SKY)
        self.show_cursor(True)

    def pause(self):
        self.aiming = False
        camera.fov = 90
        self.ui.scope.enabled = False
        self.weapons.set_visible(True)
        self.state = 'paused'
        self.weapons.trigger(False)
        self.ui.hud.enabled = False
        self.ui.pause.enabled = True
        self.show_cursor(True)

    def resume(self):
        self.ui.pause.enabled = False
        self.ui.hud.enabled = True
        self.state = 'playing'
        self.show_cursor(False)

    def can_act(self):
        return self.state == 'playing' and not self.shop_open and not self.player.dead

    def begin_intermission(self, seconds=INTERMISSION):
        self.phase = 'intermission'
        self.intermission = seconds
        self.apply_sky(NORMAL_SKY)

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
        self.apply_sky({**NORMAL_SKY, **mod} if mod else NORMAL_SKY)
        self.sounds.play('wave_start')
        n = self.wave_number
        if mod:
            self.ui.banner(f"WAVE {n}: {mod['name']}", '#ff8c5a', 3.5, mod['desc'])
        elif BOSS in self.wave['enemies']:
            self.ui.banner(f'WAVE {n}', '#ff5a5a', 3.5, 'A boss approaches...')
        else:
            self.ui.banner(f'WAVE {n}', '#ffffff', 2.5, f'{self.remaining} enemies incoming')

    def end_wave(self):
        bonus = self.wave['clear_bonus']
        self.coins += bonus
        self.score += self.wave_number * 50
        self.sounds.play('wave_clear')
        self.ui.banner('WAVE CLEARED', '#7dff8a', 3, f'+{bonus} coins  ·  press B to open the shop')
        self.begin_intermission()

    # ── shop ─────────────────────────────────────────────────────────────────
    def open_shop(self):
        if self.phase != 'intermission':
            self.ui.banner('SHOP CLOSED', '#ff7070', 1.2, 'The shop opens between waves')
            return
        self.shop_open = True
        self.aiming = False
        camera.fov = 90
        self.ui.scope.enabled = False
        self.weapons.trigger(False)
        self.ui.refresh_shop()
        self.ui.hud.enabled = False
        self.ui.shop.enabled = True
        self.show_cursor(True)

    def close_shop(self):
        if not self.shop_open:
            return
        self.shop_open = False
        self.ui.shop.enabled = False
        self.ui.hud.enabled = True
        self.show_cursor(False)

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

    def buy_upgrade(self, uid):
        u = next(x for x in UPGRADES if x['id'] == uid)
        lvl = self.upgrade_levels.get(uid, 0)
        price = self.upgrade_price(u)
        p = self.player
        if lvl >= u['max'] or self.coins < price or (uid == 'medkit' and p.health >= p.max_health):
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
        if not self.can_act() or self.player.ability_cd > 0:
            return
        self.ability['use'](self)
        self.player.ability_cd = self.ability['cooldown']

    def on_enemy_killed(self, e, headshot):
        self.kills += 1
        self.remaining -= 1
        d = e.d
        self.score += round(d['score'] * (1.5 if headshot else 1) * (1 + self.wave_number * 0.1))
        lo, hi = d['coins']
        coins = round((lo + random.random() * (hi - lo)) * e.coin_mult * (1 + self.wave_number * 0.04))
        self.pickups.drop_coins(e.position, coins)
        if random.random() < (1 if d.get('boss') else 0.07):
            self.pickups.drop(e.position, 'heal', 60 if d.get('boss') else 20)
        self.effects.burst(e.chest_pos(), d['colors']['shirt'], 10, speed=5, size=0.18)
        if d.get('boss'):
            self.ui.banner('BOSS DEFEATED', '#ffd54a', 3)
            self.shake(0.5)
        self.ui.kill_feed(f"{'HEADSHOT ' if headshot else ''}{d['name']} +{coins}")

    def on_player_death(self):
        self.weapons.trigger(False)
        self.aiming = False
        camera.fov = 90
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
        return self.aiming and self.weapons.d.get('scope') and camera.fov < 45

    def update_aim(self, dt):
        d = self.weapons.d
        can_aim = self.aiming and not d.get('melee') and self.can_act() and self.weapons.reloading <= 0
        target = (28 if d.get('scope') else 62) if can_aim else 90
        camera.fov += (target - camera.fov) * min(1, dt * 12)
        scoped = can_aim and d.get('scope') and camera.fov < 45
        self.ui.scope.enabled = bool(scoped)
        self.weapons.set_visible(not scoped)

    def shake(self, n):
        self.shake_amt = min(0.6, self.shake_amt + n)

    # ── sky & fog per wave modifier ──────────────────────────────────────────
    def apply_sky(self, cfg, instant=False):
        c = {**NORMAL_SKY, **cfg}
        self.sky_target = list(hex_rgb(c['sky']) + hex_rgb(c['fog']) + (c['fog_near'], c['fog_far']))
        if instant:
            self.sky = list(self.sky_target)
            self.blend_sky(0)

    def blend_sky(self, k):
        self.sky = [a + (b - a) * k for a, b in zip(self.sky, self.sky_target)]
        s = self.sky
        window.color = ucolor.Color(s[0], s[1], s[2], 1)
        set_fog(scene, s[3:6], s[6], s[7])

    # ── input ────────────────────────────────────────────────────────────────
    def input(self, key):
        if key == 'f11':
            window.fullscreen = not window.fullscreen
        if key == 'm':
            self.sounds.toggle_mute()
        if self.state == 'paused':
            if key == 'escape':
                self.resume()
            return
        if self.state != 'playing':
            return
        if self.shop_open:
            if key in ('b', 'escape'):
                self.close_shop()
            return
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
        elif key in '123456789' and len(key) == 1:
            self.weapons.equip(int(key) - 1)
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

    def keys(self):
        k = held_keys
        return {
            'w': max(k['w'], k['up arrow']), 's': max(k['s'], k['down arrow']),
            'a': max(k['a'], k['left arrow']), 'd': max(k['d'], k['right arrow']),
            'space': k['space'], 'shift': max(k['left shift'], k['right shift'], k['shift']),
        }

    # ── main loop ────────────────────────────────────────────────────────────
    def update(self):
        self.step(min(0.05, utime.dt))

    def step(self, dt):
        self.blend_sky(min(1, dt * 1.5))
        if self.state in ('playing', 'dead'):
            self.simulate(dt)
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
                sens = self.sensitivity * camera.fov / 90     # slower aiming when zoomed in
                p.look(v[0] * sens, v[1] * sens)
            p.update(dt, {} if self.shop_open else self.keys())
            self.weapons.update(dt)

            if self.phase == 'intermission' and not self.shop_open:
                self.intermission -= dt
                if self.intermission <= 0:
                    self.start_wave()
            if self.phase == 'wave':
                self.spawn_t -= dt
                if self.spawn_queue and self.spawn_t <= 0 and self.enemies.alive_count() < self.wave['max_alive']:
                    self.spawn_t = self.wave['spawn_interval'] * (0.6 + random.random() * 0.8)
                    kind = self.spawn_queue.pop(0)
                    self.enemies.spawn(kind, self.wave, self.world.random_spawn(p.position))
                    if kind == BOSS:
                        self.sounds.play('boss_roar')
                        self.shake(0.4)
                if not self.spawn_queue and self.remaining <= 0:
                    self.end_wave()
        self.enemies.update(dt)
        self.projectiles.update(dt)
        self.pickups.update(dt)
        self.ui.update(dt)
