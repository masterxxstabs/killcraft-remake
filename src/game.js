import * as THREE from 'three';
import { World } from './world.js';
import { Player } from './player.js';
import { Weapons } from './weapons.js';
import { EnemyManager } from './enemies.js';
import { Projectiles } from './projectiles.js';
import { Pickups } from './pickups.js';
import { Effects } from './effects.js';
import { Audio } from './audio.js';
import { UI } from './ui.js';
import { buildWave, INTERMISSION } from './data/waves.js';
import { WEAPONS } from './data/weapons.js';
import { UPGRADES } from './data/upgrades.js';
import { ABILITIES } from './data/abilities.js';

const SAVE_KEY = 'blockhold-save-v1';
const SETTINGS_KEY = 'blockhold-settings-v1';
const NORMAL_SKY = { sky: '#8ec9f0', fog: '#a9d6f2', fogNear: 30, fogFar: 110, sun: '#fff4dc', ambient: 0.9 };

export class Game {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.autoClear = false;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, 1, 0.05, 300);
    this.camera.rotation.order = 'YXZ';
    this.scene.add(this.camera);

    this.hemi = new THREE.HemisphereLight(0xdfefff, 0x5a4a30, 0.9);
    this.scene.add(this.hemi);
    this.sun = new THREE.DirectionalLight(0xfff4dc, 2.2);
    this.sun.position.set(30, 50, 20);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    const sc = this.sun.shadow.camera;
    sc.left = sc.bottom = -40; sc.right = sc.top = 40; sc.far = 150;
    this.scene.add(this.sun);
    this.scene.fog = new THREE.Fog(0xa9d6f2, 30, 110);
    this.skyColor = new THREE.Color();
    this.skyTarget = { ...NORMAL_SKY };

    this.audio = new Audio();
    this.ui = new UI(this);
    this.effects = new Effects(this);
    this.player = new Player(this);
    this.weapons = new Weapons(this);
    this.enemies = new EnemyManager(this);
    this.projectiles = new Projectiles(this);
    this.pickups = new Pickups(this);

    this.keys = {};
    this.state = 'menu';
    this.shakeAmt = 0;
    this.save = this.loadJSON(SAVE_KEY, { bestWave: 0, bestScore: 0, totalKills: 0, games: 0 });
    const st = this.loadJSON(SETTINGS_KEY, {});
    this.sensitivity = st.sensitivity ?? 0.0022;
    this.audio.setVolume(st.volume ?? 0.5);
    this.abilityId = st.ability ?? ABILITIES[0].id;

    this.newWorld();
    this.bindInput();
    this.bindButtons();
    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.ui.buildMenu();
    this.applySky(NORMAL_SKY, true);

    this.last = performance.now();
    this.renderer.setAnimationLoop(() => this.frame());
  }

  // ── persistence ──────────────────────────────────────────────────────────
  loadJSON(key, fallback) {
    try { return { ...fallback, ...JSON.parse(localStorage.getItem(key) || '{}') }; } catch { return fallback; }
  }
  saveSettings() {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify({ sensitivity: this.sensitivity, volume: this.audio.volume, ability: this.abilityId }));
  }
  get ability() { return ABILITIES.find((a) => a.id === this.abilityId) || ABILITIES[0]; }

  newWorld() {
    if (this.world) this.scene.remove(this.world.group);
    this.world = new World(this.scene, (Math.random() * 1e9) | 0);
  }

  // ── input ────────────────────────────────────────────────────────────────
  bindInput() {
    document.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      this.keys[e.code] = true;
      if (this.state !== 'playing') {
        if (e.code === 'KeyB' && this.shopOpen) this.closeShop();
        return;
      }
      if (e.code === 'Space') e.preventDefault();
      const n = parseInt(e.key, 10);
      if (n >= 1 && n <= 9) this.weapons.equip(n - 1);
      if (e.code === 'KeyR') this.weapons.startReload();
      if (e.code === 'KeyQ') this.useAbility();
      if (e.code === 'KeyB') this.shopOpen ? this.closeShop() : this.openShop();
      if ((e.code === 'KeyN' || e.code === 'Enter') && this.phase === 'intermission') this.startWave();
      if (e.code === 'KeyM') this.audio.toggleMute();
    });
    document.addEventListener('keyup', (e) => { this.keys[e.code] = false; });
    window.addEventListener('blur', () => { this.keys = {}; this.weapons.trigger(false); });

    document.addEventListener('mousemove', (e) => {
      if (this.state === 'playing' && this.locked && !this.shopOpen) this.player.look(e.movementX, e.movementY, this.sensitivity);
    });
    this.canvas.addEventListener('mousedown', (e) => {
      if (this.state !== 'playing' || this.shopOpen) return;
      if (!this.locked) { this.lock(); return; }
      if (e.button === 0) this.weapons.trigger(true);
    });
    document.addEventListener('mouseup', (e) => { if (e.button === 0) this.weapons.trigger(false); });
    document.addEventListener('wheel', (e) => {
      if (this.state === 'playing' && !this.shopOpen) this.weapons.cycle(e.deltaY > 0 ? 1 : -1);
    }, { passive: true });
    document.addEventListener('contextmenu', (e) => e.preventDefault());

    document.addEventListener('pointerlockchange', () => {
      const was = this.locked;
      this.locked = document.pointerLockElement === this.canvas;
      if (was && !this.locked && this.state === 'playing' && !this.shopOpen && !this.ignoreUnlock) this.pause();
      this.ignoreUnlock = false;
    });
  }

  lock() {
    try {
      const r = this.canvas.requestPointerLock();
      if (r && r.catch) r.catch(() => {});
    } catch { /* pointer lock unavailable */ }
  }

  unlock(silent = true) {
    if (document.pointerLockElement) {
      this.ignoreUnlock = silent;
      document.exitPointerLock();
    }
  }

  bindButtons() {
    const $ = (id) => document.getElementById(id);
    $('play').onclick = () => this.startGame();
    $('resume').onclick = () => this.resume();
    $('quit').onclick = () => this.toMenu();
    $('again').onclick = () => this.startGame();
    $('dead-menu').onclick = () => this.toMenu();
    $('shop-close').onclick = () => this.closeShop();
    $('shop-start').onclick = () => { this.closeShop(); this.startWave(); };
    const sens = $('sens'), vol = $('vol');
    sens.value = this.sensitivity * 10000;
    vol.value = this.audio.volume * 100;
    sens.oninput = () => { this.sensitivity = sens.value / 10000; this.saveSettings(); };
    vol.oninput = () => { this.audio.setVolume(vol.value / 100); this.saveSettings(); };
    document.addEventListener('keydown', (e) => {
      if (e.code === 'Escape' && this.shopOpen) this.closeShop();
      else if (e.code === 'Escape' && this.state === 'paused') this.resume();
    });
  }

  resize() {
    const w = window.innerWidth, h = window.innerHeight;
    this.renderer.setSize(w, h);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  // ── flow ─────────────────────────────────────────────────────────────────
  startGame() {
    this.audio.unlock();
    this.ui.show('menu', false);
    this.ui.show('dead', false);
    this.ui.show('pause', false);
    this.ui.show('hud');
    this.enemies.clear();
    this.projectiles.clear();
    this.pickups.clear();
    this.effects.clear();
    this.newWorld();
    this.player.reset();
    this.weapons.reset();
    this.coins = 0;
    this.score = 0;
    this.kills = 0;
    this.time = 0;
    this.waveNumber = 0;
    this.upgradeLevels = {};
    this.shopOpen = false;
    this.state = 'playing';
    this.godMode = false;
    this.beginIntermission(8);
    this.ui.banner('GET READY', '#ffe066', 3, 'Survive as many waves as you can');
    this.ui.updateWeapon();
    this.lock();
  }

  toMenu() {
    this.unlock();
    this.state = 'menu';
    this.shopOpen = false;
    for (const id of ['hud', 'pause', 'dead', 'shop']) this.ui.show(id, false);
    this.ui.buildMenu();
    this.ui.show('menu');
    this.applySky(NORMAL_SKY);
  }

  pause() {
    this.state = 'paused';
    this.weapons.trigger(false);
    this.ui.show('pause');
  }

  resume() {
    this.ui.show('pause', false);
    this.state = 'playing';
    this.last = performance.now();
    this.lock();
  }

  canAct() { return this.state === 'playing' && !this.shopOpen && !this.player.dead; }

  beginIntermission(time = INTERMISSION) {
    this.phase = 'intermission';
    this.intermission = time;
    this.applySky(NORMAL_SKY);
  }

  startWave() {
    if (this.phase !== 'intermission') return;
    this.waveNumber++;
    this.wave = buildWave(this.waveNumber);
    this.spawnQueue = [...this.wave.enemies];
    this.remaining = this.spawnQueue.length;
    this.spawnT = 1;
    this.phase = 'wave';
    const mod = this.wave.modifier;
    this.applySky(mod ? { ...NORMAL_SKY, ...mod } : NORMAL_SKY);
    this.audio.waveStart();
    const boss = this.wave.enemies.includes('hollowKing');
    if (mod) this.ui.banner(`WAVE ${this.waveNumber}: ${mod.name}`, '#ff8c5a', 3.5, mod.desc);
    else if (boss) this.ui.banner(`WAVE ${this.waveNumber}`, '#ff5a5a', 3.5, 'A boss approaches...');
    else this.ui.banner(`WAVE ${this.waveNumber}`, '#ffffff', 2.5, `${this.remaining} enemies incoming`);
  }

  endWave() {
    const bonus = this.wave.clearBonus;
    this.addCoins(bonus);
    this.score += this.waveNumber * 50;
    this.audio.waveClear();
    this.ui.banner('WAVE CLEARED', '#7dff8a', 3, `+${bonus} coins · press B to open the shop`);
    this.beginIntermission();
  }

  openShop() {
    if (this.phase !== 'intermission') {
      this.ui.banner('SHOP CLOSED', '#ff7070', 1.2, 'The shop opens between waves');
      return;
    }
    this.shopOpen = true;
    this.weapons.trigger(false);
    this.unlock();
    this.ui.buildShop();
    this.ui.show('shop');
  }

  closeShop() {
    if (!this.shopOpen) return;
    this.shopOpen = false;
    this.ui.show('shop', false);
    this.lock();
  }

  upgradePrice(u) {
    return Math.round(u.price * Math.pow(u.growth, this.upgradeLevels[u.id] || 0));
  }

  buyWeapon(id) {
    const d = WEAPONS.find((w) => w.id === id);
    if (this.weapons.owns(id) || this.coins < d.price) { this.audio.deny(); return; }
    this.coins -= d.price;
    this.weapons.give(id);
    this.audio.buy();
    this.ui.buildShop();
  }

  buyUpgrade(id) {
    const u = UPGRADES.find((x) => x.id === id);
    const lvl = this.upgradeLevels[id] || 0;
    const price = this.upgradePrice(u);
    if (lvl >= u.max || this.coins < price || (id === 'medkit' && this.player.health >= this.player.maxHealth)) {
      this.audio.deny();
      return;
    }
    this.coins -= price;
    if (!u.consumable) this.upgradeLevels[id] = lvl + 1;
    u.apply(this.player);
    this.audio.buy();
    this.ui.buildShop();
  }

  addCoins(n) { this.coins += n; }

  useAbility() {
    if (!this.canAct() || this.player.abilityCd > 0) return;
    this.ability.use(this);
    this.player.abilityCd = this.ability.cooldown;
  }

  onEnemyKilled(e, headshot) {
    this.kills++;
    this.remaining--;
    const d = e.def;
    this.score += Math.round(d.score * (headshot ? 1.5 : 1) * (1 + this.waveNumber * 0.1));
    const coins = Math.round((d.coins[0] + Math.random() * (d.coins[1] - d.coins[0])) * e.coinMult * (1 + this.waveNumber * 0.04));
    this.pickups.dropCoins(e.position, coins);
    if (Math.random() < (d.boss ? 1 : 0.07)) this.pickups.drop(e.position, 'heal', d.boss ? 60 : 20);
    this.effects.burst(e.chestPos(), new THREE.Color(d.colors.shirt).getHex(), 10, { speed: 5, size: 0.18 });
    if (d.boss) {
      this.ui.banner('BOSS DEFEATED', '#ffd54a', 3);
      this.shake(0.5);
    }
    this.ui.killFeed(`${headshot ? '🎯 ' : ''}${d.name} +${coins}⛁`, headshot ? '#ffd54a' : '#ddd');
  }

  onPlayerDeath() {
    this.weapons.trigger(false);
    this.state = 'dead';
    this.audio.gameOver();
    this.unlock();
    const s = this.save;
    const stats = { wave: this.waveNumber, kills: this.kills, score: this.score, time: this.time };
    const record = this.score > s.bestScore || this.waveNumber > s.bestWave;
    s.bestWave = Math.max(s.bestWave, this.waveNumber);
    s.bestScore = Math.max(s.bestScore, this.score);
    s.totalKills += this.kills;
    s.games++;
    localStorage.setItem(SAVE_KEY, JSON.stringify(s));
    setTimeout(() => {
      this.ui.show('hud', false);
      this.ui.showDeath(stats, record);
    }, 1200);
  }

  shake(n) { this.shakeAmt = Math.min(0.6, this.shakeAmt + n); }

  // ── sky & lighting per wave modifier ─────────────────────────────────────
  applySky(cfg, instant = false) {
    this.skyTarget = { ...NORMAL_SKY, ...cfg };
    if (instant) this.blendSky(1);
  }

  blendSky(k) {
    const t = this.skyTarget;
    const bg = this.scene.background instanceof THREE.Color ? this.scene.background : (this.scene.background = new THREE.Color(t.sky));
    bg.lerp(new THREE.Color(t.sky), k);
    this.scene.fog.color.lerp(new THREE.Color(t.fog), k);
    this.scene.fog.near += (t.fogNear - this.scene.fog.near) * k;
    this.scene.fog.far += (t.fogFar - this.scene.fog.far) * k;
    this.sun.color.lerp(new THREE.Color(t.sun), k);
    this.hemi.intensity += (t.ambient - this.hemi.intensity) * k;
  }

  // ── main loop ────────────────────────────────────────────────────────────
  frame() {
    const now = performance.now();
    const dt = Math.min(0.05, (now - this.last) / 1000);
    this.last = now;

    this.blendSky(Math.min(1, dt * 1.5));

    if (this.state === 'playing' || this.state === 'dead') this.update(dt);
    else if (this.state === 'menu') {
      // slow flyover on the menu
      const t = now / 1000 * 0.08;
      this.camera.position.set(Math.cos(t) * 26, 14, Math.sin(t) * 26);
      this.camera.lookAt(0, 0, 0);
    }

    this.shakeAmt = Math.max(0, this.shakeAmt - dt * 1.5);
    this.effects.update(dt, this.camera);
    this.renderer.clear();
    this.renderer.render(this.scene, this.camera);
    if (this.state === 'playing' || this.state === 'paused') {
      this.renderer.clearDepth();
      this.renderer.render(this.weapons.vmScene, this.camera);
    }
  }

  update(dt) {
    if (this.state === 'playing' && !this.player.dead) {
      this.time += dt;
      this.player.update(dt, this.shopOpen ? {} : this.keys);
      this.weapons.update(dt);

      if (this.phase === 'intermission' && !this.shopOpen) {
        this.intermission -= dt;
        if (this.intermission <= 0) this.startWave();
      }
      if (this.phase === 'wave') {
        this.spawnT -= dt;
        if (this.spawnQueue.length && this.spawnT <= 0 && this.enemies.aliveCount < this.wave.maxAlive) {
          this.spawnT = this.wave.spawnInterval * (0.6 + Math.random() * 0.8);
          const type = this.spawnQueue.shift();
          const pos = this.world.randomSpawnPoint(this.player.position);
          this.enemies.spawn(type, this.wave, pos);
          if (type === 'hollowKing') {
            this.audio.bossRoar();
            this.shake(0.4);
          }
        }
        if (!this.spawnQueue.length && this.remaining <= 0) this.endWave();
      }
    }
    this.enemies.update(dt);
    this.projectiles.update(dt);
    this.pickups.update(dt);
    this.sun.position.set(this.player.position.x + 30, 50, this.player.position.z + 20);
    this.sun.target.position.copy(this.player.position);
    this.sun.target.updateMatrixWorld();
    this.ui.update(dt);
  }
}
