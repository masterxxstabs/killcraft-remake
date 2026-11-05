"""Levels, XP, skill points and the class you picked (see data/classes.py).

Each player has their own level, XP and skills (player.level, .xp, .skill_points,
.skills). They're saved in your profile (save.json, 'profile') and carry over from
game to game. XP comes from kills (the zombie's score), cleared waves and NPC jobs.
Every level is a skill point; spend them in the skill tree (K). Skills in another
class's column stay learned but only work while you play that class. RESET SKILLS
gives every point back.
Events: xp_gained, level_up, skill_bought.
"""
from .data.classes import (CLASSES, DEFAULT_CLASS, MAX_LEVEL, SKILLS, XP_QUEST, XP_SHOVE_KILL, XP_WAVE, tree_for,
                           xp_to_next)


class Progression:
    def __init__(self, game):
        self.game = game
        game.events.on('enemy_killed', self.on_kill)
        game.events.on('wave_cleared', self.on_wave)
        game.events.on('quest_done', self.on_quest)

    # ── starting a run ───────────────────────────────────────────────────────
    def start(self, player, cls_id):
        """Load your character (level, XP, skills) for a game as class cls_id (call right after player.reset())."""
        cls_id = cls_id if cls_id in CLASSES else DEFAULT_CLASS
        player.cls = cls_id
        prof = self.profile()
        player.level = max(1, min(MAX_LEVEL, int(prof.get('level', 1))))
        player.xp = max(0, int(prof.get('xp', 0)))
        player.skill_points = max(0, int(prof.get('points', 0)))
        player.skills = {k: v for k, v in prof.get('skills', {}).items() if k in SKILLS}
        CLASSES[cls_id]['apply'](player)
        for sid, rank in player.skills.items():                     # learned skills that work for this class
            if self.active(player, sid):
                for _ in range(min(rank, SKILLS[sid]['ranks'])):
                    SKILLS[sid]['apply'](player)

    def profile(self):
        return self.game.save.setdefault('profile', dict(level=1, xp=0, points=0, skills={}))

    def store(self, player):
        """Write the local player's character into the profile and save it to disk."""
        if not getattr(player, 'is_local', False):
            return
        self.game.save['profile'] = dict(level=player.level, xp=player.xp, points=player.skill_points,
                                         skills=dict(player.skills))
        self.game.save_progress()

    def active(self, player, sid):
        s = SKILLS.get(sid)
        return s is not None and (s['branch'] != 'class' or s.get('cls') == player.cls)

    def reset_skills(self, player):
        """Give back every point (the stats go back when the next game starts)."""
        spent = sum(player.skills.values())
        player.skill_points += spent
        player.skills = {}
        self.store(player)
        return spent

    # ── XP ───────────────────────────────────────────────────────────────────
    def add_xp(self, player, amount, why=''):
        if player is None or not hasattr(player, 'xp') or player.level >= MAX_LEVEL:
            return
        amount = max(1, round(amount * player.xp_mult))
        player.xp += amount
        self.game.events.emit('xp_gained', player=player, amount=amount, why=why)
        while player.level < MAX_LEVEL and player.xp >= xp_to_next(player.level):
            player.xp -= xp_to_next(player.level)
            player.level += 1
            player.skill_points += 1
            self.game.events.emit('level_up', player=player, level=player.level)
            self.store(player)
            if getattr(player, 'is_local', False):
                self.game.sounds.play('powerup')
                self.game.ui.banner(f'LEVEL {player.level}', '#ffd84a', 2.2, 'Skill point ready: press K')
        if player.level >= MAX_LEVEL:
            player.xp = 0

    def on_kill(self, enemy=None, attacker=None, **_):
        if enemy is None:
            return
        owner = getattr(attacker, 'owner', attacker) or self.game.player
        xp = enemy.d.get('score', 10) * getattr(enemy, 'reward', 1)      # higher-level zombies give more
        if getattr(enemy, 'was_shoved', False):
            xp += XP_SHOVE_KILL
        self.add_xp(owner, xp, 'kill')

    def on_wave(self, wave=0, **_):
        for p in self.game.players:
            if not p.dead:
                self.add_xp(p, XP_WAVE * wave, 'wave')

    def on_quest(self, player=None, **_):
        self.add_xp(player, XP_QUEST, 'quest')

    # ── skills ───────────────────────────────────────────────────────────────
    def rank(self, player, sid):
        return player.skills.get(sid, 0)

    def unlocked(self, player, sid):
        """A skill opens up once the one above it in its column has a point."""
        s = SKILLS[sid]
        if s['branch'] == 'class' and s.get('cls') != player.cls:
            return False
        if s['tier'] == 1:
            return True
        column = tree_for(player.cls)[s['branch']]
        above = [k for k in column if SKILLS[k]['tier'] == s['tier'] - 1]
        return any(self.rank(player, k) > 0 for k in above)

    def why_not(self, player, sid):
        """'' if player can buy a point in sid, else the reason."""
        s = SKILLS[sid]
        if self.rank(player, sid) >= s['ranks']:
            return 'MAXED'
        if not self.unlocked(player, sid):
            return 'LOCKED'
        if player.skill_points <= 0:
            return 'NO POINTS'
        return ''

    def buy(self, player, sid):
        if self.why_not(player, sid):
            self.game.sounds.play('deny')
            return False
        player.skill_points -= 1
        player.skills[sid] = self.rank(player, sid) + 1
        SKILLS[sid]['apply'](player)
        self.store(player)
        self.game.sounds.play('buy')
        self.game.events.emit('skill_bought', player=player, skill=sid, rank=player.skills[sid])
        return True
