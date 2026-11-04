"""Sound effects, synthesised in pure Python the first time the game runs.

Want your own sounds? Put a .wav or .ogg file in the `sounds/` folder next to
main.py, named after the effect (for example `sounds/shoot_pistol.wav`), and it
will be used instead of the generated one.
"""
import math
import random
import struct
import wave
from pathlib import Path

RATE = 22050
VERSION = 8           # bump when sounds are added or changed (regenerates the cache)
from .paths import CUSTOM_SOUND_DIRS, SOUND_CACHE as CACHE_DIR


# ── tiny synth ───────────────────────────────────────────────────────────────
def _buf(dur):
    return [0.0] * int(RATE * dur)


def _gain(t, dur, vol, attack):
    if t < attack:
        return vol * t / attack
    return vol * (0.0001 / vol) ** ((t - attack) / max(1e-4, dur - attack))


def noise(dur, freq=1000, kind='low', vol=0.5, attack=0.002, sweep=None, seed=1):
    rnd = random.Random(seed).random
    out = _buf(dur)
    lp = lp2 = 0.0
    for i in range(len(out)):
        t = i / RATE
        f = freq * (sweep / freq) ** (t / dur) if sweep else freq
        a = min(1.0, 2 * math.pi * f / RATE)
        x = rnd() * 2 - 1
        lp += a * (x - lp)
        if kind == 'low':
            y = lp
        elif kind == 'high':
            y = x - lp
        else:  # band
            lp2 += a * 0.5 * (lp - lp2)
            y = (lp - lp2) * 2
        out[i] = y * _gain(t, dur, vol, attack)
    return out


def tone(freq, dur, shape='square', vol=0.2, to=None, attack=0.005):
    out = _buf(dur)
    phase = 0.0
    for i in range(len(out)):
        t = i / RATE
        f = freq * (to / freq) ** (t / dur) if to else freq
        phase += f / RATE
        p = phase % 1
        if shape == 'square':
            y = 1 if p < 0.5 else -1
        elif shape == 'saw':
            y = p * 2 - 1
        elif shape == 'triangle':
            y = 4 * abs(p - 0.5) - 1
        else:
            y = math.sin(phase * 2 * math.pi)
        out[i] = y * _gain(t, dur, vol, attack)
    return out


def mix(*parts):
    """parts: buffers or (delay_seconds, buffer)"""
    parts = [(0, p) if isinstance(p, list) else p for p in parts]
    length = max(int(d * RATE) + len(b) for d, b in parts)
    out = [0.0] * length
    for d, b in parts:
        o = int(d * RATE)
        for i, v in enumerate(b):
            out[o + i] += v
    return out


def seq(notes, dur, shape='triangle', vol=0.15, gap=None):
    return mix(*[(i * (gap or dur * 0.5), tone(f, dur, shape, vol)) for i, f in enumerate(notes)])


# ── gunshot designer ─────────────────────────────────────────────────────────
#  A real gunshot is several sounds on top of each other: the action clicking,
#  a sharp crack, the "punch" of the muzzle blast and a long echo off the
#  surroundings. gunshot() builds all four; the numbers below shape each gun.

def lowpass(buf, freq):
    a = min(1.0, 2 * math.pi * freq / RATE)
    y, out = 0.0, []
    for v in buf:
        y += a * (v - y)
        out.append(y)
    return out


def highpass(buf, freq):
    lp = lowpass(buf, freq)
    return [v - l for v, l in zip(buf, lp)]


def echo(buf, delay, feedback=0.35, count=3, damp=2500):
    """Repeat a sound a few times, quieter and duller each time (a room / outdoor slap-back)."""
    out = list(buf) + [0.0] * int(delay * RATE * count)
    tap = buf
    for k in range(1, count + 1):
        tap = lowpass(tap, damp / k)
        o = int(delay * RATE * k)
        g = feedback ** k
        for i, v in enumerate(tap):
            out[o + i] += v * g
    return out


def saturate(buf, drive=1.6):
    """Soft clipping: makes shots sound loud and punchy instead of just clipped."""
    t = math.tanh(drive)
    return [math.tanh(v * drive) / t for v in buf]


def env_noise(dur, decay, seed, vol=1.0):
    rnd = random.Random(seed).random
    n = int(RATE * dur)
    return [(rnd() * 2 - 1) * vol * math.exp(-i / RATE / decay) for i in range(n)]


def thump(freq, to, dur, vol):
    out, phase = [], 0.0
    n = int(RATE * dur)
    for i in range(n):
        t = i / RATE
        f = freq * (to / freq) ** (t / dur)
        phase += f / RATE
        out.append(math.sin(phase * math.tau) * vol * math.exp(-t / (dur * 0.35)))
    return out


