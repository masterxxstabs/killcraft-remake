import * as THREE from 'three';
import { WEAPONS } from './data/weapons.js';

const box = new THREE.BoxGeometry(1, 1, 1);

function gunModel(def) {
  const g = new THREE.Group();
  const md = def.model;
  const body = new THREE.MeshLambertMaterial({ color: md.body });
  const accent = new THREE.MeshLambertMaterial({ color: md.accent });
  const add = (mat, sx, sy, sz, x, y, z, rx = 0) => {
    const m = new THREE.Mesh(box, mat);
    m.scale.set(sx, sy, sz);
    m.position.set(x, y, z);
    m.rotation.x = rx;
    g.add(m);
    return m;
  };
  if (def.melee) {
    add(accent, 0.05, 0.05, md.length, 0, 0, -md.length / 2);                 // handle
    add(body, 0.16, 0.06, 0.08, 0, 0, -md.length);                            // head
    add(body, 0.05, 0.06, 0.12, -0.06, 0, -md.length - 0.08);
    add(body, 0.05, 0.06, 0.12, 0.06, 0, -md.length - 0.08);
    g.rotation.x = 0.5;
  } else {
    const L = md.length, W = md.width;
    add(body, W, W * 1.2, L, 0, 0, -L / 2);                                   // body
    add(accent, W * 0.5, W * 0.5, L * 0.35, 0, W * 0.25, -L - L * 0.12);      // barrel
    add(accent, W * 1.02, W * 0.3, L * 0.3, 0, W * 0.5, -L * 0.45);           // top stripe
    add(body, W * 0.8, W * 2, W * 0.9, 0, -W * 1.3, -W * 0.6, 0.25);          // grip
    if (def.mag > 10) add(accent, W * 0.6, W * 1.8, W * 0.7, 0, -W * 1.2, -L * 0.55); // magazine
  }
  g.userData.muzzle = new THREE.Vector3(0, 0.02, -(md.length * 1.3));
  return g;
}

export class Weapons {
  constructor(game) {
    this.game = game;
    this.defs = WEAPONS;
    this.vmScene = new THREE.Scene();
    this.vmScene.add(new THREE.HemisphereLight(0xffffff, 0x666655, 2.2));
    const dl = new THREE.DirectionalLight(0xffffff, 1.5);
    dl.position.set(1, 2, 1);
    this.vmScene.add(dl);
    this.vmRoot = new THREE.Group();
    this.vmScene.add(this.vmRoot);
    this.holder = new THREE.Group();
    this.holder.scale.setScalar(0.7);
    this.vmRoot.add(this.holder);
    this.reset();
  }

  reset() {
    this.owned = [];
    this.state = {};
    this.held = null;
    for (const d of this.defs) if (d.price === 0) this.give(d.id, false);
    this.cooldown = 0;
    this.reloading = 0;
    this.swing = 0;
    this.kick = 0;
    this.switchAnim = 0;
    this.triggerDown = false;
    this.triggerPressed = false;
    this.equip(Math.min(1, this.owned.length - 1));
  }

  owns(id) { return this.owned.some((d) => d.id === id); }

  give(id, equip = true) {
    const def = this.defs.find((d) => d.id === id);
    if (!def || this.owns(id)) return;
    this.owned.push(def);
    this.owned.sort((a, b) => this.defs.indexOf(a) - this.defs.indexOf(b));
    this.state[id] = { ammo: def.mag || 0 };
    if (this.held) this.current = this.owned.indexOf(this.held);
    if (equip) this.equip(this.owned.indexOf(def));
    else this.game.ui.updateWeapon();
  }

  get def() { return this.held; }

  equip(i) {
    if (i < 0 || i >= this.owned.length) return;
    if (this.owned[i] === this.held && this.model) return;
    this.held = this.owned[i];
    this.current = i;
    this.reloading = 0;
    this.cooldown = Math.max(this.cooldown, 0.25);
    if (this.model) this.holder.remove(this.model);
    this.model = gunModel(this.def);
    this.holder.add(this.model);
    this.switchAnim = 0.25;
    this.game.ui.updateWeapon();
  }

  cycle(dir) {
    const n = this.owned.length;
    this.equip(((this.current + dir) % n + n) % n);
  }

  trigger(down) {
    if (down && !this.triggerDown) this.triggerPressed = true;
    this.triggerDown = down;
  }

  startReload() {
    const d = this.def, st = this.state[d.id];
    if (d.melee || this.reloading > 0 || st.ammo >= d.mag) return;
    this.reloading = d.reload * this.game.player.reloadMult;
    this.reloadTotal = this.reloading;
    this.game.audio.reload();
  }

  rateMult() {
    const p = this.game.player;
    return p.fireRateMult * (p.buffs.adrenaline > 0 ? 2 : 1);
  }

