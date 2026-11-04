"""The shove (F), like Left 4 Dead and Project Zomboid.

Push the zombies in front of you away. Normal zombies are knocked off their feet
(they go limp, then climb back up and keep coming); big ones stumble back; bosses
barely move. It does a little damage, more with the Bash skill.

Shoving tires you out: you get `shove_stamina` good shoves in a row, then they get
slow and weak (zombies only stumble) until you catch your breath (one shove's worth
every 1.6 s). Skills in the Defense column make shoves stronger, wider and cheaper.
Events: shove (player, hits).
"""
import math
from ursina import Vec3

BASE_RANGE = 2.3       # metres in front of you
BASE_ARC = 0.42        # cos of the half-angle of the cone (0.42 = about 65 degrees each side)
BASE_PUSH = 3.4        # how hard it pushes (m/s); stronger shoves push a little further and knock down longer


def tired(p):
    """Out of breath: shoves are slow and weak."""
    free = p.rage and p.health < p.max_health / 2                # Juggernaut
    return p.shove_fatigue >= p.shove_stamina and not free


def shove(game, p):
    """Returns how many zombies it hit, or None if you couldn't shove right now."""
    if p.shove_cd > 0 or p.downed or p.dead or p.using is not None:
        return None
    worn_out = tired(p)
    p.shove_cd = 0.9 if worn_out else 0.45
    if not (p.rage and p.health < p.max_health / 2):
        p.shove_fatigue = min(p.shove_fatigue + 1, p.shove_stamina + 2)
    power = p.shove_power * (0.35 if worn_out else 1.0)
    f = p.forward()
    flat = Vec3(f.x, 0, f.z)
    flat = flat.normalized() if flat.length() > 0.01 else Vec3(0, 0, 1)
    reach = BASE_RANGE + p.shove_range
    arc = max(-0.2, BASE_ARC - p.shove_arc)
    hits = 0
    for e in list(game.enemies.alive()):
        if e.rise > 0.3:
            continue
        to = Vec3(e.position.x - p.position.x, 0, e.position.z - p.position.z)
        dist = to.length()
        if dist - e.radius > reach:
            continue
        way = to / dist if dist > 0.01 else flat
        if way.dot(flat) < arc and dist > e.radius + 0.5:
            continue
        push = (way * 0.6 + flat * 0.4).normalized() * BASE_PUSH * power ** 0.5
        e.shoved(push, power, p)
        hits += 1
    w = game.weapons
    w.shove_t = SHOVE_ANIM
    game.sounds.play('swing', pitch=0.7 if worn_out else 0.9)
    if hits:
        game.sounds.play('thud', pitch=0.8)
        game.shake(0.12)
        if p.is_local:
            game.ui.hitmarker(False)
    game.events.emit('shove', player=p, hits=hits)
    return hits


SHOVE_ANIM = 0.3


def stamina_frac(p):
    """1 = fresh, 0 = worn out (for the HUD)."""
    return max(0.0, 1 - p.shove_fatigue / max(1, p.shove_stamina))


def shove_offset(t):
    """How far the gun / fists move forward during the shove animation (0..1 over SHOVE_ANIM)."""
    if t <= 0:
        return 0.0
    k = 1 - t / SHOVE_ANIM
    return math.sin(k * math.pi)
