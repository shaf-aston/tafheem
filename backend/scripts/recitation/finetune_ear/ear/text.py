"""The Qur'an's own text: what each ayah says, how a printed ayah is matched, which ayahs the model can write."""
import re
from bisect import bisect_right

import requests
from transformers import WhisperConfig, WhisperProcessor

from . import settings as S
from .spelling import as_heard  # the app's own (services/recitation/spelling.py), zipped in by cloud.py

# Plain vowelled spelling, the spelling this model writes; Uthmani would score right words as wrong.
_verses = requests.get('https://api.quran.com/api/v4/quran/verses/imlaei', timeout=60).json()['verses']
IMLAEI = {v['verse_key']: v['text_imlaei'] for v in _verses}
# What an ear is taught and judged on: the spelling the app checks each word in. Taught raw imlaei, the last
# tuned ear read a word-initial shadda (مِّن) the checker never asks about, and scored 9 of 252 right words low.
SAID = {k: ' '.join(as_heard(t)) for k, t in IMLAEI.items()}
_uthmani = requests.get('https://api.quran.com/api/v4/quran/verses/uthmani', timeout=60).json()['verses']


def letters(text):
    """Bare letters, one alef, one yeh: the key a printed ayah is matched by in either script."""
    text = re.sub('[ٱأإآ]', 'ا', text).replace('ی', 'ي').replace('ى', 'ي')
    return re.sub('[^ء-ي]|ـ', '', text)  # the stretch mark sits inside the letter range


# Letters to the one ayah they spell. A spelling shared by ayahs that read differently is
# ambiguous and left out; a repeated ayah (55:13 and its echoes) reads the same, so it stays.
SPELT = {}
for _v in _verses + _uthmani:
    SPELT.setdefault(letters(_v.get('text_imlaei') or _v['text_uthmani']), set()).add(_v['verse_key'])
SPELT = {k: min(keys) for k, keys in SPELT.items() if len({IMLAEI[x] for x in keys}) == 1}

processor = WhisperProcessor.from_pretrained(S.NAME, language='ar', task='transcribe')
# Whisper writes so many marks at most, start marks included. An ayah spelt in more can be
# neither taught (training stops on it) nor heard whole, so it is left out on both sides.
_most = WhisperConfig.from_pretrained(S.NAME).max_target_positions


def WRITABLE(text):
    return len(processor.tokenizer(text).input_ids) <= _most


SAYABLE = {k for k, t in SAID.items() if WRITABLE(t)}
print(len(SAID) - len(SAYABLE), 'ayahs too long for the model to write, left out', flush=True)


def canon(key):
    """One name for every ayah that reads the same (55:13 and its echoes): held-out checks compare these, or a
    held ayah could still be taught under an echo's number."""
    return SPELT.get(letters(IMLAEI[key]), key)


_KEYS = list(IMLAEI)
_WHOLE = ' '.join(letters(IMLAEI[k]) for k in _KEYS)  # every ayah's letters, a space between ayahs
_STARTS = [0]
for _k in _KEYS:
    _STARTS.append(_STARTS[-1] + len(letters(IMLAEI[_k])) + 1)


def ayahs_of(spelt):
    """Every ayah (as canon()) whose letters hold the run `spelt`; empty when it is not the Qur'an's or runs across two
    ayahs. A phrase repeated in several ayahs names them all, so a held ayah cannot hide in an echo."""
    found, at = set(), _WHOLE.find(spelt)
    while spelt and at >= 0:
        found.add(canon(_KEYS[bisect_right(_STARTS, at) - 1]))
        at = _WHOLE.find(spelt, at + 1)
    return found


# Marks off both sides: this measures letters. A stop changes the last vowel by rule,
# and vowels are the sureness check's job, a different model run. Pause signs (ۖ ۗ ۚ) too:
# printed apart, each was counted as a word, so a pause sign heard or not cost a whole word.
MARKS = re.compile('[ً-ْٰۖ-ۭ]')


def bare(text):
    return MARKS.sub('', text).replace('ٱ', 'ا').strip()
