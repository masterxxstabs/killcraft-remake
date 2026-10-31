"""The secret quest: THE HOLLOW LANCE.

1. Three soul lanterns are hidden around every map. You hear whispers near them.
   Shoot one (or press E next to it) to light it.
2. When all three burn, a bone altar rises. Zombies killed near it feed it souls.
3. A full altar summons the Hollow Herald.
4. The Herald drops the Hollow Lance, a weapon you can't buy.

Everything is driven by the event bus, so it will also work in co-op later.
"""
import math
import random
from ursina import Entity, Vec3
from .lowpoly import LowPoly
from .net import new_id
from .render import col, node, destroy

SOULS_NEEDED = 20
ALTAR_RADIUS = 7.5


def _lantern_mesh(lit):
    lp = LowPoly(seed=3)
    lp.cylinder((0, 0, 0), 0.06, 1.2, '#2a2230', sides=5)
    lp.box((0, 1.25, 0), (0.34, 0.06, 0.34), '#1d1e22')
    lp.box((0, 1.62, 0), (0.34, 0.06, 0.34), '#1d1e22')
    for x, z in ((-0.15, -0.15), (0.15, -0.15), (-0.15, 0.15), (0.15, 0.15)):
        lp.box((x, 1.44, z), (0.035, 0.36, 0.035), '#1d1e22')
    lp.blob((0, 1.44, 0), 0.11 if lit else 0.07, '#ffd27a' if lit else '#7a4fb0', detail=1, jitter=0.05)
    lp.cylinder((0, 1.65, 0), 0.12, 0.12, '#1d1e22', sides=4, top_radius=0)
    return lp.mesh()


def _altar_mesh():
    lp = LowPoly(seed=9)
    lp.cylinder((0, 0, 0), 1.3, 0.25, '#4a4450', sides=8, top_colour='#5a5460')
    lp.cylinder((0, 0.25, 0), 0.9, 0.35, '#e6dfcf', sides=8, top_colour='#d9d0bc')
    for i in range(6):                                    # bone spikes
        a = i / 6 * math.tau
        lp.beam((math.cos(a) * 0.95, 0.2, math.sin(a) * 0.95), (math.cos(a) * 1.15, 1.3, math.sin(a) * 1.15),
                0.08, '#efe8d8', end_radius=0.02)
    lp.blob((0, 0.95, 0), 0.32, '#e6dfcf', detail=1, jitter=0.08)   # skull
    lp.box((-0.1, 1.0, 0.27), (0.1, 0.1, 0.05), '#1d1e22')
    lp.box((0.1, 1.0, 0.27), (0.1, 0.1, 0.05), '#1d1e22')
    return lp.mesh()


def _soul_orb_mesh():
    lp = LowPoly(seed=5)
    lp.blob((0, 0, 0), 0.25, '#d6a3ff', detail=1, jitter=0.1, colours=['#d6a3ff', '#b37bff', '#f0d9ff'])
    return lp.mesh()


