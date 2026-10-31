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
        lvl = w.total_level(d)
        self.set_text(self.weapon_name, d['name'] + (f'  +{lvl}' if lvl else ''))
        if d.get('melee'):
            self.set_text(self.ammo, '--')
            self.ammo.color = ucolor.white
        else:
            mag = w.stat(d, 'mag')
            self.set_text(self.ammo, f"{st['ammo']} / {mag}")
            self.ammo.color = col('#ff5a5a') if st['ammo'] <= math.ceil(mag * 0.25) else ucolor.white
        self.set_text(self.slots, '  '.join(f'[{i + 1}]' if o is w.held else f' {i + 1} ' for i, o in enumerate(w.owned[:9])))

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
        # version + updates (bottom left)
        a = window.aspect_ratio
        self.version_text = label(m, '', (-a / 2 + 0.03, -0.2), 0.8, '#aaaaaa')
        self.update_button = button(m, 'UPDATE NOW', (-a / 2 + 0.15, -0.44), (0.24, 0.05),
                                    lambda: self.game.install_update(), '#2f7fbf', 0.9)
        self.update_button.enabled = False
        self.credits_text = label(m, '', (a / 2 - 0.03, -0.44), 0.7, '#888888', origin=(0.5, 0))
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
        from .custom_models import credits
        lines = credits()
        self.credits_text.text = ('3D models: ' + ';  '.join(lines)) if lines else ''
        s = g.save
        self.records.text = (f"Best wave {s['best_wave']}   ·   Best score {s['best_score']}   ·   "
                             f"Total kills {s['total_kills']}   ·   Games {s['games']}")

    def update_menu(self):
        u = getattr(self.game, 'updater', None)
        if u is None:
            return
        status = {
            'idle': '', 'checking': 'Checking for updates...', 'up_to_date': 'Up to date',
            'offline': 'Could not check for updates', 'installing': 'Downloading update...',
            'installed': f'Updated to v{u.local}! Restarting...', 'failed': u.message[:120],
        }
        if u.status == 'available':
            notes = [n if len(n) <= 38 else n[:36] + '...' for n in u.notes[:5]]
            text = f'Update available: v{u.remote}\n' + '\n'.join('- ' + n for n in notes)
        else:
            text = status.get(u.status, '')
        self.set_text(self.version_text, f'BLOCKHOLD v{u.local}\n{text}')
        self.update_button.enabled = u.status == 'available'

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
        quad(s, ucolor.Color(0.04, 0.05, 0.08, 0.88), (4, 1), z=1)
        self.shop_title = label(s, '', (0, 0.44), 2.6, YELLOW, origin=(0, 0))
        self.shop_stats = label(s, '', (0, 0.39), 0.9, '#cccccc', origin=(0, 0))
        self.shop_tab = 'weapons'
        self.shop_sel = None
        self.tab_buttons = {
            'weapons': button(s, 'WEAPONS', (-0.11, 0.33), (0.2, 0.05), lambda: self.set_tab('weapons')),
            'player': button(s, 'PLAYER', (0.11, 0.33), (0.2, 0.05), lambda: self.set_tab('player')),
        }
        self.shop_list = Entity(parent=s)
        button(s, 'Close (B)', (-0.2, -0.455), (0.2, 0.05), lambda: self.game.close_shop())
        button(s, 'START NEXT WAVE', (0.12, -0.455), (0.36, 0.06), lambda: self.game.shop_start_wave(), '#4f8a2b', 1.2)

    def set_tab(self, tab):
        self.shop_tab = tab
        self.refresh_shop()

    def select_weapon(self, wid):
        self.shop_sel = wid
        self.refresh_shop()

    def shop_row(self, x, y, title, desc, price, state, on_click, w=0.58, h=0.072, selected=False):
        """state: 'ok' | 'poor' | 'owned'"""
        cont = self.shop_list
        colour = '#4a5468' if selected else ('#262b34' if state == 'owned' else '#363c48')
        b = button(cont, '', (x + w / 2, y), (w, h), on_click, colour)
        tall = h >= 0.06
        label(cont, title, (x + 0.015, y + (0.028 if tall else 0.012)), 1.0 if tall else 0.9,
              '#888888' if state == 'owned' and not selected else YELLOW, z=-0.1)
        if desc:
            label(cont, desc, (x + 0.015, y - (0.002 if tall else 0.006)), 0.72, '#bbbbbb', z=-0.1)
        pc = {'ok': '#f2c230', 'poor': '#ff6a6a', 'owned': '#7dff8a'}[state]
        label(cont, price, (x + w - 0.015, y), 1.0, pc, origin=(0.5, 0), z=-0.1)
        return b

    def weapon_lines(self, d):
        w = self.game.weapons
        dm = 1 + 0.15 * w.level(d, 'damage')
        lines = []
        if d.get('projectile'):
            lines.append(f"Blast damage {round(d['projectile']['damage'] * dm)}  (radius {d['projectile']['radius']}m)")
        elif d.get('pellets', 1) > 1:
            lines.append(f"Damage {w.stat(d, 'damage'):.0f} x {d['pellets']} pellets")
        else:
            lines.append(f"Damage {w.stat(d, 'damage'):.0f}")
        lines.append(f"{'Swings' if d.get('melee') else 'Fire rate'} {w.stat(d, 'rate'):.1f} per second")
        if d.get('melee'):
            lines.append(f"Reach {w.stat(d, 'range'):.1f}m" + (f",  hits up to {d['cleave']} enemies" if d.get('cleave') else ''))
        else:
            lines.append(f"Magazine {w.stat(d, 'mag')}   Reload {w.stat(d, 'reload'):.1f}s")
        if d.get('pierce'):
            lines.append('Goes through enemies')
        if d.get('headshot'):
            lines.append(f"Headshots x{d['headshot']}")
        if d.get('burn'):
            lines.append(f"Burns: {d['burn']['dps'] * dm:.0f} damage/s for {d['burn']['seconds']}s")
        if d.get('slow'):
            lines.append(f"Freezes: {round((1 - d['slow']['mult']) * 100)}% slower for {d['slow']['seconds']}s")
        if d.get('chain'):
            lines.append(f"Lightning jumps to {d['chain']['count']} more enemies")
        if d.get('spinup'):
            lines.append(f"Spins up for {d['spinup']}s before full speed")
        if d.get('move_mult', 1) != 1:
            lines.append(f"You move {round((1 - d['move_mult']) * 100)}% slower holding it")
        return lines

    def refresh_shop(self):
        g, p, w = self.game, self.game.player, self.game.weapons
        for c in list(self.shop_list.children):
            destroy(c)
        self.shop_title.text = f'SHOP      {g.coins} coins'
        self.shop_stats.text = (f'Health {math.ceil(p.health)}/{p.max_health}    Damage {round(p.damage_mult * 100)}%    '
                                f'Speed {round(p.speed_mult * 100)}%    Regen {p.regen:.1f}/s    Armor {round(p.armor * 100)}%')
        for tab, b in self.tab_buttons.items():
            b.color = col('#4f6a9a' if tab == self.shop_tab else DARK)
        if self.shop_tab == 'player':
            self.refresh_player_tab()
        else:
            self.refresh_weapon_tab()

    def refresh_weapon_tab(self):
        g, w = self.game, self.game.weapons
        if self.shop_sel is None or not w.get_def(self.shop_sel):
            self.shop_sel = next((d['id'] for d in WEAPONS if not w.owns(d['id'])), WEAPONS[0]['id'])
        y = 0.27
        for d in WEAPONS:
            owned = w.owns(d['id'])
            lvl = w.total_level(d)
            title = d['name'] + (f'   +{lvl}' if lvl else '')
            price = ('EQUIPPED' if w.held is d else 'OWNED') if owned else str(d['price'])
            state = 'owned' if owned else ('ok' if g.coins >= d['price'] else 'poor')
            self.shop_row(-0.75, y, title, '', price, state, lambda wid=d['id']: self.select_weapon(wid),
                          w=0.5, h=0.04, selected=d['id'] == self.shop_sel)
            y -= 0.045

        d = w.get_def(self.shop_sel)
        cont, x = self.shop_list, -0.2
        quad(cont, '#1c2029', (0.92, 0.68), (x + 0.46, -0.06), z=0.02)
        label(cont, d['name'], (x + 0.03, 0.26), 2.0, YELLOW)
        label(cont, d['desc'], (x + 0.03, 0.2), 0.9, '#dddddd', wordwrap=60)
        label(cont, '\n'.join(self.weapon_lines(d)), (x + 0.03, 0.15), 0.9, '#9ad0ff')
        owned = w.owns(d['id'])
        if not owned:
            ok = g.coins >= d['price']
            button(cont, f"BUY  -  {d['price']} coins", (x + 0.46, -0.1), (0.4, 0.07),
                   lambda: g.buy_weapon(d['id']), '#4f8a2b' if ok else '#5a3030', 1.2)
            return
        if w.held is not d:
            button(cont, 'EQUIP', (x + 0.8, 0.255), (0.14, 0.045), lambda: (w.equip(w.owned.index(d)), self.refresh_shop()), '#4f6a9a')
        label(cont, 'UPGRADES', (x + 0.03, -0.035), 1.0, '#aaaaaa')
        y = -0.085
        for u in w.upgrades_for(d):
            lv = w.level(d, u['id'])
            maxed = lv >= u['max']
            price = w.upgrade_price(d, u['id'])
            pips = '#' * lv + '-' * (u['max'] - lv)
            state = 'owned' if maxed else ('ok' if g.coins >= price else 'poor')
            self.shop_row(x + 0.03, y, f"{u['name']}   [{pips}]", u['desc'], 'MAX' if maxed else str(price), state,
                          lambda uid=u['id']: g.buy_weapon_upgrade(d['id'], uid), w=0.86, h=0.06)
            y -= 0.068

    def refresh_player_tab(self):
        g, p = self.game, self.game.player
        y = 0.25
        for i, u in enumerate(UPGRADES):
            lvl = g.upgrade_levels.get(u['id'], 0)
            price = g.upgrade_price(u)
            maxed = lvl >= u['max']
            useless = u['id'] == 'medkit' and p.health >= p.max_health
            title = u['name'] if u.get('consumable') else f"{u['name']}  (lvl {lvl}/{u['max']})"
            self.shop_row(-0.6 + (i % 2) * 0.62, y - (i // 2) * 0.09, title, u['desc'], 'MAX' if maxed else str(price),
                          'owned' if maxed else ('ok' if g.coins >= price and not useless else 'poor'),
                          lambda uid=u['id']: g.buy_upgrade(uid))

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
