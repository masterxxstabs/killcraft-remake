import * as THREE from 'three';

export function rng(seed) {
  let s = (seed >>> 0) || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

function shade(color, f) {
  const c = new THREE.Color(color);
  return `rgb(${Math.min(255, c.r * 255 * f) | 0},${Math.min(255, c.g * 255 * f) | 0},${Math.min(255, c.b * 255 * f) | 0})`;
}

// Makes a tiny noisy pixel-art texture. `draw` can paint extra details on top.
export function pixelTexture(base, { variance = 0.14, seed = 1, size = 16, draw } = {}) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const ctx = c.getContext('2d');
  const r = rng(seed);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      ctx.fillStyle = shade(base, 1 + (r() - 0.5) * 2 * variance);
      ctx.fillRect(x, y, 1, 1);
    }
  }
  if (draw) draw(ctx, r, size, shade);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter;
  t.minFilter = THREE.NearestFilter;
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

const lambert = (map) => new THREE.MeshLambertMaterial({ map });

export function makeMaterials() {
  const grassTop = pixelTexture('#5d9b3a', { seed: 3, variance: 0.18 });
  const dirt = pixelTexture('#7a5534', { seed: 5, variance: 0.2 });
  const grassSide = pixelTexture('#7a5534', {
    seed: 7, variance: 0.2,
    draw(ctx, r, s, sh) {
      for (let x = 0; x < s; x++) {
        const h = 3 + Math.floor(r() * 3);
        for (let y = 0; y < h; y++) {
          ctx.fillStyle = sh('#5d9b3a', 1 + (r() - 0.5) * 0.3);
          ctx.fillRect(x, y, 1, 1);
        }
      }
    },
  });
  const stone = pixelTexture('#7d7d80', {
    seed: 11, variance: 0.12,
    draw(ctx, r, s, sh) {
      for (let i = 0; i < 10; i++) {
        ctx.fillStyle = sh('#5a5a5e', 1);
        ctx.fillRect((r() * s) | 0, (r() * s) | 0, 2, 1);
      }
    },
  });
  const brick = pixelTexture('#8d4a3a', {
    seed: 13, variance: 0.1,
    draw(ctx, r, s, sh) {
      ctx.fillStyle = sh('#c9c0b0', 0.8);
      for (let y = 0; y < s; y += 4) {
        ctx.fillRect(0, y, s, 1);
        const off = (y / 4) % 2 ? 0 : 4;
        for (let x = off; x < s; x += 8) ctx.fillRect(x, y, 1, 4);
      }
    },
  });
  const planks = pixelTexture('#a8804a', {
    seed: 17, variance: 0.1,
    draw(ctx, r, s, sh) {
      ctx.fillStyle = sh('#6b4f2a', 1);
      for (let y = 3; y < s; y += 4) ctx.fillRect(0, y, s, 1);
    },
  });
  const crate = pixelTexture('#b08850', {
    seed: 19, variance: 0.1,
    draw(ctx, r, s, sh) {
      ctx.fillStyle = sh('#5e4322', 1);
      ctx.fillRect(0, 0, s, 2); ctx.fillRect(0, s - 2, s, 2);
      ctx.fillRect(0, 0, 2, s); ctx.fillRect(s - 2, 0, 2, s);
      for (let i = 0; i < s; i++) ctx.fillRect(i, i, 2, 1);
    },
  });
  const logSide = pixelTexture('#6b4a2b', {
    seed: 23, variance: 0.12,
    draw(ctx, r, s, sh) {
      ctx.fillStyle = sh('#4a321c', 1);
      for (let x = 1; x < s; x += 3) ctx.fillRect(x, 0, 1, s);
    },
  });
  const logTop = pixelTexture('#b38b5a', {
    seed: 29,
    draw(ctx, r, s, sh) {
      ctx.strokeStyle = sh('#7a5a34', 1);
      for (let rad = 2; rad < 8; rad += 2) ctx.strokeRect(8 - rad, 8 - rad, rad * 2, rad * 2);
    },
  });
  const leaves = pixelTexture('#3f7d2a', {
    seed: 31, variance: 0.3,
    draw(ctx, r, s, sh) {
      for (let i = 0; i < 20; i++) {
        ctx.fillStyle = sh('#2a5a1c', 1);
        ctx.fillRect((r() * s) | 0, (r() * s) | 0, 1, 1);
      }
    },
  });
  const obsidian = pixelTexture('#1d1528', { seed: 37, variance: 0.3 });

  const grassMat = [lambert(grassSide), lambert(grassSide), lambert(grassTop), lambert(dirt), lambert(grassSide), lambert(grassSide)];
  const logMat = [lambert(logSide), lambert(logSide), lambert(logTop), lambert(logTop), lambert(logSide), lambert(logSide)];
  const leafMat = new THREE.MeshLambertMaterial({ map: leaves });

  return {
    textures: { grassTop, dirt },
    grass: grassMat,
    dirt: lambert(dirt),
    stone: lambert(stone),
    brick: lambert(brick),
    planks: lambert(planks),
    crate: lambert(crate),
    log: logMat,
    leaves: leafMat,
    obsidian: lambert(obsidian),
  };
}

// Face texture for an enemy head (front face).
export function faceTexture(skin, eyes) {
  return pixelTexture(skin, {
    size: 8, variance: 0.08, seed: 41,
    draw(ctx, r, s, sh) {
      ctx.fillStyle = eyes;
      ctx.fillRect(1, 3, 2, 1);
      ctx.fillRect(5, 3, 2, 1);
      ctx.fillStyle = sh(skin, 0.45);
      ctx.fillRect(2, 6, 4, 1);
    },
  });
}
