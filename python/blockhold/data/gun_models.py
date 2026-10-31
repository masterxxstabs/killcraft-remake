# ─────────────────────────────────────────────────────────────────────────────
#  DETAILED GUN MODELS
#  One function per weapon id, built with the Gunsmith (blockhold/gunsmith.py).
#  Weapons without a function here use the block model from weapons.py.
#
#  Useful Gunsmith calls (all sizes in metres, z = forward, y = up):
#    s.box(x0, x1, y0, y1, z0, z1, material, slot, bevel)   bevelled box
#    s.side([(z, y), ...], width, material, slot)            a part drawn from the side
#    s.tube(z0, z1, radius, material, y=..)                  barrel, tube, suppressor
#    s.grip(z, y_top, length, angle)    s.magazine(z, y_top, length, curve=..)
#    s.rail(z0, z1, y)                  s.trigger_guard(z0, z1, y)
#    s.iron_front(z, y)  s.iron_rear(z, y)  s.muzzle_brake(z, y)  s.flash_hider(z, y)
#    s.stock_ar(z, y)  s.stock_wood(z, y)  s.stock_skeleton(z, y)  s.stock_folding(z, y)
#  slot: 'main' and 'furniture' parts get repainted by camos, 'metal' parts don't.
#  Mount points for attachments:
#    s.mount('optic', (rail_top_y, z_middle))   s.mount('under', (bottom_y, z_middle))
#    s.mount('muzzle', (x, y, z_end))  (muzzle_brake / flash_hider set this for you)
# ─────────────────────────────────────────────────────────────────────────────


def _pistol_slide(s, z0, z1, y0, y1, w, mat, slot='main', bevel=0.006):
    s.box(-w / 2, w / 2, y0, y1, z0, z1, mat, slot, bevel=bevel)
    for k in range(6):                                     # grip serrations at the back
        z = z0 + 0.006 + k * 0.008
        s.box(-w / 2 - 0.0008, w / 2 + 0.0008, y0 + 0.008, y1 - 0.006, z, z + 0.0028, 'black', 'metal')
    s.box(w / 2 - 0.002, w / 2 + 0.0008, y0 + 0.024, y1 - 0.004, z0 + 0.09, z0 + 0.135, 'steel', 'metal')  # ejection port


def pistol(s):
    _pistol_slide(s, -0.035, 0.2, 0.004, 0.056, 0.04, 'gunmetal')
    s.box(-0.018, 0.018, -0.02, 0.008, -0.025, 0.19, 'polymer', 'furniture', bevel=0.004)
    s.tube(0.2, 0.207, 0.009, 'black', y=0.03)
    s.grip(0.0, -0.004, length=0.11, angle=16, width=0.032)
    s.trigger_guard(0.0, 0.068, -0.018)
    s.box(-0.003, 0.003, 0.056, 0.064, 0.182, 0.192, 'black', 'metal')
    s.box(-0.01, 0.01, 0.056, 0.065, -0.03, -0.019, 'black', 'metal')
    s.mount('muzzle', (0, 0.03, 0.207))


def glock(s):
    _pistol_slide(s, -0.03, 0.17, 0.008, 0.058, 0.037, 'black', bevel=0.003)
    s.box(-0.017, 0.017, -0.018, 0.01, -0.025, 0.162, 'polymer', 'furniture', bevel=0.003)
    s.box(-0.0175, 0.0175, -0.014, -0.004, 0.11, 0.16, 'polymer', 'furniture')      # accessory rail bump
    s.tube(0.17, 0.174, 0.008, 'gunmetal', y=0.033)
    s.grip(0.0, -0.002, length=0.105, angle=20, width=0.031, back=0.04)
    s.trigger_guard(0.0, 0.065, -0.016)
    s.box(-0.003, 0.003, 0.058, 0.066, 0.155, 0.165, 'black', 'metal')
    s.box(-0.0015, 0.0015, 0.0625, 0.0655, 0.1645, 0.1652, 'green', 'metal')         # night sight dot
    s.box(-0.011, 0.011, 0.058, 0.067, -0.026, -0.016, 'black', 'metal')
    s.mount('muzzle', (0, 0.033, 0.174))


