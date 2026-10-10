"""The word lists: each meaning written once in English, each dialect's Arabic linked to it.

data/colloquial/words.json holds every meaning: an id, its English and its group
(family, food, actions ...). A spine lesson's `words` names the ids that topic
teaches, in order. <dialect>/words.json gives that dialect's Arabic and spelling
for an id, once, however many topics teach it. So an English meaning is never
written twice, a word shared by two topics is said once per dialect, and adding a
word to a topic is one id in the spine, reported missing by every dialect that
has written the topic until each one says it.

A word that only changes its ending for a woman is one meaning, its two forms
split by a slash: تعبان / تعبانة, ta3baan / ta3baane. Two meanings only when the
words themselves differ, like brother and sister.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from backend.config import data_path
from backend.services.colloquial.knobs import knob

FILE = "words.json"
GROUPS = "groups.json"
_ARABIC = re.compile(r"[؀-ۿ]")
_NOT_ARABIC = re.compile(r"[^؀-ۿ\s/]")


def _read(path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["words"] if path.is_file() else {}


@lru_cache(maxsize=1)
def meanings() -> dict:
    """Every meaning by id: {"english", "group"}."""
    return _read(data_path("colloquial_dir") / FILE)


@lru_cache(maxsize=1)
def groups() -> set[str]:
    """Every heading a word may sit under; a word naming any other is a typo or a new heading to list first."""
    return set(json.loads((data_path("colloquial_dir") / GROUPS).read_text(encoding="utf-8"))["groups"])


def said_in(folder: str) -> dict:
    """One dialect's words by id: {"arabic", "transliteration"}; none yet is an empty dict."""
    return _read(data_path("colloquial_dir") / folder / FILE)


def text(words: dict, about: str = "") -> str:
    """A words.json as written to disk: one word to a line, so a change reads as one line in a diff."""
    lines = [f"  {json.dumps(one, ensure_ascii=False)}: {json.dumps(word, ensure_ascii=False)}" for one, word in words.items()]
    head = f'  "_about": {json.dumps(about, ensure_ascii=False)},\n' if about else ""
    return "{\n" + head + '  "words": {\n  ' + ",\n  ".join(lines) + "\n  }\n}\n"


def outline_faults(spine: list[dict], known: dict) -> list[str]:
    """The meanings and the spine's word lists, checked against each other."""
    said, used = [], set()
    least = knob("least-topic-words")
    for unit in spine:
        for lesson in unit["lessons"]:
            ids = lesson.get("words") or []
            where = f"spine {unit['unit']} {lesson['lesson']}"
            if ids and len(ids) < least:
                said.append(f"{where} teaches {len(ids)} words, fewer than {least}")
            said += [f"{where} teaches {one!r} twice" for one in sorted({i for i in ids if ids.count(i) > 1})]
            said += [f"{where} teaches {one!r}, which {FILE} does not have" for one in ids if one not in known]
            used.update(ids)
    for one, meaning in known.items():
        if not (str(meaning.get("english") or "").strip() and str(meaning.get("group") or "").strip()):
            said.append(f"{FILE} {one!r} has no english or no group")
        elif _ARABIC.search(meaning["english"]):
            said.append(f"{FILE} {one!r} has Arabic letters in its English")
        elif meaning["group"] not in groups():
            said.append(f"{FILE} {one!r} has the group {meaning['group']!r}, which {GROUPS} does not list")
        if one not in used:
            said.append(f"{FILE} {one!r} is taught by no topic")
    return said


def unknown(said: dict, known: dict, folder: str) -> list[str]:
    return [f"{folder}/{FILE} says {one!r}, which {FILE} does not have" for one in said if one not in known]


def _word_faults(word: dict, where: str) -> list[str]:
    arabic, spelling = str(word.get("arabic") or "").strip(), str(word.get("transliteration") or "").strip()
    if not (arabic and spelling):
        return [f"{where} has no arabic or no transliteration"]
    said = []
    if _NOT_ARABIC.search(arabic):
        said.append(f"{where} has a non-Arabic letter in its Arabic: {arabic!r}")
    forms = arabic.split("/")
    if any(len(form.split()) > knob("most-word-parts") for form in forms):
        said.append(f"{where} is a phrase, not a word: {arabic!r}")
    if len(spelling.split("/")) != len(forms):
        said.append(f"{where} has {len(forms)} forms in Arabic but not in its transliteration")
    if _ARABIC.search(spelling):
        said.append(f"{where} has Arabic letters in its transliteration")
    return said


def bank(ids: list[str], said: dict, where: str) -> tuple[list[dict], list[str]]:
    """A topic's words in one dialect: all of them, or none yet. Never half."""
    ids = [one for one in ids if one in meanings()]
    missing = [one for one in ids if one not in said]
    if len(missing) == len(ids):
        return [], []
    if missing:
        return [], [f"{where} has no word for {', '.join(missing)}"]
    words = [{"id": one, "english": meanings()[one]["english"], "category": meanings()[one]["group"],
              "arabic": said[one].get("arabic"), "transliteration": said[one].get("transliteration")}
             for one in ids]
    faults, seen = [], set()
    for word in words:
        name = f"{where} word {word['id']!r}"
        faults += _word_faults(word, name)
        if word["arabic"] in seen:
            faults.append(f"{name} repeats {word['arabic']!r}")
        seen.add(word["arabic"])
    return words, faults
