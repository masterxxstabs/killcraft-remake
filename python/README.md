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

**Tip:** get the game with `git clone` instead of downloading a ZIP. Updates then install
with `git pull`, which is the most reliable way (see [Updates](#updates)).

### Controls

| Key | Action |
| --- | --- |
| WASD / arrow keys | move |
| Mouse | aim; left click to shoot (hold for automatic weapons) |
| Space / Shift | jump / sprint |
| 1–9 or mouse wheel | switch weapon |
| R | reload |
| Q | use your ability |
| B | shop (between waves) |
| N | start the next wave early |
| M | mute |
| F11 | fullscreen on/off |
| Esc | pause (mouse sensitivity and volume are here) |
| F8 / F9 | turn / roll a downloaded 3D gun model that's facing the wrong way |

Your best wave, best score and total kills are saved in a `.blockhold` folder in your
home folder.

## Weapons and upgrades

There are 14 weapons. Two are melee (Rusty Wrench, Fire Axe). Others have special effects:

| Weapon | Special |
| --- | --- |
| Six-Shooter | huge damage, 2.5x headshots |
| Buzz SMG / Nail Gun / Ranger Rifle | automatic |
| Scattercannon | 9 pellets per shot |
| Fire Axe | each swing hits up to 3 enemies |
| Torch | flamethrower cone that sets enemies on fire |
| Railspike | goes through every enemy in a line |
| Frostbite | freeze ray that slows enemies |
| Arc Caster | lightning jumps to 4 more enemies |
| Firework Launcher | explosive rockets |
| Shredder | minigun that spins up, but slows you down |

Between waves, the shop's **Weapons** tab lets you buy guns and upgrade each one separately:
damage, fire rate, magazine size and reload speed (melee weapons get reach instead). The
**Player** tab has the upgrades that affect everything: health, power, speed, regen, armor
and more.

## Real 3D gun models from Sketchfab

Every weapon has a textured block model. You can swap any of them for a real 3D model from
[Sketchfab](https://sketchfab.com/search?features=downloadable&q=tag%3Agun&sort_by=-likeCount&type=models).

1. Make a free Sketchfab account. Your **API token** is under Settings → Password & API.
2. Run the downloader and answer its questions:

   ```bash
   python tools/sketchfab_guns.py
   ```

   It lists the most-liked downloadable guns, you pick one, then pick which weapon it
   replaces. It saves the model to `models/<weapon id>/`.
3. Start the game and hold that weapon. If the model faces the wrong way, press **F8** to
   turn it or **F9** to roll it. Your fix is saved.

Other commands: `search <words>`, `get <model link> <weapon id>`, `list`, `remove <weapon id>`.
Run `python tools/sketchfab_guns.py --help` for details.

**Licences:** by default the tool only shows models you're allowed to share: CC0, CC-BY and
CC-BY-SA. CC-BY means you must credit the author. The tool writes `models/CREDITS.md` for
you, and the game shows the credits on the main menu. Use `--license any` to see everything,
but check each model's rules before sharing the game. Your API token is never saved inside
the game folder, so it can't end up on GitHub.

You can also drop your own `.glb`, `.gltf` or `.obj` file into `models/<weapon id>/`.

## Updates

On launch, the game checks GitHub for a newer version. If one exists, the main menu shows
**UPDATE NOW** and what's new. Click it and the game updates itself and restarts.

- If you got the game with `git clone`, it runs `git pull`.
- If you downloaded a ZIP, it downloads the new files and copies them over. Any file it
  replaces that you had changed is backed up first in `_backup/<old version>/`.

You can also update from the terminal with `python main.py --update`, or start without
checking using `python main.py --offline`.

**Publishing an update** (for you as the developer):

1. Change the number in `python/VERSION` (for example `1.1.0` → `1.2.0`).
2. Add a `## 1.2.0` section with bullet points at the top of `python/CHANGELOG.md`.
   Players see these bullet points.
3. Push to the repository's default branch on GitHub.

The repository and branch it checks are set at the top of `blockhold/updater.py`.

## Add your own stuff

Everything you'd want to change is in plain, commented Python files in `blockhold/data/`.
Edit them, save, and start the game again. No build step is needed.

| File | What's in it |
| --- | --- |
| `blockhold/data/weapons.py` | every weapon: stats, special effects, block model parts, and the per-weapon upgrades |
| `blockhold/data/enemies.py` | every enemy: health, speed, damage, size, colours, skin look, ranged attacks |
| `blockhold/data/waves.py` | enemies per wave, which types appear, boss timing, special wave modifiers |
| `blockhold/data/upgrades.py` | shop upgrades, prices, and what they do |
| `blockhold/data/abilities.py` | the Q abilities (each is a small Python function) |

For example, to add a new gun, copy one of the `dict(...)` entries in `weapons.py`, give it
a new `id` and `name`, and change the numbers. It appears in the shop automatically, with its
own upgrades. Its 3D look is a list of boxes, `(material, size, position)`. The comment at
the top of the file lists every material: steel, wood, rubber grip, brass, camo, glowing
energy and more.

To change how a zombie looks, edit its `colors` and `look` in `enemies.py`: hair colour,
shirt / tank top / vest / robe, blood, scar, mouth, and extra parts like shoulder pads or a
crown. Its skin is painted from those settings automatically.

**Your own sounds:** put `.wav` or `.ogg` files in the `sounds/` folder, named after the
effect (for example `shoot_pistol.wav`). `sounds/README.txt` lists every name.

**Your own block looks:** the pixel-art textures (blocks, gun materials and zombie skins)
are drawn in code in `blockhold/textures.py`. Change the colours there, or add a new tile.

### Code map

| File | What it does |
| --- | --- |
| `main.py` | starts the game |
| `blockhold/game.py` | main loop, input, waves, shop, saving |
| `blockhold/world.py` | builds the block arena; collisions and line-of-sight |
| `blockhold/player.py` | movement, jumping and health |
| `blockhold/weapons.py` | shooting, special effects, weapon upgrades and the gun you hold |
| `blockhold/custom_models.py` | loads downloaded 3D gun models and fits them in your hand |
| `blockhold/updater.py` | checks GitHub for updates and installs them |
| `tools/sketchfab_guns.py` | downloads gun models from Sketchfab |
| `blockhold/enemies.py` | enemy models, hit detection and AI |
| `blockhold/projectiles.py` | rockets and enemy spit |
| `blockhold/pickups.py` | coins and health drops |
| `blockhold/effects.py` | particles, tracers, explosions, damage numbers |
| `blockhold/sounds.py` | makes every sound effect with code on first launch |
| `blockhold/ui.py` | HUD, menus and shop |
| `blockhold/render.py` | the shader (fog) and block mesh helpers |
| `blockhold/textures.py` | pixel-art textures drawn with Pillow |
