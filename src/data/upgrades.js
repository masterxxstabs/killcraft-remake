// ─────────────────────────────────────────────────────────────────────────────
//  SHOP UPGRADES
//  Each upgrade can be bought many times; the price goes up every level.
//  apply(player) runs once per purchase.
// ─────────────────────────────────────────────────────────────────────────────

export const UPGRADES = [
  {
    id: 'vitality', name: 'Vitality', desc: '+25 max health (and heals that much).',
    price: 60, growth: 1.45, max: 20,
    apply: (p) => { p.maxHealth += 25; p.health += 25; },
  },
  {
    id: 'power', name: 'Power', desc: '+12% damage with every weapon.',
    price: 80, growth: 1.5, max: 25,
    apply: (p) => { p.damageMult += 0.12; },
  },
  {
    id: 'swift', name: 'Swift Boots', desc: '+7% movement speed.',
    price: 50, growth: 1.6, max: 8,
    apply: (p) => { p.speedMult += 0.07; },
  },
  {
    id: 'regen', name: 'Regeneration', desc: '+0.6 health per second.',
    price: 70, growth: 1.55, max: 15,
    apply: (p) => { p.regen += 0.6; },
  },
  {
    id: 'hands', name: 'Quick Hands', desc: '-12% reload time, +6% fire rate.',
    price: 65, growth: 1.55, max: 6,
    apply: (p) => { p.reloadMult *= 0.88; p.fireRateMult += 0.06; },
  },
  {
    id: 'armor', name: 'Plating', desc: 'Take 6% less damage.',
    price: 90, growth: 1.6, max: 8,
    apply: (p) => { p.armor = Math.min(0.6, p.armor + 0.06); },
  },
  {
    id: 'magnet', name: 'Coin Magnet', desc: 'Pick up coins from further away.',
    price: 40, growth: 1.5, max: 6,
    apply: (p) => { p.magnet += 2; },
  },
  {
    id: 'medkit', name: 'Medkit', desc: 'Instantly restore all health.',
    price: 45, growth: 1.0, max: Infinity, consumable: true,
    apply: (p) => { p.health = p.maxHealth; },
  },
];
