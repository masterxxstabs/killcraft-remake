"""HUD, main menu, pause screen, shop and game-over screen (Ursina UI)."""
import math
import time as pytime
from ursina import Button, Entity, Slider, Text, Vec2, camera, color as ucolor, destroy, window
from .data.abilities import ABILITIES
from .data.upgrades import UPGRADES
from .data.weapons import WEAPONS
from .render import col
from .textures import vignette_texture

YELLOW = '#ffe066'
DARK = '#2c313c'


def quad(parent, color, scale, position=(0, 0), origin=(0, 0), z=0, **kw):
    return Entity(parent=parent, model='quad', color=col(color) if isinstance(color, str) else color,
                  scale=scale, position=position, origin=origin, z=z, **kw)


def label(parent, text='', position=(0, 0), scale=1.0, color='#ffffff', origin=(-0.5, 0.5), **kw):
    return Text(text, parent=parent, position=position, scale=scale, color=col(color), origin=origin, **kw)


def button(parent, text, position, scale, on_click, color=DARK, text_scale=1.0):
    b = Button(parent=parent, text=text, position=position, scale=scale, color=col(color),
               highlight_color=col(color).tint(0.15), pressed_color=col(color).tint(-0.15), on_click=on_click)
    if b.text_entity:
        b.text_entity.scale *= text_scale
    return b


class Bar:
    """A left-to-right fill bar."""
    def __init__(self, parent, position, size, fill, back='#111111'):
        self.back = quad(parent, back, size, position, origin=(-0.5, 0), z=0.01)
        self.fill = quad(parent, fill, size, position, origin=(-0.5, 0))
        self.size = size

    def set(self, frac):
        self.fill.scale_x = self.size[0] * max(0.0, min(1.0, frac))


