# ─────────────────────────────────────────────────────────────────────────────
#  ATMOSPHERE  (Settings > Atmosphere)
#  How the world looks: sky, fog, how dark it is and how bright the lights are.
#  Dusk is the default, in the spirit of the original game: dark and foggy, with
#  a torch lighting up the ground around you.
#
#    sky, fog        colour high in the sky / at the horizon (and of the fog)
#    fog_near/far    fog starts / is solid at these distances (metres)
#    ambient         light level everywhere (r, g, b): 1 = full daylight
#    clouds          cloud colour, cloud_amt how cloudy (0-1), stars how many stars (0-1)
#    torch           strength of the light you carry (0 = none), torch_radius its reach
#    lights          strength of every other light (lamps, campfires, muzzle flashes...)
#    mod_dim         wave modifier skies (Blood Moon...) are darkened by this much
# ─────────────────────────────────────────────────────────────────────────────

ATMOSPHERES = {
    'dusk': dict(name='Dusk', sky='#15121a', fog='#2e2622', fog_near=6, fog_far=60,
                 ambient=(0.52, 0.48, 0.5), clouds='#3a302d', cloud_amt=0.85, stars=0.35,
                 torch=1.25, torch_radius=13, lights=1.0, mod_dim=0.45),
    'night': dict(name='Night', sky='#05060b', fog='#0e0e13', fog_near=3, fog_far=44,
                  ambient=(0.2, 0.21, 0.29), clouds='#17171d', cloud_amt=0.6, stars=1.0,
                  torch=1.55, torch_radius=15, lights=1.25, mod_dim=0.25),
    'day': dict(name='Day', sky='#6fb6ea', fog='#a9d6f2', fog_near=30, fog_far=110,
                ambient=(1.0, 1.0, 1.0), clouds='#ffffff', cloud_amt=0.65, stars=0.0,
                torch=0.0, torch_radius=0, lights=0.35, mod_dim=1.0),
    # the map editor: bright and clear
    'editor': dict(name='Editor', sky='#6fb6ea', fog='#a9d6f2', fog_near=150, fog_far=320,
                   ambient=(1.0, 1.0, 1.0), clouds='#ffffff', cloud_amt=0.5, stars=0.0,
                   torch=0.0, torch_radius=0, lights=0.0, mod_dim=1.0, hidden=True),
}

DEFAULT_ATMOSPHERE = 'dusk'
TORCH_COLOUR = (1.0, 0.7, 0.42)
