import * as THREE from 'three';
import { makeMaterials, rng } from './textures.js';

// The arena is a grid of 1x1 block columns. `heights` stores how tall the
// solid column is at each cell (0 = open ground).
export class World {
  constructor(scene, seed = Date.now()) {
    this.scene = scene;
    this.half = 34;               // arena goes from -half .. +half
    this.n = this.half * 2;
    this.heights = new Uint8Array(this.n * this.n);
    this.blocks = new Map();      // material key -> [x, y, z][]
    this.mats = makeMaterials();
    this.r = rng(seed);
    this.group = new THREE.Group();
    scene.add(this.group);
    this.build();
  }

  idx(ix, iz) { return iz * this.n + ix; }

  cellHeight(ix, iz) {
    if (ix < 0 || iz < 0 || ix >= this.n || iz >= this.n) return 99;
    return this.heights[this.idx(ix, iz)];
  }

  heightAt(x, z) {
    return this.cellHeight(Math.floor(x) + this.half, Math.floor(z) + this.half);
  }

  place(mat, ix, y, iz, solid = true) {
    if (!this.blocks.has(mat)) this.blocks.set(mat, []);
    this.blocks.get(mat).push([ix - this.half + 0.5, y + 0.5, iz - this.half + 0.5]);
    if (solid && ix >= 0 && iz >= 0 && ix < this.n && iz < this.n) {
      const i = this.idx(ix, iz);
      this.heights[i] = Math.max(this.heights[i], y + 1);
    }
  }

  column(mat, ix, iz, h, topMat = mat) {
    for (let y = 0; y < h; y++) this.place(y === h - 1 ? topMat : mat, ix, y, iz);
  }

  free(ix, iz, pad = 0) {
    for (let dx = -pad; dx <= pad; dx++)
      for (let dz = -pad; dz <= pad; dz++) {
        const x = ix + dx, z = iz + dz;
        if (x < 1 || z < 1 || x >= this.n - 1 || z >= this.n - 1) return false;
        if (this.heights[this.idx(x, z)] > 0) return false;
      }
    // keep the centre clear for the player spawn
    const cx = ix - this.half, cz = iz - this.half;
    return cx * cx + cz * cz > 30;
  }

  build() {
    const n = this.n, r = this.r;

    // Ground
    const groundTex = this.mats.textures.grassTop.clone();
    groundTex.needsUpdate = true;
    groundTex.repeat.set(n, n);
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(n + 60, n + 60),
      new THREE.MeshLambertMaterial({ map: groundTex }),
    );
    groundTex.repeat.set(n + 60, n + 60);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.group.add(ground);

    // Outer wall: stone with a brick trim
    for (let i = 0; i < n; i++) {
      for (const [x, z] of [[i, 0], [i, n - 1], [0, i], [n - 1, i]]) {
        this.column('stone', x, z, 3, 'brick');
      }
    }

    // Trees
    for (let t = 0; t < 22; t++) {
      const ix = 2 + Math.floor(r() * (n - 4)), iz = 2 + Math.floor(r() * (n - 4));
      if (!this.free(ix, iz, 2)) continue;
      const h = 3 + Math.floor(r() * 3);
      this.column('log', ix, iz, h);
      for (let y = h - 1; y <= h + 1; y++) {
        const rad = y === h + 1 ? 1 : 2;
        for (let dx = -rad; dx <= rad; dx++)
          for (let dz = -rad; dz <= rad; dz++) {
            if ((dx || dz) || y >= h) {
              if (Math.abs(dx) === rad && Math.abs(dz) === rad && r() < 0.6) continue;
              this.place('leaves', ix + dx, y, iz + dz, false);
            }
          }
      }
    }

    // Crate piles (good for jumping on)
    for (let t = 0; t < 26; t++) {
      const ix = 2 + Math.floor(r() * (n - 4)), iz = 2 + Math.floor(r() * (n - 4));
      if (!this.free(ix, iz, 1)) continue;
      const w = 1 + Math.floor(r() * 2), d = 1 + Math.floor(r() * 2);
      for (let dx = 0; dx < w; dx++)
        for (let dz = 0; dz < d; dz++) {
          const h = r() < 0.3 ? 2 : 1;
          this.column('crate', ix + dx, iz + dz, h);
        }
    }

    // Ruined walls
    for (let t = 0; t < 10; t++) {
      const ix = 4 + Math.floor(r() * (n - 8)), iz = 4 + Math.floor(r() * (n - 8));
      const horiz = r() < 0.5, len = 4 + Math.floor(r() * 6);
      let ok = true;
      for (let k = 0; k < len; k++) if (!this.free(horiz ? ix + k : ix, horiz ? iz : iz + k, 1)) ok = false;
      if (!ok) continue;
      for (let k = 0; k < len; k++) {
        const h = 1 + Math.floor(r() * 3);
        this.column(r() < 0.3 ? 'planks' : 'brick', horiz ? ix + k : ix, horiz ? iz : iz + k, h);
      }
    }

    // Stone pillars
    for (let t = 0; t < 12; t++) {
      const ix = 3 + Math.floor(r() * (n - 6)), iz = 3 + Math.floor(r() * (n - 6));
      if (!this.free(ix, iz, 1)) continue;
      this.column('stone', ix, iz, 3 + Math.floor(r() * 3), 'obsidian');
    }