def m1911(s):
    _pistol_slide(s, -0.04, 0.18, 0.006, 0.05, 0.032, 'steel', bevel=0.004)
    s.box(-0.016, 0.016, -0.016, 0.008, -0.03, 0.12, 'gunmetal', 'main', bevel=0.003)
    s.tube(0.12, 0.18, 0.012, 'gunmetal', y=0.0)                                       # recoil spring plug
    s.tube(0.18, 0.186, 0.0075, 'black', y=0.028)
    s.grip(0.0, -0.002, length=0.108, angle=12, width=0.03, back=0.042, mat='gunmetal', slot='main')
    for x in (-0.0165, 0.0165):                                                         # wooden grip panels
        s.side([(-0.038, -0.012), (0.004, -0.012), (-0.015, -0.1), (-0.055, -0.095)], 0.004, 'wood', 'furniture', x=x)
    s.side([(-0.05, 0.03), (-0.035, 0.03), (-0.035, 0.012), (-0.048, 0.014)], 0.01, 'gunmetal', 'metal')  # hammer
    s.trigger_guard(0.0, 0.062, -0.014, mat='gunmetal')
    s.box(-0.0025, 0.0025, 0.05, 0.058, 0.168, 0.176, 'black', 'metal')
    s.box(-0.009, 0.009, 0.05, 0.059, -0.032, -0.022, 'black', 'metal')
    s.mount('muzzle', (0, 0.028, 0.186))


def deagle(s):
    s.box(-0.022, 0.022, 0.01, 0.07, -0.04, 0.23, 'chrome', 'main', bevel=0.008)
    s.side([(-0.04, 0.07), (0.23, 0.07), (0.23, 0.08), (-0.01, 0.082)], 0.018, 'chrome', 'main')   # top rib
    for k in range(7):
        z = -0.035 + k * 0.007
        s.box(-0.0228, 0.0228, 0.02, 0.064, z, z + 0.003, 'gunmetal', 'metal')
    s.box(-0.019, 0.019, -0.02, 0.012, -0.03, 0.2, 'chrome', 'main', bevel=0.004)
    s.box(0.012, 0.0226, 0.018, 0.04, 0.12, 0.16, 'black', 'metal')                    # port
    s.tube(0.23, 0.236, 0.011, 'black', y=0.04)
    s.grip(0.0, -0.006, length=0.12, angle=14, width=0.036, back=0.045, mat='polymer')
    s.trigger_guard(0.0, 0.075, -0.018, mat='chrome')
    s.side([(-0.055, 0.04), (-0.04, 0.04), (-0.04, 0.02), (-0.052, 0.022)], 0.01, 'chrome', 'metal')
    s.box(-0.003, 0.003, 0.082, 0.09, 0.215, 0.225, 'black', 'metal')
    s.mount('muzzle', (0, 0.04, 0.236))


def revolver(s):
    s.box(-0.016, 0.016, -0.01, 0.045, -0.06, 0.02, 'steel', 'main', bevel=0.004)      # frame
    s.tube(-0.035, 0.045, 0.034, 'steel', y=0.008, sides=6)                            # cylinder
    for k in range(6):                                                                  # cylinder flutes
        a = k / 6 * 6.283 + 0.52
        import math
        cx, cy = math.cos(a) * 0.034, 0.008 + math.sin(a) * 0.034
        s.box(cx - 0.004, cx + 0.004, cy - 0.004, cy + 0.004, -0.025, 0.035, 'gunmetal', 'metal')
    s.tube(0.045, 0.27, 0.013, 'steel', y=0.03, sides=10)
    s.box(-0.007, 0.007, 0.03, 0.05, 0.045, 0.27, 'steel', 'main', bevel=0.003)          # top rib
    s.tube(0.04, 0.19, 0.008, 'gunmetal', y=0.006)                                      # ejector rod
    s.side([(-0.075, 0.05), (-0.06, 0.05), (-0.055, 0.03), (-0.07, 0.025)], 0.01, 'steel', 'metal')  # hammer
    s.grip(-0.035, -0.008, length=0.11, angle=24, width=0.036, back=0.045, mat='wood')
    s.trigger_guard(-0.04, 0.012, -0.008, mat='steel')
    s.box(-0.0025, 0.0025, 0.05, 0.063, 0.252, 0.265, 'brass', 'metal')
    s.mount('muzzle', (0, 0.03, 0.27))


