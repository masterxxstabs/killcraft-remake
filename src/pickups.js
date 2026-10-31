import * as THREE from 'three';

const geo = new THREE.BoxGeometry(1, 1, 1);
const coinMat = new THREE.MeshLambertMaterial({ color: 0xf2c230, emissive: 0x5a4000 });
const healMat = new THREE.MeshLambertMaterial({ color: 0xff3355, emissive: 0x550011 });

// Coins and health cubes that enemies drop.
export class Pickups {
  constructor(game) {
    this.game = game;
    this.list = [];
  }

  drop(pos, kind, value) {
    const m = new THREE.Mesh(geo, kind === 'coin' ? coinMat : healMat);
    m.scale.setScalar(kind === 'coin' ? 0.22 + Math.min(0.2, value / 100) : 0.35);
    m.position.copy(pos).setY(pos.y + 0.8);
    m.castShadow = true;
    this.game.scene.add(m);
    const vel = new THREE.Vector3((Math.random() - 0.5) * 4, 4 + Math.random() * 2, (Math.random() - 0.5) * 4);
    this.list.push({ m, kind, value, vel, life: 30, t: Math.random() * 6 });
  }

  dropCoins(pos, total) {
    // split big amounts into a few coins
    const pieces = Math.min(6, Math.max(1, Math.round(total / 6)));
    let left = total;
    for (let i = 0; i < pieces; i++) {
      const v = i === pieces - 1 ? left : Math.round(total / pieces);
      left -= v;
      if (v > 0) this.drop(pos, 'coin', v);
    }
  }

  update(dt) {
    const g = this.game, pl = g.player;
    const target = pl.position.clone().setY(pl.position.y + 0.9);
    for (let i = this.list.length - 1; i >= 0; i--) {
      const p = this.list[i];
      p.life -= dt;
      p.t += dt;
      const d = p.m.position.distanceTo(target);
      // between waves, every coin flies to you
      const magnet = p.kind === 'coin' ? (g.phase === 'intermission' ? 999 : pl.magnet) : 2;
      if (d < magnet) {
        const pull = target.clone().sub(p.m.position).normalize().multiplyScalar(Math.max(14 * (1.2 - d / magnet), 10));
        p.vel.lerp(pull, Math.min(1, dt * 8));
      } else {
        p.vel.y -= 20 * dt;
        p.vel.x *= 1 - dt * 2;
        p.vel.z *= 1 - dt * 2;
      }
      p.m.position.addScaledVector(p.vel, dt);
      const floor = g.world.groundAt(p.m.position.x, p.m.position.z, 0.1, p.m.position.y) + 0.3;
      if (p.m.position.y < floor && d >= magnet) {
        p.m.position.y = floor;
        p.vel.y = Math.abs(p.vel.y) * 0.3;
      }
      p.m.rotation.y += dt * 3;
      p.m.rotation.x = Math.sin(p.t * 2) * 0.3;

      if (d < 0.9) {
        if (p.kind === 'coin') { g.addCoins(p.value); g.audio.coin(); }
        else { pl.heal(p.value); g.audio.heal(); }
        g.scene.remove(p.m);
        this.list.splice(i, 1);
        continue;
      }
      if (p.life <= 0) {
        g.scene.remove(p.m);
        this.list.splice(i, 1);
        continue;
      }
      p.m.visible = p.life > 4 || Math.floor(p.life * 6) % 2 === 0;
    }
  }

  clear() {
    for (const p of this.list) this.game.scene.remove(p.m);
    this.list = [];
  }
}
