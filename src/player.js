import * as THREE from 'three';

export class Player {
  constructor(game) {
    this.game = game;
    this.camera = game.camera;
    this.position = new THREE.Vector3();
    this.vel = new THREE.Vector3();
    this.radius = 0.35;
    this.eyeHeight = 1.62;
    this.reset();
  }

  reset() {
    this.position.set(0, 0, 0);
    this.vel.set(0, 0, 0);
    this.yaw = 0;
    this.pitch = 0;
    this.recoil = 0;
    this.onGround = true;
    this.bob = 0;
    this.maxHealth = 100;
    this.health = 100;
    this.damageMult = 1;
    this.speedMult = 1;
    this.regen = 0;
    this.reloadMult = 1;
    this.fireRateMult = 1;
    this.armor = 0;
    this.magnet = 3;
    this.buffs = {};
    this.dead = false;
    this.abilityCd = 0;
  }

  eye() { return new THREE.Vector3(this.position.x, this.position.y + this.eyeHeight, this.position.z); }

  forward() { return new THREE.Vector3(0, 0, -1).applyQuaternion(this.camera.quaternion); }

  look(dx, dy, sens) {
    this.yaw -= dx * sens;
    this.pitch -= dy * sens;
    this.pitch = Math.max(-1.55, Math.min(1.55, this.pitch));
  }

  hurt(amount, from) {
    if (this.dead || this.game.godMode) return;
    amount *= 1 - this.armor;
    this.health -= amount;
    this.game.ui.hurt(amount / this.maxHealth, from);
    this.game.audio.hurt();
    this.game.shake(Math.min(0.25, amount / 60));
    if (this.health <= 0) {
      this.health = 0;
      this.dead = true;
      this.game.onPlayerDeath();
    }
  }

  heal(n) {
    this.health = Math.min(this.maxHealth, this.health + n);
    this.game.effects.damageNumber(this.eye().add(this.forward().multiplyScalar(1.5)), n, { color: '#5dff7a' });
  }

  get moveSpeed() {
    return 5.6 * this.speedMult * (this.buffs.adrenaline > 0 ? 1.5 : 1);
  }

  update(dt, keys) {
    const world = this.game.world;

    for (const k in this.buffs) this.buffs[k] = Math.max(0, this.buffs[k] - dt);
    if (this.abilityCd > 0) this.abilityCd -= dt;
    if (this.regen > 0 && this.health < this.maxHealth) this.health = Math.min(this.maxHealth, this.health + this.regen * dt);

    // input -> wish direction
    let fx = 0, fz = 0;
    if (keys.KeyW || keys.ArrowUp) fz -= 1;
    if (keys.KeyS || keys.ArrowDown) fz += 1;
    if (keys.KeyA || keys.ArrowLeft) fx -= 1;
    if (keys.KeyD || keys.ArrowRight) fx += 1;
    const len = Math.hypot(fx, fz);
    if (len) { fx /= len; fz /= len; }
    const sin = Math.sin(this.yaw), cos = Math.cos(this.yaw);
    const wx = fx * cos + fz * sin;
    const wz = -fx * sin + fz * cos;
    const sprint = keys.ShiftLeft || keys.ShiftRight ? 1.4 : 1;
    const speed = this.moveSpeed * sprint;

    const accel = this.onGround ? 14 : 4;
    const k = Math.min(1, accel * dt);
    this.vel.x += (wx * speed - this.vel.x) * k;
    this.vel.z += (wz * speed - this.vel.z) * k;

    if (keys.Space && this.onGround) {
      this.vel.y = 7.2;
      this.onGround = false;
    }
    this.vel.y -= 22 * dt;

    // move horizontally, then resolve against blocks
    this.position.x += this.vel.x * dt;
    this.position.z += this.vel.z * dt;
    world.collide(this.position, this.radius);

    // vertical
    this.position.y += this.vel.y * dt;
    const floor = world.groundAt(this.position.x, this.position.z, this.radius, this.position.y - this.vel.y * dt);
    if (this.position.y <= floor) {
      this.position.y = floor;
      this.vel.y = 0;
      this.onGround = true;
    } else {
      this.onGround = this.position.y - floor < 0.02;
    }

    // camera
    const moving = this.onGround && len > 0;
    this.bob += dt * (moving ? speed * 1.8 : 0);
    const bobY = moving ? Math.abs(Math.sin(this.bob)) * 0.06 : 0;
    this.recoil = Math.max(0, this.recoil - dt * 6 * Math.max(0.2, this.recoil));
    const s = this.game.shakeAmt;
    this.camera.position.set(
      this.position.x + (Math.random() - 0.5) * s * 0.3,
      this.position.y + this.eyeHeight + bobY + (Math.random() - 0.5) * s * 0.3,
      this.position.z + (Math.random() - 0.5) * s * 0.3,
    );
    this.camera.rotation.set(this.pitch + this.recoil, this.yaw, 0, 'YXZ');
    this.moving = moving;
  }
}