def uzi(s):
    s.box(-0.026, 0.026, -0.015, 0.06, -0.12, 0.2, 'black', 'main', bevel=0.004)
    s.box(-0.027, 0.027, 0.02, 0.05, -0.06, 0.12, 'gunmetal', 'main')                    # ribbed cover
    for k in range(5):
        z = -0.05 + k * 0.035
        s.box(-0.028, 0.028, 0.044, 0.062, z, z + 0.008, 'black', 'metal')
    s.tube(0.2, 0.26, 0.011, 'gunmetal', y=0.025)
    s.tube(0.2, 0.215, 0.018, 'black', y=0.025, sides=8)                                 # barrel nut
    s.grip(0.04, -0.015, length=0.13, angle=6, width=0.034, back=0.04)
    s.magazine(0.025, -0.14, 0.09, depth=0.03, width=0.024, mat='gunmetal', slot='metal')
    s.trigger_guard(0.03, 0.1, -0.015)
    s.stock_skeleton(-0.12, 0.03, length=0.2)
    s.box(-0.004, 0.004, 0.06, 0.08, 0.17, 0.18, 'black', 'metal')
    s.box(-0.01, 0.01, 0.06, 0.075, -0.1, -0.09, 'black', 'metal')
    s.mount('muzzle', (0, 0.025, 0.26))
    s.mount('optic', (0.062, 0.03))
    s.mount('under', (-0.015, 0.16))


def mp5(s):
    s.box(-0.024, 0.024, -0.005, 0.055, -0.08, 0.22, 'black', 'main', bevel=0.012)
    s.tube(0.03, 0.31, 0.012, 'black', y=0.062, x=-0.008, sides=8)                       # cocking tube
    s.tube(0.2, 0.33, 0.024, 'polymer', y=0.015, sides=10)                                # slim handguard
    s.tube(0.33, 0.42, 0.011, 'gunmetal', y=0.03)
    s.box(-0.015, 0.015, 0.03, 0.09, 0.37, 0.39, 'black', 'metal')                         # front sight hood
    s.box(-0.004, 0.004, 0.06, 0.082, 0.375, 0.385, 'black', 'metal')
    s.cyl_x(-0.016, 0.016, 0.075, -0.06, 0.016, 'black')                                   # drum rear sight
    s.flash_hider(0.42, 0.03, r=0.013, length=0.035)
    s.grip(0.02, -0.005, length=0.11, angle=14, width=0.033, back=0.04)
    s.box(-0.02, 0.02, -0.03, -0.004, -0.04, 0.09, 'polymer', 'furniture', bevel=0.004)    # trigger group
    s.magazine(0.15, -0.005, 0.15, depth=0.032, width=0.022, curve=0.045, mat='black')
    s.trigger_guard(0.02, 0.09, -0.03)
    s.side([(-0.08, 0.05), (-0.08, -0.03), (-0.3, -0.06), (-0.31, -0.05), (-0.31, 0.04), (-0.2, 0.05)], 0.04, 'polymer', 'furniture')
    s.mount('optic', (0.075, 0.08))
    s.mount('under', (-0.01, 0.27))


