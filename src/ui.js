import { WEAPONS } from './data/weapons.js';
import { UPGRADES } from './data/upgrades.js';
import { ABILITIES } from './data/abilities.js';

const $ = (id) => document.getElementById(id);

export class UI {
  constructor(game) {
    this.game = game;
    this.bannerT = 0;
    this.hitT = 0;
    this.hurtT = 0;
    this.feed = [];
  }

  show(id, on = true) { $(id).classList.toggle('hidden', !on); }

  // ── main menu ────────────────────────────────────────────────────────────
  buildMenu() {
    const g = this.game;
    const wrap = $('abilities');
    wrap.innerHTML = '';
    for (const a of ABILITIES) {
      const el = document.createElement('button');
      el.className = 'card' + (g.abilityId === a.id ? ' selected' : '');
      el.style.setProperty('--c', a.color);
      el.innerHTML = `<b>${a.name}</b><span>${a.desc}</span><i>Cooldown ${a.cooldown}s</i>`;
      el.onclick = () => { g.abilityId = a.id; g.saveSettings(); this.buildMenu(); };
      wrap.appendChild(el);
    }
    const s = g.save;
    $('records').innerHTML = `Best wave <b>${s.bestWave}</b> · Best score <b>${s.bestScore}</b> · Total kills <b>${s.totalKills}</b> · Games <b>${s.games}</b>`;
  }

  // ── HUD ──────────────────────────────────────────────────────────────────
  updateWeapon() {
    const w = this.game.weapons;
    if (!w || !w.def) return;
    const d = w.def, st = w.state[d.id];
    $('weapon-name').textContent = d.name;
    $('ammo').textContent = d.melee ? '∞' : `${st.ammo} / ${d.mag}`;
    $('ammo').classList.toggle('low', !d.melee && st.ammo <= Math.ceil(d.mag * 0.25));
    $('slots').innerHTML = w.owned
      .map((o, i) => `<span class="${i === w.current ? 'on' : ''}">${i + 1}</span>`)
      .join('');
  }

  banner(text, color = '#fff', time = 2.5, sub = '') {
    $('banner').innerHTML = `${text}${sub ? `<small>${sub}</small>` : ''}`;
    $('banner').style.color = color;
    $('banner').classList.add('on');
    this.bannerT = time;
  }

  hitmarker(head) {
    $('hitmarker').className = 'on' + (head ? ' head' : '');
    this.hitT = 0.12;
  }

  hurt(frac) {
    this.hurtT = Math.min(1, this.hurtT + 0.35 + frac * 2);
  }

  killFeed(text, color) {
    const el = document.createElement('div');
    el.textContent = text;
    el.style.color = color;
    $('feed').prepend(el);
    setTimeout(() => el.remove(), 3000);
    while ($('feed').children.length > 5) $('feed').lastChild.remove();
  }

  update(dt) {
    const g = this.game, p = g.player;
    $('hp-fill').style.width = `${(p.health / p.maxHealth) * 100}%`;
    $('hp-text').textContent = `${Math.ceil(p.health)} / ${p.maxHealth}`;
    $('coins').textContent = g.coins;
    $('score').textContent = g.score;
    $('wave').textContent = g.waveNumber;
    if (g.phase === 'wave') {
      $('remaining').textContent = `${g.remaining} enemies left`;
    } else {
      $('remaining').textContent = `Next wave in ${Math.ceil(g.intermission)}s`;
    }
    $('intermission').classList.toggle('hidden', g.phase !== 'intermission' || g.shopOpen);

    // ability
    const a = g.ability;
    const cd = Math.max(0, p.abilityCd);
    $('ability').style.setProperty('--c', a.color);
    $('ability-name').textContent = a.name;
    $('ability-fill').style.height = `${(1 - cd / a.cooldown) * 100}%`;
    $('ability-cd').textContent = cd > 0 ? Math.ceil(cd) : 'Q';
    $('ability').classList.toggle('ready', cd <= 0);

    // reload bar
    const w = g.weapons;
    $('reload').classList.toggle('hidden', !(w.reloading > 0));
    if (w.reloading > 0) $('reload-fill').style.width = `${(1 - w.reloading / w.reloadTotal) * 100}%`;

    // boss bar
    const boss = g.enemies.list.find((e) => e.def.boss && !e.dead);
    $('boss').classList.toggle('hidden', !boss);
    if (boss) {
      $('boss-name').textContent = boss.def.name;
      $('boss-fill').style.width = `${(boss.hp / boss.maxHp) * 100}%`;
    }

    if (this.bannerT > 0) {
      this.bannerT -= dt;
      if (this.bannerT <= 0) $('banner').classList.remove('on');
    }
    if (this.hitT > 0) {
      this.hitT -= dt;
      if (this.hitT <= 0) $('hitmarker').className = '';
    }
    this.hurtT = Math.max(0, this.hurtT - dt * 1.5);
    const low = p.health / p.maxHealth < 0.3 ? 0.35 + Math.sin(performance.now() / 200) * 0.1 : 0;
    $('vignette').style.opacity = Math.max(this.hurtT, low);
    $('adrenaline').style.opacity = p.buffs.adrenaline > 0 ? 1 : 0;
  }