def gunshot(crack=1.0, crack_tone=6000, body=1.0, body_tone=1800, body_decay=0.05, punch=1.0, punch_freq=110,
            tail=0.5, tail_decay=0.35, tail_tone=900, echo_delay=0.11, click=0.3, drive=1.8, seed=1):
    parts = []
    if click:
        parts.append(highpass(env_noise(0.012, 0.003, seed + 1, click), 3000))
    if crack:
        parts.append(highpass(env_noise(0.03, 0.006, seed + 2, crack), crack_tone * 0.5))
    if body:
        parts.append(lowpass(env_noise(body_decay * 6, body_decay, seed + 3, body), body_tone))
    if punch:
        parts.append(thump(punch_freq, punch_freq * 0.4, 0.18, punch))
    shot = saturate(mix(*parts), drive)
    if tail:
        t = lowpass(env_noise(tail_decay * 3, tail_decay * 0.7, seed + 4, tail * 0.5), tail_tone)
        shot = mix(shot, (0.01, t))
    return echo(shot, echo_delay, 0.3, 2) if echo_delay else shot


def mech(clicks, seed=5):
    """Metal parts moving: a list of (time, brightness, loudness) clicks."""
    parts = []
    for i, (t, tone_hz, vol) in enumerate(clicks):
        n = highpass(env_noise(0.04, 0.008, seed + i, vol), tone_hz)
        ring = [math.sin(k / RATE * math.tau * tone_hz * 1.3) * vol * 0.25 * math.exp(-k / RATE / 0.01)
                for k in range(int(RATE * 0.04))]
        parts.append((t, mix(n, ring)))
    return mix(*parts)