def smg(s):
    """Buzz SMG: a compact futuristic bullet hose."""
    s.side([(-0.12, 0.06), (0.24, 0.06), (0.28, 0.03), (0.28, -0.01), (0.14, -0.03), (-0.12, -0.03)], 0.05, 'polymer')
    s.box(-0.026, 0.026, 0.0, 0.03, 0.02, 0.22, 'gunmetal', 'main', bevel=0.004)
    s.rail(-0.08, 0.2, 0.072)
    s.tube(0.28, 0.33, 0.012, 'black', y=0.015)
    s.flash_hider(0.33, 0.015, r=0.013, length=0.03)
    s.grip(0.0, -0.025, length=0.1, angle=18, width=0.034)
    s.magazine(0.12, -0.03, 0.15, depth=0.034, width=0.024, mat='black')
    s.box(-0.02, 0.02, -0.03, 0.04, -0.2, -0.12, 'polymer', 'furniture', bevel=0.01)
    s.box(-0.012, 0.012, 0.012, 0.022, 0.0, 0.25, 'glow_cyan', 'metal')
    s.mount('optic', (0.072, 0.06))
    s.mount('under', (-0.03, 0.2))


def _ar_core(s, upper='black', lower='black', furniture='polymer', hg_len=0.24, quad=False):
    s.box(-0.022, 0.022, 0.0, 0.05, -0.04, 0.2, upper, 'main', bevel=0.006)              # upper receiver
    s.side([(-0.04, 0.0), (0.2, 0.0), (0.2, -0.02), (0.12, -0.03), (0.1, -0.05), (0.04, -0.05), (0.02, -0.025),
            (-0.04, -0.025)], 0.04, lower, 'main')                                         # lower receiver + mag well
    s.rail(-0.03, 0.2, 0.062)
    s.cyl_x(0.022, 0.032, 0.03, 0.06, 0.009, 'black')                                     # forward assist
    s.box(-0.012, 0.012, 0.035, 0.05, -0.06, -0.035, 'black', 'metal')                      # charging handle
    if quad:
        s.box(-0.026, 0.026, -0.008, 0.052, 0.2, 0.2 + hg_len, furniture, 'furniture', bevel=0.008)
        s.rail(0.2, 0.2 + hg_len, 0.062)
        s.rail(0.205, 0.2 + hg_len - 0.01, -0.008 - 0.0, x=0.0)
    else:
        s.tube(0.2, 0.2 + hg_len, 0.028, furniture, slot='furniture', y=0.022, sides=10)
        for k in range(int(hg_len / 0.03)):
            z = 0.215 + k * 0.03
            s.box(-0.029, 0.029, 0.0, 0.006, z, z + 0.012, 'black', 'metal')
    s.grip(0.04, -0.02, length=0.1, angle=20, width=0.032, mat='polymer', slot='furniture')
    s.trigger_guard(0.03, 0.1, -0.025)
    s.stock_ar(-0.04, 0.025)
    s.mount('optic', (0.062, 0.07))
    s.mount('under', (-0.006, 0.2 + hg_len * 0.6))


def ar15(s):
    _ar_core(s, hg_len=0.26, quad=True)
    s.tube(0.46, 0.6, 0.0105, 'gunmetal', y=0.025)
    s.side([(0.5, 0.012), (0.53, 0.012), (0.528, 0.07), (0.52, 0.075), (0.508, 0.07)], 0.014, 'black', 'metal')  # FSB
    s.flash_hider(0.6, 0.025, r=0.012, length=0.04)
    s.magazine(0.075, -0.035, 0.16, depth=0.05, width=0.024, curve=0.02, mat='gunmetal', slot='metal')


def rifle(s):
    """Ranger Rifle: a modern carbine with OD furniture."""
    _ar_core(s, furniture='od', hg_len=0.24, quad=True)
    s.tube(0.44, 0.56, 0.011, 'gunmetal', y=0.025)
    s.muzzle_brake(0.56, 0.025, r=0.015, length=0.05)
    s.magazine(0.075, -0.035, 0.155, depth=0.05, width=0.024, curve=0.02, mat='od', slot='furniture')


