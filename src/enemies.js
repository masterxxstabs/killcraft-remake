import * as THREE from 'three';
import { ENEMIES } from './data/enemies.js';
import { faceTexture } from './textures.js';

const box = new THREE.BoxGeometry(1, 1, 1);
const faceCache = new Map();

function part(mat, w, h, d, x, y, z) {
  const m = new THREE.Mesh(box, mat);
  m.scale.set(w, h, d);
  m.position.set(x, y, z);
  m.castShadow = true;
  return m;
}

// A limb hangs from a pivot so it can swing.
function limb(mat, w, h, x, y) {
  const pivot = new THREE.Group();
  pivot.position.set(x, y, 0);
  const m = part(mat, w, h, w, 0, -h / 2, 0);
  pivot.add(m);
  return { pivot, mesh: m };
}

function buildModel(type, def) {
  const c = def.colors;
  if (!faceCache.has(type)) faceCache.set(type, faceTexture(c.skin, c.eyes));
  const skin = new THREE.MeshLambertMaterial({ color: c.skin });
  const face = new THREE.MeshLambertMaterial({ map: faceCache.get(type) });
  const shirt = new THREE.MeshLambertMaterial({ color: c.shirt });
  const pants = new THREE.MeshLambertMaterial({ color: c.pants });
  const mats = [skin, face, shirt, pants];

  const root = new THREE.Group();
  root.rotation.order = 'YXZ';   // yaw first, then tip over when dying
  const body = new THREE.Group();     // scaled container
  body.scale.setScalar(def.scale);
  root.add(body);

  const torso = part(shirt, 0.5, 0.72, 0.28, 0, 1.11, 0);
  const head = part([skin, skin, skin, skin, face, skin], 0.5, 0.5, 0.5, 0, 1.72, 0);
  const legL = limb(pants, 0.24, 0.75, -0.13, 0.75);
  const legR = limb(pants, 0.24, 0.75, 0.13, 0.75);
  const armL = limb(skin, 0.2, 0.72, -0.36, 1.44);
  const armR = limb(skin, 0.2, 0.72, 0.36, 1.44);
  // short sleeves
  armL.pivot.add(part(shirt, 0.22, 0.24, 0.22, 0, -0.1, 0));
  armR.pivot.add(part(shirt, 0.22, 0.24, 0.22, 0, -0.1, 0));
  if (def.boss) {
    const crown = new THREE.MeshLambertMaterial({ color: '#e0b030', emissive: '#4a3000' });
    mats.push(crown);
    head.add(part(crown, 1.1, 0.25, 1.1, 0, 0.62, 0));
    for (const [x, z] of [[-0.45, -0.45], [0.45, -0.45], [-0.45, 0.45], [0.45, 0.45], [0, 0.45]])
      head.add(part(crown, 0.18, 0.3, 0.18, x, 0.85, z));
  }
  body.add(torso, head, legL.pivot, legR.pivot, armL.pivot, armR.pivot);

  return {
    root, mats, head, torso, legL, legR, armL, armR,
    hitMeshes: [head, torso, legL.mesh, legR.mesh, armL.mesh, armR.mesh],
  };
}

export class Enemy {
  constructor(game, type, wave) {
    const def = ENEMIES[type];
    this.game = game;
    this.type = type;
    this.def = def;
    this.maxHp = Math.round(def.hp * wave.hpMult);
    this.hp = this.maxHp;
    this.speed = def.speed * wave.speedMult * (0.9 + Math.random() * 0.2);
    this.damage = def.damage * wave.damageMult;
    this.coinMult = wave.coinMult;
    this.radius = 0.35 * def.scale;
    this.height = 2 * def.scale;
    this.model = buildModel(type, def);
    for (const m of this.model.hitMeshes) m.userData.enemy = this;
    this.model.head.userData.head = true;
    this.position = this.model.root.position;
    this.kb = new THREE.Vector3();
    this.attackCd = 0.5;
    this.rangedCd = 1 + Math.random() * 2;
    this.attackAnim = 0;
    this.flash = 0;
    this.walk = Math.random() * 10;
    this.rise = 0.9;                 // climbing out of the ground
    this.dead = false;
    this.deathT = 0;
    this.stuckT = 0;
    this.detour = 0;
    this.detourSide = 1;
    this.lastPos = new THREE.Vector3();
    this.groanT = 3 + Math.random() * 8;
  }

  get alive() { return !this.dead; }

  headPos() { return this.position.clone().setY(this.position.y + 1.72 * this.def.scale); }
  chestPos() { return this.position.clone().setY(this.position.y + 1.1 * this.def.scale); }