class UI:
    def __init__(self, game):
        self.game = game
        self.banner_t = 0
        self.hit_t = 0
        self.hurt_t = 0
        self.feed = []
        self._cache = {}
        self.shop_items = []
        self.build_hud()
        self.build_menu()
        self.build_pause()
        self.build_shop()
        self.build_dead()

    def set_text(self, t, value):
        """Only rebuild text when it changes (it's slow-ish)."""
        if self._cache.get(id(t)) != value:
            self._cache[id(t)] = value
            t.text = value

    # ── HUD ──────────────────────────────────────────────────────────────────
    def build_hud(self):
        a = window.aspect_ratio
        L, R, T, B = -a / 2, a / 2, 0.5, -0.5
        h = self.hud = Entity(parent=camera.ui, enabled=False)
        self.vignette = Entity(parent=h, model='quad', texture=vignette_texture(), scale=(a, 1), z=1, color=ucolor.Color(1, 1, 1, 0))
        self.adrenaline = Entity(parent=h, model='quad', texture=vignette_texture((255, 60, 110)), scale=(a, 1), z=1, color=ucolor.Color(1, 1, 1, 0))
        # crosshair + hitmarker
        quad(h, '#ffffff', (0.022, 0.0028))
        quad(h, '#ffffff', (0.0028, 0.022))
        self.hit = Entity(parent=h, enabled=False)
        quad(self.hit, '#ffffff', (0.04, 0.003), rotation_z=45)
        quad(self.hit, '#ffffff', (0.04, 0.003), rotation_z=-45)
        self.reload_bar = Bar(h, (-0.04, -0.045), (0.08, 0.006), '#ffffff', '#000000')

        label(h, 'WAVE', (L + 0.03, T - 0.03), 0.9, '#cccccc')
        self.wave = label(h, '0', (L + 0.03, T - 0.055), 3)
        self.remaining = label(h, '', (L + 0.03, T - 0.135), 1.1)

        self.coins = label(h, '', (R - 0.03, T - 0.03), 2.2, YELLOW, origin=(0.5, 0.5))
        self.score = label(h, '', (R - 0.03, T - 0.09), 1.0, '#dddddd', origin=(0.5, 0.5))
        self.feed_text = label(h, '', (R - 0.03, T - 0.13), 0.9, '#dddddd', origin=(0.5, 0.5))

        self.banner_text = label(h, '', (0, 0.24), 3.2, origin=(0, 0))
        self.banner_sub = label(h, '', (0, 0.175), 1.2, '#eeeeee', origin=(0, 0))

        self.boss = Entity(parent=h, enabled=False)
        self.boss_name = label(self.boss, '', (0, T - 0.05), 1.2, '#ff8c1a', origin=(0, 0))
        self.boss_bar = Bar(self.boss, (-0.35, T - 0.085), (0.7, 0.022), '#a52fc9')

        self.hint = label(h, 'B = shop   ·   N = start the next wave now', (0, B + 0.17), 1.0, '#ffffff', origin=(0, 0))

        self.hp_bar = Bar(h, (L + 0.03, B + 0.05), (0.42, 0.035), '#d93a3a')
        self.hp_text = label(h, '', (L + 0.03 + 0.21, B + 0.05), 1.0, origin=(0, 0), z=-0.1)

        self.ability_back = quad(h, '#111111', (0.075, 0.075), (0, B + 0.06), z=0.01)
        self.ability_fill = quad(h, '#ffffff', (0.075, 0.075), (0, B + 0.06 - 0.0375), origin=(0, -0.5))
        self.ability_cd = label(h, 'Q', (0, B + 0.06), 1.8, origin=(0, 0), z=-0.1)
        self.ability_name = label(h, '', (0, B + 0.115), 0.85, origin=(0, 0))

        self.slots = label(h, '', (R - 0.03, B + 0.15), 1.0, '#bbbbbb', origin=(0.5, 0.5))
        self.weapon_name = label(h, '', (R - 0.03, B + 0.115), 1.2, origin=(0.5, 0.5))
        self.ammo = label(h, '', (R - 0.03, B + 0.085), 2.6, origin=(0.5, 0.5))

    def update_weapon(self):
        w = getattr(self.game, 'weapons', None)
        if not w or not w.held:
            return
        d, st = w.d, w.state[w.d['id']]
        self.set_text(self.weapon_name, d['name'])
        if d.get('melee'):
            self.set_text(self.ammo, '--')
            self.ammo.color = ucolor.white
        else:
            self.set_text(self.ammo, f"{st['ammo']} / {d['mag']}")
            self.ammo.color = col('#ff5a5a') if st['ammo'] <= math.ceil(d['mag'] * 0.25) else ucolor.white
        self.set_text(self.slots, '  '.join(f'[{i + 1}]' if o is w.held else f' {i + 1} ' for i, o in enumerate(w.owned)))

    def banner(self, text, color='#ffffff', duration=2.5, sub=''):
        self.banner_text.text = text
        self.banner_text.color = col(color)
        self.banner_sub.text = sub
        self.banner_t = duration

    def hitmarker(self, head):
        for c in self.hit.children:
            c.color = col('#ff4040') if head else ucolor.white
        self.hit.enabled = True
        self.hit_t = 0.12

    def hurt(self, frac):
        self.hurt_t = min(1, self.hurt_t + 0.35 + frac * 2)

    def kill_feed(self, text):
        self.feed.insert(0, (text, pytime.time()))
        del self.feed[5:]

    def update(self, dt):
        g, p = self.game, self.game.player
        self.hp_bar.set(p.health / p.max_health)
        self.set_text(self.hp_text, f'{math.ceil(p.health)} / {p.max_health}')
        self.set_text(self.coins, f'{g.coins} coins')
        self.set_text(self.score, f'SCORE {g.score}')
        self.set_text(self.wave, str(g.wave_number))
        if g.phase == 'wave':
            self.set_text(self.remaining, f'{g.remaining} enemies left')
        else:
            self.set_text(self.remaining, f'Next wave in {math.ceil(g.intermission)}s')
        self.hint.enabled = g.phase == 'intermission' and not g.shop_open

        now = pytime.time()
        self.feed = [f for f in self.feed if now - f[1] < 3]
        self.set_text(self.feed_text, '\n'.join(f[0] for f in self.feed))

        a = g.ability
        cd = max(0, p.ability_cd)
        self.ability_fill.color = col(a['color'], 0.85 if cd <= 0 else 0.4)
        self.ability_fill.scale_y = 0.075 * (1 - cd / a['cooldown'])
        self.set_text(self.ability_cd, str(math.ceil(cd)) if cd > 0 else 'Q')
        self.set_text(self.ability_name, a['name'])

        w = g.weapons
        self.reload_bar.back.enabled = self.reload_bar.fill.enabled = w.reloading > 0
        if w.reloading > 0:
            self.reload_bar.set(1 - w.reloading / w.reload_total)

        boss = next((e for e in g.enemies.alive() if e.d.get('boss')), None)
        self.boss.enabled = boss is not None
        if boss:
            self.set_text(self.boss_name, boss.d['name'])
            self.boss_bar.set(boss.hp / boss.max_hp)

        if self.banner_t > 0:
            self.banner_t -= dt
            fade = min(1, self.banner_t * 3)
            self.banner_text.alpha = fade
            self.banner_sub.alpha = fade
        if self.hit_t > 0:
            self.hit_t -= dt
            if self.hit_t <= 0:
                self.hit.enabled = False
        self.hurt_t = max(0, self.hurt_t - dt * 1.5)
        low = 0.35 + math.sin(now * 5) * 0.1 if p.health / p.max_health < 0.3 else 0
        self.vignette.alpha = max(self.hurt_t, low)
        self.adrenaline.alpha = 0.8 if p.buffs.get('adrenaline', 0) > 0 else 0

    # ── main menu ────────────────────────────────────────────────────────────
    def build_menu(self):
        m = self.menu = Entity(parent=camera.ui, z=-1)
        quad(m, ucolor.Color(0.04, 0.05, 0.08, 0.55), (4, 1), z=1)
        label(m, 'BLOCK', (-0.02, 0.38), 7, '#8fd14f', origin=(0.5, 0))
        label(m, 'HOLD', (-0.02, 0.38), 7, '#c94a3a', origin=(-0.5, 0))
        label(m, 'Hold the arena. Survive the waves. Spend your coins.', (0, 0.29), 1.1, '#cccccc', origin=(0, 0))
        label(m, 'CHOOSE YOUR ABILITY', (0, 0.22), 1.1, '#aaaaaa', origin=(0, 0))
        self.cards = Entity(parent=m)
        button(m, 'PLAY', (0, -0.12), (0.32, 0.085), lambda: self.game.start_game(), '#4f8a2b', 1.6)
        self.records = label(m, '', (0, -0.2), 1.0, '#aaaaaa', origin=(0, 0))
        label(m, 'WASD move · mouse aim/shoot · Space jump · Shift sprint · 1-6 / wheel switch weapon\n'
                 'R reload · Q ability · B shop (between waves) · N start wave · M mute · F11 fullscreen · Esc pause',
              (0, -0.3), 0.85, '#bbbbbb', origin=(0, 0))
        button(m, 'Quit', (0, -0.41), (0.14, 0.05), lambda: self.game.quit(), DARK, 0.9)
        self.refresh_menu()

    def refresh_menu(self):
        for c in list(self.cards.children):
            destroy(c)
        g = self.game
        n = len(ABILITIES)
        for i, ab in enumerate(ABILITIES):
            x = (i - (n - 1) / 2) * 0.36
            selected = g.ability_id == ab['id']
            b = button(self.cards, '', (x, 0.07), (0.33, 0.24), lambda a=ab: self.pick_ability(a['id']),
                       '#3c4555' if selected else DARK)
            if selected:
                quad(self.cards, ab['color'], (0.34, 0.25), (x, 0.07), z=0.02)
            label(self.cards, ab['name'], (x - 0.15, 0.175), 1.3, ab['color'], z=-0.1)
            label(self.cards, ab['desc'], (x - 0.15, 0.13), 0.85, '#dddddd', wordwrap=30, z=-0.1)
            label(self.cards, f"Cooldown {ab['cooldown']}s", (x - 0.15, -0.025), 0.8, '#999999', z=-0.1)
        s = g.save
        self.records.text = (f"Best wave {s['best_wave']}   ·   Best score {s['best_score']}   ·   "
                             f"Total kills {s['total_kills']}   ·   Games {s['games']}")

    def pick_ability(self, aid):
        self.game.ability_id = aid
        self.game.save_settings()
        self.refresh_menu()

    # ── pause ────────────────────────────────────────────────────────────────
    def build_pause(self):
        p = self.pause = Entity(parent=camera.ui, z=-1, enabled=False)
        quad(p, ucolor.Color(0.04, 0.05, 0.08, 0.75), (4, 1), z=1)
        label(p, 'PAUSED', (0, 0.25), 4, origin=(0, 0))
        g = self.game
        self.sens = Slider(10, 120, default=g.sensitivity, step=1, text='Mouse sensitivity', parent=p,
                           position=(-0.25, 0.1), dynamic=True)
        self.sens.on_value_changed = lambda: g.set_sensitivity(self.sens.value)
        self.vol = Slider(0, 100, default=round(g.sounds.volume * 100), step=1, text='Volume', parent=p,
                          position=(-0.25, 0.03), dynamic=True)
        self.vol.on_value_changed = lambda: g.set_volume(self.vol.value / 100)
        button(p, 'RESUME', (0, -0.08), (0.3, 0.08), lambda: g.resume(), '#4f8a2b', 1.5)
        button(p, 'Quit to menu', (0, -0.18), (0.22, 0.055), lambda: g.to_menu())

    # ── shop ─────────────────────────────────────────────────────────────────
    def build_shop(self):
        s = self.shop = Entity(parent=camera.ui, z=-1, enabled=False)
        quad(s, ucolor.Color(0.04, 0.05, 0.08, 0.85), (4, 1), z=1)
        self.shop_title = label(s, '', (0, 0.43), 3, YELLOW, origin=(0, 0))
        self.shop_stats = label(s, '', (0, 0.37), 0.95, '#cccccc', origin=(0, 0))
        label(s, 'WEAPONS', (-0.6, 0.32), 1.1, '#aaaaaa')
        label(s, 'UPGRADES', (0.02, 0.32), 1.1, '#aaaaaa')
        self.shop_list = Entity(parent=s)
        button(s, 'Close (B)', (-0.2, -0.43), (0.2, 0.06), lambda: self.game.close_shop())
        button(s, 'START NEXT WAVE', (0.12, -0.43), (0.36, 0.07), lambda: self.game.shop_start_wave(), '#4f8a2b', 1.2)

    def shop_row(self, x, y, title, desc, price, state, on_click):
        """state: 'ok' | 'poor' | 'owned'"""
        w, h = 0.58, 0.072
        cont = self.shop_list
        b = button(cont, '', (x + w / 2, y), (w, h), on_click, '#262b34' if state == 'owned' else '#363c48')
        label(cont, title, (x + 0.015, y + 0.028), 1.05, '#888888' if state == 'owned' else YELLOW, z=-0.1)
        label(cont, desc, (x + 0.015, y - 0.002), 0.72, '#bbbbbb', z=-0.1)
        pc = {'ok': '#f2c230', 'poor': '#ff6a6a', 'owned': '#7dff8a'}[state]
        label(cont, price, (x + w - 0.015, y), 1.1, pc, origin=(0.5, 0), z=-0.1)
        return b

    def refresh_shop(self):
        g, p = self.game, self.game.player
        for c in list(self.shop_list.children):
            destroy(c)
        self.shop_title.text = f'SHOP   {g.coins} coins'
        self.shop_stats.text = (f'Health {math.ceil(p.health)}/{p.max_health}    Damage {round(p.damage_mult * 100)}%    '
                                f'Speed {round(p.speed_mult * 100)}%    Regen {p.regen:.1f}/s    Armor {round(p.armor * 100)}%')
        y = 0.26
        for d in WEAPONS:
            if d['price'] == 0:
                continue
            owned = g.weapons.owns(d['id'])
            stats = (f"{d['projectile']['damage']} blast" if d.get('projectile')
                     else f"{d['damage']}{' x ' + str(d['pellets']) if d.get('pellets', 1) > 1 else ''} dmg")
            self.shop_row(-0.6, y, f"{d['name']}   ({stats}, {d['rate']}/s)", d['desc'],
                          'OWNED' if owned else str(d['price']),
                          'owned' if owned else ('ok' if g.coins >= d['price'] else 'poor'),
                          lambda wid=d['id']: g.buy_weapon(wid))
            y -= 0.082
        y = 0.26
        for u in UPGRADES:
            lvl = g.upgrade_levels.get(u['id'], 0)
            price = g.upgrade_price(u)
            maxed = lvl >= u['max']
            useless = u['id'] == 'medkit' and p.health >= p.max_health
            title = u['name'] if u.get('consumable') else f"{u['name']}  (lvl {lvl}/{u['max']})"
            self.shop_row(0.02, y, title, u['desc'], 'MAX' if maxed else str(price),
                          'owned' if maxed else ('ok' if g.coins >= price and not useless else 'poor'),
                          lambda uid=u['id']: g.buy_upgrade(uid))
            y -= 0.082

    # ── game over ────────────────────────────────────────────────────────────
    def build_dead(self):
        d = self.dead = Entity(parent=camera.ui, z=-1, enabled=False)
        quad(d, ucolor.Color(0.08, 0.02, 0.02, 0.8), (4, 1), z=1)
        label(d, 'YOU FELL', (0, 0.25), 5, '#ff5a5a', origin=(0, 0))
        self.record = label(d, '* NEW RECORD *', (0, 0.15), 1.5, '#ffd54a', origin=(0, 0))
        self.dead_stats = label(d, '', (0, 0.05), 1.6, origin=(0, 0))
        button(d, 'PLAY AGAIN', (0, -0.1), (0.32, 0.085), lambda: self.game.start_game(), '#4f8a2b', 1.5)
        button(d, 'Main menu', (0, -0.2), (0.2, 0.055), lambda: self.game.to_menu())

    def show_dead(self, stats, record):
        t = stats['time']
        self.dead_stats.text = (f"Wave {stats['wave']}     Kills {stats['kills']}     "
                                f"Score {stats['score']}     Time {int(t // 60)}:{int(t % 60):02d}")
        self.record.enabled = record
        self.dead.enabled = True