def ak47(s):
    s.box(-0.022, 0.022, -0.02, 0.04, -0.05, 0.22, 'gunmetal', 'main', bevel=0.003)       # stamped receiver
    s.box(-0.02, 0.02, 0.04, 0.058, -0.04, 0.2, 'gunmetal', 'main', bevel=0.009)           # dust cover
    s.side([(0.22, 0.04), (0.42, 0.035), (0.42, -0.008), (0.22, -0.02)], 0.046, 'wood', 'furniture')   # lower handguard
    s.side([(0.24, 0.045), (0.4, 0.045), (0.4, 0.072), (0.26, 0.074)], 0.036, 'wood', 'furniture')    # upper handguard
    s.tube(0.24, 0.48, 0.009, 'gunmetal', y=0.06)                                           # gas tube
    s.tube(0.42, 0.62, 0.011, 'gunmetal', y=0.02)
    s.side([(0.56, 0.01), (0.6, 0.01), (0.6, 0.07), (0.592, 0.072), (0.585, 0.05), (0.565, 0.045)], 0.016, 'black', 'metal')
    s.box(-0.002, 0.002, 0.07, 0.085, 0.588, 0.594, 'black', 'metal')                       # front post
    s.side([(0.62, 0.008), (0.665, 0.012), (0.665, 0.03), (0.62, 0.032)], 0.026, 'black', 'metal')  # slant brake
    s.mount('muzzle', (0, 0.02, 0.665))
    s.box(-0.012, 0.012, 0.058, 0.07, 0.17, 0.215, 'black', 'metal')                         # rear sight
    s.box(0.022, 0.032, 0.02, 0.032, 0.08, 0.12, 'steel', 'metal')                           # charging handle
    s.magazine(0.13, -0.02, 0.2, depth=0.052, width=0.026, curve=0.07, angle=6, mat='black')
    s.grip(0.04, -0.02, length=0.1, angle=18, width=0.034, mat='wood')
    s.trigger_guard(0.03, 0.1, -0.02)
    s.stock_wood(-0.05, 0.02, drop=0.05, length=0.27)
    s.mount('optic', (0.072, 0.12))
    s.mount('under', (-0.008, 0.33))


def asval(s):
    s.box(-0.022, 0.022, -0.015, 0.05, -0.05, 0.2, 'black', 'main', bevel=0.006)
    s.box(-0.026, 0.026, -0.01, 0.05, 0.2, 0.3, 'polymer', 'furniture', bevel=0.01)          # handguard
    s.tube(0.25, 0.52, 0.026, 'gunmetal', y=0.022, sides=12)                                 # built-in suppressor
    s.tube(0.517, 0.522, 0.02, 'rubber', y=0.022, sides=12)
    s.mount('muzzle', (0, 0.022, 0.522))
    s.box(-0.004, 0.004, 0.048, 0.072, 0.48, 0.49, 'black', 'metal')
    s.box(-0.01, 0.01, 0.05, 0.068, 0.12, 0.15, 'black', 'metal')
    s.magazine(0.11, -0.015, 0.11, depth=0.045, width=0.024, curve=0.02, mat='black')
    s.grip(0.03, -0.015, length=0.1, angle=16, width=0.034)
    s.trigger_guard(0.02, 0.09, -0.015)
    s.stock_skeleton(-0.05, 0.035, length=0.25)
    s.mount('optic', (0.05, 0.06))
    s.mount('under', (-0.01, 0.25))