  // ── shop ─────────────────────────────────────────────────────────────────
  buildShop() {
    const g = this.game, p = g.player;
    $('shop-coins').textContent = g.coins;
    const wl = $('shop-weapons');
    wl.innerHTML = '';
    for (const d of WEAPONS) {
      if (d.price === 0) continue;
      const owned = g.weapons.owns(d.id);
      const el = document.createElement('button');
      el.className = 'item' + (owned ? ' owned' : g.coins < d.price ? ' poor' : '');
      el.innerHTML = `<div><b>${d.name}</b><span>${d.desc}</span>
        <em>${d.projectile ? `${d.projectile.damage} blast dmg` : `${d.damage}${d.pellets > 1 ? ' × ' + d.pellets : ''} dmg`} · ${d.rate}/s${d.mag ? ' · ' + d.mag + ' mag' : ''}</em></div>
        <div class="price">${owned ? 'OWNED' : '⛁ ' + d.price}</div>`;
      el.onclick = () => g.buyWeapon(d.id);
      wl.appendChild(el);
    }
    const ul = $('shop-upgrades');
    ul.innerHTML = '';
    for (const u of UPGRADES) {
      const lvl = g.upgradeLevels[u.id] || 0;
      const price = g.upgradePrice(u);
      const maxed = lvl >= u.max;
      const useless = u.id === 'medkit' && p.health >= p.maxHealth;
      const el = document.createElement('button');
      el.className = 'item' + (maxed ? ' owned' : g.coins < price || useless ? ' poor' : '');
      el.innerHTML = `<div><b>${u.name}${u.consumable ? '' : ` <small>lvl ${lvl}${u.max < 99 ? '/' + u.max : ''}</small>`}</b><span>${u.desc}</span></div>
        <div class="price">${maxed ? 'MAX' : '⛁ ' + price}</div>`;
      el.onclick = () => g.buyUpgrade(u.id);
      ul.appendChild(el);
    }
    $('shop-stats').innerHTML = [
      ['Health', `${Math.ceil(p.health)}/${p.maxHealth}`],
      ['Damage', `${Math.round(p.damageMult * 100)}%`],
      ['Speed', `${Math.round(p.speedMult * 100)}%`],
      ['Regen', `${p.regen.toFixed(1)}/s`],
      ['Armor', `${Math.round(p.armor * 100)}%`],
    ].map(([k, v]) => `<span>${k} <b>${v}</b></span>`).join('');
  }

  // ── game over ────────────────────────────────────────────────────────────
  showDeath(stats, record) {
    $('dead-stats').innerHTML = `
      <div><span>Wave reached</span><b>${stats.wave}</b></div>
      <div><span>Kills</span><b>${stats.kills}</b></div>
      <div><span>Score</span><b>${stats.score}</b></div>
      <div><span>Time</span><b>${Math.floor(stats.time / 60)}:${String(Math.floor(stats.time % 60)).padStart(2, '0')}</b></div>`;
    $('dead-record').classList.toggle('hidden', !record);
    this.show('dead');
  }
}
