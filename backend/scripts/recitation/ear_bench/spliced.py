"""Planted slips, letter by letter: one sound cut out of, or swapped in, a professional recitation.

IqraEval holds 97 distinct slips, so a letter-and-vowel cell there is one slip said by ten
people. This makes many per cell. Reciters are the professional test's (no ear trained on
them); each ayah is timed sound by sound with the phoneme ear (CTC, forced alignment), then
one sound is changed:

  letter dropped  - a plain consonant's sound cut out (sukun after a/i/u, or voweled)
  letter swapped  - its sound replaced by its usual confusion (ت/ط, س/ص, ح/ه ...) from the same voice
  vowel swapped   - a short vowel replaced by another one from the same voice
  vowel length    - short for long or long for short, same voice

A planted slip is kept only if it landed, judged at that spot alone: the meant sound was
clearly there before (peak share HEARD), is not after (under GONE), and a swapped-in sound
is. Judging the whole ayah fails: the phoneme ear, like the word ear, fills a missing
letter back in from the words around it. The untouched clips are the right words.

    python -m backend.scripts.recitation.ear_bench.spliced build   # ~1 h, downloads ~600 ayahs
    python -m backend.scripts.recitation.ear_bench.spliced score [--model repo@rev]
then letters.py --set spliced prints the breakdown.
"""
from __future__ import annotations

import argparse
import difflib
import io
import json
import random
import urllib.request
import wave
from collections import Counter

import numpy as np

from backend.config import data_path, get_settings
from backend.scripts.recitation.finetune_ear.ear.settings import EVERYAYAH_URL
from backend.scripts.recitation.paths import DOWNLOADS
from backend.scripts.recitation.rescore_recitation import pieces_path
from backend.services.recitation import checker, sounds, whisper
from backend.services.recitation.spelling import as_heard

FOLDER = DOWNLOADS / "spliced"
META = FOLDER / "slips.jsonl"
RECITERS = ("Husary_128kbps", "Minshawy_Murattal_128kbps", "Alafasy_128kbps")
SR, HOP, FADE = 16000, 320, 80  # the phoneme ear hears one frame per 320 samples; 5 ms crossfade
CAP = 20          # slips per (kind, letter, context) cell, each on a different word
PER_CLIP = 6      # slips made from one recording, on different words
MAX_WORDS = 14    # longer ayahs run past the ear's 30 s window
CLIPS = 900       # recordings read at most
MATCH = 0.85      # what the phoneme ear hears must match the ayah this well, or the timing is not trusted
HEARD, GONE = 0.5, 0.2  # a sound's peak share at its spot: there at HEARD or more, gone under GONE
WINDOW = SR       # sound either side of an edit the phoneme ear re-hears
SEED = 7
# Teaching (cloud.py --lone uploads it): reciters no test hears, more per cell, never the test's ayahs.
TAUGHT = DOWNLOADS / "lone-slips"
TEACH = ("Abdullah_Basfar_192kbps", "Hani_Rifai_192kbps", "Muhammad_Ayyoub_128kbps", "MaherAlMuaiqly128kbps",
         "Abu_Bakr_Ash-Shaatree_128kbps", "Muhammad_Jibreel_128kbps", "Nasser_Alqatami_128kbps", "Fares_Abbad_64kbps")
TEACH_CAP, TEACH_CLIPS = 80, 1500

ARABIC = {"b": "ب", "t": "ت", "θ": "ث", "ʒ": "ج", "ħ": "ح", "x": "خ", "d": "د", "ð": "ذ", "r": "ر",
          "rˤ": "ر", "z": "ز", "s": "س", "ʃ": "ش", "sˤ": "ص", "dˤ": "ض", "tˤ": "ط", "ðˤ": "ظ",
          "ʕ": "ع", "ɣ": "غ", "f": "ف", "q": "ق", "k": "ك", "l": "ل", "lˤ": "ل", "m": "م", "n": "ن",
          "h": "ه", "w": "و", "j": "ي", "ʔ": "ء"}
