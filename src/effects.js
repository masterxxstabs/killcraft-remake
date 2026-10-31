import * as THREE from 'three';

const cube = new THREE.BoxGeometry(1, 1, 1);

// Visual-only stuff: particles, tracers, explosions, floating damage numbers.
export class Effects {
  constructor(game) {
    this.game = game;
    this.scene = game.scene;
    this.particles = [];
    this.tracers = [];
    this.rings = [];
    this.numbers = [];
    this.matCache = new Map();
    this.numLayer = document.getElementById('numbers');
    // A fixed pool of lights: adding/removing lights makes three.js recompile shaders.
    this.lightPool = [];
    for (let i = 0; i < 4; i++) {
      const l = new THREE.PointLight(0xffffff, 0, 8);
      this.scene.add(l);
      this.lightPool.push({ l, life: 0, max: 1, i: 0 });
    }
  }

  mat(color) {
    if (!this.matCache.has(color)) this.matCache.set(color, new THREE.MeshBasicMaterial({ color }));
    return this.matCache.get(color);
  }

  burst(pos, color, count = 8, { speed = 5, size = 0.12, life = 0.7, gravity = 18 } = {}) {
    for (let i = 0; i < count; i++) {
      if (this.particles.length > 400) this.remove(this.particles.shift());
      const m = new THREE.Mesh(cube, this.mat(color));
      const s = size * (0.6 + Math.random() * 0.8);
      m.scale.setScalar(s);
      m.position.copy(pos);
      this.scene.add(m);
      const v = new THREE.Vector3(Math.random() - 0.5, Math.random() * 0.8 + 0.2, Math.random() - 0.5)
        .normalize().multiplyScalar(speed * (0.4 + Math.random()));
      this.particles.push({ m, v, life, max: life, gravity, s });
    }
  }

  remove(p) { this.scene.remove(p.m); }

  tracer(from, to, color = 0xfff2a8, width = 0.025, life = 0.07) {
    const len = from.distanceTo(to);
    const m = new THREE.Mesh(cube, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.9 }));
    m.scale.set(width, width, len);
    m.position.copy(from).lerp(to, 0.5);
    m.lookAt(to);
    this.scene.add(m);
    this.tracers.push({ m, life, max: life });
  }

  flash(pos, color = 0xffc46b, intensity = 6, life = 0.06, distance = 8) {
    let slot = this.lightPool[0];
    for (const s of this.lightPool) if (s.life < slot.life) slot = s;
    slot.l.color.set(color);
    slot.l.distance = distance;
    slot.l.position.copy(pos);
    slot.life = slot.max = life;
    slot.i = intensity;
  }

  ring(pos, radius, color) {
    const m = new THREE.Mesh(
      new THREE.RingGeometry(0.8, 1, 32),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.8, side: THREE.DoubleSide }),
    );
    m.rotation.x = -Math.PI / 2;
    m.position.set(pos.x, pos.y + 0.1, pos.z);
    this.scene.add(m);
    this.rings.push({ m, life: 0.45, max: 0.45, radius });
  }

  explosion(pos, radius) {
    this.flash(pos, 0xff9a3c, 30, 0.25, radius * 4);
    this.burst(pos, 0xffb13b, 18, { speed: radius * 3, size: 0.35, life: 0.7, gravity: 4 });
    this.burst(pos, 0xff4d2e, 12, { speed: radius * 2, size: 0.3, life: 0.6, gravity: 4 });
    this.burst(pos, 0x444444, 10, { speed: radius * 1.5, size: 0.45, life: 1.1, gravity: -2 });
    this.ring(pos.clone().setY(Math.max(0, pos.y - 0.5)), radius, 0xffa040);
  }

  damageNumber(pos, amount, { crit = false, color } = {}) {
    const el = document.createElement('div');
    el.className = 'dmg' + (crit ? ' crit' : '');
    el.textContent = Math.round(amount);
    if (color) el.style.color = color;
    this.numLayer.appendChild(el);
    this.numbers.push({
      el, pos: pos.clone().add(new THREE.Vector3((Math.random() - 0.5) * 0.4, 0, (Math.random() - 0.5) * 0.4)),
      life: 0.8, max: 0.8,
    });
    if (this.numbers.length > 40) { const n = this.numbers.shift(); n.el.remove(); }
  }

  clear() {
    for (const p of this.particles) this.remove(p);
    for (const t of this.tracers) this.scene.remove(t.m);
    for (const r of this.rings) this.scene.remove(r.m);
    for (const s of this.lightPool) { s.life = 0; s.l.intensity = 0; }
    for (const n of this.numbers) n.el.remove();
    this.particles = []; this.tracers = []; this.rings = []; this.numbers = [];
  }

  update(dt, camera) {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.life -= dt;
      p.v.y -= p.gravity * dt;
      p.m.position.addScaledVector(p.v, dt);
      if (p.m.position.y < p.s / 2) { p.m.position.y = p.s / 2; p.v.multiplyScalar(0.5); p.v.y *= -0.3; }
      p.m.scale.setScalar(p.s * Math.max(0.01, p.life / p.max));
      if (p.life <= 0) { this.remove(p); this.particles.splice(i, 1); }
    }
    for (let i = this.tracers.length - 1; i >= 0; i--) {
      const t = this.tracers[i];
      t.life -= dt;
      t.m.material.opacity = Math.max(0, t.life / t.max);
      if (t.life <= 0) { this.scene.remove(t.m); t.m.material.dispose(); this.tracers.splice(i, 1); }
    }
    for (let i = this.rings.length - 1; i >= 0; i--) {
      const r = this.rings[i];
      r.life -= dt;
      const k = 1 - r.life / r.max;
      r.m.scale.setScalar(0.5 + k * r.radius);
      r.m.material.opacity = 0.8 * (1 - k);
      if (r.life <= 0) { this.scene.remove(r.m); r.m.geometry.dispose(); r.m.material.dispose(); this.rings.splice(i, 1); }
    }
    for (const s of this.lightPool) {
      s.life = Math.max(0, s.life - dt);
      s.l.intensity = s.i * (s.life / s.max);
    }
    const w = window.innerWidth, h = window.innerHeight;
    const v = new THREE.Vector3();
    for (let i = this.numbers.length - 1; i >= 0; i--) {
      const n = this.numbers[i];
      n.life -= dt;
      n.pos.y += dt * 1.4;
      v.copy(n.pos).project(camera);
      if (v.z > 1 || n.life <= 0) {
        if (n.life <= 0) { n.el.remove(); this.numbers.splice(i, 1); continue; }
        n.el.style.display = 'none';
        continue;
      }
      n.el.style.display = '';
      n.el.style.transform = `translate(${(v.x * 0.5 + 0.5) * w}px, ${(-v.y * 0.5 + 0.5) * h}px) translate(-50%, -50%)`;
      n.el.style.opacity = Math.min(1, n.life / n.max * 2);
    }
  }
}
