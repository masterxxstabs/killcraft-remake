"""NPCs placed in the map editor: traders, quest givers and people who just talk.

Walk up to one and press E: they turn to face you and the talk window opens
(npc_ui.py) with their greeting and buttons for TALK, TRADE and their JOB.
Zombies leave NPCs alone (they're behind the lines), and you can't shoot them.
Quests are per player: each player has their own progress with each NPC.
Events: npc_talk, npc_trade, quest_taken, quest_done.
"""
import math
from panda3d.core import NodePath
from ursina import Entity, Text, Vec3
from .data.items import ITEMS
from .data.npcs import quest_goal_text
from .lowpoly import LowPoly
from .render import box_mesh, col, node, destroy
from .textures import zombie_skin

TALK_RANGE = 2.8


def _skin(data):
    colors = dict(skin=data['skin'], shirt=data['shirt'], pants=data['pants'], eyes=data.get('eyes', '#3a2a1a'))
    look = dict(human=True, hair=data.get('hair'), top='shirt', blood=False, beard=bool(data.get('beard')),
                goggles=bool(data.get('goggles')))
    key = 'npc_' + '_'.join(str(v) for v in (*colors.values(), *look.values()))
    return zombie_skin(key, colors, look)


def _extras(data):
    """Hat and apron, as one low-poly mesh (in the same space as the body)."""
    lp = LowPoly(seed=7, variation=0.03)
    hat = data.get('hat')
    hc = data.get('shirt', '#3a3d42')
    if hat == 'cap':
        lp.box((0, 2.0, 0), (0.54, 0.12, 0.54), hc)
        lp.box((0, 1.95, 0.32), (0.44, 0.04, 0.2), hc)
    elif hat == 'helmet':
        lp.box((0, 2.02, 0), (0.58, 0.2, 0.58), '#4f5a3a')
        lp.box((0, 1.93, 0.02), (0.62, 0.05, 0.64), '#4f5a3a')
    elif hat == 'cowboy':
        lp.box((0, 1.98, 0), (0.86, 0.04, 0.86), '#6b4a2b')
        lp.box((0, 2.1, 0), (0.48, 0.22, 0.48), '#6b4a2b')
        lp.box((0, 2.02, 0), (0.5, 0.05, 0.5), '#3a2618')
    elif hat == 'beanie':
        lp.box((0, 2.0, 0), (0.54, 0.16, 0.54), '#b84a2a')
        lp.box((0, 2.11, 0), (0.12, 0.08, 0.12), '#f2efe6')
    elif hat == 'hood':
        lp.box((0, 1.74, -0.04), (0.58, 0.58, 0.5), hc)
        lp.box((0, 2.04, 0), (0.58, 0.06, 0.56), hc)
        lp.box((0, 1.47, 0.0), (0.56, 0.08, 0.56), hc)
    if data.get('apron'):
        lp.box((0, 1.0, 0.152), (0.42, 0.62, 0.02), '#e8e4da')
        lp.box((0, 1.29, 0.152), (0.42, 0.04, 0.025), '#b0302a')
    return lp.mesh() if lp.verts else None