def scarh(s):
    s.box(-0.026, 0.026, 0.0, 0.06, -0.06, 0.38, 'tan', 'main', bevel=0.008)               # long upper
    s.rail(-0.055, 0.38, 0.072)
    for x in (-0.028, 0.028):
        s.box(x - 0.004, x + 0.004, 0.012, 0.032, 0.26, 0.37, 'black', 'metal')              # side rails
    s.side([(-0.06, 0.0), (0.22, 0.0), (0.22, -0.02), (0.15, -0.03), (0.13, -0.05), (0.07, -0.05), (0.05, -0.025),
            (-0.06, -0.025)], 0.044, 'tan', 'main')                                           # lower
    s.box(0.026, 0.04, 0.035, 0.05, 0.1, 0.13, 'black', 'metal')                              # charging handle
    s.tube(0.38, 0.55, 0.012, 'gunmetal', y=0.025)
    s.flash_hider(0.55, 0.025, r=0.014, length=0.045)
    s.magazine(0.1, -0.035, 0.12, depth=0.06, width=0.028, mat='tan', slot='furniture')
    s.grip(0.05, -0.02, length=0.1, angle=18, width=0.034, mat='black', slot='metal')
    s.trigger_guard(0.04, 0.11, -0.025)
    s.stock_folding(-0.06, 0.04)
    s.mount('optic', (0.072, 0.1))
    s.mount('under', (0.0, 0.32))


def remington(s):
    s.tube(0.1, 0.56, 0.016, 'gunmetal', y=0.04)                                             # barrel
    s.tube(0.1, 0.48, 0.014, 'black', y=0.008)                                               # magazine tube
    s.tube(0.47, 0.5, 0.016, 'black', y=0.008)
    s.box(-0.026, 0.026, -0.012, 0.03, 0.22, 0.36, 'wood', 'furniture', bevel=0.01)        # pump
    for k in range(6):
        z = 0.235 + k * 0.02
        s.box(-0.027, 0.027, -0.01, 0.028, z, z + 0.006, 'wood_dark', 'metal')
    s.box(-0.024, 0.024, -0.02, 0.06, -0.08, 0.1, 'black', 'main', bevel=0.006)            # receiver
    s.box(0.024, 0.026, 0.01, 0.04, -0.02, 0.06, 'steel', 'metal')                           # ejection port
    s.box(-0.002, 0.002, 0.056, 0.062, 0.545, 0.55, 'brass', 'metal')                        # bead
    s.mount('muzzle', (0, 0.04, 0.56))
    s.trigger_guard(-0.03, 0.04, -0.02)
    s.stock_wood(-0.08, 0.02, drop=0.07, length=0.3)
    s.mount('optic', (0.062, -0.01))
    s.mount('under', (-0.012, 0.29))


def scatter(s):
    """Scattercannon: a chunky drum-fed combat shotgun."""
    s.box(-0.03, 0.03, -0.03, 0.06, -0.06, 0.25, 'gunmetal', 'main', bevel=0.012)
    s.tube(0.25, 0.48, 0.024, 'black', y=0.03, sides=10)
    s.muzzle_brake(0.48, 0.03, r=0.028, length=0.06, mat='steel')
    s.cyl_x(-0.045, 0.045, -0.075, 0.1, 0.07, 'black', sides=12)                              # drum
    s.cyl_x(-0.047, 0.047, -0.075, 0.1, 0.02, 'steel', sides=8)
    s.rail(-0.04, 0.24, 0.072)
    s.grip(0.0, -0.03, length=0.1, angle=16, width=0.036)
    s.stock_folding(-0.06, 0.045)
    s.mount('optic', (0.072, 0.1))
    s.mount('under', (-0.03, 0.36))


def barrett(s):
    s.box(-0.03, 0.03, -0.02, 0.07, -0.1, 0.36, 'gunmetal', 'main', bevel=0.01)
    s.rail(-0.08, 0.3, 0.082)
    s.box(-0.03, 0.03, 0.0, 0.06, 0.36, 0.52, 'gunmetal', 'main', bevel=0.012)            # barrel shroud
    for k in range(4):
        z = 0.38 + k * 0.035
        s.box(-0.031, 0.031, 0.015, 0.045, z, z + 0.018, 'black', 'metal')                  # cooling holes
    s.tube(0.52, 0.82, 0.015, 'gunmetal', y=0.03)
    s.box(-0.04, 0.04, 0.005, 0.055, 0.82, 0.9, 'steel', 'metal', bevel=0.01)              # huge muzzle brake
    for z in (0.835, 0.865):
        s.box(-0.041, 0.041, 0.015, 0.045, z, z + 0.014, 'black', 'metal')
    s.mount('muzzle', (0, 0.03, 0.9))
    s.magazine(0.12, -0.02, 0.1, depth=0.08, width=0.036, mat='black')
    s.grip(0.04, -0.02, length=0.11, angle=16, width=0.036, mat='polymer')
    s.trigger_guard(0.03, 0.11, -0.02)
    s.side([(-0.1, 0.06), (-0.1, -0.02), (-0.36, -0.05), (-0.37, -0.03), (-0.37, 0.07), (-0.22, 0.07)], 0.05, 'gunmetal', 'main')
    s.box(-0.028, 0.028, -0.055, 0.075, -0.385, -0.37, 'rubber', 'metal')
    for x in (-0.012, 0.012):                                                                 # folded bipod
        s.box(x - 0.005, x + 0.005, -0.005, 0.005, 0.36, 0.62, 'black', 'metal')
    s.mount('optic', (0.082, 0.1))
    s.mount('under', (0.0, 0.45))


