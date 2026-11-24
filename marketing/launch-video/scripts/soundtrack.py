"""Builds public/audio/soundtrack.wav: a music bed and the UI sounds, all synthesised.

Every cue comes from src/timeline.json (frames at 60 fps), so a click in the picture
and a click in the sound are the same number. No samples, no licences: run
`python3 scripts/soundtrack.py` after changing the timeline.
"""
import json
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

ROOT = Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "src/timeline.json").read_text())
SR = 48000
FPS = T["fps"]
DUR = T["total"] / FPS
N = int(SR * DUR)
rng = np.random.default_rng(7)

BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT


def sec(frame):
    return frame / FPS


def t_(n):
    return np.arange(n) / SR


def lp(x, hz, order=2):
    return sosfilt(butter(order, hz, "low", fs=SR, output="sos"), x)


def hp(x, hz, order=2):
    return sosfilt(butter(order, hz, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


def place(buf, clip, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(clip))
    buf[i:j] += clip[: j - i] * gain


def env(n, a, r):
    e = np.ones(n)
    ai = max(1, int(a * SR))
    ri = max(1, int(r * SR))
    e[:ai] = np.linspace(0, 1, ai)
    e[-ri:] *= np.exp(-np.linspace(0, 6, ri))
    return e


def hz(midi):
    return 440 * 2 ** ((midi - 69) / 12)


# Dm – B♭ – F – C, one chord a bar, as MIDI notes.
CHORDS = [[50, 57, 62, 65, 69], [46, 53, 58, 62, 65], [41, 53, 57, 60, 65], [48, 55, 60, 64, 67]]

music = np.zeros(N)

# Pad: detuned saws, low-passed, swelling with each chord.
for b in range(int(DUR / BAR) + 1):
    start = b * BAR
    chord = CHORDS[b % 4]
    n = int((BAR + 1.2) * SR)
    tt = t_(n)
    tone = np.zeros(n)
    for m in chord:
        for det in (-0.08, 0.0, 0.08):
            f = hz(m + det)
            tone += 2 * ((tt * f) % 1) - 1
    tone = lp(tone / (len(chord) * 3), 900)
    e = np.minimum(1, tt / 0.6) * np.exp(-np.maximum(0, tt - BAR) * 3)
    place(music, tone * e, start, 0.22)

# Sub bass on the chord root.
for b in range(int(DUR / BAR) + 1):
    root = CHORDS[b % 4][0] - 12
    n = int(BAR * SR)
    tt = t_(n)
    place(music, np.sin(2 * np.pi * hz(root) * tt) * env(n, 0.02, 0.4), b * BAR, 0.32 if b * BAR > sec(T["music"]["beatFrom"]) else 0.12)


def pluck(f, dur=0.5):
    n = int(dur * SR)
    tt = t_(n)
    x = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) + 0.12 * np.sin(2 * np.pi * 3 * f * tt)
    return x * np.exp(-tt * 7) * np.minimum(1, tt / 0.004)


# Arpeggio in eighths, up an octave, from the problem scene on; sparse in the hook.
step = BEAT / 2
k = 0
t0 = 0.0
while t0 < DUR - 0.5:
    chord = CHORDS[int(t0 / BAR) % 4]
    note = chord[[1, 2, 3, 4, 3, 2][k % 6]] + 12
    if t0 < sec(T["music"]["beatFrom"]):
        if k % 4 == 0:
            place(music, pluck(hz(note), 0.9), t0, 0.12)
    elif t0 < sec(T["music"]["drop"]):
        place(music, pluck(hz(note)), t0, 0.10 if t0 < sec(T["music"]["beatFrom"]) else 0.13)
    k += 1
    t0 += step


def kick():
    n = int(0.35 * SR)
    tt = t_(n)
    f = 45 + 90 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)


def hat():
    n = int(0.06 * SR)
    return hp(rng.standard_normal(n), 7000) * np.exp(-t_(n) * 70)


# Beat from "Meet Tafheem" to the logo; hats join once the analysis starts streaming.
beat_from = sec(T["music"]["beatFrom"])
beat_to = sec(T["music"]["drop"]) - 0.05
b = 0
t0 = beat_from
while t0 < beat_to:
    if b % 2 == 0:
        place(music, kick(), t0, 0.5)
    if t0 > sec(T["shots"][5][1]):
        place(music, hat(), t0 + BEAT / 2, 0.08)
    b += 1
    t0 += BEAT