def npc_model(data):
    """A blocky person in their colours, facing +z. Parts that move are named
    head, arm_l, arm_r, leg_l, leg_r."""
    skin = _skin(data)
    tex = skin.texture._texture
    r = skin.rect

    def faces(front, side, back=None, top=None, bottom=None):
        return {'north': r(front), 'south': r(back or front), 'east': r(side), 'west': r(side),
                'top': r(top or side), 'bottom': r(bottom or side)}

    root = NodePath('npc')

    def part(parent, size, center, uv):
        m = box_mesh(size, center, uv)
        m.reparentTo(parent)
        m.setTexture(tex, 1)
        return m

    part(root, (0.5, 0.72, 0.28), (0, 1.11, 0), faces('torso_front', 'torso_side', 'torso_back', 'torso_top',
                                                      'torso_bottom'))
    head = root.attachNewNode('head')
    head.setPos(0, 1.47, 0)
    part(head, (0.5, 0.5, 0.5), (0, 0.25, 0), faces('head_front', 'head_side', 'head_back', 'head_top',
                                                    'head_bottom'))
    leg = faces('leg_side', 'leg_side', 'leg_side', 'leg_top', 'leg_bottom')
    arm = faces('arm_side', 'arm_side', 'arm_side', 'arm_top', 'arm_bottom')
    for name, x, y, w, h, uv in (('leg_l', -0.13, 0.75, 0.24, 0.75, leg), ('leg_r', 0.13, 0.75, 0.24, 0.75, leg),
                                 ('arm_l', -0.36, 1.44, 0.2, 0.72, arm), ('arm_r', 0.36, 1.44, 0.2, 0.72, arm)):
        piv = root.attachNewNode(name)
        piv.setPos(x, y, 0)
        part(piv, (w, h, w), (0, -h / 2, 0), uv)
    apron = _extras(dict(data, hat=None))             # the apron sits on the body
    if apron is not None:
        apron.reparentTo(root)
    hat = _extras(dict(data, apron=False))            # the hat turns with the head
    if hat is not None:
        hat.reparentTo(head)
        hat.setPos(0, -1.47, 0)
    return root


class NPC:
    def __init__(self, game, prop):
        self.game = game
        self.data = prop['data']
        self.uid = self.data['uid']
        self.name = self.data['name']
        self.position = Vec3(prop['x'], 0, prop['z'])
        self.home_yaw = prop.get('rot', 0.0)
        self.yaw = self.home_yaw
        self.talking = False
        self.t = 0.0
        self.root = node(game.world_root, position=self.position, rotation_y=self.yaw, scale=prop.get('scale', 1))
        self.model = npc_model(self.data)
        self.model.reparentTo(self.root)
        self.head = self.model.find('head')
        self.arms = [self.model.find('arm_l'), self.model.find('arm_r')]
        self.tag = Entity(parent=self.root, y=2.5, billboard=True)
        role = self.data.get('role')
        mark = {'trader': '$', 'quest': '!', 'talker': ''}.get(role, '')
        Text(self.name, parent=self.tag, scale=7, origin=(0, 0), color=col('#f5f4f2'))
        self.mark = Text(mark, parent=self.tag, scale=14, origin=(0, 0), y=0.28,
                         color=col('#ffd84a' if role == 'quest' else '#3ddc97'))

    def destroy(self):
        destroy(self.root)

    def update(self, dt, player):
        self.t += dt
        to = Vec3(player.position.x - self.position.x, 0, player.position.z - self.position.z)
        near = to.length() < 7
        want = math.degrees(math.atan2(to.x, to.z)) if near else self.home_yaw
        diff = (want - self.yaw + 180) % 360 - 180
        self.yaw += diff * min(1, dt * (4 if near else 1.5))
        self.root.rotation_y = self.yaw
        # breathing, and a wave of the hand while you talk
        self.model.setZ(0)
        self.head.setP(math.sin(self.t * 1.3) * 3)
        if self.talking:
            self.arms[1].setP(-60 + math.sin(self.t * 3) * 25)
        else:
            self.arms[1].setP(math.sin(self.t * 1.1) * 3)
        self.arms[0].setP(-math.sin(self.t * 1.1) * 3)