    // Build one InstancedMesh per material
    const geo = new THREE.BoxGeometry(1, 1, 1);
    const m = new THREE.Matrix4();
    for (const [key, list] of this.blocks) {
      const mesh = new THREE.InstancedMesh(geo, this.mats[key], list.length);
      list.forEach(([x, y, z], i) => { m.makeTranslation(x, y, z); mesh.setMatrixAt(i, m); });
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      this.group.add(mesh);
    }
  }

  // Highest floor under a circle that is at or below `feetY`.
  groundAt(x, z, radius, feetY) {
    let g = 0;
    this.forCells(x, z, radius, (h) => { if (h <= feetY + 0.05 && h > g) g = h; });
    return g;
  }

  blocked(x, z, radius, feetY) {
    let b = false;
    this.forCells(x, z, radius, (h) => { if (h > feetY + 0.05) b = true; });
    return b;
  }

  forCells(x, z, radius, fn) {
    const x0 = Math.floor(x - radius), x1 = Math.floor(x + radius);
    const z0 = Math.floor(z - radius), z1 = Math.floor(z + radius);
    for (let cx = x0; cx <= x1; cx++)
      for (let cz = z0; cz <= z1; cz++) {
        const h = this.cellHeight(cx + this.half, cz + this.half);
        if (!h) continue;
        const px = Math.max(cx, Math.min(x, cx + 1)), pz = Math.max(cz, Math.min(z, cz + 1));
        const dx = x - px, dz = z - pz;
        if (dx * dx + dz * dz < radius * radius) fn(h, cx, cz);
      }
  }

  // Push a circle out of any block column taller than feetY. Mutates pos.
  collide(pos, radius) {
    for (let iter = 0; iter < 3; iter++) {
      let moved = false;
      const x0 = Math.floor(pos.x - radius), x1 = Math.floor(pos.x + radius);
      const z0 = Math.floor(pos.z - radius), z1 = Math.floor(pos.z + radius);
      for (let cx = x0; cx <= x1; cx++)
        for (let cz = z0; cz <= z1; cz++) {
          const h = this.cellHeight(cx + this.half, cz + this.half);
          if (h <= pos.y + 0.05) continue;
          const px = Math.max(cx, Math.min(pos.x, cx + 1));
          const pz = Math.max(cz, Math.min(pos.z, cz + 1));
          let dx = pos.x - px, dz = pos.z - pz;
          const d2 = dx * dx + dz * dz;
          if (d2 >= radius * radius) continue;
          if (d2 < 1e-8) {
            // centre is inside the block: push out along the shortest axis
            const l = pos.x - cx, rr = cx + 1 - pos.x, b = pos.z - cz, t = cz + 1 - pos.z;
            const mn = Math.min(l, rr, b, t);
            if (mn === l) pos.x = cx - radius; else if (mn === rr) pos.x = cx + 1 + radius;
            else if (mn === b) pos.z = cz - radius; else pos.z = cz + 1 + radius;
          } else {
            const d = Math.sqrt(d2), push = radius - d;
            pos.x += (dx / d) * push;
            pos.z += (dz / d) * push;
          }
          moved = true;
        }
      if (!moved) break;
    }
  }

  // Distance along a ray until it hits a block or the ground (voxel DDA).
  raycast(o, dir, maxDist) {
    let tGround = dir.y < -1e-6 ? -o.y / dir.y : Infinity;
    const limit = Math.min(maxDist, tGround);
    let ix = Math.floor(o.x), iz = Math.floor(o.z);
    const stepX = dir.x > 0 ? 1 : -1, stepZ = dir.z > 0 ? 1 : -1;
    const tdx = Math.abs(dir.x) > 1e-9 ? Math.abs(1 / dir.x) : Infinity;
    const tdz = Math.abs(dir.z) > 1e-9 ? Math.abs(1 / dir.z) : Infinity;
    let tmx = Math.abs(dir.x) > 1e-9 ? (dir.x > 0 ? ix + 1 - o.x : o.x - ix) * tdx : Infinity;
    let tmz = Math.abs(dir.z) > 1e-9 ? (dir.z > 0 ? iz + 1 - o.z : o.z - iz) * tdz : Infinity;
    let t = 0;
    while (t < limit) {
      const h = this.cellHeight(ix + this.half, iz + this.half);
      const tNext = Math.min(tmx, tmz, limit);
      if (h > 0) {
        const y0 = o.y + dir.y * t, y1 = o.y + dir.y * tNext;
        if (y0 < h) return t;
        if (y1 < h) return t + (h - y0) / dir.y;
      }
      if (tNext >= limit) break;
      if (tmx < tmz) { t = tmx; tmx += tdx; ix += stepX; }
      else { t = tmz; tmz += tdz; iz += stepZ; }
    }
    return limit;
  }

  hasLineOfSight(a, b) {
    const d = b.clone().sub(a);
    const len = d.length();
    return this.raycast(a, d.divideScalar(len), len) >= len - 0.05;
  }

  randomSpawnPoint(awayFrom, minDist = 16) {
    for (let tries = 0; tries < 60; tries++) {
      // spawn near the edges, like they climbed over the wall
      const edge = Math.floor(Math.random() * 4);
      const along = (Math.random() * 2 - 1) * (this.half - 3);
      const inset = this.half - 2 - Math.random() * 4;
      const x = edge === 0 ? along : edge === 1 ? along : edge === 2 ? -inset : inset;
      const z = edge === 0 ? -inset : edge === 1 ? inset : along;
      if (this.heightAt(x, z) > 0 || this.blocked(x, z, 0.8, 0)) continue;
      if (Math.hypot(x - awayFrom.x, z - awayFrom.z) < minDist) continue;
      return new THREE.Vector3(x, 0, z);
    }
    return new THREE.Vector3(this.half - 3, 0, this.half - 3);
  }
}
