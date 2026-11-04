# ─────────────────────────────────────────────────────────────────────────────
#  CLASSES, LEVELS AND THE SKILL TREE
#
#  Pick a class on the main menu. It gives you a passive bonus, its Q ability, and
#  its own branch of the skill tree. Kill zombies, clear waves and finish NPC jobs
#  for XP; every level gives a skill point to spend in the tree (press K). Like a
#  Project Zomboid character, your level only lasts for this run.
#
#  CLASSES
#    name, colour, desc   shown on the menu
#    ability              the Q ability (id in data/abilities.py)
#    passive              what it says; apply(player) does it at the start of a run
#    branch               the name of its own column in the skill tree
#
#  SKILLS (in the tree, 4 columns x 4 tiers)
#    branch     'combat', 'survival', 'defense', or 'class' (the class's own column)
#    cls        for 'class' skills: which class it belongs to
#    tier       1-4 (row). A skill needs at least 1 point in the skill above it.
#    ranks      how many points it takes
#    desc       what one point does
#    apply(p)   called once per point
# ─────────────────────────────────────────────────────────────────────────────

MAX_LEVEL = 50


def xp_to_next(level):
    """XP needed to go from `level` to the next one."""
    return 80 + 45 * (level - 1)


# XP for the things you do (kills give the zombie's score: 10 for a shambler ... 800 for a boss)
XP_WAVE = 25          # x the wave number, when a wave is cleared
XP_QUEST = 150        # for finishing an NPC's job
XP_SHOVE_KILL = 5     # extra for killing a zombie you knocked down


def _add(attr, amount):
    def f(p):
        setattr(p, attr, getattr(p, attr) + amount)
    return f


def _mul(attr, k):
    def f(p):
        setattr(p, attr, getattr(p, attr) * k)
    return f


def _health(n):
    def f(p):
        p.max_health += n
        p.health += n
    return f


def _armor(n):
    def f(p):
        p.base_armor = min(0.6, p.base_armor + n)
    return f


def _both(*fs):
    def f(p):
        for g in fs:
            g(p)
    return f


CLASSES = {
    'soldier': dict(
        name='Soldier', colour='#d9912b', ability='adrenaline', branch='Firearms',
        desc='All-round gunfighter. Reloads fast and hits hard.',
        passive='+10% damage, 15% faster reloads.',
        apply=_both(_mul('damage_mult', 1.10), _mul('reload_mult', 0.85))),
    'brawler': dict(
        name='Brawler', colour='#d64541', ability='shockwave', branch='Brawn',
        desc='Gets up close. Shoves send zombies flying and melee hits hurt.',
        passive='+30 health, shoves twice as strong, +25% melee damage.',
        apply=_both(_health(30), _mul('shove_power', 2.0), _mul('melee_mult', 1.25))),
    'scout': dict(
        name='Scout', colour='#b37bff', ability='blink', branch='Recon',
        desc='Fast and slippery. Hard to pin down.',
        passive='+12% speed, +2 shoves before you tire, +20% headshot damage.',
        apply=_both(_mul('speed_mult', 1.12), _add('shove_stamina', 2), _mul('headshot_mult', 1.2))),
    'medic': dict(
        name='Medic', colour='#2e9e6a', ability='field_heal', branch='Medicine',
        desc='Keeps everyone standing. Patches up fast.',
        passive='Bandages and medkits 40% faster, +1 health per second.',
        apply=_both(_mul('heal_speed', 1.4), _add('regen', 1.0))),
    'engineer': dict(
        name='Engineer', colour='#1197b0', ability='sentry', branch='Engineering',
        desc='Builds a fortress. Barricades and turrets do the work.',
        passive='Barricades and turrets have +50% health.',
        apply=_mul('barricade_hp_mult', 1.5)),
}
DEFAULT_CLASS = 'soldier'

BRANCHES = [('combat', 'Combat'), ('survival', 'Survival'), ('defense', 'Defense'), ('class', None)]

