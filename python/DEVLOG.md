# BLOCKHOLD devlog

What changed in each version, and why. The newest entry is first. Each entry starts with a line
`## version | date | title`; the text under it is shown on the DEVLOG tab of the main menu.
Lines starting with "- " become bullet points.

## 1.23.0 | 2026-11-05 | What you wear is what you carry
The second step towards the extraction mode. The old backpack was a big 10 by 7 grid that everybody had from the start, so you never had to choose what to take. Now your inventory is made of what you wear. You start with a T-shirt and jeans: four pockets and a couple of small grids, and that's it.

Every piece of clothing adds a grid of its own: a hoodie, a field jacket, cargo pants, a chest rig, and four backpacks from a small satchel up to a 6 by 6 military pack. Backpacks are real things. Take one off, or drop it on the ground, and everything inside goes with it. Pick it up again and it's all still there. That's what extraction needs: when you go down in a raid, your bag stays where you fell.

Everything weighs something now, guns included. Up to 25 kg you move at full speed. Past that you slow down, and past 40 kg you can't sprint. The total is in the corner of the inventory screen, and the HUD warns you when you're heavy.

Loot works like Rust now. Barrels break when you hit or shoot them and leave a sack of scrap parts: springs, pipes, gears, rope, cloth, tarp, sheet metal. Toolboxes, medical boxes, military crates and clothes racks open with E, and you drag what you want into your clothes. An emptied container fills up again a few minutes later, but never while someone is close enough to see it happen.

Those parts are what you craft with. A gun needs springs, a pipe for the barrel and, for the bigger ones, an SMG or rifle body from a military crate, plus a few ingots from the furnace. Clothes and backpacks are sewn from cloth, rope and tarp, and bandages from cloth.

The editor has a new Loot tab with all of it, and random arenas get containers and barrels too.

Coming next: the extraction loop itself. Raids, extracting with what you found, a stash in the hideout, and a banker who keeps your items safe for every merchant down there.

## 1.22.0 | 2026-11-05 | Building towards extraction
This is the first step towards a much bigger goal: an open-world extraction mode, played with friends. We're building it in stages, and this update brings the map-making tools you need to set it up.

The editor has a new Zones tab. Level zones decide how tough the zombies are in each part of the map: a quiet field at level 1, a military base at level 15. Random encounter zones can throw a group of zombies at you when you walk in. Safe zones keep zombies out, and later they'll keep other players' bullets out too. Extraction points mark where you'll leave a raid with your loot. Every zone shows its size as a coloured ring, and placing one opens its settings.

Zombies have levels now. Each level adds health and damage, and gives more XP and coins. Aim at one to see its name, level and health.

Your character is persistent: level, XP and skills carry over from game to game. If you want to rebuild, RESET SKILLS on the skill screen gives every point back.

There's also a new Hideout tab with 24 underground tunnel pieces, for building the base you'll come home to between raids: tunnels, blast doors, a bank counter with a vault door, merchant stalls, bunks, lockers and lamps.

Coming next: Rust-style scrap loot from barrels and crates, clothing that decides how much you can carry, physical backpacks, and weight.

## 1.21.1 | 2026-11-04 | Welcome to the devlog
This tab is new. The changelog lists what changed in a few words; the devlog explains why. Every update from now on gets an entry here, and we've written up all the old ones too, back to the very first version, so you can see how the game got to where it is.

When there's an entry you haven't read, the tab says NEW.

Also in this update: the About tab now credits the 3D models that ship with the game (the Kenney blasters), not just the ones you download.

## 1.21.0 | 2026-11-04 | Six new zombies, fourteen new weapons
Waves were starting to feel samey: by wave 20 you'd seen everything. So this update is all about variety, with six new zombies that each ask you to play a little differently.

- The Crawler drags itself along the ground. It's low, so you have to aim down at it.
- The Bloater pops when it dies and leaves a toxic cloud. Kill it at range, never up close.
- The Leaper pounces from 4 to 11 metres away. A well-timed shove knocks it out of the air.
- The Screamer stops and shrieks, sending the horde into a frenzy and calling more out of the ground. Kill it first.
- The Riot Zombie's helmet and vest soak up body shots. Aim for the face.
- The Firefighter can't be burned and shrugs off half of any explosion.