# Ending: a held Dm chord after the logo lands, fading out.
end_n = int((DUR - sec(T["music"]["drop"])) * SR)
tt = t_(end_n)
chord = sum(np.sin(2 * np.pi * hz(m + 12) * tt) for m in CHORDS[0][1:])
place(music, lp(chord, 2500) * np.exp(-tt * 0.6) * np.minimum(1, tt / 0.05), sec(T["music"]["drop"]), 0.08)

sfx = np.zeros(N)


def click():
    n = int(0.05 * SR)
    tt = t_(n)
    return (bp(rng.standard_normal(n), 2000, 6000) * 0.6 + np.sin(2 * np.pi * 1800 * tt)) * np.exp(-tt * 120)


def pop(i):
    n = int(0.12 * SR)
    tt = t_(n)
    f0 = 700 + 60 * (i % 6)
    f = f0 * (1 - 0.35 * tt / 0.12)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40)


def bell(m):
    n = int(1.2 * SR)
    tt = t_(n)
    f = hz(m)
    return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt * 6)) * np.exp(-tt * 3.5)


def whoosh(dur=0.45):
    n = int(dur * SR)
    tt = t_(n)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    blocks = 24
    for i in range(blocks):
        a, z = i * n // blocks, (i + 1) * n // blocks
        lo = 300 + 5000 * (i / blocks) ** 2
        out[a:z] = bp(noise, lo, min(lo * 2.5, 20000))[a:z]
    return out * np.sin(np.pi * tt / dur) ** 2


def impact():
    n = int(2.2 * SR)
    tt = t_(n)
    boom = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 2.2)
    air = lp(rng.standard_normal(n), 3000) * np.exp(-tt * 4) * 0.25
    return boom + air


def riser(dur):
    n = int(dur * SR)
    tt = t_(n)
    x = bp(rng.standard_normal(n), 800, 9000) * (tt / dur) ** 3
    return x


for f in T["sfx"]["click"]:
    place(sfx, click(), sec(f), 0.5)
for i, f in enumerate(T["sfx"]["pop"]):
    place(sfx, pop(i), sec(f), 0.16)
for i, f in enumerate(T["sfx"]["tick"]):
    place(sfx, bell([74, 77, 81, 84, 86][i % 5]), sec(f), 0.13)
for f in T["sfx"]["whoosh"]:
    place(sfx, whoosh(), sec(f) - 0.3, 0.22)
for f in T["sfx"]["impact"]:
    place(sfx, impact(), sec(f), 0.55)
    place(sfx, riser(1.2), sec(f) - 1.2, 0.12)

# Typing: a soft key tick every 3 frames while text types on.
for a, z in T["sfx"]["type"]:
    for f in range(a, z, 3):
        n = int(0.025 * SR)
        k_ = bp(rng.standard_normal(n), 3000, 9000) * np.exp(-t_(n) * 200)
        place(sfx, k_, sec(f) + rng.uniform(0, 0.01), 0.07 * rng.uniform(0.6, 1))

# Room: a short tail of decaying noise as the reverb, on the music and a little on the sounds.
ir_n = int(1.8 * SR)
ir = rng.standard_normal(ir_n) * np.exp(-t_(ir_n) * 3.2)
ir = lp(ir, 5000)
ir /= np.abs(ir).sum() ** 0.5 * 12


def stereo(x, wet, spread):
    tail = fftconvolve(x, ir)[:N] * wet
    d = int(spread * SR)
    left = x + tail
    right = x + np.concatenate([np.zeros(d), tail[:-d]]) if d else x + tail
    return np.stack([left, right], 1)


mix = stereo(music, 0.6, 0.011) + stereo(sfx, 0.25, 0.007)
fade = np.ones(N)
fn = int(1.0 * SR)
fade[-fn:] = np.linspace(1, 0, fn)
fade[: int(0.05 * SR)] = np.linspace(0, 1, int(0.05 * SR))
mix *= fade[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.6) * 0.71

out = ROOT / "public/audio/soundtrack.wav"
out.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(out), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(out, f"{DUR:.1f}s")
