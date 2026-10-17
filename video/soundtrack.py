"""Synthesize the soundtrack (118 s, stereo) and mix the voiceover over it.

All of the music is generated here from sines and filtered noise: no samples,
so there is nothing to license. The voiceover lines are vo/line_N.wav, made by
voiceover.py, and the music ducks under them.
"""
import wave
from pathlib import Path

import numpy as np

SR, DUR = 44100, 138.4
t = np.arange(int(SR * DUR)) / SR
L, R = np.zeros_like(t), np.zeros_like(t)
rng = np.random.default_rng(19)
note = lambda m: 440 * 2 ** ((m - 69) / 12)

# One line per scene; keep in step with SCENES in src/Film.jsx.
VO_START = [1.2, 10.2, 29.7, 43.7, 57.7, 72.2, 82.2, 98.7, 111.2, 130.03]
SCENE_EDGE = [9, 28.5, 42.5, 56.5, 71, 81, 97.5, 110, 128.83]


def env(start, attack, decay):
    x = np.clip(t - start, 0, None)
    return np.where(t < start, 0, np.where(x < attack, x / max(attack, 1e-6), np.exp(-(x - attack) / decay)))


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


# A cold, wide pad. Suspended chords, so nothing resolves: Asus2 - Fmaj7 - Csus2 - Gsus4.
chords = [[45, 52, 59, 64], [41, 48, 55, 60], [48, 55, 62, 67], [43, 50, 57, 62]]
for i in range(11):
    s, e = i * 14.0, i * 14.0 + 16.0
    w = np.clip((t - s) / 4.0, 0, 1) * np.clip((e - t) / 4.0, 0, 1)
    for m in chords[i % 4]:
        f = note(m)
        L += 0.048 * w * np.sin(2 * np.pi * f * t)
        R += 0.048 * w * np.sin(2 * np.pi * f * 1.003 * t + 1.4)
        L += 0.011 * w * np.sin(2 * np.pi * f * 2 * t + 0.6)

# A very low drone all the way through: the Moon itself.
L += 0.07 * np.sin(2 * np.pi * note(33) * t) * np.clip(t / 6, 0, 1)
R += 0.07 * np.sin(2 * np.pi * note(33) * 1.002 * t) * np.clip(t / 6, 0, 1)

# Sparse high bells, slow and irregular, like something turning in the cold.
for i, b in enumerate(np.arange(3.0, DUR - 4, 5.5)):
    m = [84, 88, 91, 86, 79][i % 5]
    bell = 0.09 * env(b, 0.005, 1.6) * np.sin(2 * np.pi * note(m) * t)
    L += bell * (0.6 + 0.4 * (i % 2))
    R += bell * (1.0 - 0.4 * (i % 2))

# The year of sunlight sweeping round: a slow rotating filter sweep under scene 3.
x = np.clip(t - 30.0, 0, 11.0)
freq = 110 + 90 * np.sin(2 * np.pi * x / 5.5)
sweep = 0.12 * ((t > 30) & (t < 41)) * np.sin(2 * np.pi * np.cumsum(freq) / SR)
L += sweep
R += np.roll(sweep, 600)

# Permanent shadow: the pad drops away and a deep fifth opens underneath.
w = np.clip((t - 42) / 3, 0, 1) * np.clip((56 - t) / 3, 0, 1)
for m in (28, 35, 47):
    L += 0.05 * w * np.sin(2 * np.pi * note(m) * t)
    R += 0.05 * w * np.sin(2 * np.pi * note(m) * 1.004 * t)

# The scarcity scene: a quiet pulse, counting down the area that is left.
for b in np.arange(57.0, 80.0, 0.85):
    x = np.clip(t - b, 0, None)
    hit = 0.22 * env(b, 0.004, 0.09) * np.sin(2 * np.pi * (44 + 48 * np.exp(-x * 30)) * x)
    L += hit
    R += hit

# The twelve sites arrive as twelve small chimes.
for i in range(12):
    b = 82.5 + i * 0.55
    ping = 0.11 * env(b, 0.003, 0.7) * np.sin(2 * np.pi * note(72 + (i % 4) * 5) * t)
    L += ping * (0.5 + 0.5 * (i % 2))
    R += ping * (1.0 - 0.5 * (i % 2))

# The caveat scene: four tones, each lower than the last, one per terrain grid.
for i, b in enumerate(np.arange(113.0, 126.0, 3.1)):
    m = [69, 64, 60, 55][i % 4]
    tone = 0.1 * env(b, 0.01, 1.3) * np.sin(2 * np.pi * note(m) * t)
    L += tone
    R += 0.9 * tone

# A whoosh into each new scene.
air = lowpass(rng.standard_normal(len(t)), 44)
for s in SCENE_EDGE:
    w = np.exp(-((t - s + 0.4) / 0.34) ** 2)
    L += 0.38 * w * air
    R += 0.38 * w * np.roll(air, 540)

# Voiceover, with the music ducked underneath it.
vo = np.zeros_like(t)
for i, start in enumerate(VO_START, 1):
    f = Path(f"vo/line_{i}.wav")
    if not f.exists():
        continue
    with wave.open(str(f)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2") / 32768
        x = np.interp(np.arange(0, len(x), w.getframerate() / SR), np.arange(len(x)), x)
    a = int(start * SR)
    vo[a:a + len(x)] += x[:len(vo) - a]
speaking = lowpass((np.abs(vo) > 0.01).astype(float), int(0.4 * SR))
duck = 1 - 0.68 * np.clip(speaking * 3, 0, 1)
peak = max(np.abs(L).max(), np.abs(R).max())
L = L / peak * 0.6 * duck + 0.92 * vo
R = R / peak * 0.6 * duck + 0.92 * vo

fade = np.clip(t / 1.5, 0, 1) * np.clip((DUR - t) / 3.0, 0, 1)
st = np.stack([L, R], 1) * fade[:, None]
st = st / np.abs(st).max() * 0.86
Path("public").mkdir(exist_ok=True)
with wave.open("public/soundtrack.wav", "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes((st * 32767).astype("<i2").tobytes())
print("public/soundtrack.wav")
