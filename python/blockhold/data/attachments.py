# ─────────────────────────────────────────────────────────────────────────────
#  WEAPON ATTACHMENTS  (bought and fitted in the shop: Weapons tab -> CUSTOMIZE)
#
#    slot       'optic', 'muzzle', 'under' or 'mag' (a gun only shows the slots it has)
#    build      draws it on the gun (see gunsmith.py); None = no visible part
#    Stat changes (multipliers, 1 = no change):
#      recoil     kick per shot           spread   hip-fire inaccuracy
#      aim_spread inaccuracy when aiming  range    bullet range
#      mag        magazine size           reload   reload time
#      zoom       extra zoom when aiming  (bigger = closer)
#    scope      True = right-click gives a real sniper scope
#    sound      replaces the shot sound (e.g. 'suppressed')
# ─────────────────────────────────────────────────────────────────────────────
from ..gunsmith import (att_compensator, att_foregrip, att_holo, att_laser, att_reddot, att_scope,
                        att_suppressor)

ATTACHMENTS = {
    'reddot': dict(name='Red dot', slot='optic', price=150, build=att_reddot, aim_spread=0.75, zoom=1.15,
                   desc='Clear sight picture: steadier aim.'),
    'holo': dict(name='Holo sight', slot='optic', price=220, build=att_holo, aim_spread=0.65, zoom=1.2,
                 desc='Wide window: the most accurate when aiming.'),
    'scope': dict(name='4x scope', slot='optic', price=400, build=att_scope, scope=True, aim_spread=0.4,
                  desc='Right-click zooms right in. Headshot machine.'),
    'suppressor': dict(name='Suppressor', slot='muzzle', price=300, build=att_suppressor, sound='suppressed',
                       recoil=0.8, range=0.85, desc='Quiet shots, less kick, a bit less range.'),
    'compensator': dict(name='Compensator', slot='muzzle', price=200, build=att_compensator, recoil=0.55,
                        desc='Much less recoil.'),
    'foregrip': dict(name='Foregrip', slot='under', price=150, build=att_foregrip, recoil=0.75, spread=0.8,
                     desc='Steadier: less recoil and spread.'),
    'laser': dict(name='Laser', slot='under', price=180, build=att_laser, spread=0.6,
                  desc='Much tighter hip-fire.'),
    'ext_mag': dict(name='Extended mag', slot='mag', price=250, build=None, mag=1.5, reload=1.15,
                    desc='+50% ammo per mag, slower reload.'),
}

SLOT_NAMES = {'optic': 'Optic', 'muzzle': 'Muzzle', 'under': 'Underbarrel', 'mag': 'Magazine'}