# Each letter's commonest learner confusion, so every letter gets a swap.
PARTNER = {"t": "tˤ", "tˤ": "t", "d": "dˤ", "dˤ": "d", "s": "sˤ", "sˤ": "s", "ð": "z", "z": "ð",
           "θ": "s", "ðˤ": "ð", "ħ": "h", "h": "ħ", "ʕ": "ʔ", "ʔ": "ʕ", "q": "k", "k": "q", "x": "ħ",
           "ɣ": "x", "ʃ": "s", "ʒ": "z", "r": "l", "rˤ": "l", "l": "r", "m": "n", "n": "m", "b": "m",
           "f": "θ", "w": "j", "j": "w"}
SHORT = {"a": "fatha", "aˤ": "fatha", "u": "damma", "i": "kasra"}
LONG = {"a:": "fatha", "aˤ:": "fatha", "u:": "damma", "i:": "kasra"}
VOWEL_OTHER = {"a": ("i", "u"), "i": ("a", "u"), "u": ("a", "i")}
LENGTH = {"a": "a:", "i": "i:", "u": "u:", "a:": "a", "i:": "i", "u:": "u"}


def vowel_name(p: str) -> str | None:
    return SHORT.get(p) or (("long " + LONG[p]) if p in LONG else None)


def context(flat: list[str], k: int) -> str:
    """fatha / long kasra / sukun after damma ... for the consonant flat[k], as letters.py files it."""
    own = vowel_name(flat[k + 1]) if k + 1 < len(flat) else None
    if own:
        return own
    before = next((vowel_name(p) for p in reversed(flat[:k]) if vowel_name(p)), None)
    return "sukun after " + (before.replace("long ", "") if before else "nothing")


# --- CTC: where each sound sits (blank is id 0) -----------------------------------------

def _states(ids: list[int]) -> list[int]:
    return [x for i in ids for x in (0, i)] + [0]


def align(logp: np.ndarray, ids: list[int]) -> list[tuple[int, int]] | None:
    """Each sound's frames [start, next sound's start), by the best CTC path."""
    s = _states(ids)
    n, T = len(s), len(logp)
    if T < len(ids):
        return None
    a = np.full(n, -np.inf)
    a[0], a[1] = logp[0, s[0]], logp[0, s[1]]
    back = np.zeros((T, n), dtype=np.int8)
    skip = np.array([i >= 2 and s[i] != 0 and s[i] != s[i - 2] for i in range(n)])
    for t in range(1, T):
        stay, step = a, np.concatenate(([-np.inf], a[:-1]))
        jump = np.where(skip, np.concatenate(([-np.inf, -np.inf], a[:-2])), -np.inf)
        best = np.stack([stay, step, jump])
        back[t] = best.argmax(0)
        a = best.max(0) + logp[t, s]
    i = n - 1 if a[-1] >= a[-2] else n - 2
    first = {}
    for t in range(T - 1, -1, -1):
        if i % 2:
            first[i // 2] = t
        i -= int(back[t, i])
    starts = [first.get(k) for k in range(len(ids))]
    if None in starts:
        return None
    return [(st, starts[k + 1] if k + 1 < len(ids) else T) for k, st in enumerate(starts)]


# --- sound ----------------------------------------------------------------------------

def logits(sound: np.ndarray) -> np.ndarray:
    (out,) = sounds._model.run("spliced", {"audio": sound[None, :].astype(np.float32)})
    x = out[0].astype(np.float64)
    return x - np.logaddexp.reduce(x, axis=1, keepdims=True)


def joined(*parts: np.ndarray) -> np.ndarray:
    """Pieces end to end with a short crossfade at each seam, so a cut leaves no click."""
    out = parts[0]
    for p in parts[1:]:
        f = min(FADE, len(out), len(p))
        if f:
            ramp = np.linspace(0, 1, f, dtype=np.float32)
            out = np.concatenate([out[:-f], out[-f:] * (1 - ramp) + p[:f] * ramp, p[f:]])
        else:
            out = np.concatenate([out, p])
    return out


def wav_bytes(sound: np.ndarray) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(sound, -1, 1) * 32767).astype("<i2").tobytes())
    return buf.getvalue()


