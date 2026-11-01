# Changelog

The auto-updater shows the bullet points under the newest version to players.
To publish an update: bump the number in VERSION, add a section here, push to GitHub.

## 1.9.0
- BLOCKHOLD is now a real Windows game: download the installer from the GitHub Releases page, no Python needed
- Installs without admin rights, adds Start menu and desktop shortcuts, and has an uninstaller
- The installed game updates itself from GitHub Releases
- Portable Windows zip and a Linux build too
- Your maps, sounds and caches go in your .blockhold folder when the game is installed
- New game icon

## 1.8.0
- First-person arms like the original: blocky hands on the grip (and under the barrel for two-handed guns) with dark sleeves
- Guns resized and moved up so you can see the whole weapon
- Aiming down the sights now lines the sights (or red dot / holo) up with the crosshair
- Smaller, cleaner ammo counter that no longer covers your gun
- Fixed two memory leaks that made long games slower and slower (tested over 100 waves)
- Zombies now find their way around walls and through doors instead of getting stuck
- A zombie that gets stuck anyway digs down and climbs out near you, so a wave can never hang

## 1.7.0
- New look inspired by the original game: a dark, foggy dusk with a torch lighting up the ground around you
- Real lights: muzzle flashes, explosions, rockets, campfires, lamp posts, workbench lanterns, crystals and power-ups light up their surroundings
- A cloudy sky with stars and dark mountains on the horizon
- Detailed grass, soft-edged reddish dirt tracks, and mossy cobblestone walls
- Random arenas get winding dirt tracks, campfires and lamp posts
- Settings: choose the atmosphere (Dusk, Night or the old bright Day look)

## 1.6.0
- Mining! Ore nodes (stone, iron, copper, crystal) spawn around the map. Hit them with a melee weapon
- New Pickaxe: mines 2.5x faster
- Crafting: press E at a workbench to craft any gun from ore instead of buying it, plus bandages, medkits and armor plating
- Workbenches work during waves too, so watch your back
- Map editor: new Mining tab with workbenches and ore spawns, so you can build your own mine
- The Village and Forest Camp maps now have a workbench and a quarry

## 1.5.0
- Movement: crouch (C / Ctrl), sprint-slide, climb up ledges, vault over low cover
- All-new weapon sounds: layered gunshots per gun type, reload steps, shell casings, footsteps
- Detailed semi-realistic gun models for 19 guns (the world stays blocky)
- Weapon customization: optics, suppressors, compensators, foregrips, lasers, extended mags
- 9 camos to unlock, from Woodland to Gold
- Hire survivors in the new ALLIES shop tab; revive them with E when they go down
- Power-ups drop from zombies: Bonebreaker (one-hit kills), Gold Rush (double coins), Overdrive (bottomless mags) and Shock Blast
- With allies alive you go down instead of dying, and the nearest ally runs over to revive you
- Hold Tab for the scoreboard
- A secret is hidden on every map... listen for whispers
- Groundwork for co-op multiplayer (see MULTIPLAYER.md)

## 1.4.0
- Map editor! Build your own maps from the new MAPS tab
- 38 low-poly assets: trees, shrubs, houses, cabins, ruins, towers, fences, props and more
- Paint paths (dirt, gravel, cobblestone, road, sand, wood floor) and block walls
- Zombie graves: zombies climb out of them on your maps
- Two example maps: Village and Forest Camp
- Play-test a map straight from the editor

## 1.3.0
- Brand-new flat-design menus, shop, pause and game-over screens
- Shop shows weapon stats as bars, with upgrade buttons right next to them
- Milestones to work towards on the main menu
- New settings: field of view, sound on/off, check for updates on start
- Cleaner HUD with new icons

## 1.2.0
- 12 real guns: M1911, Glock 17, Desert Eagle, Uzi, MP5, AR-15, AK-47, AS Val, SCAR-H, Remington 870, Barrett M82, M249 SAW
- Right-click to aim; the Barrett and Railspike have a sniper scope
- Shop sorted into weapon categories
- Recommended 3D model pack: python tools/sketchfab_guns.py pack
- Downloaded models now point the right way automatically

## 1.1.0
- 9 new weapons: Six-Shooter, Buzz SMG, Fire Axe, Ranger Rifle, Torch, Frostbite, Arc Caster, Shredder and more
- Fire, freeze and chain-lightning effects
- Upgrade every weapon: damage, fire rate, magazine, reload
- Detailed textured guns and painted zombie skins
- Download real 3D gun models from Sketchfab (tools/sketchfab_guns.py)
- Auto-updates from GitHub

## 1.0.0
- First Python version of BLOCKHOLD
