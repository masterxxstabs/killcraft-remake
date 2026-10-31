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
VERSION = 2
HERE = Path(__file__).resolve().parent
CUSTOM_DIR = HERE.parent / 'sounds'
CACHE_DIR = HERE / '_generated_sounds'


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


# ── the sound list ───────────────────────────────────────────────────────────
RECIPES = {
    'shoot_pistol': lambda: mix(noise(0.12, 2200, vol=0.6, sweep=400), tone(180, 0.08, vol=0.2, to=60)),
    'shoot_nailgun': lambda: mix(noise(0.06, 3500, 'band', vol=0.5), tone(900, 0.04, vol=0.08, to=400)),
    'shoot_scatter': lambda: mix(noise(0.3, 1400, vol=0.9, sweep=150), tone(90, 0.2, vol=0.35, to=40)),
    'shoot_railspike': lambda: mix(tone(1800, 0.35, 'saw', vol=0.2, to=120), noise(0.25, 5000, 'high', vol=0.3)),
    'shoot_rifle': lambda: mix(noise(0.18, 3000, vol=0.75, sweep=300), tone(140, 0.12, vol=0.25, to=50),
                               (0.03, noise(0.25, 600, vol=0.25, sweep=120))),
    'shoot_suppressed': lambda: mix(noise(0.08, 900, 'band', vol=0.45, sweep=300), tone(220, 0.05, 'sine', vol=0.1, to=90)),
    'shoot_sniper': lambda: mix(noise(0.6, 2200, vol=1.0, sweep=80), tone(60, 0.5, 'sine', vol=0.6, to=28),
                                (0.08, noise(0.9, 500, vol=0.35, sweep=60))),
    'shoot_firework': lambda: noise(0.4, 800, 'band', vol=0.6, sweep=3000),
    'swing': lambda: noise(0.15, 600, 'band', vol=0.4, attack=0.03, sweep=1800),
    'hit': lambda: tone(520, 0.05, vol=0.15, to=300),
    'headshot': lambda: tone(1200, 0.08, vol=0.18, to=1600),
    'thud': lambda: noise(0.08, 400, vol=0.6),
    'reload': lambda: mix(tone(300, 0.05, vol=0.12), (0.12, tone(500, 0.05, vol=0.12))),
    'empty': lambda: tone(1400, 0.03, vol=0.1),
    'hurt': lambda: tone(160, 0.18, 'saw', vol=0.25, to=80),
    'coin': lambda: mix(tone(988, 0.06, vol=0.1), (0.06, tone(1319, 0.12, vol=0.1))),
    'heal': lambda: mix(tone(523, 0.1, 'sine', vol=0.2), (0.08, tone(784, 0.15, 'sine', vol=0.2))),
    'buy': lambda: seq([660, 880, 1320], 0.1, 'square', 0.12, gap=0.08),
    'deny': lambda: tone(200, 0.15, vol=0.15),
    'groan': lambda: tone(110, 0.5, 'saw', vol=0.08, to=60),
    'spit': lambda: noise(0.2, 900, 'band', vol=0.4, sweep=300),
    'boom': lambda: mix(noise(0.9, 900, vol=1.0, sweep=60), tone(70, 0.6, 'sine', vol=0.6, to=30)),
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
    CACHE_DIR.mkdir(exist_ok=True)
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
            for ext in ('.wav', '.ogg'):
                if (CUSTOM_DIR / f'{name}{ext}').exists():
                    path = CUSTOM_DIR / f'{name}{ext}'
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

    def shoot(self, weapon):
        self.play('shoot_' + weapon.get('sound', 'pistol'), pitch=0.95 + random.random() * 0.1)

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted
