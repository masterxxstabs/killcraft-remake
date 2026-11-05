# ─────────────────────────────────────────────────────────────────────────────
#  RAIDS  (climb the ladder out of the hideout to start one)
#
#  A raid is a trip to the surface: loot what you can, then reach an EXTRACTION point
#  and stand in it to go home with everything you carry. Die out there and everything
#  you carried stays where you fell; you wake up back in the hideout with nothing but
#  a T-shirt, jeans and the starting weapons. Coins in the bank and items in the bank
#  are always safe, and so are your level and skills.
#
#  Zombies keep climbing out of the ground around you for as long as you're up there,
#  more the longer you stay. How tough they are depends on the level zone you're in.
#
#  RAIDS: the generated ones (any map you build with extraction points shows up too).
#    size       half the map's width in metres
#    levels     zombie levels: (edges low, edges high, middle low, middle high)
#    exits      how many extraction points
#    zombies    how many are about at the start, and at most
# ─────────────────────────────────────────────────────────────────────────────

RAIDS = [
    dict(id='outskirts', name='The Outskirts', size=64, levels=(1, 3, 4, 7), exits=3, zombies=(7, 18),
         desc='Farms, camps and roadside wrecks. Quiet, mostly. A good first trip.'),
    dict(id='wildlands', name='The Wildlands', size=128, levels=(2, 5, 8, 14), exits=4, zombies=(9, 24),
         desc='Miles of forest and ruins. Better loot further in, and worse company.'),
    dict(id='blacksite', name='The Blacksite', size=200, levels=(5, 9, 14, 22), exits=4, zombies=(12, 30),
         desc='A huge stretch of dead country. Only for the well armed.'),
]

EXIT_NAMES = ['North Road', 'East Gate', 'South Bridge', 'West Tunnel', 'Old Mill', 'Radio Tower', 'Rail Yard',
              'Water Tower']
EXIT_RADIUS, EXIT_TIME = 5, 8          # generated extraction points: size and seconds to stand in them

RAMP_EVERY = 120.0           # seconds: one more zombie about every this long (up to the maximum)
SPAWN_EVERY = 1.6            # seconds between zombies climbing out while there are too few
DESPAWN_DIST = 85.0          # zombies this far from every player wander off
XP_EXTRACT = 120             # XP for getting out alive (plus XP_PER_MINUTE for every minute up there)
XP_PER_MINUTE = 10