def m249(s):
    s.box(-0.035, 0.035, -0.02, 0.06, -0.08, 0.26, 'gunmetal', 'main', bevel=0.006)
    s.box(-0.033, 0.033, 0.06, 0.08, -0.05, 0.16, 'black', 'main', bevel=0.004)            # feed cover
    s.rail(-0.04, 0.15, 0.092)
    s.box(-0.03, 0.03, -0.03, 0.04, 0.26, 0.42, 'polymer', 'furniture', bevel=0.012)       # handguard
    s.tube(0.42, 0.62, 0.013, 'gunmetal', y=0.03)
    s.flash_hider(0.62, 0.03, r=0.014, length=0.04)
    s.side([(0.42, 0.05), (0.52, 0.05), (0.5, 0.1), (0.44, 0.1)], 0.01, 'black', 'metal')   # carry handle
    s.box(-0.03, 0.03, 0.095, 0.105, 0.43, 0.51, 'black', 'metal')
    s.box(-0.12, -0.035, -0.12, -0.0, 0.0, 0.14, 'od', 'furniture', bevel=0.006)           # ammo box
    s.box(-0.04, -0.034, -0.02, 0.02, 0.03, 0.1, 'brass', 'metal')                           # belt
    s.grip(0.05, -0.02, length=0.1, angle=16, width=0.034)
    s.trigger_guard(0.04, 0.11, -0.02)
    s.stock_ar(-0.08, 0.03)
    for x in (-0.012, 0.012):
        s.box(x - 0.005, x + 0.005, -0.035, -0.025, 0.42, 0.6, 'black', 'metal')
    s.mount('optic', (0.092, 0.06))
    s.mount('under', (-0.03, 0.34))


def nailgun(s):
    s.side([(-0.05, 0.1), (0.24, 0.1), (0.3, 0.06), (0.3, -0.03), (0.2, -0.04), (-0.05, -0.02)], 0.07, 'orange')
    s.box(-0.03, 0.03, 0.1, 0.13, -0.03, 0.2, 'black', 'metal', bevel=0.01)
    s.tube(0.3, 0.38, 0.018, 'steel', y=0.0, sides=8)
    s.tube(0.375, 0.385, 0.01, 'black', y=0.0)
    s.side([(0.18, -0.03), (0.22, -0.03), (0.16, -0.2), (0.13, -0.2)], 0.02, 'steel', 'metal')  # nail strip
    s.grip(0.0, -0.02, length=0.12, angle=10, width=0.045, mat='black', slot='metal')
    s.box(-0.035, 0.035, -0.17, -0.13, -0.05, 0.06, 'orange', 'main', bevel=0.008)           # battery
    s.box(-0.036, 0.036, -0.15, -0.14, -0.04, 0.05, 'black', 'metal')
    s.mount('muzzle', (0, 0.0, 0.385))


