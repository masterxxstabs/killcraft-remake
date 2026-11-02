# Multiplayer plan

Multiplayer isn't built yet, but the game is being written so it can be added
without a rewrite. This file explains the plan and the rules every new feature
should follow.

## How it will work

**Host + clients (co-op, 2–4 players).** One player hosts. The host's game is the
only one that runs the "real" simulation: zombies, waves, damage, coins and pickups.
Friends connect to the host over the internet or a LAN.

```
 client                         host                          client
 ──────                         ────                          ──────
 keyboard → PlayerInput  ──►  applies inputs to players  ◄──  PlayerInput ← keyboard
                              runs zombies, waves, shots
 draws the world        ◄──   snapshots (positions, hp)  ──►  draws the world
 plays sounds/effects   ◄──   events (kills, pickups)    ──►  plays sounds/effects
```

* **Clients send inputs**, not results: a `PlayerInput` (movement, jump, crouch...)
  plus "I fired weapon X in direction D" every frame.
* **The host sends snapshots** about 20 times a second: the position, rotation and
  health of every player, zombie, pickup and projectile, keyed by network id.
* **The host sends events** when something happens (`enemy_killed`, `pickup`,
  `wave_started`...) so clients can play the matching sounds and effects.
* **Clients predict their own movement.** The local player moves instantly; the host's
  snapshot corrects it if they disagree. Zombies and other players are smoothed between
  snapshots.

The transport will probably be UDP using Python's `socket` module (or Panda3D's
built-in networking), with a small reliable channel for events, shop purchases and
chat. A direct-IP join screen comes first, then maybe a lobby.

## What's already in place

| Piece | Where | Why it matters |
| --- | --- | --- |
| Network ids | `net.new_id()`, used by players, enemies, pickups and projectiles | snapshots and events refer to things by id |
| `PlayerInput` | `net.py`; `Player.update(dt, input)` | movement is driven by commands, so a remote player's input can drive them the same way |
| Event bus | `game.events.emit(...)` / `.on(...)` | gameplay announces what happened; sounds, UI, quests and (later) the network listen |
| Several players | `game.players`; `game.player` is the local one | zombies chase `game.nearest_target()`, any player can pick up coins, wave bonuses go to everyone |
| Per-player economy | `player.coins`, `.score`, `.kills`, `.upgrade_levels` | each friend has their own money and upgrades (`game.coins` is the local player's) |
| Kill credit | `enemy.hurt(..., attacker=player)` | the right player gets the score and coins |
| Shared map data | maps are JSON; random arenas come from a seed | the host sends the map once when you join |
| Allies belong to a player | `ally.owner`; `game.targets()` includes allies | each friend can hire their own survivors |
| Revive by holding E | `game.update_revives(dt, input)` uses `input.use` | the same code will revive downed friends |
| Quests listen to events | `quests.py` reacts to `enemy_killed` and shots | the host runs the quest; clients only see the effects |
| Team power-ups | `game.powerups` (timers are team-wide, any player can pick one up) | the host runs them and sends `powerup_*` events |
| Mining and crafting | `player.resources`; nodes have ids; `game.craft(recipe, player)` | each friend mines and crafts for themselves; the host runs the nodes |
| Barricades belong to a player | `barricade['owner']`, ids, `player.placeables`; `barricades.place(player, ...)`; events `barricade_placed`, `barricade_hit`, `barricade_destroyed`, `mine_exploded` | the host runs turrets, mines and zombie smashing; turret, spike and mine kills earn the owner coins |
| Lighting is presentation only | `lighting.py` picks lights from what each client can see | nothing to send over the network |
| Attachments and camos per weapon | `weapons.attach`, `weapons.camo` | a remote player's gun can be rebuilt from a small dict |

## Rules for new features

1. **Simulation and presentation stay separate.** Gameplay code decides what happens
   and emits an event; sounds, particles and UI react to it. Only the host runs
   gameplay, but everyone runs presentation.
2. **Never read the keyboard inside gameplay code.** Read it once in
   `Game.local_input()` (or the input handler) and pass the result in.
3. **Anything the network needs to know about gets an id** (`new_id()`).
4. **Things belong to a player.** Use `player.coins` and `weapons.owner`, not a single
   global. Effects only shake or flash the screen `if player.is_local`.
5. **Randomness that changes gameplay happens on the host**, such as wave contents,
   drops and enemy choices. Cosmetic randomness (particles) can happen anywhere.
6. **Zombies and allies pick targets from `game.targets()`**, never `game.player`.

## Still to do (when we build it)

- [ ] `net_host.py` / `net_client.py`: sockets, join screen, connect / disconnect
- [ ] Snapshot encode / decode and interpolation of remote entities
- [ ] Remote player models (the blocky character with the held gun)
- [ ] One `Weapons` loadout per player (today `game.weapons` is the local player's)
- [x] Downed state for players (`player.downed`, bleed-out timer; allies revive their owner)
- [ ] Let players revive each other too (reuse `update_revives`)
- [ ] Shared shop between waves (each player buys with their own coins)
- [x] Scoreboard (hold Tab): already lists every player in `game.players` and every ally
- [ ] Text chat
