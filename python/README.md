# BLOCKHOLD (Python version)

The same blocky first-person wave survival game, written in Python with the
[Ursina](https://www.ursinaengine.org/) game engine.

## Play

You need [Python 3.10 or newer](https://www.python.org/downloads/). On Windows, tick
**"Add Python to PATH"** when installing.

Open a terminal in this `python` folder, then install the engine (only needed once):

```bash
pip install -r requirements.txt
```

Then start the game:

```bash
python main.py
```

It opens fullscreen. Press **F11** to switch to a window.

### Controls

| Key | Action |
| --- | --- |
| WASD / arrow keys | move |
| Mouse | aim; left click to shoot (hold for automatic weapons) |
| Space / Shift | jump / sprint |
| 1–6 or mouse wheel | switch weapon |
| R | reload |
| Q | use your ability |
| B | shop (between waves) |
| N | start the next wave early |
| M | mute |
| F11 | fullscreen on/off |
| Esc | pause (mouse sensitivity and volume are here) |

Your best wave, best score and total kills are saved in a `.blockhold` folder in your
home folder.

## Add your own stuff

Everything you'd want to change is in plain, commented Python files in `blockhold/data/`.
Edit them, save, and start the game again. No build step is needed.

| File | What's in it |
| --- | --- |
| `blockhold/data/weapons.py` | every gun: damage, fire rate, magazine, spread, price, colours |
| `blockhold/data/enemies.py` | every enemy: health, speed, damage, size, colours, ranged attacks |
| `blockhold/data/waves.py` | enemies per wave, which types appear, boss timing, special wave modifiers |
| `blockhold/data/upgrades.py` | shop upgrades, prices, and what they do |
| `blockhold/data/abilities.py` | the Q abilities (each is a small Python function) |

For example, to add a new gun, copy one of the `dict(...)` entries in `weapons.py`, give it
a new `id` and `name`, and change the numbers. It appears in the shop automatically.

**Your own sounds:** put `.wav` or `.ogg` files in the `sounds/` folder, named after the
effect (for example `shoot_pistol.wav`). `sounds/README.txt` lists every name.

**Your own block looks:** the pixel-art textures are drawn in code in
`blockhold/textures.py`. Change the colours there, or add a new tile.

### Code map

| File | What it does |
| --- | --- |
| `main.py` | starts the game |
| `blockhold/game.py` | main loop, input, waves, shop, saving |
| `blockhold/world.py` | builds the block arena; collisions and line-of-sight |
| `blockhold/player.py` | movement, jumping and health |
| `blockhold/weapons.py` | shooting, reloading and the gun you hold |
| `blockhold/enemies.py` | enemy models, hit detection and AI |
| `blockhold/projectiles.py` | rockets and enemy spit |
| `blockhold/pickups.py` | coins and health drops |
| `blockhold/effects.py` | particles, tracers, explosions, damage numbers |
| `blockhold/sounds.py` | makes every sound effect with code on first launch |
| `blockhold/ui.py` | HUD, menus and shop |
| `blockhold/render.py` | the shader (fog) and block mesh helpers |
| `blockhold/textures.py` | pixel-art textures drawn with Pillow |