On the weapons side there are four new melee weapons (bat, machete, sledgehammer, katana) and real-world guns like the P90, KRISS Vector, M14, AA-12 and Mosin-Nagant, plus a crossbow and an M79 grenade launcher.

The two Blasters are the first weapons that ship with downloaded 3D models: they come from Kenney's free Starter Kit FPS. The game can now carry its own models, so expect more of those.

## 1.20.0 | 2026-11-04 | Classes, levels and the shove
Two big ideas from Left 4 Dead and Project Zomboid.

The shove (F) pushes the zombies in front of you over. They go limp, lie there for a couple of seconds, then climb back up and keep coming. It's a panic button, not a kill button: it buys you room to reload or run. It tires you out, so you can't spam it.

Classes give each run a shape. The Soldier, Brawler, Scout, Medic and Engineer each have their own Q ability and passive bonus, and their own branch of the new skill tree (K). Kills, cleared waves and NPC jobs give XP, and every level is a skill point. Levels last for one run, like a Zomboid character: every game starts at level 1.

## 1.19.1 | 2026-11-03 | Making big hordes run smoothly
Late waves were getting slow. The profiler showed the real problem: the game engine (Ursina) checked every single object in the scene every frame (each zombie limb, coin, particle and label), just to find the dozen or so that needed updating. With 40 zombies on screen that alone cost about 10 milliseconds a frame.

The fix was to replace that loop with one that only visits the objects that need it. Zombies, animals and ragdolls are also built from plain engine nodes now, copied from one template per type, so they spawn and animate much faster.

We also found a memory leak: switching to or from a melee weapon left a copy of your arms behind every time. That's why long games got slower and slower. The game's own work per frame is now about a quarter of what it was with 80 zombies around.

## 1.19.0 | 2026-11-03 | Ragdolls and patching yourself up
Dead zombies used to tip over like planks. Now they're ragdolls: a little skeleton of 15 joints with physics, and the zombie's own body parts hung on it. They crumple, fold at the knees and slump over walls. The killing shot pushes them, so a headshot snaps the head back and a shotgun sends them flying.

Healing changed too. Bandages and medkits used to heal instantly, which made them a button you pressed when things got bad. Now they're items in your backpack that take a few seconds to use, during which you can't shoot. Healing is a decision: find cover first.

## 1.18.0 | 2026-11-03 | NPCs, animals and a bigger town
Maps felt empty between waves. Now you can place NPCs in the editor: traders, quest givers, and people who just want to talk. Each one gets an edit panel (inspired by the Custom NPCs Minecraft mod) for their looks, dialogue, trades and jobs.

Deer, pigs and chickens wander around their spawners, graze, and run from you and the zombies. Hunt them for meat, cook it in the furnace and eat it.

There's also a pile of new map pieces: a whole church set, privacy fences, playgrounds, parking lots, burnt-out and boarded-up buildings, and lots more plants.

## 1.17.0 | 2026-11-03 | Turn anything, any way
Map builders asked for more control than 90-degree turns. The new ROTATION panel turns things to any angle, and can tilt and roll them too: a car wreck on its side, a leaning sign, a fallen tree. Ctrl+click picks up something you already placed so you can turn or delete it later.

## 1.16.0 | 2026-11-03 | Three hands and a proper furnace
Carrying every gun at once made picking one meaningless. Now you hold three, like most survival games: a tool, a handgun and a rifle. Everything else waits in your backpack. Swapping is a choice you make between fights.

The furnace now works like Minecraft's, with slots for ore and fuel, a flame for the burn time and an arrow for progress. Coal burns longest.

## 1.15.0 | 2026-11-03 | The backpack update
Resources used to be numbers in a corner. Now they're things: everything you mine, chop or loot goes into a grid backpack (I) where every item takes up space, Tarkov-style. When it's full, it's full.

Workbenches now want ingots instead of raw ore, so the new furnace sits in the middle of the crafting loop. And there's armor: helmets and vests that take damage off and wear out as they protect you.

## 1.14.0 | 2026-11-03 | UI styles
Themes changed the colours; styles change the shapes. Rounded corners, pill buttons, a tactical look with cut corners and a typewriter font, see-through glass panels and more. Any style works with any theme.

