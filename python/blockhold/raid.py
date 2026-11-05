"""The extraction loop: the hideout, raids, your kit and the bank.

The game starts in the HIDEOUT (maps/hideout.json, see hideout.py): a safe place under
ground with the banker, merchants, your stash and a workbench. Climb the ladder (E) to
pick a RAID. Up top zombies keep climbing out of the ground around you (more the longer
you stay, tougher in higher-level zones). Stand in an extraction point to get out with
everything you carry; die and it's gone, and you wake up in the hideout with the
starting kit.

What you carry and wear, and the weapons you own, are your KIT. It's saved when you go up
the ladder, when you get out and whenever you leave the hideout. Quitting the game in the
middle of a raid counts as dying there. Coins, your bank (items) and your level and
skills are always safe.
Events: raid_started, raid_extracted, raid_lost.
"""
import copy
import math
import random
from ursina import Vec3
from . import maps
from .data.items import GEAR_SLOTS
from .data.merchants import BANK_GRID
from .data.raids import (DESPAWN_DIST, EXIT_NAMES, EXIT_RADIUS, EXIT_TIME, RAIDS, RAMP_EVERY, SPAWN_EVERY,
                         XP_EXTRACT, XP_PER_MINUTE)
from .data.waves import BOSS, weights
from .inventory import Grid

HIDEOUT = 'hideout'


def calm_wave(max_alive=30):
    """What zombies scale from outside of waves (their level does the rest)."""
    return dict(number=0, enemies=[], modifier=None, max_alive=max_alive, spawn_interval=SPAWN_EVERY, hp_mult=1,
                damage_mult=1, speed_mult=1, coin_mult=1, clear_bonus=0)


def clean(v):
    """A deep copy that saves to JSON (no drag bookkeeping, no sets)."""
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items() if k != '_g'}
    if isinstance(v, (list, tuple, set)):
        return [clean(x) for x in v]
    return v


def pick_kind(level):
    w = weights(max(1, round(level * 1.6)))
    kinds = [k for k in w if w[k] > 0]
    if level >= 10 and random.random() < 0.004:
        return BOSS
    return random.choices(kinds, weights=[w[k] for k in kinds])[0]


def bearing(player, pos):
    """'ahead', 'to your left', 'behind you'... for a point."""
    dx, dz = pos.x - player.position.x, pos.z - player.position.z
    a = (math.degrees(math.atan2(dx, dz)) - player.yaw + 540) % 360 - 180      # 0 = straight ahead
    for limit, word in ((25, 'ahead'), (70, 'ahead-right'), (115, 'right'), (160, 'behind-right')):
        if abs(a) <= limit:
            return word.replace('right', 'left') if a < 0 else word
    return 'behind'


