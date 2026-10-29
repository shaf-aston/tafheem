"""What a clip should sound like: its ayah's phonemes, made by quranic-phonemizer from the ayah's own text."""
import json
from functools import cache
from pathlib import Path


@cache
def _phonemizer():
    from quranic_phonemizer import Phonemizer
    return Phonemizer()


def by_word(key):
    """The ayah '2:255' as a tuple of words, each a tuple of phoneme symbols."""
    return _phonemizer().analyse(key).phonemes(by='word')


def flat(key):
    return tuple(p for word in by_word(key) for p in word)


def vocab(folder):
    """Symbol to id, from the start model's vocab.json."""
    return json.loads((Path(folder) / 'vocab.json').read_text(encoding='utf-8'))


def ids(key, symbols):
    """The ayah as the ids a CTC loss wants. A symbol the model has no id for raises: a silent drop would teach a lie."""
    return [symbols[p] for p in flat(key)]
