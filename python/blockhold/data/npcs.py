# ─────────────────────────────────────────────────────────────────────────────
#  NPCs  (placed in the map editor: ANIMALS & NPCS tab → NPC)
#
#  Every NPC you place has its own settings, saved in the map with it. Pick an NPC
#  in the editor (Ctrl+click, or right after placing it) and press N, or click
#  EDIT NPC, to change them. In a game, walk up to an NPC and press E to talk.
#
#    name        shown over their head
#    role        'trader'  has a TRADE button: swaps your items / coins for theirs
#                'quest'   gives you a job, rewards you when it's done
#                'talker'  just has things to say
#    skin, shirt, pants, hair, eyes    colours
#    hat         None, 'cap', 'helmet', 'cowboy', 'beanie', 'hood'
#    beard, goggles, apron             True / False
#    greeting    what they say when you walk up
#    lines       what they say when you pick TALK (one after another)
#    farewell    what they say when you leave
#    trades      [dict(give=item, give_n=how many, get=item, get_n=how many)]
#                item = an item id from items.py (weapons are 'w_' + weapon id) or 'coins'
#    quest       dict(kind='bring' | 'kill' | 'hunt', ...)
#                bring: item, n      bring them n of an item (they take it)
#                kill:  n            kill n zombies after you take the job
#                hunt:  animal, n    kill n animals ('any', 'deer', 'pig', 'chicken')
#                reward_coins, reward_item, reward_n    what you get
#                offer, progress, done                  what they say about it
#                repeat     True = they give the same job again after you finish
# ─────────────────────────────────────────────────────────────────────────────
import copy

ROLES = [('trader', 'Trader'), ('quest', 'Quest giver'), ('talker', 'Talker')]
HATS = [None, 'cap', 'helmet', 'cowboy', 'beanie', 'hood']
QUEST_KINDS = [('bring', 'Bring items'), ('kill', 'Kill zombies'), ('hunt', 'Hunt animals')]
HUNT_TARGETS = ['any', 'deer', 'pig', 'chicken']

# colours offered in the NPC editor
SKIN_COLOURS = ['#f0c8a0', '#e0b08a', '#c68f63', '#a8714a', '#8a5a3a', '#5e3b26']
CLOTH_COLOURS = ['#4f7fb8', '#3a3d42', '#556043', '#8a3a32', '#e8e8e4', '#b5803a', '#6a3a7a', '#2a4a6a',
                 '#c8a050', '#3e4530']
HAIR_COLOURS = [None, '#1d1e22', '#3a2a1a', '#6b4a2b', '#c9a050', '#a8a8a8', '#b84a2a']

PRESETS = {
    'trader': dict(
        name='Butcher Bram', role='trader',
        skin='#e0b08a', shirt='#e8e8e4', pants='#3a3d42', hair='#6b4a2b', eyes='#3a2a1a',
        hat=None, beard=True, goggles=False, apron=True,
        greeting="Fresh meat, fair prices. Got anything for me?",
        lines=["Hunt the deer out past the fences. Cook the meat before you eat it, trust me.",
               "Feathers and hides are worth something to the right buyer. That's me.",
               "Zombies don't eat pork. Lucky pigs."],
        farewell="Come back when your bag's full.",
        trades=[dict(give='raw_meat', give_n=3, get='coins', get_n=60),
                dict(give='hide', give_n=1, get='coins', get_n=80),
                dict(give='feather', give_n=5, get='coins', get_n=40),
                dict(give='coins', give_n=120, get='cooked_meat', get_n=3),
                dict(give='coins', give_n=250, get='padded_vest', get_n=1)],
        quest=None),
    'quest': dict(
        name='Sheriff Hale', role='quest',
        skin='#c68f63', shirt='#b5803a', pants='#2a4a6a', hair='#3a2a1a', eyes='#1d1e22',
        hat='cowboy', beard=False, goggles=False, apron=False,
        greeting="Stranger. This town needs every gun it can get.",
        lines=["The church bell used to ring at noon. Now it just brings them in.",
               "Keep your head down at night. They come in bigger numbers."],
        farewell="Watch your back out there.",
        trades=[],
        quest=dict(kind='kill', item='raw_meat', animal='any', n=15, reward_coins=400, reward_item='combat_helmet',
                   reward_n=1, repeat=False,
                   offer="Clear out 15 of those things and the town's spare helmet is yours.",
                   progress="Keep at it. They won't thin themselves out.",
                   done="That's some fine shooting. Here, you earned this.")),
    'talker': dict(
        name='Old Martha', role='talker',
        skin='#f0c8a0', shirt='#6a3a7a', pants='#3a3d42', hair='#a8a8a8', eyes='#2a5a8a',
        hat='hood', beard=False, goggles=False, apron=False,
        greeting="Oh! A living face. How lovely.",
        lines=["My grandson built that furnace. Coal burns longest, you know.",
               "If you hear the bell, run.",
               "The trader by the square pays well for hides."],
        farewell="Stay safe, dear.",
        trades=[], quest=None),
}

DEFAULT_QUEST = dict(kind='bring', item='raw_meat', animal='any', n=5, reward_coins=150, reward_item=None,
                     reward_n=0, repeat=True,
                     offer="Bring me 5 raw meat and I'll make it worth your while.",
                     progress="Still waiting on that meat.",
                     done="Perfect. Here's your pay.")


def fill_npc(data):
    """An NPC's settings with every field filled in (missing ones from the trader preset)."""
    import uuid
    role = (data or {}).get('role', 'trader')
    out = copy.deepcopy(PRESETS.get(role, PRESETS['trader']))
    for k, v in (data or {}).items():
        out[k] = copy.deepcopy(v)
    if out.get('quest') is not None:
        q = copy.deepcopy(DEFAULT_QUEST)
        q.update(out['quest'])
        out['quest'] = q
    if not out.get('uid'):                  # saved with the map, so it has to be unique for good
        out['uid'] = uuid.uuid4().hex[:10]
    return out


def preset(role, uid=None):
    d = fill_npc(dict(role=role))
    if uid:
        d['uid'] = uid
    return d


def quest_goal_text(q):
    """'Bring 5 Raw meat' / 'Kill 15 zombies' / 'Hunt 3 deer'."""
    from .items import ITEMS
    if q['kind'] == 'bring':
        return f"Bring {q['n']} {ITEMS.get(q['item'], {}).get('name', q['item'])}"
    if q['kind'] == 'kill':
        return f"Kill {q['n']} zombies"
    what = 'animals' if q.get('animal', 'any') == 'any' else q['animal'] + ('s' if q['animal'] != 'deer' else '')
    return f"Hunt {q['n']} {what}"
