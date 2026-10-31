// ─────────────────────────────────────────────────────────────────────────────
//  ABILITIES  (press Q in game)
//  Pick one on the main menu. Each has a cooldown in seconds.
//  use(game) does the effect — look at the existing ones for examples.
// ─────────────────────────────────────────────────────────────────────────────

export const ABILITIES = [
  {
    id: 'shockwave',
    name: 'Shockwave',
    desc: 'Slam the ground: 120 damage and a huge knockback to everything within 7m.',
    cooldown: 14,
    color: '#5ad1ff',
    use(game) {
      const p = game.player.position;
      game.effects.ring(p, 7, 0x5ad1ff);
      game.audio.boom(0.7);
      for (const e of game.enemies.list) {
        const d = e.position.distanceTo(p);
        if (d < 7 + e.radius) {
          const dir = e.position.clone().sub(p).setY(0).normalize();
          e.hurt(120 * game.player.damageMult, false, dir.multiplyScalar(18));
        }
      }
    },
  },
  {
    id: 'adrenaline',
    name: 'Adrenaline',
    desc: 'For 7 seconds: double fire rate, +50% speed, and you heal 30 health.',
    cooldown: 26,
    color: '#ff4d6d',
    use(game) {
      const pl = game.player;
      pl.health = Math.min(pl.maxHealth, pl.health + 30);
      pl.buffs.adrenaline = 7;
      game.audio.powerup();
      game.ui.banner('ADRENALINE!', '#ff4d6d', 1.2);
    },
  },
  {
    id: 'blink',
    name: 'Blink',
    desc: 'Teleport 9 metres in the direction you are looking. Short cooldown.',
    cooldown: 5,
    color: '#b37bff',
    use(game) {
      const pl = game.player;
      const dir = pl.forward().setY(0).normalize();
      const start = pl.position.clone();
      // step forward until a wall blocks us
      let best = start.clone();
      for (let s = 0.5; s <= 9; s += 0.5) {
        const t = start.clone().addScaledVector(dir, s);
        if (game.world.blocked(t.x, t.z, pl.radius, pl.position.y)) break;
        best = t;
      }
      game.effects.burst(start.clone().setY(start.y + 1), 0xb37bff, 14);
      pl.position.copy(best);
      game.effects.burst(best.clone().setY(best.y + 1), 0xb37bff, 14);
      game.audio.blink();
    },
  },
];
