"""An ayah written the way the Qur'an ear writes it. Pure: text in, words out.

The ear is checked by asking how sure it is of each expected word, and it is
only sure of a word in its own spelling. Asked about the same word spelt
another way it says no: صِرَاطَ with the vowel before the shadda scored 0.00 on
a perfect recitation. So the expected words are respelt first.

It writes plain vowelled spelling (quran.com's imlaei text) with four habits
of its own, each measured against what it wrote for 36 ayahs (293 of 294
words then agreed; the one left was a word it misheard):

  - no standing alif ٰ and no pause signs;
  - the shadda before its vowel;
  - no shadda where a letter merges from the word before: هُدًى مِنْ, not مِّن;
  - a letter with no mark gets a sukun, unless it is a long vowel or the
    silent lam before a sun letter.
"""
from __future__ import annotations

import re

LETTERS = "ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىي"
MARKS = "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652"
SHADDA, SUKUN, DAMMA, KASRA = "\u0651", "\u0652", "\u064f", "\u0650"
VOWEL_THEN_SHADDA = re.compile("([\u064b-\u0650\u0652])" + SHADDA)
def _with_sukun(word: str) -> str:
    out = []
    for i, letter in enumerate(word):
        out.append(letter)
        if letter not in LETTERS or word[i + 1:i + 2] in tuple(MARKS):
            continue
        before = word[i - 1] if i else ""
        long_vowel = (letter in "اىآ" or (letter == "و" and before == DAMMA)
                      or (letter == "ي" and before == KASRA))
        silent_lam = letter == "ل" and word[i + 2:i + 3] == SHADDA
        if not (long_vowel or silent_lam):
            out.append(SUKUN)
    return "".join(out)


def as_heard(text: str) -> list[str]:
    """The words of `text` in the ear's spelling, pause signs dropped."""
    words = []
    for word in text.split():
        word = "".join(c for c in word if c in LETTERS or c in MARKS)
        if not any(c in LETTERS for c in word):
            continue
        word = VOWEL_THEN_SHADDA.sub(SHADDA + r"\1", word)
        if word[1:2] == SHADDA:
            word = word[0] + word[2:]
        words.append(_with_sukun(word))
    return words
