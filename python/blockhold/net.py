"""Multiplayer groundwork. There is no networking yet, but the game is built so
it can be added later without a rewrite (see MULTIPLAYER.md):

* every player, enemy, pickup and projectile has a network id (`new_id()`)
* players are driven by `PlayerInput` commands, never by reading the keyboard
  directly, so a remote player can be driven by commands from the network
* things that happen in the game are announced on the `Events` bus, so a host
  can forward them to clients and clients can play the sounds / effects
"""
import itertools
from dataclasses import asdict, dataclass

_ids = itertools.count(1)


def new_id():
    """A unique id for anything that will need to be synced over the network."""
    return next(_ids)


class Events:
    """A tiny publish / subscribe bus.

        game.events.on('enemy_killed', my_function)
        game.events.emit('enemy_killed', enemy=e, player=p, headshot=True)
    """

    def __init__(self):
        self._subs = {}
        self.log = []            # recent events (a future host will send these to clients)

    def on(self, name, fn):
        self._subs.setdefault(name, []).append(fn)

    def off(self, name, fn):
        if fn in self._subs.get(name, []):
            self._subs[name].remove(fn)

    def emit(self, name, **data):
        self.log.append((name, data))
        del self.log[:-200]
        for fn in list(self._subs.get(name, [])):
            fn(**data)


@dataclass
class PlayerInput:
    """Everything a player can do in one frame. Locally it comes from the
    keyboard and mouse; for a remote player it will come from the network."""
    move_x: float = 0.0          # -1 left .. 1 right
    move_z: float = 0.0          # -1 back .. 1 forward
    jump: bool = False           # held
    jump_pressed: bool = False   # pressed this frame
    sprint: bool = False
    crouch: bool = False         # held
    crouch_pressed: bool = False
    use: bool = False            # held: revive team-mates / allies, interact

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