SKILLS = {
    # ── combat ──
    'marksman': dict(branch='combat', tier=1, ranks=3, name='Marksman', desc='+6% damage with every weapon.',
                     apply=_mul('damage_mult', 1.06)),
    'quickhands': dict(branch='combat', tier=2, ranks=3, name='Quick Hands', desc='8% faster reloads.',
                       apply=_mul('reload_mult', 0.92)),
    'deadeye': dict(branch='combat', tier=3, ranks=2, name='Deadeye', desc='+20% headshot damage.',
                    apply=_mul('headshot_mult', 1.2)),
    'trigger': dict(branch='combat', tier=4, ranks=2, name='Hair Trigger', desc='+6% fire rate.',
                    apply=_mul('fire_rate_mult', 1.06)),
    # ── survival ──
    'tough': dict(branch='survival', tier=1, ranks=4, name='Tough', desc='+15 max health.', apply=_health(15)),
    'thickskin': dict(branch='survival', tier=2, ranks=3, name='Thick Skin', desc='Take 4% less damage.',
                      apply=_armor(0.04)),
    'secondwind': dict(branch='survival', tier=3, ranks=3, name='Second Wind', desc='+0.5 health per second.',
                       apply=_add('regen', 0.5)),
    'fieldmedic': dict(branch='survival', tier=4, ranks=2, name='First Aid', desc='Use bandages and kits 20% faster.',
                       apply=_mul('heal_speed', 1.2)),
    # ── defense: the shove (F) ──
    'shove': dict(branch='defense', tier=1, ranks=3, name='Strong Arms',
                  desc='Shoves push 25% further and knock zombies down longer.', apply=_mul('shove_power', 1.25)),
    'stamina': dict(branch='defense', tier=2, ranks=3, name='Stamina', desc='+1 shove before you get tired.',
                    apply=_add('shove_stamina', 1)),
    'bash': dict(branch='defense', tier=3, ranks=2, name='Bash', desc='Shoves do +15 damage.',
                 apply=_add('shove_damage', 15)),
    'sweep': dict(branch='defense', tier=4, ranks=2, name='Sweep', desc='Shoves hit a wider arc, and further.',
                  apply=_both(_add('shove_arc', 0.15), _add('shove_range', 0.4))),
    # ── class branches ──
    'sol_rapid': dict(branch='class', cls='soldier', tier=1, ranks=3, name='Rapid Fire', desc='+5% fire rate.',
                      apply=_mul('fire_rate_mult', 1.05)),
    'sol_drill': dict(branch='class', cls='soldier', tier=2, ranks=2, name='Drilled',
                      desc='Adrenaline comes back 15% sooner.', apply=_mul('ability_cd_mult', 0.85)),
    'sol_vest': dict(branch='class', cls='soldier', tier=3, ranks=2, name='Kevlar Lining', desc='Take 5% less damage.',
                     apply=_armor(0.05)),
    'sol_vet': dict(branch='class', cls='soldier', tier=4, ranks=1, name='Veteran', desc='+15% damage.',
                    apply=_mul('damage_mult', 1.15)),
    'bra_fist': dict(branch='class', cls='brawler', tier=1, ranks=3, name='Iron Fist', desc='+15% melee damage.',
                     apply=_mul('melee_mult', 1.15)),
    'bra_pound': dict(branch='class', cls='brawler', tier=2, ranks=2, name='Ground and Pound',
                      desc='Knocked-down zombies take +40% damage.', apply=_mul('downed_dmg_mult', 1.4)),
    'bra_slam': dict(branch='class', cls='brawler', tier=3, ranks=2, name='Earthshaker',
                     desc='Shockwave comes back 15% sooner.', apply=_mul('ability_cd_mult', 0.85)),
    'bra_tank': dict(branch='class', cls='brawler', tier=4, ranks=1, name='Juggernaut',
                     desc='+50 max health, and shoves cost no stamina when you are below half health.',
                     apply=_both(_health(50), _add('rage', 1))),
    'sco_swift': dict(branch='class', cls='scout', tier=1, ranks=3, name='Light Feet', desc='+5% speed.',
                      apply=_mul('speed_mult', 1.05)),
    'sco_blink': dict(branch='class', cls='scout', tier=2, ranks=2, name='Slipstream', desc='Blink comes back 20% sooner.',
                      apply=_mul('ability_cd_mult', 0.8)),
    'sco_eye': dict(branch='class', cls='scout', tier=3, ranks=2, name='Hunter', desc='+25% headshot damage.',
                    apply=_mul('headshot_mult', 1.25)),
    'sco_learn': dict(branch='class', cls='scout', tier=4, ranks=1, name='Quick Study', desc='+30% XP.',
                      apply=_mul('xp_mult', 1.3)),
    'med_hands': dict(branch='class', cls='medic', tier=1, ranks=3, name='Steady Hands',
                      desc='Bandages and kits 15% faster.', apply=_mul('heal_speed', 1.15)),
    'med_aura': dict(branch='class', cls='medic', tier=2, ranks=2, name='Triage',
                     desc='Field Heal heals 30% more.', apply=_mul('heal_power', 1.3)),
    'med_cd': dict(branch='class', cls='medic', tier=3, ranks=2, name='Prepared',
                   desc='Field Heal comes back 15% sooner.', apply=_mul('ability_cd_mult', 0.85)),
    'med_life': dict(branch='class', cls='medic', tier=4, ranks=1, name='Lifeline', desc='+2 health per second.',
                     apply=_add('regen', 2.0)),
    'eng_walls': dict(branch='class', cls='engineer', tier=1, ranks=3, name='Reinforced',
                      desc='Barricades +20% health.', apply=_mul('barricade_hp_mult', 1.2)),
    'eng_sentry': dict(branch='class', cls='engineer', tier=2, ranks=2, name='Long Shift',
                       desc='Sentries last 10 seconds longer.', apply=_add('sentry_time', 10)),
    'eng_cd': dict(branch='class', cls='engineer', tier=3, ranks=2, name='Spare Parts',
                   desc='Sentry comes back 15% sooner.', apply=_mul('ability_cd_mult', 0.85)),
    'eng_twin': dict(branch='class', cls='engineer', tier=4, ranks=1, name='Twin Sentries',
                     desc='Sentry drops two turrets.', apply=_add('sentry_count', 1)),
}


def tree_for(cls):
    """The skills in this class's tree: {branch: [skill ids by tier]}"""
    out = {}
    for b, _ in BRANCHES:
        out[b] = sorted([k for k, s in SKILLS.items() if s['branch'] == b and (b != 'class' or s.get('cls') == cls)],
                        key=lambda k: SKILLS[k]['tier'])
    return out