  hurt(amount, headshot = false, knock = null) {
    if (this.dead) return;
    this.hp -= amount;
    this.flash = 0.1;
    if (knock) this.kb.add(knock.clone().divideScalar(Math.max(1, this.def.scale * this.def.scale)));
    const g = this.game;
    g.effects.damageNumber(headshot ? this.headPos().setY(this.headPos().y + 0.4) : this.chestPos().setY(this.position.y + this.height + 0.2), amount, { crit: headshot });
    g.effects.burst(headshot ? this.headPos() : this.chestPos(), new THREE.Color(this.def.colors.skin).multiplyScalar(0.6).getHex(), headshot ? 8 : 4, { speed: 4, size: 0.1 });
    if (this.hp <= 0) this.die(headshot);
  }

  die(headshot) {
    this.dead = true;
    this.hp = 0;
    this.game.audio.death();
    this.game.onEnemyKilled(this, headshot);
    for (const m of this.model.hitMeshes) m.userData.enemy = null;
  }

  update(dt) {
    const g = this.game, m = this.model;

    if (this.flash > 0) this.flash -= dt;
    const flashOn = this.flash > 0;
    for (const mat of m.mats) mat.emissive.setRGB(flashOn ? 0.8 : 0, flashOn ? 0.8 : 0, flashOn ? 0.8 : 0);

    if (this.dead) {
      this.deathT += dt;
      m.root.rotation.x = Math.max(-Math.PI / 2, -this.deathT * 5);
      this.position.addScaledVector(this.kb, dt);
      this.kb.multiplyScalar(Math.max(0, 1 - dt * 6));
      if (this.deathT > 1.2) this.position.y -= dt * 1.5;
      return this.deathT < 2.4;
    }

    if (this.rise > 0) {
      this.rise -= dt;
      this.position.y = -this.height * Math.max(0, this.rise / 0.9);
      if (Math.random() < 0.3) g.effects.burst(this.position.clone().setY(0.1), 0x6b4a2b, 1, { speed: 3, size: 0.15 });
      if (this.rise <= 0) this.position.y = 0;
      this.face(g.player.position);
      return true;
    }

    const p = g.player.position;
    const to = new THREE.Vector3(p.x - this.position.x, 0, p.z - this.position.z);
    const dist = to.length();
    if (dist > 1e-4) to.divideScalar(dist);

    // Taunt-free simple AI: ranged enemies keep distance and shoot when they can see you.
    let move = to.clone();
    let speed = this.speed;
    const r = this.def.ranged;
    if (r) {
      this.rangedCd -= dt;
      const canSee = dist < r.range && g.world.hasLineOfSight(this.headPos(), g.player.eye());
      if (canSee && dist > 6 && !this.def.boss) {
        move.set(-to.z, 0, to.x).multiplyScalar(Math.sin(this.walk * 0.3) > 0 ? 0.6 : -0.6);
        speed *= 0.6;
      }
      if (canSee && this.rangedCd <= 0) {
        this.rangedCd = 1 / r.rate * (0.8 + Math.random() * 0.4);
        this.shoot(r);
      }
    }

    // stuck? walk sideways for a moment
    if (this.detour > 0) {
      this.detour -= dt;
      move.set(-to.z * this.detourSide, 0, to.x * this.detourSide).add(to.clone().multiplyScalar(0.3));
    }

    // separation from other enemies
    for (const o of g.enemies.list) {
      if (o === this || o.dead || o.rise > 0) continue;
      const dx = this.position.x - o.position.x, dz = this.position.z - o.position.z;
      const min = this.radius + o.radius + 0.25;
      const d2 = dx * dx + dz * dz;
      if (d2 < min * min && d2 > 1e-6) {
        const d = Math.sqrt(d2);
        move.x += (dx / d) * (min - d) * 3;
        move.z += (dz / d) * (min - d) * 3;
      }
    }

    const reachH = this.def.reach + g.player.radius;
    const closeEnough = dist < reachH * 0.8;
    if (closeEnough) speed = 0;
    if (move.lengthSq() > 1) move.normalize();

    this.position.x += (move.x * speed + this.kb.x) * dt;
    this.position.z += (move.z * speed + this.kb.z) * dt;
    this.kb.multiplyScalar(Math.max(0, 1 - dt * 8));
    this.position.y = 0;
    g.world.collide(this.position, this.radius);

    // stuck detection
    this.stuckT += dt;
    if (this.stuckT > 0.6) {
      const moved = this.lastPos.distanceTo(this.position);
      if (speed > 0 && moved < this.speed * 0.6 * 0.25 && this.detour <= 0) {
        this.detour = 0.8 + Math.random() * 0.6;
        this.detourSide = Math.random() < 0.5 ? 1 : -1;
      }
      this.lastPos.copy(this.position);
      this.stuckT = 0;
    }

    // melee
    this.attackCd -= dt;
    const dy = Math.abs(p.y - this.position.y);
    if (dist < reachH && dy < this.height * 0.8 + 0.6 && this.attackCd <= 0) {
      this.attackCd = 1 / this.def.attackRate;
      this.attackAnim = 0.3;
      g.player.hurt(this.damage, this.position);
    }

    this.groanT -= dt;
    if (this.groanT <= 0) {
      this.groanT = 6 + Math.random() * 10;
      if (dist < 20) g.audio.groan();
    }

    this.face(p);
    this.animate(dt, speed > 0 ? speed : 0);
    return true;
  }

