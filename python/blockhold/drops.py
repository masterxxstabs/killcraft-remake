"""Dropped guns lying on the ground.

Press X to drop the gun you're holding (not your last one). It keeps its ammo,
upgrades, attachments and camo. Walk up to it and press E to pick it up again.
Every drop has a network id and remembers who dropped it.
Events: weapon_dropped, weapon_picked_up.
"""
import math
from ursina import Vec3
from .net import new_id
from .render import destroy, node

PICKUP_RANGE = 1.8


class WeaponDrops:
    def __init__(self, game):
        self.game = game
        self.list = []
        self.t = 0.0

    def drop(self, player):
        g = self.game
        w = g.weapons
        d = w.held
        if d is None or player.downed or player.dead:
            return None
        if len(w.owned) <= 1:
            g.ui.banner("CAN'T DROP IT", '#d9912b', 1.4, "It's your last weapon")
            g.sounds.play('deny')
            return None
        pack = w.take_out(d)
        fwd = player.forward()
        flat = Vec3(fwd.x, 0, fwd.z).normalized() if (fwd.x or fwd.z) else Vec3(0, 0, 1)
        pos = Vec3(player.position.x, 0, player.position.z) + flat * 1.1
        if g.world.height_at(pos.x, pos.z) > 0:              # a wall in front: drop it at your feet
            pos = Vec3(player.position.x, 0, player.position.z)
        item = self.spawn(pack, pos, player.yaw + 70, player)
        g.sounds.play('reload_out', volume=0.8, pitch=0.8)
        g.events.emit('weapon_dropped', id=item['id'], weapon=d['id'], player=player, pos=pos)
        return item

    def drop_item(self, player, it):
        """Drop a backpack item (a pile, or a piece of armor) on the ground in front of player."""
        fwd = player.forward()
        flat = Vec3(fwd.x, 0, fwd.z).normalized() if (fwd.x or fwd.z) else Vec3(0, 0, 1)
        pos = Vec3(player.position.x, 0, player.position.z) + flat * 1.0
        if self.game.world.height_at(pos.x, pos.z) > 0:
            pos = Vec3(player.position.x, 0, player.position.z)
        item = self.spawn(dict(item=it), pos, player.yaw, player)
        self.game.sounds.play('equip', volume=0.6, pitch=0.8)
        self.game.events.emit('item_dropped', id=item['id'], item=it['id'], count=it['n'], player=player)
        return item

    def spawn(self, pack, pos, yaw=0.0, owner=None):
        g = self.game
        if 'item' in pack:                                   # a backpack item: a little sack in its colour
            from .data.items import ITEMS
            d = dict(ITEMS[pack['item']['id']], id=pack['item']['id'])
            e = node(g.world_root, position=Vec3(pos.x, 0.1, pos.z), rotation_y=yaw)
            body = node(e)
            from .lowpoly import LowPoly
            lp = LowPoly(seed=7)
            lp.blob((0, 0.18, 0), 0.24, d['colour'], squash=(1, 0.8, 1), detail=0, jitter=0.1)
            lp.box((0, 0.36, 0), (0.12, 0.08, 0.12), '#8a6a3a')
            node(body, model=lp.mesh())
            item = dict(id=new_id(), pack=pack, d=d, pos=Vec3(pos.x, 0, pos.z), e=e, body=body, owner=owner,
                        phase=len(self.list) * 1.3)
            self.list.append(item)
            return item
        d = g.weapons.get_def(pack['wid'])
        e = node(g.world_root, position=Vec3(pos.x, 0.1, pos.z), rotation_y=yaw)
        body = node(e, rotation_z=90, scale=0.75)            # lying on its side
        g.weapons.ground_model(d, body)
        item = dict(id=new_id(), pack=pack, d=d, pos=Vec3(pos.x, 0, pos.z), e=e, body=body, owner=owner,
                    phase=len(self.list) * 1.3)
        self.list.append(item)
        return item

    def nearest(self, pos, max_dist=PICKUP_RANGE):
        best, best_d = None, max_dist
        for it in self.list:
            dist = math.hypot(it['pos'].x - pos.x, it['pos'].z - pos.z)
            if dist < best_d:
                best, best_d = it, dist
        return best

    def pick_up(self, player, item=None):
        g = self.game
        item = item or self.nearest(player.position)
        if item is None or player.downed or player.dead:
            return False
        if 'item' in item['pack']:                           # a backpack item
            it = item['pack']['item']
            if 'dur' in it:
                ok = player.inventory.put_back(dict(it, x=0, y=0))
                left = 0 if ok else 1
            else:
                left = player.inventory.add(it['id'], it['n'])
            if left >= it['n'] or (left and 'dur' in it):
                g.ui.banner('BACKPACK FULL', '#d9912b', 1.4, 'Make room first (press I)')
                g.sounds.play('deny')
                return False
            if left:                                         # only some of the pile fitted
                it['n'] = left
                return True
            self.list.remove(item)
            destroy(item['e'])
            g.sounds.play('equip', volume=0.7)
            g.events.emit('item_picked_up', id=item['id'], item=it['id'], player=player)
            return True
        if g.weapons.owns(item['d']['id']):
            g.ui.banner('ALREADY GOT ONE', '#d9912b', 1.4, f"You already carry a {item['d']['name']}")
            g.sounds.play('deny')
            return False
        self.list.remove(item)
        destroy(item['e'])
        g.weapons.put_back(item['pack'])
        g.events.emit('weapon_picked_up', id=item['id'], weapon=item['d']['id'], player=player)
        return True

    def prompt(self, player):
        item = self.nearest(player.position)
        if item and 'item' in item['pack']:
            n = item['pack']['item']['n']
            return f"Press E to pick up {item['d']['name']}" + (f' x{n}' if n > 1 else '')
        return f"Press E to pick up the {item['d']['name']}" if item else ''

    def clear(self):
        for it in self.list:
            destroy(it['e'])
        self.list = []

    def update(self, dt):
        self.t += dt
        for it in self.list:                                 # a slow bob and turn so you notice it
            it['e'].y = 0.12 + 0.05 * math.sin(self.t * 2.4 + it['phase'])
            it['e'].rotation_y += dt * 25

    def lights(self):
        return [(it['pos'] + Vec3(0, 0.4, 0), (0.55, 0.85, 1.0), 2.2, 0.6) for it in self.list]