def fetch(who: str, key: str, folder=FOLDER) -> bytes | None:
    surah, ayah = map(int, key.split(":"))
    path = folder / "mp3" / who / f"{surah:03d}{ayah:03d}.mp3"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(EVERYAYAH_URL.format(who=who, surah=surah, ayah=ayah), timeout=30) as r:
                path.write_bytes(r.read())
        except OSError:
            return None
    return path.read_bytes()


# --- what an edited clip says, spelt as the ear writes it (for teaching) ----------------

HARAKA = {"a": "َ", "u": "ُ", "i": "ِ"}
LONG_LETTER = {"a": "ا", "u": "و", "i": "ي"}
SPELT_AS = {**{p: {c} for p, c in ARABIC.items()}, "ʔ": set("ءأإؤئآ"), "t": {"ت", "ة"},
            "ñ": {"ن"}, "ŋ": {"ن"}, "m̃": {"م"}, "j̃": {"ي"}, "w̃": {"و"}}
MARKS = set("ًٌٍَُِّْ")


def _single(p: str) -> str:
    half = len(p) // 2
    return p[:half] if len(p) % 2 == 0 and p[:half] == p[half:] else p


def said_word(word: str, ph: list[str], j: int, kind: str, donor: str | None) -> str | None:
    """`word` with the slip at its sound ph[j] written in, or None where the sounds and letters do not
    pair up one to one (assimilated letters, nasal marks): a target that may be wrong is not taught."""
    slots = [i for i, c in enumerate(word) if c not in MARKS and word[i + 1:i + 2] in MARKS]
    cons = [k for k, p in enumerate(ph) if vowel_name(p) is None and p != "Q"]  # Q: a qalqala bounce, no letter
    if len(slots) != len(cons) or any(word[i] not in SPELT_AS.get(_single(ph[k]), ()) for i, k in zip(slots, cons)):
        return None
    at = dict(zip(cons, slots))
    if kind.startswith("letter"):
        i = at[j]
        end = i + 1
        while end < len(word) and word[end] in MARKS:
            end += 1
        if kind == "letter dropped":
            return word[:i] + word[end:] if word[i + 1:end] == "ْ" else None  # only a silent letter is spellable
        return word[:i] + ARABIC[donor] + word[i + 1:]
    i = at.get(j - 1)
    if i is None:
        return None
    end = i + 1
    while end < len(word) and word[end] in MARKS:
        end += 1
    meant = ph[j].replace("ˤ", "")
    if HARAKA.get(meant[0]) not in word[i + 1:end]:
        return None
    is_long = word[end:end + 1] == LONG_LETTER[meant[0]] and word[end + 1:end + 2] not in MARKS
    if (":" in meant) != is_long:
        return None
    if kind == "vowel swapped":
        return word[:i + 1] + word[i + 1:end].replace(HARAKA[meant[0]], HARAKA[donor]) + word[end:]
    if ":" in meant:  # long to short: the long letter goes
        return word[:end] + word[end + 1:]
    return word[:end] + LONG_LETTER[meant[0]] + word[end:]


# --- building -------------------------------------------------------------------------

def candidates(flat: list[str]):
    """(kind, position, letter, context, donor sound or None) for every slip this ayah could hold."""
    for k, p in enumerate(flat):
        if p in ARABIC:
            ctx = context(flat, k)
            yield "letter dropped", k, ARABIC[p], ctx, None
            yield "letter swapped", k, ARABIC[p], ctx, PARTNER[p]
        base = p.replace("ˤ", "")
        if k and flat[k - 1] in ARABIC and base in VOWEL_OTHER:
            for q in VOWEL_OTHER[base]:
                yield "vowel swapped", k, ARABIC[flat[k - 1]], f"{SHORT[base]} -> {SHORT[q]}", q
        if k and flat[k - 1] in ARABIC and base in LENGTH:
            q = LENGTH[base]
            yield "vowel length", k, ARABIC[flat[k - 1]], f"{vowel_name(base)} -> {vowel_name(q)}", q


def ayahs(quran: dict, ref: dict, skip=frozenset(), teach=False) -> list[str]:
    """The ayahs a build reads, in the order it reads them: short enough, words matching the phonemes."""
    keys = [k for k in ref if k in quran and k not in skip and len(ref[k]) == len(as_heard(quran[k])) <= MAX_WORDS]
    random.Random(SEED + teach).shuffle(keys)
    return keys


