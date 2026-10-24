"""The Qur'an's own text: what each ayah says, how a printed ayah is matched, which ayahs the model can write."""
import re

import requests
from transformers import WhisperConfig, WhisperProcessor

from . import settings as S

# Plain vowelled spelling, the spelling this model writes; Uthmani would score right words as wrong.
_verses = requests.get('https://api.quran.com/api/v4/quran/verses/imlaei', timeout=60).json()['verses']
IMLAEI = {v['verse_key']: v['text_imlaei'] for v in _verses}
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
SAYABLE = {k for k, t in IMLAEI.items() if len(processor.tokenizer(t).input_ids) <= _most}
print(len(IMLAEI) - len(SAYABLE), 'ayahs too long for the model to write, left out', flush=True)


def canon(key):
    """One name for every ayah that reads the same (55:13 and its echoes): held-out checks compare these, or a
    held ayah could still be taught under an echo's number."""
    return SPELT.get(letters(IMLAEI[key]), key)


# Marks off both sides: this measures letters. A stop changes the last vowel by rule,
# and vowels are the sureness check's job, a different model run. Pause signs (ۖ ۗ ۚ) too:
# printed apart, each was counted as a word, so a pause sign heard or not cost a whole word.
MARKS = re.compile('[ً-ْٰۖ-ۭ]')


def bare(text):
    return MARKS.sub('', text).replace('ٱ', 'ا').strip()
