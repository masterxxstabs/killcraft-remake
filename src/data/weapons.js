// ─────────────────────────────────────────────────────────────────────────────
//  WEAPONS
//  Add a new gun by copying one of the entries below and changing the numbers.
//  It will show up in the shop automatically.
//
//  Fields:
//    id        unique name used in code (no spaces)
//    name      what the player sees
//    desc      shop description
//    price     coins to buy (0 = you start with it)
//    melee     true for close-range swings (no ammo)
//    damage    damage per hit / per pellet
//    rate      shots (or swings) per second
//    auto      true = hold mouse button to keep firing
//    mag       bullets per magazine (reserve ammo is unlimited)
//    reload    seconds to reload
//    pellets   bullets per shot (shotguns use more than 1)
//    spread    how inaccurate each bullet is (0 = laser accurate)
//    range     how far bullets / swings reach (metres)
//    pierce    true = bullets go through enemies (not through walls)
//    headshot  damage multiplier for head hits (default 2)
//    knockback how hard hits push enemies back
//    projectile  { speed, radius, damage }  -> fires an exploding rocket instead of a bullet
//    model     colours + size of the blocky gun held on screen
// ─────────────────────────────────────────────────────────────────────────────

export const WEAPONS = [
  {
    id: 'wrench',
    name: 'Rusty Wrench',
    desc: 'Close-range bonk. Never needs reloading.',
    price: 0,
    melee: true,
    damage: 40,
    rate: 2.2,
    range: 2.6,
    knockback: 6,
    model: { body: '#8a8f99', accent: '#5b3a1e', length: 0.55, width: 0.08 },
  },
  {
    id: 'pistol',
    name: 'Pebble Pistol',
    desc: 'Reliable sidearm. Click fast!',
    price: 0,
    damage: 26,
    rate: 5,
    auto: false,
    mag: 12,
    reload: 1.1,
    pellets: 1,
    spread: 0.008,
    range: 80,
    knockback: 1.5,
    model: { body: '#3a3f48', accent: '#c9a227', length: 0.32, width: 0.09 },
  },
  {
    id: 'nailgun',
    name: 'Nail Gun',
    desc: 'Hold to spray nails. Big magazine.',
    price: 180,
    damage: 17,
    rate: 11,
    auto: true,
    mag: 45,
    reload: 1.8,
    pellets: 1,
    spread: 0.03,
    range: 70,
    knockback: 0.8,
    model: { body: '#d9682b', accent: '#2b2b2b', length: 0.5, width: 0.11 },
  },
  {
    id: 'scatter',
    name: 'Scattercannon',
    desc: 'Nine pellets per blast. Devastating up close.',
    price: 320,
    damage: 14,
    rate: 1.4,
    auto: false,
    mag: 6,
    reload: 2.1,
    pellets: 9,
    spread: 0.085,
    range: 35,
    knockback: 3,
    model: { body: '#6b4423', accent: '#9aa0a6', length: 0.62, width: 0.12 },
  },
  {
    id: 'railspike',
    name: 'Railspike',
    desc: 'Pierces through every enemy in a line. Triple headshot damage.',
    price: 600,
    damage: 240,
    rate: 0.9,
    auto: false,
    mag: 4,
    reload: 2.4,
    pellets: 1,
    spread: 0,
    range: 150,
    pierce: true,
    headshot: 3,
    knockback: 4,
    model: { body: '#1f6f8b', accent: '#7fe7ff', length: 0.8, width: 0.1 },
  },
  {
    id: 'firework',
    name: 'Firework Launcher',
    desc: 'Explosive rockets. Hits everything nearby.',
    price: 950,
    damage: 0,
    rate: 1.1,
    auto: false,
    mag: 3,
    reload: 2.6,
    pellets: 1,
    spread: 0.004,
    range: 120,
    projectile: { speed: 32, radius: 5, damage: 220 },
    knockback: 10,
    model: { body: '#b0263c', accent: '#f2d24b', length: 0.7, width: 0.16 },
  },
];