def build(reciters=RECITERS, folder=FOLDER, skip=frozenset(), cap=CAP, clips=CLIPS, teach=False) -> None:
    """Planted slips into folder/slips.jsonl and folder/clips. `teach`: only slips whose new spelling is
    certain (said_word), each row carrying `said`, the words as the edited clip says them."""
    quran = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    ref = json.loads(data_path("recitation_sounds_reference_path").read_text(encoding="utf-8"))
    vocab = json.loads((data_path("recitation_sounds_path") / "vocab.json").read_text(encoding="utf-8"))
    keys = ayahs(quran, ref, skip, teach)
    (folder / "clips").mkdir(parents=True, exist_ok=True)
    # Rows are written as made, so a stopped build resumes: done recordings only refill the donors.
    meta = folder / META.name
    rows = [json.loads(line) for line in meta.open(encoding="utf-8")] if meta.exists() else []
    done = {r["id"] for r in rows if r["k"] is None}
    filled = Counter((r["kind"], r["letter"], r["context"]) for r in rows if r["k"] is not None)
    words_used = {(r["key"], r["k"], (r["kind"], r["letter"], r["context"])) for r in rows if r["k"] is not None}
    out = meta.open("a", encoding="utf-8")
    donors: dict[str, dict] = {w: {} for w in reciters}
    tried = Counter()
    for n, key in enumerate(keys[:clips]):
        who = reciters[n % len(reciters)]
        words = as_heard(quran[key])
        mp3 = fetch(who, key, folder)
        if mp3 is None:
            tried["not on everyayah"] += 1
            continue
        sound = np.asarray(whisper.sound_of(mp3), dtype=np.float32)
        if len(sound) > 29 * SR:
            tried["over 29 s"] += 1
            continue
        flat = [p for w in ref[key] for p in w]
        word_of = [i for i, w in enumerate(ref[key]) for _ in w]
        if any(p not in vocab for p in flat):
            tried["sound not in the ear's list"] += 1
            continue
        lp = logits(sound)
        heard, _ = sounds.collapse(lp.argmax(1).tolist(), {i: s for s, i in vocab.items()})
        if difflib.SequenceMatcher(None, heard, flat, autojunk=False).ratio() < MATCH:
            tried["timing not trusted"] += 1
            continue
        spans = align(lp, [vocab[p] for p in flat])
        if spans is None:
            tried["timing not trusted"] += 1
            continue
        cut = [(a * HOP, b * HOP) for a, b in spans]
        post = np.exp(lp)
        # Every sound this voice made clearly, for swaps later, filed also by the sound after it
        # so a swapped-in letter carries the right movement into its vowel.
        for i, (p, (a, b)) in enumerate(zip(flat, cut)):
            if post[spans[i][0]:spans[i][1], vocab[p]].max() >= HEARD:
                for key_ in (p, (p, flat[i + 1] if i + 1 < len(flat) else None)):
                    donors[who].setdefault(key_, []).append(sound[a:b])
        clip = f"{who}/{key}"
        if clip in done:
            continue
        rows.append({"id": clip, "key": key, "sentence": quran[key], "k": None, "said": " ".join(words)})
        out.write(json.dumps(rows[-1], ensure_ascii=False) + "\n")
        (folder / "clips" / f"{who}-{key.replace(':', '_')}.wav").write_bytes(wav_bytes(sound))
        made, words_here = 0, set()
        options = list(candidates(flat))
        random.Random(f"{SEED}{clip}").shuffle(options)
        for kind, k, letter, ctx, donor in options:
            cell, w = (kind, letter, ctx), word_of[k]
            if made >= PER_CLIP or filled[cell] >= cap or w in words_here or (key, w, cell) in words_used:
                continue
            start = word_of.index(w)
            new = said_word(words[w], ref[key][w], k - start, kind, donor)
            if teach and new is None:
                continue
            said = None if new is None else " ".join(words[:w] + [new] + words[w + 1:])
            a, b = cut[k]
            if post[spans[k][0]:spans[k][1], vocab[flat[k]]].max() < HEARD:
                tried["sound not clear in the recording"] += 1
                continue
            piece = np.zeros(0, dtype=np.float32)
            if donor is not None:
                after = flat[k + 1] if k + 1 < len(flat) else None
                pool = donors[who].get((donor, after)) or donors[who].get(donor)
                if not pool:
                    tried["no donor yet"] += 1
                    continue
                piece = pool[len(pool) // 2]
            edited = joined(sound[:a], piece, sound[b:]) if len(piece) else joined(sound[:a], sound[b:])
            # Landed = at that spot the meant sound is no longer heard, and the swapped-in one is.
            lo = max(0, a - WINDOW)
            near = np.exp(logits(edited[lo:a + len(piece) + WINDOW]))
            f0, f1 = (a - lo) // HOP, (a - lo + len(piece)) // HOP
            spot = near[max(0, f0 - 2):f1 + 3]
            if spot[:, vocab[flat[k]]].max() >= GONE or (donor is not None and spot[:, vocab[donor]].max() < HEARD):
                tried[f"did not land: {kind}"] += 1
                continue
            tried[f"landed: {kind}"] += 1
            sid = f"{clip}#{k}"
            (folder / "clips" / f"{who}-{key.replace(':', '_')}-{k}.wav").write_bytes(wav_bytes(edited))
            rows.append({"id": sid, "key": key, "sentence": quran[key], "k": w,
                         "kind": kind, "letter": letter, "context": ctx, "said": said})
            out.write(json.dumps(rows[-1], ensure_ascii=False) + "\n")
            filled[cell] += 1
            words_used.add((key, w, cell))
            words_here.add(w)
            made += 1
        out.flush()
        if n % 25 == 0:
            print(f"{n} recordings, {len(rows)} rows, {len(filled)} cells", dict(tried), flush=True)
    out.close()
    print(f"wrote {len(rows)} rows ({sum(r['k'] is not None for r in rows)} slips) to {meta}")
    print(dict(tried))


def audio_of(row: dict) -> bytes:
    who, rest = row["id"].split("/")
    key, _, k = rest.partition("#")
    return (FOLDER / "clips" / f"{who}-{key.replace(':', '_')}{'-' + k if k else ''}.wav").read_bytes()


def scored_path(model: str):
    return pieces_path(model).with_name("spliced-" + pieces_path(model).name)


def score(model: str) -> None:
    path = scored_path(model)
    done = {json.loads(line)["id"] for line in path.open(encoding="utf-8")} if path.exists() else set()
    rows = [json.loads(line) for line in META.open(encoding="utf-8")]
    with path.open("a", encoding="utf-8") as kept:
        for n, row in enumerate(rows):
            if row["id"] in done:
                continue
            probs = [w["probs"] for w in checker.scores(audio_of(row), as_heard(row["sentence"]), model)]
            kept.write(json.dumps({"id": row["id"], "probs": probs}) + "\n")
            if n % 200 == 0:
                print(f"{n}/{len(rows)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=("build", "teach", "score"))
    parser.add_argument("--model", default=get_settings().recitation_model)
    args = parser.parse_args()
    if args.step == "build":
        build()
    elif args.step == "teach":
        build(TEACH, TAUGHT, skip=untaught(), cap=TEACH_CAP, clips=TEACH_CLIPS, teach=True)
    else:
        score(args.model)


def untaught() -> set[str]:
    """Ayahs teaching may never use: the spliced test's, and any holding an IqraEval phrase."""
    from backend.scripts.recitation.ear_bench.iqra import clips as iqra_clips
    from backend.services.recitation.spelling import LETTERS
    quran = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    ref = json.loads(data_path("recitation_sounds_reference_path").read_text(encoding="utf-8"))
    bare = lambda t: "".join(c for c in t if c in LETTERS)  # noqa: E731
    phrases = {bare(r["sentence"]) for r in iqra_clips()}
    tested = set(ayahs(quran, ref)[:CLIPS])  # every ayah the test build reads, whether or not it made a slip
    return tested | {k for k, t in quran.items() if any(p in bare(t) for p in phrases)}


if __name__ == "__main__":
    main()