# ── the sound list ───────────────────────────────────────────────────────────
RECIPES = {
    # guns (each weapon's `sound` field picks one of these: shoot_<sound>)
    'shoot_pistol': lambda: gunshot(crack=0.8, body=0.8, body_tone=2200, punch=0.6, punch_freq=150, tail=0.35,
                                    tail_decay=0.25, echo_delay=0.09, seed=10),
    'shoot_heavy_pistol': lambda: gunshot(crack=1.0, body=1.0, body_tone=1500, body_decay=0.07, punch=1.0,
                                          punch_freq=95, tail=0.55, tail_decay=0.45, echo_delay=0.12, seed=20),
    'shoot_smg': lambda: gunshot(crack=0.7, crack_tone=7000, body=0.6, body_tone=2600, body_decay=0.03, punch=0.45,
                                 punch_freq=170, tail=0.25, tail_decay=0.18, echo_delay=0.07, click=0.4, seed=30),
    'shoot_rifle': lambda: gunshot(crack=1.0, crack_tone=7500, body=0.8, body_tone=2400, body_decay=0.045,
                                   punch=0.7, punch_freq=120, tail=0.55, tail_decay=0.5, tail_tone=1100,
                                   echo_delay=0.13, seed=40),
    'shoot_battle_rifle': lambda: gunshot(crack=1.0, crack_tone=6000, body=1.0, body_tone=1700, body_decay=0.06,
                                          punch=1.0, punch_freq=85, tail=0.7, tail_decay=0.6, tail_tone=850,
                                          echo_delay=0.14, drive=2.2, seed=50),
    'shoot_shotgun': lambda: mix(gunshot(crack=0.6, body=1.2, body_tone=1200, body_decay=0.09, punch=1.2,
                                         punch_freq=70, tail=0.8, tail_decay=0.55, tail_tone=700, echo_delay=0.15,
                                         drive=2.4, seed=60),
                                 (0.32, mech([(0, 1800, 0.35), (0.12, 1200, 0.45)], seed=61))),
    'shoot_scatter': lambda: gunshot(crack=0.5, body=1.3, body_tone=1000, body_decay=0.1, punch=1.3, punch_freq=60,
                                     tail=0.8, tail_decay=0.5, tail_tone=650, echo_delay=0.15, drive=2.4, seed=65),
    'shoot_sniper': lambda: gunshot(crack=1.2, crack_tone=5000, body=1.2, body_tone=1300, body_decay=0.09,
                                    punch=1.4, punch_freq=55, tail=1.0, tail_decay=1.0, tail_tone=600,
                                    echo_delay=0.22, drive=2.6, seed=70),
    'shoot_suppressed': lambda: mix(lowpass(env_noise(0.09, 0.018, 81, 0.9), 1300),
                                    thump(240, 120, 0.06, 0.25),
                                    mech([(0.0, 3500, 0.45), (0.035, 2500, 0.4)], seed=82)),
    'shoot_nailgun': lambda: mix(lowpass(env_noise(0.07, 0.015, 91, 0.6), 2500),
                                 mech([(0.0, 4500, 0.5), (0.03, 3000, 0.35)], seed=92)),
    'shoot_railspike': lambda: mix(tone(1800, 0.35, 'saw', vol=0.2, to=120), noise(0.25, 5000, 'high', vol=0.3),
                                   (0.0, thump(90, 40, 0.3, 0.6))),
    'shoot_firework': lambda: mix(noise(0.45, 800, 'band', vol=0.6, sweep=3000), thump(80, 50, 0.2, 0.4)),
    'shoot_spit': lambda: noise(0.12, 900, 'band', vol=0.35, sweep=400),
    'shoot_blink': lambda: tone(500, 0.08, 'sine', vol=0.18, to=900),
    'shoot_blaster': lambda: mix(tone(1400, 0.12, 'square', vol=0.12, to=300), tone(700, 0.1, 'sine', vol=0.15, to=180)),
    'shoot_crossbow': lambda: mix(tone(220, 0.12, 'saw', vol=0.15, to=90), noise(0.06, 3000, 'high', vol=0.15)),
    'scream': lambda: mix(tone(900, 0.9, 'saw', vol=0.12, to=1400), noise(0.9, 2500, 'band', vol=0.18, sweep=900)),
    'bloat_pop': lambda: mix(lowpass(env_noise(0.5, 0.12, 131, 0.9), 700), thump(60, 35, 0.25, 0.6)),
    'leap': lambda: mix(noise(0.25, 700, 'band', vol=0.35, sweep=1500), tone(260, 0.2, 'saw', vol=0.1, to=420)),
    # weapon handling
    'reload_out': lambda: mech([(0, 2200, 0.5), (0.05, 900, 0.35)], seed=101),
    'reload_in': lambda: mix(mech([(0, 1500, 0.7), (0.03, 3200, 0.4)], seed=102),
                             lowpass(env_noise(0.06, 0.012, 103, 0.5), 600)),
    'reload_rack': lambda: mech([(0, 2600, 0.55), (0.09, 1800, 0.65)], seed=104),
    'pump': lambda: mech([(0, 1500, 0.5), (0.13, 1100, 0.6)], seed=105),
    'equip': lambda: mix(lowpass(env_noise(0.15, 0.04, 106, 0.3), 900), (0.08, mech([(0, 2400, 0.35)], seed=107))),
    'reload': lambda: mix(tone(300, 0.05, vol=0.12), (0.12, tone(500, 0.05, vol=0.12))),
    'empty': lambda: mech([(0, 3800, 0.45)], seed=108),
    'casing': lambda: mix(*[(t, [math.sin(k / RATE * math.tau * f) * 0.12 * math.exp(-k / RATE / 0.03)
                                 for k in range(int(RATE * 0.08))]) for t, f in ((0, 5200), (0.07, 4700), (0.12, 5600))]),
    # movement
    'step': lambda: lowpass(env_noise(0.08, 0.018, 111, 0.7), 500),
    'land': lambda: mix(lowpass(env_noise(0.18, 0.04, 112, 0.9), 350), thump(70, 40, 0.15, 0.5)),
    'slide': lambda: lowpass(highpass(noise(0.6, 2000, 'band', vol=0.5, attack=0.03, sweep=600), 300), 3000),
    'mantle': lambda: mix(lowpass(env_noise(0.2, 0.05, 113, 0.6), 800), (0.12, lowpass(env_noise(0.1, 0.02, 114, 0.6), 400))),
    'swing': lambda: noise(0.15, 600, 'band', vol=0.4, attack=0.03, sweep=1800),
    'hit': lambda: tone(520, 0.05, vol=0.15, to=300),
    'headshot': lambda: tone(1200, 0.08, vol=0.18, to=1600),
    'thud': lambda: noise(0.08, 400, vol=0.6),

    'hurt': lambda: tone(160, 0.18, 'saw', vol=0.25, to=80),
    'coin': lambda: mix(tone(988, 0.06, vol=0.1), (0.06, tone(1319, 0.12, vol=0.1))),
    'heal': lambda: mix(tone(523, 0.1, 'sine', vol=0.2), (0.08, tone(784, 0.15, 'sine', vol=0.2))),
    'buy': lambda: seq([660, 880, 1320], 0.1, 'square', 0.12, gap=0.08),
    'deny': lambda: tone(200, 0.15, vol=0.15),
    'groan': lambda: tone(110, 0.5, 'saw', vol=0.08, to=60),
    'spit': lambda: noise(0.2, 900, 'band', vol=0.4, sweep=300),
    'boom': lambda: mix(noise(0.9, 900, vol=1.0, sweep=60), tone(70, 0.6, 'sine', vol=0.6, to=30)),
    'mine_hit': lambda: mix(highpass(env_noise(0.12, 0.022, 121, 0.75), 1400), tone(1900, 0.08, 'sine', vol=0.1, to=1650),
                            mech([(0, 2700, 0.35)], seed=122)),
    'mine_break': lambda: mix(lowpass(env_noise(0.55, 0.16, 123, 0.9), 900), thump(90, 45, 0.25, 0.5),
                              (0.07, lowpass(env_noise(0.35, 0.08, 124, 0.5), 2200))),
    'craft': lambda: mix(mech([(0, 2400, 0.6)], seed=125), (0.15, mech([(0, 2200, 0.6)], seed=126)),
                         (0.3, mech([(0, 2700, 0.6)], seed=127)), (0.45, seq([660, 990], 0.12, 'triangle', 0.12))),
    'chop': lambda: mix(lowpass(env_noise(0.16, 0.03, 131, 0.9), 1300), thump(150, 90, 0.12, 0.55),
                        (0.01, highpass(env_noise(0.05, 0.01, 132, 0.35), 2500))),
    'build_place': lambda: mix(lowpass(env_noise(0.3, 0.06, 133, 0.8), 700), thump(95, 55, 0.22, 0.7),
                               (0.16, mech([(0, 1900, 0.55)], seed=134)), (0.3, mech([(0, 2100, 0.5)], seed=135))),
    'barricade_hit': lambda: mix(lowpass(env_noise(0.2, 0.04, 136, 0.9), 900), thump(120, 70, 0.14, 0.6),
                                 (0.02, highpass(env_noise(0.08, 0.015, 137, 0.3), 1800))),
    'barricade_break': lambda: mix(lowpass(env_noise(0.7, 0.2, 138, 0.9), 1100), thump(80, 40, 0.3, 0.6),
                                   (0.05, highpass(env_noise(0.25, 0.05, 139, 0.5), 1500)),
                                   (0.18, lowpass(env_noise(0.3, 0.06, 140, 0.6), 2000))),
    'powerup_drop': lambda: seq([1046, 1318, 1568, 2093], 0.08, 'sine', 0.12, gap=0.045),
    'powerup': lambda: seq([440, 554, 659, 880], 0.12, 'square', 0.1, gap=0.06),
    'blink': lambda: tone(300, 0.2, 'sine', vol=0.2, to=1500),
    'death': lambda: tone(200, 0.25, 'square', vol=0.08, to=60),
    'wave_start': lambda: mix(tone(220, 0.6, 'saw', vol=0.15), (0.25, tone(330, 0.6, 'saw', vol=0.1))),
    'wave_clear': lambda: seq([523, 659, 784, 1046], 0.25, 'triangle', 0.18, gap=0.1),
    'boss_roar': lambda: mix(tone(70, 1.4, 'saw', vol=0.35, to=40), noise(1.2, 300, vol=0.5)),
    'game_over': lambda: seq([392, 330, 262, 196], 0.4, 'triangle', 0.18, gap=0.25),
}


