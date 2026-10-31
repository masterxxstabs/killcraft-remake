import { ENEMIES } from './enemies.js';

// ─────────────────────────────────────────────────────────────────────────────
//  WAVES
//  buildWave(n) decides which enemies show up in wave n. Tweak the weights to
//  change how often each enemy appears.
// ─────────────────────────────────────────────────────────────────────────────

export const BOSS_EVERY = 5;       // a boss shows up every Nth wave
export const MODIFIER_EVERY = 4;   // a special modifier every Nth wave
export const INTERMISSION = 25;    // seconds of shopping time between waves

// Special wave modifiers. Add your own! Any field left out uses the normal value.
export const MODIFIERS = [
  {
    id: 'bloodmoon',
    name: 'BLOOD MOON',
    desc: 'Enemies are 35% faster.',
    speedMult: 1.35,
    sky: '#3b0707', fog: '#3b0707', fogNear: 10, fogFar: 70,
    sun: '#ff5a3c', ambient: 0.45,
  },
  {
    id: 'fog',
    name: 'THE FOG',
    desc: 'You can barely see past your nose.',
    sky: '#a9b2b6', fog: '#a9b2b6', fogNear: 1, fogFar: 17,
    ambient: 0.8,
  },
  {
    id: 'swarm',
    name: 'SWARM',
    desc: 'Twice as many enemies, but they are fragile.',
    countMult: 2, hpMult: 0.5,
    sky: '#4b3a6b', fog: '#4b3a6b', fogNear: 20, fogFar: 90,
    sun: '#c7a3ff', ambient: 0.55,
  },
  {
    id: 'goldrush',
    name: 'GOLD RUSH',
    desc: 'Enemies drop triple coins.',
    coinMult: 3,
    sky: '#f2c14e', fog: '#e8b84a', fogNear: 25, fogFar: 100,
    sun: '#fff1b0', ambient: 0.7,
  },
];

function weights(n) {
  return {
    shambler: 10,
    sprinter: n >= 3 ? 2 + n * 0.45 : 0,
    brute: n >= 4 ? 0.7 + n * 0.15 : 0,
    spitter: n >= 6 ? 1.5 + n * 0.2 : 0,
  };
}

function pick(w) {
  let total = 0;
  for (const k in w) total += w[k];
  let r = Math.random() * total;
  for (const k in w) {
    r -= w[k];
    if (r <= 0) return k;
  }
  return 'shambler';
}

export function buildWave(n) {
  const modifier = n % MODIFIER_EVERY === 0
    ? MODIFIERS[(n / MODIFIER_EVERY - 1) % MODIFIERS.length]
    : null;
  const countMult = modifier?.countMult ?? 1;
  const total = Math.round((6 + n * 2.6) * countMult);
  const w = weights(n);
  const enemies = [];
  for (let i = 0; i < total; i++) enemies.push(pick(w));
  if (n % BOSS_EVERY === 0) enemies.splice(Math.min(3, enemies.length), 0, 'hollowKing');

  return {
    number: n,
    enemies,
    modifier,
    maxAlive: Math.min(12 + n * 2, 45),
    spawnInterval: Math.max(0.3, 1.3 - n * 0.06),
    hpMult: (1 + 0.16 * (n - 1)) * (modifier?.hpMult ?? 1),
    damageMult: 1 + 0.06 * (n - 1),
    speedMult: modifier?.speedMult ?? 1,
    coinMult: modifier?.coinMult ?? 1,
    clearBonus: 30 + n * 12,
  };
}

export { ENEMIES };