class HollowLanceQuest:
    def __init__(self, game):
        self.game = game
        self.root = node(game.world_root)
        self.lanterns = []         # dicts: id, pos, lit, entity
        self.altar = None
        self.souls = 0
        self.stage = 'lanterns'    # lanterns -> altar -> herald -> reward -> done
        self.reward = None
        self.whisper_t = 4.0
        self.heard = False
        self.t = 0.0
        game.events.on('enemy_killed', self.on_kill)
        self.place_lanterns()

    def destroy(self):
        self.game.events.off('enemy_killed', self.on_kill)
        destroy(self.root)

    # ── setup ────────────────────────────────────────────────────────────────
    def free_spot(self, near=None, min_from_player=15, avoid=(), min_apart=12, tries=400):
        w, g = self.game.world, self.game
        spawn = w.player_spawn
        for _ in range(tries):
            if near is not None:
                x = near.x + (random.random() - 0.5) * 2 * 8
                z = near.z + (random.random() - 0.5) * 2 * 8
            else:
                x = (random.random() - 0.5) * 2 * (w.half - 3)
                z = (random.random() - 0.5) * 2 * (w.half - 3)
            x, z = math.floor(x) + 0.5, math.floor(z) + 0.5
            if w.blocked(x, z, 0.6, 0) or w.height_at(x, z) > 0:
                continue
            if math.hypot(x - spawn.x, z - spawn.z) < min_from_player:
                continue
            if any(math.hypot(x - a.x, z - a.z) < min_apart for a in avoid):
                continue
            # prefer spots tucked next to something (behind walls, trees, crates)
            cover = sum(1 for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)) if w.height_at(x + dx, z + dz) > 0)
            if near is None and cover == 0 and random.random() < 0.7:
                continue
            return Vec3(x, 0, z)
        return Vec3((random.random() - 0.5) * w.half, 0, (random.random() - 0.5) * w.half)

    def place_lanterns(self):
        spots = []
        for _ in range(3):
            spots.append(self.free_spot(avoid=spots))
        for p in spots:
            e = node(self.root, model=_lantern_mesh(False), position=p, rotation_y=random.random() * 90)
            self.lanterns.append(dict(id=new_id(), pos=p, lit=False, entity=e))

    # ── progress ─────────────────────────────────────────────────────────────
    def lights(self):
        """Lit lanterns and the altar's soul orb give off a purple glow."""
        out = [(l['pos'] + Vec3(0, 1.45, 0), (0.8, 0.5, 1.0), 6, 1.0) for l in self.lanterns if l['lit']]
        if getattr(self, 'orb', None) is not None and self.stage in ('altar', 'herald'):
            out.append((Vec3(self.orb.world_position), (0.75, 0.45, 1.0), 9, 1.2))
        if self.reward is not None:
            out.append((Vec3(self.reward.world_position), (0.85, 0.6, 1.0), 7, 1.3))
        return out

    def light(self, lantern, player=None):
        g = self.game
        if lantern['lit']:
            return
        lantern['lit'] = True
        lantern['entity'].model = _lantern_mesh(True)
        lantern['entity'].setShaderInput('glow', 0.7)
        g.effects.burst(lantern['pos'] + Vec3(0, 1.45, 0), '#ffd27a', 14, speed=3, size=0.1, gravity=-3)
        g.sounds.play('powerup', pitch=0.7)
        lit = sum(1 for l in self.lanterns if l['lit'])
        g.events.emit('quest_progress', quest='hollow_lance', stage='lanterns', value=lit)
        if lit < 3:
            g.ui.kill_feed(f'A lantern flickers to life... ({lit}/3)')
        else:
            self.raise_altar()

    def raise_altar(self):
        g = self.game
        self.stage = 'altar'
        pos = self.free_spot(near=Vec3(0, 0, 0), min_from_player=4, min_apart=0)
        self.altar_pos = pos
        self.altar = node(self.root, model=_altar_mesh(), position=pos - Vec3(0, 1.5, 0))
        self.orb = Entity(parent=self.root, model=_soul_orb_mesh(), position=pos + Vec3(0, 1.9, 0), scale=0.3)
        g.ui.banner('THE ALTAR AWAKENS', '#c07bff', 4, 'Kill zombies near it to feed it souls')
        g.sounds.play('boss_roar', pitch=1.4, volume=0.6)
        g.shake(0.3)
        g.events.emit('quest_progress', quest='hollow_lance', stage='altar', value=0)

    def on_kill(self, enemy, attacker=None, headshot=False, **_):
        g = self.game
        if self.stage == 'altar' and (enemy.position - self.altar_pos).length() < ALTAR_RADIUS:
            self.souls = min(SOULS_NEEDED, self.souls + (5 if enemy.d.get('boss') else 1))
            g.effects.lightning(enemy.chest_pos(), self.altar_pos + Vec3(0, 1.9, 0), '#d6a3ff', segments=6, life=0.25)
            g.events.emit('quest_progress', quest='hollow_lance', stage='altar', value=self.souls)
            if self.souls >= SOULS_NEEDED:
                self.summon()
        elif self.stage == 'herald' and enemy.kind == 'hollow_herald':
            self.drop_reward(Vec3(enemy.position.x, 0, enemy.position.z))

    def summon(self):
        g = self.game
        self.stage = 'herald'
        g.remaining += 1                          # the wave isn't over until the Herald falls
        g.enemies.spawn('hollow_herald', g.wave if g.phase == 'wave' else _calm_wave(g), self.altar_pos + Vec3(2.5, 0, 0))
        g.ui.banner('THE HOLLOW HERALD', '#c07bff', 4, 'Something answers the altar...')
        g.sounds.play('boss_roar', pitch=0.8)
        g.shake(0.5)

    def drop_reward(self, pos):
        g = self.game
        self.stage = 'reward'
        self.reward_pos = pos + Vec3(0, 1.2, 0)
        self.reward = Entity(parent=self.root, model=_soul_orb_mesh(), position=self.reward_pos, scale=1.2)
        g.ui.banner('A WEAPON REMAINS', '#d6a3ff', 4, 'Pick up what the Herald left behind')

    def claim(self, player):
        g = self.game
        self.stage = 'done'
        destroy(self.reward)
        self.reward = None
        g.weapons.give('hollow_lance')
        g.save['lance'] = True
        g.save_progress()
        g.ui.banner('THE HOLLOW LANCE', '#d6a3ff', 5, 'Pierces, chains, and heals you on every hit')
        g.sounds.play('wave_clear', pitch=0.8)
        g.events.emit('quest_complete', quest='hollow_lance', player=player)

    # ── per frame ────────────────────────────────────────────────────────────
    def update(self, dt, use_held):
        g = self.game
        p = g.player
        self.t += dt
        if self.stage == 'lanterns':
            nearest = min((l for l in self.lanterns if not l['lit']),
                          key=lambda l: (l['pos'] - p.position).length(), default=None)
            if nearest is not None:
                d = (nearest['pos'] - p.position).length()
                if random.random() < dt * 3:
                    g.effects.burst(nearest['pos'] + Vec3(0, 1.45, 0), '#b37bff', 1, speed=0.6, size=0.06, life=0.8, gravity=-1)
                self.whisper_t -= dt
                if d < 12 and self.whisper_t <= 0:
                    self.whisper_t = 5 + random.random() * 4
                    g.sounds.play('groan', volume=0.35 * (1 - d / 12) + 0.1, pitch=1.8)
                    if not self.heard:
                        self.heard = True
                        g.ui.kill_feed('You hear whispers nearby...')
                if d < 2.2 and use_held:
                    self.light(nearest, p)
        elif self.stage in ('altar', 'herald'):
            k = self.souls / SOULS_NEEDED
            self.altar.y += (self.altar_pos.y - self.altar.y) * min(1, dt * 1.5)
            self.orb.scale = 0.3 + k * 0.9 + math.sin(self.t * 4) * 0.05
            self.orb.rotation_y += dt * 60
        elif self.stage == 'reward' and self.reward is not None:
            self.reward.y = self.reward_pos.y + math.sin(self.t * 2) * 0.15
            self.reward.rotation_y += dt * 90
            if (Vec3(self.reward.x, 0, self.reward.z) - Vec3(p.position.x, 0, p.position.z)).length() < 1.6:
                self.claim(p)

    def on_shot(self, eye, direction, max_dist):
        """Bullets can light lanterns. Called for every bullet the player fires."""
        if self.stage != 'lanterns':
            return
        for l in self.lanterns:
            if l['lit']:
                continue
            c = l['pos'] + Vec3(0, 1.44, 0)
            to = c - eye
            along = to.dot(direction)
            if 0 < along < max_dist and (to - direction * along).length() < 0.3:
                self.light(l)

    def tracker(self):
        """Text for the HUD, once the quest has been discovered."""
        lit = sum(1 for l in self.lanterns if l['lit'])
        if self.stage == 'lanterns':
            return f'Lanterns lit  {lit}/3' if lit else ''
        if self.stage == 'altar':
            return f'Altar souls  {self.souls}/{SOULS_NEEDED}'
        if self.stage == 'herald':
            return 'Defeat the Hollow Herald'
        if self.stage == 'reward':
            return 'Claim the Herald\'s weapon'
        return ''


def _calm_wave(g):
    from .data.waves import build_wave
    return build_wave(max(1, g.wave_number))
