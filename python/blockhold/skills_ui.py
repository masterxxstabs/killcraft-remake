"""The skill tree (press K): four columns of skills, four tiers each.

Combat, Survival and Defense are the same for every class; the fourth column is
your class's own. Click a skill to put a point in it. A skill opens up once the one
above it has a point. Points come from levelling up (see progression.py).
"""
from ursina import Entity, camera
from . import ui as U
from .data.abilities import ABILITIES
from .data.classes import BRANCHES, CLASSES, MAX_LEVEL, SKILLS, tree_for, xp_to_next
from .render import destroy

NODE_W, NODE_H = 0.282, 0.1
COL_GAP, ROW_GAP = 0.024, 0.025


class SkillScreen:
    def __init__(self, ui):
        self.ui, self.game = ui, ui.game
        self.root = Entity(parent=camera.ui, z=-1, enabled=False)
        U.backdrop(self.root, 0.5)
        self.win = U.Window(self.root, 'SKILLS', h=0.9, top=0.42)
        self.body = None
        self.active = False

    def open(self):
        self.active = True
        self.root.enabled = True
        self.refresh()

    def close(self):
        self.active = False
        self.root.enabled = False
        if self.body is not None:
            destroy(self.body)
            self.body = None

    def buy(self, sid):
        if self.game.progress.buy(self.game.player, sid):
            self.ui.kill_feed(f"Learned {SKILLS[sid]['name']} ({self.game.player.skills[sid]}/{SKILLS[sid]['ranks']})")
        self.refresh()

    def refresh(self):
        if not self.active:
            return
        if self.body is not None:
            destroy(self.body)
        b = self.body = Entity(parent=self.win.body)
        g, p, win = self.game, self.game.player, self.win
        cls = CLASSES[p.cls]
        ability = next((a for a in ABILITIES if a['id'] == cls['ability']), None)
        win.title.text = f"{cls['name'].upper()}  ·  LEVEL {p.level}"
        win.right.text = f'{p.skill_points} point' + ('' if p.skill_points == 1 else 's')
        x0, y = win.left, win.top + 0.02
        # XP to the next level, and what the class does
        need = xp_to_next(p.level)
        U.text(b, 'MAX LEVEL' if p.level >= MAX_LEVEL else f'XP  {p.xp} / {need}', x0, y, 0.75, 'MUTED')
        U.bar(b, x0, y - 0.025, 0.36, 0.018, 1.0 if p.level >= MAX_LEVEL else p.xp / need, fill='AMBER')
        U.text(b, f"Passive: {cls['passive']}", x0 + 0.42, y, 0.72, 'INK')
        if ability:
            U.text(b, f"Q  {ability['name']}: {ability['desc']}", x0 + 0.42, y - 0.03, 0.66, 'MUTED', wordwrap=95)
        y -= 0.085
        tree = tree_for(p.cls)
        prog = g.progress
        for c, (branch, title) in enumerate(BRANCHES):
            cx = x0 + c * (NODE_W + COL_GAP)
            U.text(b, (title or cls['branch']).upper(), cx, y, 0.85, cls['colour'] if branch == 'class' else 'MUTED')
            for t, sid in enumerate(tree[branch]):
                s = SKILLS[sid]
                ny = y - 0.035 - t * (NODE_H + ROW_GAP)
                rank = prog.rank(p, sid)
                why = prog.why_not(p, sid)
                if t > 0:                                     # the line up to the skill above
                    U.box(b, cx + NODE_W / 2 - 0.002, ny + ROW_GAP, 0.004, ROW_GAP, 'TEAL' if rank or not why else 'LINE',
                          z=0.004, round=False)
                if rank >= s['ranks']:
                    fill, edge, fg = 'GREEN', 'INK', 'AUTO'
                elif why == 'LOCKED':
                    fill, edge, fg = 'NAVY', 'LINE', 'MUTED'
                elif not why:
                    fill, edge, fg = 'PAPER', 'TEAL', 'INK'
                else:
                    fill, edge, fg = 'PAPER', 'LINE', 'INK'
                U.FlatButton(b, '', cx, ny, NODE_W, NODE_H, lambda k=sid: self.buy(k), fill=fill, edge=edge,
                             hover=0.08 if not why else 0.0)
                tc = U.contrast(fill) if fg == 'AUTO' else fg
                U.text(b, s['name'], cx + 0.012, ny - 0.012, 0.82, tc, z=-0.03)
                U.text(b, f"{rank}/{s['ranks']}", cx + NODE_W - 0.012, ny - 0.012, 0.78, tc, origin=(0.5, 0.5), z=-0.03)
                for i in range(s['ranks']):                   # one pip per point
                    U.box(b, cx + 0.012 + i * 0.022, ny - 0.036, 0.016, 0.007,
                          'AMBER' if i < rank else 'LINE', z=-0.03, round=False)
                U.text(b, s['desc'], cx + 0.012, ny - 0.05, 0.58, tc, wordwrap=40, z=-0.03)
        U.text(b, 'Click a skill to spend a point. Each one opens the next in its column. '
                  'Level up by killing zombies, clearing waves and doing NPC jobs.',
               x0, win.btn_y + 0.03, 0.66, 'MUTED', wordwrap=110)
        U.FlatButton(b, 'CLOSE  (K)', x0 + 1.24 - 0.26, win.btn_y, 0.26, U.BTN_H, self.game.close_shop)
