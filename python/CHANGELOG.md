# Changelog

The auto-updater shows the bullet points under the newest version to players.
To publish an update: bump the number in VERSION, add a section here, push to GitHub.

## 1.15.0
- Backpack (press I): a grid inventory where every item takes up space. Drag to move, R to turn, drop outside to leave it on the ground
- Ore, coal, stone, wood, crystal and ingots are now items in your backpack (the resource counter is gone)
- New resource: coal, from dark coal rocks
- Furnace: craft it from stone and coal, place it, and smelt ore into ingots (2 ore + 1 coal each). It keeps working while you fight
- Workbenches now use ingots instead of ore
- Armor: craft helmets and vests and wear them from the backpack. They take damage off and wear out as they protect you
- Loot crates can now hold coal and ingots

## 1.14.0
- UI styles that reshape every screen: Flat, Rounded, Soft (pill buttons), Tactical (cut corners and a typewriter font), Glass (see-through panels), Minimal (no outlines) and Chunky
- Pick a style under Settings; it mixes with any colour theme
- Each style button is drawn in its own shape so you can see what you're picking

## 1.13.0
- UI themes: Classic, Midnight, Military, Neon, Blood Moon, Arctic, Terminal and Sunset recolour every screen (Settings)
- Customize the HUD (Settings or the pause screen): drag any part anywhere on the screen, or switch it off
- Pick your own HUD colours: panels, accent, health bar and crosshair, plus panel see-through
- Button text now always stays readable, whatever the colours

## 1.12.2
- The walls around the edge of every map are now 8 m tall, so you can't climb out by stacking barricades or standing on buildings
- Nobody can leave the map any more, even maps without walls: players and zombies always stay inside the edge

## 1.12.1
- Fixed misaligned parts on several map assets: sandbags and the sandbag wall (rows now sit on each other), supply pallet, radar dish, camo net, burning barrel, cave lantern, coffin, gravestone, armored jeep, dumpster
- The guard tower ladder has rungs now

## 1.12.0
- Caves in the map editor: pick the depth, width, rock height and side tunnels, then click to dig one
- Caves have a rock roof you walk under, chambers with ore and a loot crate, lanterns, and a zombie grave at the end
- Loot crates: smash them or shoot them open for random crafting resources (in the editor's Mining tab, and on random arenas)
- Drop the gun you're holding with X, and pick it up again with E (it keeps its ammo, upgrades and attachments)
- 15 more military assets: army truck, armored jeep, tank wreck, guard tower, army tent, checkpoint, sandbag wall, hesco barrier, field gun, radar dish, helipad and more
- 17 more town assets: abandoned cars, police car, ambulance, street and traffic lights, corner shop, apartment block, gas station, chain-link fence and more
- Random arenas can now have a military camp or an abandoned street to find

## 1.11.0
- Huge maps: from 24 x 24 m up to 512 x 512 m
- Pick the random arena's size on the MAPS tab: Small, Normal, Large, Huge or Giant
- Big random arenas have more trees, ruins, tracks, workbenches and ore, plus farmhouses, camps and watchtowers to find
- On big maps zombies climb out of the ground around you instead of walking in from the far edges
- Far-away parts of the map are hidden in the fog to keep big maps running well
- Map editor: NEW lets you choose the size, walls, and empty ground or a random arena to start from
- Map editor: SIZE makes a map bigger or smaller
- Map editor: bigger brushes (up to 15 x 15) and you can zoom out further on big maps
- 47 new map assets in new Town, Military, Farm and Graveyard tabs: vehicles, shipping containers, barns, a church, crypts and more
- Some of them light up at night: phone booths, vending machines, floodlights, radio masts and grave lanterns

## 1.10.0
- Barricades, like the original game: craft them at a workbench (they can't be bought) and press G to build
- Spike barricades hurt zombies, plank barricades you can vault over, and tall palisade walls
- Sentry turret: a minigun on a tripod that shoots zombies by itself (hold E to refill its ammo)
- Landmines that blow up under zombies
- Zombies walk around your barricades, or smash through them if you've walled yourself in
- Hold E to repair a damaged barricade with wood
- New resource: wood, from log piles (the Axe chops fastest)
- The Village and Forest Camp maps now have log piles

## 1.9.1
- If your graphics driver can't run the game, it now tells you what to do instead of showing a black screen
- New --software-gl option for computers without a working graphics driver
- Logs for troubleshooting in your .blockhold folder (log.txt and panda.log)
- The Windows build is now play-tested automatically before every release

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