def firework(s):
    s.tube(-0.12, 0.48, 0.07, 'red_paint', slot='main', y=0.04, sides=12)
    for z in (-0.12, 0.08, 0.46):
        s.tube(z, z + 0.035, 0.076, 'brass', y=0.04, sides=12)
    s.tube(0.48, 0.481, 0.05, 'black', y=0.04, sides=12)
    s.grip(0.05, -0.03, length=0.11, angle=12, width=0.034)
    s.grip(0.25, -0.03, length=0.09, angle=-5, width=0.03)
    s.rail(0.0, 0.2, 0.122)
    s.mount('muzzle', (0, 0.04, 0.48))
    s.mount('optic', (0.122, 0.1))


MODELS = {
    'pistol': pistol, 'glock': glock, 'm1911': m1911, 'deagle': deagle, 'revolver': revolver, 'uzi': uzi,
    'mp5': mp5, 'smg': smg, 'ar15': ar15, 'rifle': rifle, 'ak47': ak47, 'asval': asval, 'scarh': scarh,
    'remington': remington, 'scatter': scatter, 'barrett': barrett, 'm249': m249, 'nailgun': nailgun,
    'firework': firework,
}


def hollow_lance(s):
    """The Easter egg reward: a rifle grown from the Herald's bones around a glowing soul core."""
    import math
    s.side([(-0.1, 0.07), (0.27, 0.07), (0.34, 0.045), (0.34, 0.0), (0.06, -0.02), (-0.1, -0.012)],
           0.05, 'obsidian', 'main')                                                       # receiver
    s.tube(-0.08, 0.66, 0.011, 'glow_purple', y=0.03, sides=8)                              # the soul core
    for k in range(5):                                                                      # glowing vents
        z = -0.04 + k * 0.065
        s.box(-0.0262, 0.0262, 0.022, 0.044, z, z + 0.032, 'glow_purple', 'metal')
    for k in range(4):                                                                      # vertebrae spikes
        z = -0.06 + k * 0.085
        s.side([(z, 0.068), (z + 0.045, 0.068), (z + 0.008, 0.115)], 0.014, 'bone', 'furniture')
    s.tube(0.33, 0.345, 0.036, 'gold', y=0.03, sides=10)
    s.tube(0.345, 0.66, 0.016, 'obsidian', y=0.03, sides=8)                                 # barrel
    for k in range(5):                                                                      # bone ribs
        z = 0.37 + k * 0.055
        s.tube(z, z + 0.022, 0.03 - k * 0.002, 'bone', 'furniture', y=0.03, sides=8)
    s.tube(0.65, 0.665, 0.03, 'gold', y=0.03, sides=10)
    for a in (90, 210, 330):                                                                # three fangs
        x, y = math.cos(math.radians(a)) * 0.026, 0.03 + math.sin(math.radians(a)) * 0.026
        s.tube(0.66, 0.79, 0.011, 'bone', 'furniture', y=y, x=x, sides=6, r1=0.002)
    s.tube(0.7, 0.73, 0.001, 'glow_purple', y=0.03, sides=6, r1=0.017)                      # floating crystal
    s.tube(0.73, 0.77, 0.017, 'glow_purple', y=0.03, sides=6, r1=0.001)
    s.mount('muzzle_end', (0, 0.03, 0.78))
    s.grip(0.02, -0.012, length=0.11, angle=18, width=0.034, mat='bone', slot='furniture')
    s.trigger_guard(0.02, 0.09, -0.014, mat='gold')
    s.magazine(0.13, -0.012, 0.075, depth=0.05, width=0.03, mat='obsidian')                 # soul canister
    s.box(-0.0165, 0.0165, -0.07, -0.025, 0.142, 0.168, 'glow_purple', 'metal')
    s.side([(-0.1, 0.062), (-0.1, -0.012), (-0.3, -0.06), (-0.345, -0.045), (-0.345, 0.05), (-0.22, 0.068)],
           0.036, 'bone', 'furniture')                                                     # spine stock
    s.box(-0.022, 0.022, -0.068, 0.058, -0.36, -0.345, 'obsidian', 'metal', bevel=0.006)


MODELS["hollow_lance"] = hollow_lance
