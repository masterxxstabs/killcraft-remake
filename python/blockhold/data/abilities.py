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


ABILITIES = [
    dict(id='shockwave', name='Shockwave', cooldown=14, color='#5ad1ff', use=shockwave,
         desc='Slam the ground: 120 damage and a huge knockback to everything within 7m.'),
    dict(id='adrenaline', name='Adrenaline', cooldown=26, color='#ff4d6d', use=adrenaline,
         desc='For 7 seconds: double fire rate, +50% speed, and heal 30 health.'),
    dict(id='blink', name='Blink', cooldown=5, color='#b37bff', use=blink,
         desc='Teleport 9 metres in the direction you are looking. Short cooldown.'),
]
