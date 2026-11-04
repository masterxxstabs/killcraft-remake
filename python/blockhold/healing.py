"""Using bandages, medkits and food: it takes time.

Press H to use the best medical item for how hurt you are (or right-click one in
the backpack, which works for food too). While you use it you walk at half speed,
your gun is lowered and you can't shoot; the heal comes when the bar fills.
Shooting, reloading or switching weapons stops it, and nothing is used up.
Taking damage doesn't stop it, so find cover first.
Events: item_use_started, item_used, item_use_cancelled.
"""
from .data.items import ITEMS

VERBS = {'bandage': 'Bandaging', 'medkit': 'Using medkit', 'surgery_kit': 'Patching yourself up'}


class Healing:
    def __init__(self, game):
        self.game = game

    def start(self, p, item_id):
        g, d = self.game, ITEMS.get(item_id, {})
        if p.downed or p.dead or d.get('kind') not in ('medical', 'food'):
            return False
        if p.inventory.count(item_id) <= 0:
            return False
        if p.health >= p.max_health:
            if p.is_local:
                g.ui.banner('FULL HEALTH', '#d9912b', 1.0, f"You don't need the {d['name'].lower()}")
            g.sounds.play('deny')
            return False
        if p.using is not None:
            self.cancel(p)
        p.using = dict(item=item_id, t=0.0, total=d.get('use_time', 2.0) / max(0.2, p.heal_speed))   # Medic skills
        g.weapons.trigger(False)
        g.aiming = False
        g.sounds.play('equip', volume=0.6, pitch=0.7)
        g.events.emit('item_use_started', player=p, item=item_id)
        return True

    def best(self, p):
        """The medical item that fits how hurt you are: the smallest that heals most of it."""
        missing = p.max_health - p.health
        have = [k for k, d in ITEMS.items() if d['kind'] == 'medical' and p.inventory.count(k) > 0]
        if not have:
            return None
        have.sort(key=lambda k: min(ITEMS[k]['heal'], 999))
        for k in have:
            if ITEMS[k]['heal'] >= missing * 0.8:
                return k
        return have[-1]

    def quick(self, p):
        """H: use something (or stop if you're already using something)."""
        if p.using is not None:
            self.cancel(p)
            return
        k = self.best(p)
        if k is None:
            if p.is_local:
                self.game.ui.banner('NO MEDICAL ITEMS', '#d9912b', 1.2, 'Craft bandages and medkits at a workbench')
            self.game.sounds.play('deny')
            return
        self.start(p, k)

    def cancel(self, p, why=''):
        if p.using is None:
            return
        item = p.using['item']
        p.using = None
        if why and p.is_local:
            self.game.ui.kill_feed(f"Stopped using the {ITEMS[item]['name'].lower()}{why}")
        self.game.events.emit('item_use_cancelled', player=p, item=item)

    def label(self, p):
        u = p.using
        d = ITEMS[u['item']]
        verb = VERBS.get(u['item'], 'Eating' if d['kind'] == 'food' else 'Using')
        return f"{verb}...  {max(0.0, u['total'] - u['t']):.1f}s   (click to stop)"

    def update(self, dt):
        g = self.game
        for p in g.players:
            u = p.using
            if u is None:
                continue
            if p.downed or p.dead or p.inventory.count(u['item']) <= 0:
                p.using = None
                continue
            u['t'] += dt
            if u['t'] >= u['total']:
                p.using = None
                d = ITEMS[u['item']]
                p.inventory.remove(u['item'], 1)
                heal = p.max_health if d['heal'] >= 999 else d['heal']
                p.heal(min(heal, p.max_health - p.health))
                g.sounds.play('heal')
                g.events.emit('item_used', player=p, item=u['item'])