## 1.13.0 | 2026-11-03 | Themes and your own HUD
Eight colour themes for every screen, from Midnight to Blood Moon. You can also customize the HUD now: drag each part wherever you like, switch parts off, and pick your own colours for panels, bars and the crosshair.

## 1.12.2 | 2026-11-03 | No climbing out
Players found they could stack barricades against the outer wall and step right off the map. The walls are now 8 metres tall, and there's a hard edge nobody can cross, zombies included.

## 1.12.1 | 2026-11-03 | Fixing wonky assets
A batch of the new map pieces had parts floating or sunk into each other: sandbag rows, the radar dish, a coffin lid and others. They're all lined up now, and the guard tower finally has ladder rungs.

## 1.12.0 | 2026-11-02 | Caves, crates and dropping guns
The map editor can dig caves now: choose the depth, width, rock height and side tunnels, then click. Every cave comes out different, with chambers, ore, lanterns and a zombie grave at the far end.

Loot crates give you something to smash for resources, and you can drop your gun with X to make room for a better one. Plus 32 more military and town pieces for the editor.

## 1.11.0 | 2026-11-02 | Huge maps
Maps can now be up to 512 by 512 metres. Big maps needed new tricks: zombies climb out of the ground near you instead of walking in from a kilometre away, and far parts of the map hide in the fog so the game keeps running smoothly. The editor got 47 new pieces in Town, Military, Farm and Graveyard tabs.

## 1.10.0 | 2026-11-02 | Barricades
Barricades come straight from the original game. You can only craft them, never buy them: spikes, planks to vault over, palisade walls, a sentry turret and landmines. Zombies path around them or smash through if you've walled yourself in completely. Wood comes from log piles, and an axe chops fastest.

## 1.9.1 | 2026-11-01 | When the graphics driver says no
Some computers showed a black screen. The game now checks the graphics driver on start and tells you what's wrong, with a software option for machines without a working driver and log files to help track problems down.

## 1.9.0 | 2026-11-01 | A real Windows game
BLOCKHOLD no longer needs Python installed. There's a proper installer (no admin rights needed), a portable zip and a Linux build, all published on GitHub Releases. The game updates itself from there.

## 1.8.0 | 2026-10-31 | Hands, sights and leaks
First-person arms like the original: blocky hands on the grip, and on the barrel for two-handed guns. Aiming lines your sights up with the crosshair properly now.

A 100-wave test run found two memory leaks and zombies getting stuck on walls. Zombies now path around walls and through doors, and any that still get stuck dig down and pop up near you.

## 1.7.0 | 2026-10-31 | Dusk
The world got its mood: a dark, foggy dusk with your torch lighting the ground. Muzzle flashes, explosions and lamps now cast real light. The bright old look is still in Settings if you prefer it.

## 1.6.0 | 2026-10-31 | Mining and crafting
Ore nodes to break with melee weapons, and workbenches to turn ore into guns instead of buying them. This is where the survival side of the game started.

## 1.5.0 | 2026-10-31 | Moving, sounding and looking better
Crouching, sliding, climbing ledges and vaulting cover. Every gun got its own layered sound and a detailed model, with attachments and camos to unlock. You can hire survivors to fight next to you now, and zombies drop power-ups. There's also a secret on every map. Listen for whispers.

## 1.4.0 | 2026-10-31 | The map editor
Build your own maps: trees, houses, ruins, fences, paths and walls, with zombie graves where they climb out. Two example maps ship with the game, Village and Forest Camp.

## 1.3.0 | 2026-10-31 | A cleaner look
A new flat-design look for every menu, the shop and the HUD, with milestones to chase on the main menu.

## 1.2.0 | 2026-10-31 | Real guns
Twelve real-world guns from the M1911 to the Barrett, right-click aiming with sniper scopes, and a shop sorted into categories.

## 1.1.0 | 2026-10-31 | More to shoot with
Nine new weapons including fire, freeze and chain-lightning guns, per-weapon upgrades, painted zombie skins, and automatic updates.

## 1.0.0 | 2026-10-31 | Hello, BLOCKHOLD
The first Python version: a blocky first-person wave survival game inspired by KillCraft. Survive the waves, earn coins, buy guns.