  face(target) {
    const want = Math.atan2(target.x - this.position.x, target.z - this.position.z);
    let diff = want - this.model.root.rotation.y;
    diff = Math.atan2(Math.sin(diff), Math.cos(diff));
    this.model.root.rotation.y += diff * 0.2;
  }

  shoot(r) {
    const g = this.game;
    const from = this.headPos();
    const target = g.player.eye().add(new THREE.Vector3(0, -0.5, 0));
    const base = target.sub(from).normalize();
    g.audio.spit();
    for (let i = 0; i < r.count; i++) {
      const off = (i - (r.count - 1) / 2) * r.spread;
      const dir = base.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), off);
      g.projectiles.spawnEnemy(from.clone().addScaledVector(dir, this.radius + 0.4), dir.multiplyScalar(r.speed), r.damage * (this.damage / this.def.damage), r.color);
    }
    this.attackAnim = 0.25;
  }

  animate(dt, speed) {
    const m = this.model;
    this.walk += dt * (2 + speed * 2.2);
    const swing = speed > 0 ? Math.sin(this.walk) * 0.7 : 0;
    m.legL.pivot.rotation.x = swing;
    m.legR.pivot.rotation.x = -swing;
    const pose = this.def.pose;
    let armBase = pose === 'reach' ? -Math.PI / 2 + 0.1 : 0;
    let armSwing = pose === 'run' ? swing * 1.3 : pose === 'heavy' ? swing * 0.5 : Math.sin(this.walk * 0.5) * 0.08;
    if (this.attackAnim > 0) {
      this.attackAnim -= dt;
      armBase = -Math.PI / 2 - Math.sin((this.attackAnim / 0.3) * Math.PI) * 0.9;
      armSwing = 0;
    }
    m.armL.pivot.rotation.x = armBase + armSwing;
    m.armR.pivot.rotation.x = armBase - armSwing;
  }
}

export class EnemyManager {
  constructor(game) {
    this.game = game;
    this.list = [];
    this.raycaster = new THREE.Raycaster();
  }

  spawn(type, wave, pos) {
    const e = new Enemy(this.game, type, wave);
    e.position.copy(pos);
    e.position.y = -e.height;
    e.lastPos.copy(pos);
    this.game.scene.add(e.model.root);
    this.list.push(e);
    return e;
  }

  get aliveCount() {
    let n = 0;
    for (const e of this.list) if (!e.dead) n++;
    return n;
  }

  update(dt) {
    for (let i = this.list.length - 1; i >= 0; i--) {
      const e = this.list[i];
      if (!e.update(dt)) {
        this.game.scene.remove(e.model.root);
        for (const m of e.model.mats) m.dispose();
        this.list.splice(i, 1);
      } else {
        e.model.root.updateMatrixWorld(true);
      }
    }
  }

  // Returns every enemy hit along a ray (closest first), one entry per enemy.
  raycast(origin, dir, maxDist) {
    const meshes = [];
    for (const e of this.list) if (!e.dead && e.rise <= 0.3) meshes.push(...e.model.hitMeshes);
    this.raycaster.set(origin, dir);
    this.raycaster.far = maxDist;
    const hits = this.raycaster.intersectObjects(meshes, false);
    const seen = new Set(), out = [];
    for (const h of hits) {
      const e = h.object.userData.enemy;
      if (!e || seen.has(e)) continue;
      seen.add(e);
      out.push({ enemy: e, dist: h.distance, point: h.point, head: !!h.object.userData.head });
    }
    return out;
  }

  clear() {
    for (const e of this.list) {
      this.game.scene.remove(e.model.root);
      for (const m of e.model.mats) m.dispose();
    }
    this.list = [];
  }
}
