# BLOCKHOLD

A blocky first-person wave survival game that runs in your browser. Hold the arena, survive
the waves, spend your coins.

## Play

**Easiest:** download this repo (green **Code** button → **Download ZIP**), unzip it, and
double-click `index.html`. That's it. It needs no install and no internet.

### Controls

| Key | Action |
| --- | --- |
| WASD | move |
| Mouse | aim; left click to shoot (hold for automatic weapons) |
| Space / Shift | jump / sprint |
| 1–6 or mouse wheel | switch weapon |
| R | reload |
| Q | use your ability |
| B | shop (between waves) |
| N | start the next wave early |
| M | mute |
| Esc | pause (mouse sensitivity and volume are here) |

### How it works

- Enemies climb out of the ground near the arena walls. Kill them all to clear the wave.
- They drop **coins** (and sometimes health). Coins left on the ground fly to you when the wave ends.
- Between waves you get 25 seconds to shop: new weapons, plus upgrades that stack.
- **Every 4th wave** has a special modifier: Blood Moon, The Fog, Swarm or Gold Rush.
- **Every 5th wave** brings a boss: *The Hollow King*.
- Your best wave, best score and total kills are saved in the browser.

## Add your own stuff

Everything you'd want to change is in plain, commented files in `src/data/`:

| File | What's in it |
| --- | --- |
| `src/data/weapons.js` | every gun: damage, fire rate, magazine, spread, price, colours |
| `src/data/enemies.js` | every enemy: health, speed, damage, size, colours, ranged attacks |
| `src/data/waves.js` | how many enemies per wave, which types, boss timing, special modifiers |
| `src/data/upgrades.js` | shop upgrades and their prices |
| `src/data/abilities.js` | the Q abilities |

For example, to add a new gun, copy one of the entries in `weapons.js`, give it a new `id`
and `name`, and change the numbers. It shows up in the shop automatically.

After editing, rebuild the game (needs [Node.js](https://nodejs.org) installed):

```bash
npm install
npm run build
```

Then refresh `index.html`. While you're editing, `npm run watch` rebuilds every time you save.

Cheat from the browser console (F12) while testing: `game.coins = 99999` or `game.godMode = true`.

### Code map

| File | What it does |
| --- | --- |
| `src/game.js` | main loop, waves, shop, saving |
| `src/world.js` | builds the block arena and handles collisions |
| `src/player.js` | movement, jumping and health |
| `src/weapons.js` | shooting, reloading and the gun you hold |
| `src/enemies.js` | enemy models and AI |
| `src/projectiles.js` | rockets and enemy spit |
| `src/pickups.js` | coins and health drops |
| `src/effects.js` | particles, explosions, damage numbers |
| `src/audio.js` | all sounds (made on the fly, no audio files) |
| `src/ui.js` | HUD, menus and shop |

Built with [three.js](https://threejs.org).