  update(dt) {
    const g = this.game, d = this.def, st = this.state[d.id];
    this.cooldown -= dt;
    if (this.reloading > 0) {
      this.reloading -= dt;
      if (this.reloading <= 0) { st.ammo = d.mag; this.reloading = 0; g.ui.updateWeapon(); }
    }

    const wants = d.auto || d.melee ? this.triggerDown : this.triggerPressed;
    if (wants && this.cooldown <= 0 && g.canAct()) this.fire();
    this.triggerPressed = false;

    // animate the held weapon
    this.kick = Math.max(0, this.kick - dt * 8);
    this.swing = Math.max(0, this.swing - dt * 4);
    this.switchAnim = Math.max(0, this.switchAnim - dt);
    const p = g.player;
    const bobX = p.moving ? Math.sin(p.bob) * 0.015 : 0;
    const bobY = p.moving ? Math.abs(Math.cos(p.bob)) * 0.012 : 0;
    const rl = this.reloading > 0 ? Math.sin((1 - this.reloading / this.reloadTotal) * Math.PI) : 0;
    this.holder.position.set(0.2 + bobX, -0.2 + bobY - this.switchAnim * 0.8 - rl * 0.1, -0.4 + this.kick * 0.06);
    this.holder.rotation.set(this.kick * 0.25 + rl * -0.6 + (d.melee ? -Math.sin(this.swing * Math.PI) * 1.4 : 0), d.melee ? Math.sin(this.swing * Math.PI) * 0.6 : 0, rl * 0.3);
    this.vmRoot.position.copy(g.camera.position);
    this.vmRoot.quaternion.copy(g.camera.quaternion);
  }

  muzzleWorld() {
    this.vmRoot.updateMatrixWorld(true);
    return this.model.userData.muzzle.clone().applyMatrix4(this.model.matrixWorld);
  }

  fire() {
    const g = this.game, d = this.def, st = this.state[d.id], p = g.player;
    const eye = g.camera.position.clone();
    const fwd = p.forward();
    this.cooldown = 1 / (d.rate * this.rateMult());

    if (d.melee) {
      this.swing = 1;
      g.audio.swing();
      let best = null, bestD = Infinity;
      for (const e of g.enemies.list) {
        if (e.dead || e.rise > 0.3) continue;
        const to = e.chestPos().sub(eye);
        const dist = Math.max(0, to.length() - e.radius);
        if (dist > d.range) continue;
        if (to.normalize().dot(fwd) < 0.55) continue;
        if (dist < bestD) { bestD = dist; best = e; }
      }
      if (best) {
        best.hurt(d.damage * p.damageMult, false, fwd.clone().setY(0).normalize().multiplyScalar(d.knockback));
        g.audio.thud();
        g.ui.hitmarker(false);
      }
      return;
    }

    if (this.reloading > 0) return;
    if (st.ammo <= 0) { g.audio.empty(); this.startReload(); return; }
    st.ammo--;
    this.kick = 1;
    p.recoil += d.projectile ? 0.04 : Math.min(0.05, d.damage * d.pellets / 4000 + 0.008);
    g.audio.shoot(d.id);
    const muzzle = this.muzzleWorld();
    g.effects.flash(eye.clone().addScaledVector(fwd, 1), d.id === 'railspike' ? 0x7fe7ff : 0xffc46b, 4, 0.06);

    if (d.projectile) {
      const pr = d.projectile;
      g.projectiles.spawnRocket(eye.clone().addScaledVector(fwd, 0.6), fwd.clone().multiplyScalar(pr.speed), {
        radius: pr.radius, damage: pr.damage, knockback: d.knockback,
      });
    } else {
      let anyHit = false, anyHead = false;
      for (let i = 0; i < (d.pellets || 1); i++) {
        const dir = fwd.clone();
        if (d.spread) {
          dir.x += (Math.random() - 0.5) * 2 * d.spread;
          dir.y += (Math.random() - 0.5) * 2 * d.spread;
          dir.z += (Math.random() - 0.5) * 2 * d.spread;
          dir.normalize();
        }
        const wall = g.world.raycast(eye, dir, d.range);
        const hits = g.enemies.raycast(eye, dir, wall);
        let end = eye.clone().addScaledVector(dir, wall);
        let stopped = false;
        for (const h of hits) {
          const mult = h.head ? (d.headshot ?? 2) : 1;
          h.enemy.hurt(d.damage * p.damageMult * mult, h.head, dir.clone().setY(0).multiplyScalar(d.knockback));
          anyHit = true;
          anyHead ||= h.head;
          if (!d.pierce) { end = h.point; stopped = true; break; }
        }
        if (!stopped && wall < d.range) g.effects.burst(end, 0x8a8a8a, 3, { speed: 2, size: 0.08, life: 0.4 });
        g.effects.tracer(muzzle, end, d.id === 'railspike' ? 0x7fe7ff : 0xfff2a8, d.id === 'railspike' ? 0.06 : 0.02, d.id === 'railspike' ? 0.25 : 0.06);
      }
      if (anyHit) { g.ui.hitmarker(anyHead); anyHead ? g.audio.headshot() : g.audio.hit(); }
    }
    if (st.ammo <= 0) this.startReload();
    g.ui.updateWeapon();
  }
}
