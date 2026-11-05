# ─────────────────────────────────────────────────────────────────────────────
#  ZONES AND SETTINGS FOR MAP MARKERS  (map editor: Zones tab)
#
#  Some things you place in the editor have settings: pick one (Ctrl+click) and press
#  N, or click EDIT, to change them. They are saved with the map.
#
#  A setting (a "field") is a dict:
#    key, label    the name in the map file / on the panel
#    kind          'int' (a number with - / + buttons), 'choice' (pick one), 'text'
#    lo, hi, step  for numbers          choices   [(value, label)] for choices
#    default       what a new marker starts with
#    help          one line shown under it
#
#  The zone kinds:
#    level        zombies spawned inside are this level (random between min and max).
#                 Where zones overlap, the smallest one wins
#    encounter    when a player walks in, there's a chance a group of zombies climbs out
#                 of the ground nearby (they don't count towards the wave)
#    safe         no PvP inside (for multiplayer) and no zombies spawn in it
#    extraction   where you leave the map with your loot (extraction games)
# ─────────────────────────────────────────────────────────────────────────────

ZOMBIE_LEVEL_MAX = 50

# what a zombie's level does to it (level 1 = normal)
LEVEL_HP = 0.22         # +22% health per level
LEVEL_DAMAGE = 0.10     # +10% damage per level
LEVEL_SPEED = 0.015     # +1.5% speed per level (capped at +45%)
LEVEL_REWARD = 0.2      # +20% XP and coins per level


def _enemy_choices():
    from .enemies import ENEMIES
    return [('mixed', 'Mixed')] + [(k, d['name'].split()[0]) for k, d in ENEMIES.items() if not d.get('boss')]


def _int(key, label, lo, hi, default, step=1, help=''):
    return dict(key=key, label=label, kind='int', lo=lo, hi=hi, step=step, default=default, help=help)


ZONE_FIELDS = {
    'level': [
        _int('radius', 'Radius (m)', 4, 160, 20, 2),
        _int('min_level', 'Lowest level', 1, ZOMBIE_LEVEL_MAX, 1),
        _int('max_level', 'Highest level', 1, ZOMBIE_LEVEL_MAX, 3,
             help='Zombies that spawn inside get a level between these two.'),
    ],
    'encounter': [
        _int('radius', 'Radius (m)', 4, 80, 15, 1),
        _int('chance', 'Chance (%)', 5, 100, 60, 5, help='Rolled when a player walks in (and the cooldown is over).'),
        _int('cooldown', 'Cooldown (s)', 15, 900, 90, 15),
        _int('group_min', 'Group size from', 1, 20, 3),
        _int('group_max', 'Group size to', 1, 30, 6),
        dict(key='kind', label='Zombies', kind='choice', choices=_enemy_choices, default='mixed'),
        _int('level', 'Level', 0, ZOMBIE_LEVEL_MAX, 0, help='0 = use the level zone it is in.'),
    ],
    'safe': [
        _int('radius', 'Radius (m)', 4, 120, 12, 2, help='No PvP inside, and no zombies spawn in it.'),
    ],
    'extraction': [
        _int('radius', 'Radius (m)', 2, 20, 4),
        _int('time', 'Time to extract (s)', 3, 60, 8, help='Stand inside this long to leave with your loot.'),
        dict(key='name', label='Name', kind='text', default='Extraction', limit=20),
    ],
    'grave': [
        _int('level', 'Zombie level', 0, ZOMBIE_LEVEL_MAX, 0, help='0 = use the level zone it is in (or none).'),
    ],
}

ZONE_COLOURS = {'level': '#e8902a', 'encounter': '#d64541', 'safe': '#3ddc97', 'extraction': '#4fd8ff'}


def choices(field):
    c = field['choices']
    return c() if callable(c) else c


def fill_fields(fields, data):
    """The settings with every field filled in (missing ones get their default)."""
    out = dict(data or {})
    for f in fields:
        if f['key'] not in out:
            out[f['key']] = f['default']
    return out


def level_scale(level):
    """(hp, damage, speed, reward) multipliers for a zombie of this level."""
    n = max(0, (level or 1) - 1)
    return (1 + LEVEL_HP * n, 1 + LEVEL_DAMAGE * n, 1 + min(0.45, LEVEL_SPEED * n), 1 + LEVEL_REWARD * n)