class Raids:
    def __init__(self, game):
        self.game = game
        self.mode = None          # 'hideout', 'raid' (or None: the old wave mode, editor play tests)
        self.raid = None          # the raid you're on (a RAIDS entry, or one made for a custom map)
        self.practice = False     # an editor play test: nothing is saved or lost
        self.t = 0.0
        self.spawn_t = 0.0
        self.extract_t = 0.0
        self.exits = []           # extraction zone props
        self.note = None          # a message for when you arrive in the hideout
        s = game.save
        if s.get('raid_active'):                     # quit in the middle of a raid last time
            s['raid_active'] = False
            s['kit'] = None
            self.note = ('RAID ABANDONED', 'You left in the middle of a raid. What you carried is gone.')
            game.save_progress()

    # ── the bank ─────────────────────────────────────────────────────────────
    @property
    def bank_items(self):
        return self.game.save.setdefault('bank', [])

    def bank(self):
        """The bank, as a container the inventory screen can open."""
        return dict(id='bank', kind='bank', d=dict(name='Bank', grid=BANK_GRID), items=self.bank_items, sack=False,
                    bank=True, pos=None)

    def bank_grid(self):
        return Grid('loot', 'BANK', BANK_GRID[0], BANK_GRID[1], self.bank_items)

    def to_bank(self, item_id, n=1):
        """Put n of item_id in the bank. Returns how many didn't fit."""
        return self.bank_grid().add(item_id, n)

    def bank_count(self, item_id):
        return sum(it['n'] for it in self.bank_items if it['id'] == item_id)

    def from_bank(self, item_id, n=1):
        taken = 0
        for it in sorted([i for i in self.bank_items if i['id'] == item_id], key=lambda i: i['n']):
            k = min(it['n'], n - taken)
            it['n'] -= k
            taken += k
            if it['n'] <= 0:
                self.bank_items.remove(it)
            if taken >= n:
                break
        return taken

    # ── your kit ─────────────────────────────────────────────────────────────
    def snapshot(self):
        p, w = self.game.player, self.game.weapons
        inv = p.inventory
        return clean(dict(equipped=inv.equipped, pockets=inv.pockets,
                          hands={s: (d['id'] if d else None) for s, d in w.slots.items()},
                          held=w.held['id'] if w.held else None,
                          weapons={wid: w.pack_of(wid) for wid in w.state}))

    def save_kit(self):
        """Write your kit, coins and bank to the save file (not during play tests)."""
        if self.practice:
            return
        g = self.game
        s = g.save
        s['kit'] = self.snapshot()
        s['coins'] = g.player.coins
        s['camos'] = sorted(g.weapons.owned_camos)
        g.progress.store(g.player)
        g.save_progress()

    def load_kit(self):
        g, p, w = self.game, self.game.player, self.game.weapons
        p.coins = int(g.save.get('coins', 0))
        w.owned_camos = set(g.save.get('camos', ['factory'])) | {'factory'}
        kit = g.save.get('kit')
        if not kit:
            return                                    # the starting kit (a fresh inventory and the free weapons)
        inv = p.inventory
        inv.equipped = {slot: copy.deepcopy(kit.get('equipped', {}).get(slot)) for slot, _ in GEAR_SLOTS}
        inv.pockets = copy.deepcopy(kit.get('pockets', []))
        w.restore(kit.get('weapons', {}), kit.get('hands', {}), kit.get('held'))
        hands = {d['id'] for d in w.owned}
        for g_ in inv.grids():                       # weapon tiles must match the weapons you own
            for it in list(g_.items):
                if it['id'].startswith('w_') and (it['id'][2:] not in w.state or it['id'][2:] in hands):
                    g_.items.remove(it)
        in_grids = {it['id'][2:] for it in inv.items if it['id'].startswith('w_')}
        for wid in w.state:
            if wid not in hands and wid not in in_grids:
                inv.add('w_' + wid)
        inv.changed()

    # ── going places ─────────────────────────────────────────────────────────
    def options(self):
        """Raids you can go on: the generated ones, then your maps with extraction points."""
        out = [dict(r, kind='random') for r in RAIDS]
        for stem, name in maps.list_maps():
            if stem == HIDEOUT:
                continue
            try:
                data = maps.load_map(stem)
            except Exception:
                continue
            exits = sum(1 for e in data.get('props', []) if e and e[0] == 'zone_extract')
            if exits:
                out.append(dict(id=stem, name=name, kind='map', size=data.get('size', 34), exits=exits,
                                levels=None, zombies=(8, 24), desc=f'Your map. {exits} way{"s" if exits > 1 else ""} out.'))
        return out

    def hideout_map(self):
        try:
            return maps.load_map(HIDEOUT)
        except Exception:
            from .hideout import build_hideout
            return build_hideout()

    def enter_hideout(self, note=None):
        g = self.game
        self.note = note or self.note
        g.start_game(self.hideout_map(), mode='hideout')

    def start_raid(self, option):
        g = self.game
        self.save_kit()                               # what you take up the ladder
        g.save['raid_active'] = True
        g.save_progress()
        data = maps.load_map(option['id']) if option.get('kind') == 'map' else None
        if data is None:
            g.arena_size_override = option['size']
        g.start_game(data, mode='raid', raid=option)

    def begin(self, mode, raid=None, practice=False):
        """Called by start_game once the world, player and weapons are set up."""
        g = self.game
        self.mode, self.raid, self.practice = mode, raid, practice
        self.t = self.spawn_t = self.extract_t = 0.0
        self.exits = []
        if not practice:
            self.load_kit()
        if mode == 'hideout':
            g.mining.clear()                          # no ore growing out of the floor down here
            g.animals.clear()
            g.atmosphere_override = 'hideout'
            g.apply_sky(instant=True)
            if self.note:
                g.ui.banner(self.note[0], '#4fd8ff' if 'EXTRACT' in self.note[0] else '#d9912b', 4.0, self.note[1])
                self.note = None
            else:
                g.ui.banner('THE HIDEOUT', '#e8c040', 3.0, 'Climb the ladder (south) to go on a raid')
            return
        g.wave = calm_wave(raid['zombies'][1] + 6 if raid else 30)
        if raid and raid.get('kind') == 'random':
            self.lay_out(raid)
        self.exits = list(g.world.zones.get('extraction', []))
        for z in self.exits:                          # a flare on every way out
            g.world.add_prop('extract_beacon', z['x'], z['z'])
        name = raid['name'] if raid else g.world.name
        g.ui.banner(name.upper(), '#ffffff', 3.5,
                    f'{len(self.exits)} way{"s" if len(self.exits) != 1 else ""} out. Find one and stand in it.'
                    if self.exits else 'No way out on this map: survive as long as you can.')
        g.events.emit('raid_started', raid=name)

    def lay_out(self, raid):
        """A generated raid: level zones (worse in the middle), a spot to start on and ways out at the edges."""
        g = self.game
        w = g.world
        half = w.half
        lo1, hi1, lo2, hi2 = raid['levels']
        mid = ((lo1 + lo2) // 2, (hi1 + hi2) // 2)
        for radius, (lo, hi) in ((int(half * 1.5), (lo1, hi1)), (int(half * 0.75), mid), (int(half * 0.4), (lo2, hi2))):
            w.add_prop('zone_level', 0.5, 0.5, data=dict(radius=radius, min_level=lo, max_level=hi))
        start = random.random() * math.tau
        g.player.position = self.free_spot(start, half - 12)
        names = random.sample(EXIT_NAMES, raid['exits'])
        for k, name in enumerate(names):
            a = start + math.pi * (0.45 + 1.1 * k / max(1, raid['exits'] - 1)) if raid['exits'] > 1 else start + math.pi
            spot = self.free_spot(a, half - 9)
            w.add_prop('zone_extract', spot.x, spot.z, data=dict(radius=EXIT_RADIUS, time=EXIT_TIME, name=name))

    def free_spot(self, angle, dist):
        w = self.game.world
        for k in range(200):
            a = angle + (random.random() - 0.5) * 0.3 * (1 + k / 40)
            r = dist - random.random() * min(dist * 0.5, k * 0.3)
            gx, gz = w.to_grid(math.cos(a) * r, math.sin(a) * r)
            if w.free(gx, gz, 1):
                return Vec3(gx - w.half + 0.5, 0, gz - w.half + 0.5)
        return Vec3(w.player_spawn)

    def extract(self):
        g = self.game
        mins = self.t / 60
        g.progress.add_xp(g.player, XP_EXTRACT + XP_PER_MINUTE * mins, 'extract')
        g.save['raid_active'] = False
        g.save['extractions'] = g.save.get('extractions', 0) + 1
        g.save['total_kills'] = g.save.get('total_kills', 0) + g.kills
        self.save_kit()
        g.sounds.play('wave_clear')
        g.events.emit('raid_extracted', raid=self.raid['name'] if self.raid else '', time=self.t)
        self.enter_hideout(('EXTRACTED', f'You made it out after {int(mins)}:{int(self.t % 60):02d} with '
                                         f'everything you carried.'))

    def lost(self):
        """You died up top: your kit stays where you fell."""
        g = self.game
        if self.practice or self.mode != 'raid':
            return
        g.save['raid_active'] = False
        g.save['kit'] = None
        g.save['coins'] = g.player.coins
        g.save['raids_lost'] = g.save.get('raids_lost', 0) + 1
        g.save_progress()
        g.events.emit('raid_lost', raid=self.raid['name'] if self.raid else '')

    def leave(self):
        """Back to the main menu from the hideout (your kit is saved)."""
        if self.mode == 'hideout':
            self.save_kit()

    # ── per frame (in a raid) ────────────────────────────────────────────────
    def nearest_exit(self):
        p = self.game.player
        best, best_d = None, 1e9
        for z in self.exits:
            d = math.hypot(z['x'] - p.position.x, z['z'] - p.position.z)
            if d < best_d:
                best, best_d = z, d
        return best, best_d

    def status(self):
        """The HUD line: where the nearest way out is."""
        if self.mode == 'hideout':
            return 'Hideout  ·  safe'
        z, d = self.nearest_exit()
        mins = f'{int(self.t // 60)}:{int(self.t % 60):02d}'
        if z is None:
            return f'Raid  ·  {mins}'
        return f"{z['data'].get('name', 'Exit')}  {round(d)} m {bearing(self.game.player, Vec3(z['x'], 0, z['z']))}"

    def prompt(self):
        """(text, progress) while you're extracting, else None."""
        if self.mode != 'raid' or not self.exits:
            return None
        p = self.game.player
        z = self.game.world.zone_at('extraction', p.position.x, p.position.z)
        if z is None:
            return None
        need = z['data'].get('time', EXIT_TIME)
        return f"EXTRACTING: {z['data'].get('name', 'Exit')}  {max(0, math.ceil(need - self.extract_t))}s", \
            min(1.0, self.extract_t / need)

    def update(self, dt):
        if self.mode != 'raid':
            return
        g = self.game
        p = g.player
        if p.dead:
            return
        self.t += dt
        # extraction
        z = g.world.zone_at('extraction', p.position.x, p.position.z) if self.exits else None
        if z is not None and not p.downed:
            self.extract_t += dt
            if self.extract_t >= z['data'].get('time', EXIT_TIME):
                self.extract()
                return
        else:
            self.extract_t = 0.0
        # zombies climb out around you, more the longer you stay
        lo, hi = self.raid['zombies'] if self.raid else (8, 24)
        target = min(hi, lo + int(self.t / RAMP_EVERY))
        players = [q for q in g.players if not q.dead]
        alive = 0
        for e in list(g.enemies.list):
            if e.dead:
                continue
            if all(math.hypot(e.position.x - q.position.x, e.position.z - q.position.z) > DESPAWN_DIST for q in players):
                e.destroy()                            # wandered off
                g.enemies.list.remove(e)
                continue
            alive += 1
        self.spawn_t -= dt
        if alive < target and self.spawn_t <= 0:
            self.spawn_t = SPAWN_EVERY * (0.6 + random.random() * 0.8)
            w = g.world
            spot = w.random_spawn(p.position)
            for _ in range(6):
                if not w.in_safe_zone(spot.x, spot.z) and w.zone_at('extraction', spot.x, spot.z) is None:
                    break
                spot = w.random_spawn(p.position)
            level = w.zombie_level(spot.x, spot.z) or 1
            kind = pick_kind(level)
            g.enemies.spawn(kind, g.wave, spot, level=level, wave_member=False)
            if kind == BOSS:
                g.sounds.play('boss_roar')
                g.ui.banner('SOMETHING BIG', '#ff5a5a', 3, 'The Hollow King is up here with you')
