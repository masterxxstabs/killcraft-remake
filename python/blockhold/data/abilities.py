# ─────────────────────────────────────────────────────────────────────────────
#  ABILITIES  (press Q in game)
#  Pick one on the main menu. Each has a cooldown in seconds.
#  use(game) does the effect — look at the existing ones for examples.
# ─────────────────────────────────────────────────────────────────────────────
from ursina import Vec3


def shockwave(game):
    p = game.player.position
    game.effects.ring(p, 7, '#5ad1ff')
    game.sounds.play('boom', volume=0.7)
    for e in list(game.enemies.alive()):
        d = (e.position - p).length()
        if d < 7 + e.radius:
            away = Vec3(e.position.x - p.x, 0, e.position.z - p.z)
            away = away.normalized() if away.length() > 0.01 else Vec3(0, 0, 1)
            e.hurt(120 * game.player.damage_mult, False, away * 18)


def adrenaline(game):
    pl = game.player
    pl.health = min(pl.max_health, pl.health + 30)
    pl.buffs['adrenaline'] = 7
    game.sounds.play('powerup')
    game.ui.banner('ADRENALINE!', '#ff4d6d', 1.2)


def blink(game):
    pl = game.player
    f = pl.forward()
    direction = Vec3(f.x, 0, f.z).normalized()
    start = Vec3(pl.position)
    best = Vec3(start)
    s = 0.5
    while s <= 9:
        t = start + direction * s
        if game.world.blocked(t.x, t.z, pl.radius, pl.position.y):
            break
        best = t
        s += 0.5
    game.effects.burst(start + Vec3(0, 1, 0), '#b37bff', 14)
    pl.position = best
    game.effects.burst(best + Vec3(0, 1, 0), '#b37bff', 14)
    game.sounds.play('blink')


def field_heal(game):
    """Medic: heal yourself and everyone near you, then keep healing for a while; gets downed allies up."""
    pl = game.player
    k = pl.heal_power
    game.effects.ring(pl.position, 8, '#3ddc97')
    game.sounds.play('heal')
    for who in [pl] + list(game.allies):
        if (who.position - pl.position).length() > 8:
            continue
        if getattr(who, 'downed', False):
            who.revive(0.5)
            continue
        if who is pl:
            pl.heal(round(40 * k))
            pl.buffs['field_heal'] = 6
        else:
            who.hp = min(who.max_hp, who.hp + 60 * k)
    game.ui.banner('FIELD HEAL', '#3ddc97', 1.2)


def sentry(game):
    """Engineer: drop a turret in front of you for a while (two with Twin Sentries)."""
    pl = game.player
    f = pl.forward()
    flat = Vec3(f.x, 0, f.z).normalized() if (f.x or f.z) else Vec3(0, 0, 1)
    side = Vec3(flat.z, 0, -flat.x)
    placed = 0
    for i in range(pl.sentry_count):
        for dist in (2.0, 1.4, 2.8):
            spot = pl.position + flat * dist + side * ((i - (pl.sentry_count - 1) / 2) * 1.6)
            pl.placeables['turret'] = pl.placeables.get('turret', 0) + 1
            b = game.barricades.place(pl, 'turret', spot.x, spot.z, 0)
            if b is not None:
                b['ttl'] = 25 + pl.sentry_time
                placed += 1
                break
            pl.placeables['turret'] -= 1
    if not placed:
        game.ui.banner('NO ROOM', '#d9912b', 1.0, 'Face open ground to drop a sentry')
        pl.ability_cd = 1.0
        return False
    game.ui.banner('SENTRY UP', '#1197b0', 1.2, f'{25 + pl.sentry_time:g} seconds')


ABILITIES = [
    dict(id='shockwave', name='Shockwave', cooldown=14, color='#5ad1ff', use=shockwave,
         desc='Slam the ground: 120 damage and a huge knockback to everything within 7m.'),
    dict(id='adrenaline', name='Adrenaline', cooldown=26, color='#ff4d6d', use=adrenaline,
         desc='For 7 seconds: double fire rate, +50% speed, and heal 30 health.'),
    dict(id='blink', name='Blink', cooldown=5, color='#b37bff', use=blink,
         desc='Teleport 9 metres in the direction you are looking. Short cooldown.'),
    dict(id='field_heal', name='Field Heal', cooldown=24, color='#3ddc97', use=field_heal,
         desc='Heal 40 now and 6 per second for 6 s, heal allies near you and get downed ones back up.'),
    dict(id='sentry', name='Sentry', cooldown=35, color='#1197b0', use=sentry,
         desc='Drop an auto-turret in front of you. It fights on its own for 25 seconds.'),
]
