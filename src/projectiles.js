import * as THREE from 'three';

const geo = new THREE.BoxGeometry(1, 1, 1);

// Rockets fired by the player and goo spat by enemies.
export class Projectiles {
  constructor(game) {
    this.game = game;
    this.list = [];
  }

  spawnRocket(pos, vel, { radius, damage, knockback }) {
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: 0xff3b3b }));
    m.scale.set(0.15, 0.15, 0.45);
    m.position.copy(pos);
    this.game.scene.add(m);
    this.list.push({ m, vel, owner: 'player', radius, damage, knockback, life: 4, gravity: 3, trail: 0xffc04a });
  }

  spawnEnemy(pos, vel, damage, color) {
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color }));
    m.scale.setScalar(0.3);
    m.position.copy(pos);
    this.game.scene.add(m);
    this.list.push({ m, vel, owner: 'enemy', damage, life: 4, gravity: 2, trail: new THREE.Color(color).getHex() });
  }

  remove(i) {
    const p = this.list[i];
    this.game.scene.remove(p.m);
    p.m.material.dispose();
    this.list.splice(i, 1);
  }

  explode(pos, p) {
    const g = this.game;
    g.effects.explosion(pos, p.radius);
    g.audio.boom();
    g.shake(0.35);
    for (const e of g.enemies.list) {
      if (e.dead) continue;
      const d = e.chestPos().distanceTo(pos);
      if (d < p.radius + e.radius) {
        const k = 1 - Math.max(0, d - e.radius) / p.radius;
        const dir = e.position.clone().sub(pos).setY(0).normalize().multiplyScalar(p.knockback * k);
        e.hurt(p.damage * (0.35 + 0.65 * k) * g.player.damageMult, false, dir);
      }
    }
  }

  update(dt) {
    const g = this.game;
    for (let i = this.list.length - 1; i >= 0; i--) {
      const p = this.list[i];
      p.life -= dt;
      p.vel.y -= p.gravity * dt;
      const step = p.vel.clone().multiplyScalar(dt);
      const len = step.length();
      const dir = step.clone().divideScalar(len || 1);
      const from = p.m.position.clone();
      const wallT = g.world.raycast(from, dir, len);

      if (p.owner === 'player') {
        const hits = g.enemies.raycast(from, dir, len + 0.3);
        if (hits.length && hits[0].dist <= wallT) {
          this.explode(hits[0].point, p);
          this.remove(i);
          continue;
        }
      } else {
        const eye = g.player.eye();
        const body = new THREE.Vector3(eye.x, eye.y - 0.6, eye.z);
        const closest = new THREE.Line3(from, from.clone().add(step)).closestPointToPoint(body, true, new THREE.Vector3());
        const dx = closest.x - body.x, dz = closest.z - body.z, dy = closest.y - body.y;
        if (dx * dx + dz * dz < 0.5 * 0.5 && Math.abs(dy) < 1) {
          g.player.hurt(p.damage, from);
          g.effects.burst(closest, p.trail, 8, { speed: 3 });
          this.remove(i);
          continue;
        }
      }

      if (wallT < len || p.life <= 0) {
        const at = from.addScaledVector(dir, wallT);
        if (p.owner === 'player') this.explode(at, p);
        else g.effects.burst(at, p.trail, 6, { speed: 3 });
        this.remove(i);
        continue;
      }

      p.m.position.add(step);
      p.m.lookAt(p.m.position.clone().add(p.vel));
      if (p.owner === 'enemy') p.m.rotation.z += dt * 10;
      if (Math.random() < 0.7) g.effects.burst(p.m.position, p.trail, 1, { speed: 0.5, size: 0.12, life: 0.35, gravity: 0 });
    }
  }

  clear() {
    while (this.list.length) this.remove(this.list.length - 1);
  }
}