class Npcs:
    def __init__(self, game):
        self.game = game
        self.list = []
        self.quests = {}          # (npc uid, player id) -> dict(state='active'|'done', count=progress)
        self.talking = None       # the NPC whose window is open
        game.events.on('enemy_killed', self.on_enemy_killed)
        game.events.on('animal_killed', self.on_animal_killed)

    def clear(self):
        for n in self.list:
            n.destroy()
        self.list = []
        self.quests = {}
        self.talking = None

    def reset(self):
        self.clear()
        for prop in self.game.world.npcs:
            self.list.append(NPC(self.game, prop))

    def nearest(self, pos, reach=TALK_RANGE):
        best, best_d = None, reach
        for n in self.list:
            dist = math.hypot(n.position.x - pos.x, n.position.z - pos.z)
            if dist < best_d:
                best, best_d = n, dist
        return best

    def update(self, dt):
        p = self.game.player
        for n in self.list:
            n.talking = n is self.talking
            n.update(dt, p)

    def prompt(self, player):
        n = self.nearest(player.position)
        if n is None:
            return None
        return f'Press E to talk to {n.name}'

    # ── quests ───────────────────────────────────────────────────────────────
    def quest_state(self, npc, player):
        return self.quests.get((npc.uid, player.id))

    def take_quest(self, npc, player):
        q = npc.data.get('quest')
        if not q:
            return
        self.quests[(npc.uid, player.id)] = dict(state='active', count=0)
        self.game.events.emit('quest_taken', npc=npc.uid, player=player)
        self.game.ui.kill_feed(f"New job from {npc.name}: {quest_goal_text(q)}")

    def progress(self, npc, player):
        """(have, need) for an active job."""
        q, st = npc.data['quest'], self.quest_state(npc, player)
        if q['kind'] == 'bring':
            return min(q['n'], player.inventory.count(q['item'])), q['n']
        return min(q['n'], st['count'] if st else 0), q['n']

    def can_finish(self, npc, player):
        st = self.quest_state(npc, player)
        if not st or st['state'] != 'active':
            return False
        have, need = self.progress(npc, player)
        return have >= need

    def finish_quest(self, npc, player):
        g, q = self.game, npc.data['quest']
        if not self.can_finish(npc, player):
            return False
        if q['kind'] == 'bring':
            player.inventory.remove(q['item'], q['n'])
        if q.get('reward_coins'):
            g.coins += q['reward_coins']
        got = []
        if q.get('reward_item') and q.get('reward_n', 0) > 0:
            got.append(self.give_item(player, q['reward_item'], q['reward_n']))
        st = self.quests[(npc.uid, player.id)]
        if q.get('repeat'):
            del self.quests[(npc.uid, player.id)]
        else:
            st['state'] = 'done'
        g.sounds.play('buy')
        g.events.emit('quest_done', npc=npc.uid, player=player)
        return True

    def give_item(self, player, item, n):
        """Hand a player items, coins or a weapon (what doesn't fit lands at their feet)."""
        g = self.game
        if item == 'coins':
            g.coins += n
            return f'{n} coins'
        d = ITEMS.get(item)
        if d is None:
            return ''
        if d['kind'] == 'weapon':
            for _ in range(n):
                g.weapons.give(d['weapon'])
            return d['name']
        left = player.inventory.add(item, n)
        if left:
            from .net import new_id
            g.drops.spawn(dict(item=dict(uid=new_id(), id=item, n=left, x=0, y=0, rot=False)), player.position)
        return f"{n} {d['name']}"

    def on_enemy_killed(self, enemy=None, attacker=None, **_):
        owner = getattr(attacker, 'owner', attacker) or self.game.player
        self._count(owner, 'kill', None)

    def on_animal_killed(self, kind=None, player=None, **_):
        if player is not None:
            self._count(player, 'hunt', kind)

    def _count(self, player, kind, animal):
        for n in self.list:
            q = n.data.get('quest')
            st = self.quests.get((n.uid, getattr(player, 'id', None)))
            if not q or not st or st['state'] != 'active' or q['kind'] != kind:
                continue
            if kind == 'hunt' and q.get('animal', 'any') not in ('any', animal):
                continue
            if st['count'] < q['n']:
                st['count'] += 1
                if st['count'] == q['n'] and getattr(player, 'is_local', True):
                    self.game.ui.kill_feed(f"Job done! Go back to {n.name}")

    # ── trading ──────────────────────────────────────────────────────────────
    def can_trade(self, player, t):
        if t['give'] == 'coins':
            return self.game.coins >= t['give_n']
        return player.inventory.count(t['give']) >= t['give_n']

    def trade(self, npc, player, t):
        g = self.game
        if not self.can_trade(player, t):
            g.sounds.play('deny')
            return False
        if t['give'] == 'coins':
            g.coins -= t['give_n']
        else:
            player.inventory.remove(t['give'], t['give_n'])
        self.give_item(player, t['get'], t['get_n'])
        g.sounds.play('buy')
        g.events.emit('npc_trade', npc=npc.uid, player=player, trade=t)
        return True
