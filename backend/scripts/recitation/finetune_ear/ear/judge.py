"""The judge: hear every held clip as the app does, count words wrong, and decide whether a candidate replaces
the held ear. Scoring needs the GPU; `compare` and `verdict` are plain numbers, so they can be checked anywhere."""
import numpy as np

from . import settings as S


def listen(model, sound):
    """What a faster-whisper model hears in one clip, as the app hears it: one guess, untimed, the clip alone."""
    segments = model.transcribe(np.asarray(sound, dtype=np.float32), language='ar', beam_size=1,
                                without_timestamps=True, condition_on_previous_text=False)[0]
    return ' '.join(s.text for s in segments)


def hear(ear, tests):
    """Per test group, (errors, words) for each clip and what was heard."""
    import jiwer
    from faster_whisper import WhisperModel

    from .text import bare
    m = WhisperModel(str(ear), device='cuda', compute_type='float16')
    out = {}
    for group, rows in tests.items():
        counts, heard = [], []
        for x, said in zip(rows['sound'], rows['said']):
            h = bare(listen(m, x))
            w = jiwer.process_words(bare(said), h)
            counts.append((w.substitutions + w.deletions + w.insertions, len(bare(said).split())))
            heard.append(h)
        out[group] = {'counts': np.array(counts, dtype=np.int64), 'heard': heard}
    return out


def wrong(counts):
    """Words wrong, in percent, over a whole group: all errors over all words, as jiwer.wer counts a list."""
    return round(100 * counts[:, 0].sum() / counts[:, 1].sum(), 2)


def scores(heard):
    return {g: wrong(h['counts']) for g, h in heard.items()}


def gain(held, cand, seed=0):
    """Points fewer words wrong for the candidate than the held ear, with its bootstrap interval. The same
    clips are drawn for both ears in each draw (they heard the same clips), so the interval is the paired one."""
    rng = np.random.default_rng(seed)
    n = len(held)
    draws = rng.integers(0, n, size=(S.RESAMPLES, n))
    a, b = held[draws], cand[draws]
    spread = 100 * (a[..., 0].sum(1) / a[..., 1].sum(1) - b[..., 0].sum(1) / b[..., 1].sum(1))
    tail = (1 - S.SURE) / 2 * 100
    return {'points': round(wrong(held) - wrong(cand), 2),
            'low': round(float(np.percentile(spread, tail)), 2), 'high': round(float(np.percentile(spread, 100 - tail)), 2)}


def verdict(held, cand, untuned):
    """Keep `cand` over `held`? Each argument is hear()'s output for one ear on the same tests."""
    gains = {g: gain(held[g]['counts'], cand[g]['counts']) for g in held}
    better = [g for g, m in S.MARGIN.items() if gains[g]['points'] >= m and gains[g]['low'] > 0]
    worse = [g for g, m in S.MARGIN.items() if -gains[g]['points'] > m]
    # Forgot: past the band around the untuned model and surely worse than the held ear there, so an ear
    # already past the band may stay (within noise) but not slip further.
    forgot = bool(wrong(cand['professional']['counts']) > wrong(untuned['professional']['counts']) + S.FORGET
                  and gains['professional']['high'] < 0)
    # Word error only refuses: whether an ear catches slips better is ear_bench's call (cloud.py --ship), so an
    # ear no worse here is handed back to be benched, not thrown away for missing a word-error margin.
    return {'keep': not worse and not forgot, 'better': better, 'worse': worse, 'forgot': forgot,
            'gains': gains}