def _write(path, samples):
    peak = max(1.0, max(abs(s) for s in samples))
    data = b''.join(struct.pack('<h', int(max(-1, min(1, s / peak)) * 32000)) for s in samples)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data)


def ensure_generated():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    marker = CACHE_DIR / f'v{VERSION}'
    if marker.exists():
        return
    for name, recipe in RECIPES.items():
        _write(CACHE_DIR / f'{name}.wav', recipe())
    marker.touch()


class Sounds:
    VOICES = 4      # how many copies of each sound can overlap

    def __init__(self):
        from ursina import application
        from panda3d.core import Filename
        ensure_generated()
        self.volume = 0.5
        self.muted = False
        self.pool = {}
        self.next = {}
        loader = application.base.loader
        for name in RECIPES:
            path = None
            for folder in reversed(CUSTOM_SOUND_DIRS):        # the first folder in the list wins
                for ext in ('.wav', '.ogg'):
                    if (folder / f'{name}{ext}').exists():
                        path = folder / f'{name}{ext}'
            path = path or CACHE_DIR / f'{name}.wav'
            try:
                self.pool[name] = [loader.loadSfx(Filename.fromOsSpecific(str(path))) for _ in range(self.VOICES)]
            except Exception as e:   # no audio device etc.
                print('could not load sound', name, e)
            self.next[name] = 0

    def play(self, name, volume=1.0, pitch=1.0):
        if self.muted or name not in self.pool:
            return
        voices = self.pool[name]
        s = voices[self.next[name]]
        self.next[name] = (self.next[name] + 1) % len(voices)
        s.setVolume(self.volume * volume)
        s.setPlayRate(pitch)
        s.play()

    def shoot(self, weapon, sound=None):
        self.play('shoot_' + (sound or weapon.get('sound', 'pistol')), pitch=0.95 + random.random() * 0.1)

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted
