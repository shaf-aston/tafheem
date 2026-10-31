"""A phrase or sentence in English: what it means, then word by word.

Two lines, the way al-Maany sets them out: the sense first, the words under it.

The words come from the grammar on this machine, every time, in milliseconds:
the i'rab reading's own analysis of each word (the one the Nahw tab shows), so
the two pages cannot disagree; CAMeL alone when the parser is not installed.
The sense comes from the surest source that has one. A whole ayah has its
published translation and the Qur'an's own word-by-word; a run of words from
inside one takes that word-by-word English onto the grammar's rows. Anything
else goes to the language model, handed those facts (each word's senses as
candidates) and asked for one English sentence. It never changes a row. A model
answer is filed on disk, so the same text asks once, on every server process.
"""
from __future__ import annotations

import logging
import re
from itertools import pairwise

from backend.config import get_settings
from backend.services import ai
from backend.services.dictionary import service as dictionary_service
from backend.services.nahw import iraab
from backend.services.sarf import morphology
from backend.services.learner import progress_store
from backend.services.quran import library as quran_library
from backend.services.quran import meanings as quran_meanings
from backend.services.quran import search as quran_search
from backend.services.text.arabic_text import words
from backend.services.nahw.book import term_ar

logger = logging.getLogger(__name__)

_TAGS_RE = re.compile(r"\[[^\]]*\]|<[^>]*>")
# The word every clause's name opens with (data/nahw_rules/tarkeeb.json).
_CLAUSE = term_ar("jumlah_ismiyyah").split()[0]
# Where a model's sense is filed (progress_store), so every server process reads the first one kept.
# Renamed whenever SENTENCE_USER changes, so answers filed under an older prompt are never reused.
# "arabic" is the other direction's answer, filed the same way.
_KEPT, _QUESTION, _ARABIC = "dict", "meaning3", "arabic"


def literal(gloss: str, senses: int) -> str:
    """CAMeL's gloss as English: each joined piece's first `senses` senses, tags dropped.

    and+write+he;it_<verb> reads "and write he/it"; the+child;son reads "the
    child/son". More than one sense shows the choice rather than guessing it.
    """
    pieces = ("/".join(_TAGS_RE.sub("", piece).split(";")[:senses]).replace("_", " ").strip() for piece in gloss.split("+"))
    return " ".join(piece for piece in pieces if piece)


def kind_of(summary: str | None, read: list[dict]) -> str:
    """"sentence" when it says something, else "phrase"; "word" when one Arabic word
    is all there is, as when the rest of what was typed is not Arabic.

    `summary` is the grammar's name for the whole (iraab.analyze, as the Analyse
    page shows it), and every clause it names is a جُمْلَةٌ: the verbal, nominal,
    question and call clauses alike. It reads البيت الكبير as a described noun and
    هل أنت جائع as a question. It does not yet see a definite noun told about by
    what follows (الحمد لله, الولد في البيت), so that is checked here too.
    """
    if len(read) < 2:
        return "word"
    told = any(
        a["pos"] in morphology.NOUNISH and a["state"] == "d" and (b["state"] == "i" or b["pos"] == "prep")
        for a, b in pairwise(read)
    )
    return "sentence" if told or (summary or "").startswith(_CLAUSE) else "phrase"


def read_words(text: str) -> tuple[list[dict], str | None]:
    """(a row per word, the grammar's name for the whole or None).

    The row is what the i'rab card says of the word: CAMeL's chosen reading plus the
    role and case the book's rules gave it, its English read in the class the grammar
    settled (إنّ "indeed", never the condition's "if"). The parser's model files may be missing,
    and then CAMeL's reading stands alone, with no role.
    """
    try:
        read = iraab.analyze(text)
        cards = [(c["word"], c["camel"], c.get("sense"), c.get("role_key") and c.get("role"), c.get("case"))
                 for c in read["words"]]
        summary = read["summary"]
    except Exception as exc:  # noqa: BLE001, the parser is optional here
        logger.info("sentence meaning  no i'rab reading: %s", exc)
        cards = [(w["word"], w, None, None, None) for w in morphology.analyze_sentence(text)]
        summary = None
    wide = get_settings().sentence_fact_senses
    return [{"arabic": word, "english": english(c, sense), "senses": english(c, sense, wide), "base": c.get("base") or word,
             "lemma": c.get("lemma") or "", "pos": c.get("pos") or "", "state": c.get("state"),
             "role": role or None, "case": case or None} for word, c, sense, role, case in cards], summary


def english(reading: dict, sense: str | None = None, senses: int | None = None) -> str:
    """One word's English: CAMeL's gloss in the class the grammar settled (morphology.gloss_as), else
    the dictionary's first sense of the very lemma (Wiktionary: مُسْرِعًا is "fast"), else "". Never a
    near spelling's: the nearest headword to آتِنَا is أتان, a she-ass. Up to `senses` senses a piece,
    the reader's setting when not given."""
    senses = senses or get_settings().sentence_senses
    first = dictionary_service.meaning_of(reading.get("lemma") or "")
    return literal(morphology.gloss_as(reading, sense), senses) or "/".join(first.split(", ")[:senses])


def translate(text: str) -> dict:
    """The sense, its source, and the words; the sense is None when nothing could give one."""
    pairs, summary = read_words(text)
    found = _whole_ayah(text, pairs) or _model_sense(text, **(_ayah_words(text, pairs) or {"rows": pairs}))
    return {"kind": kind_of(summary, pairs), **found}


def _whole_ayah(text: str, pairs: list[dict]) -> dict | None:
    """The ayah's published sense, when the text is one whole ayah and nothing more,
    and its published words too unless their count disagrees with the ayah's own,
    when CAMeL's stand rather than English landing under the wrong word."""
    if (hit := quran_search.whole_ayah(text)) is None:
        return None
    books = quran_library.for_ayah(hit.surah, hit.ayah, [get_settings().sentence_translation])
    if not books:
        return None
    found = {"meaning": standing(books[0]["text"]), "source": "translation", "ref": f"{hit.surah}:{hit.ayah}"}
    english = quran_meanings.for_ayah(hit.surah, hit.ayah)
    ayah_words = words(hit.arabic_text)
    if len(english) != len(ayah_words):
        return {**found, "words": pairs, "words_source": "camel"}
    return {**found, "words_source": "translation",
            "words": [{"arabic": w, "english": english.get(n, ""), "base": w} for n, w in enumerate(ayah_words, 1)]}


def _ayah_words(text: str, pairs: list[dict]) -> dict | None:
    """The grammar's rows with the Qur'an's word-by-word English when the text is a run from
    inside one ayah, and that ayah. None on any count mismatch or missing English, so English
    never lands under the wrong word; roles and cases stay the grammar's."""
    if (found := quran_search.ayah_run(text)) is None:
        return None
    hit, start = found
    published = quran_meanings.for_ayah(hit.surah, hit.ayah)
    run = [published.get(start + n, "") for n in range(len(pairs))]
    if len(pairs) != len(words(text)) or not all(run):
        return None
    return {"rows": [{**p, "english": en, "senses": en} for p, en in zip(pairs, run)],
            "words_source": "translation", "ref": f"{hit.surah}:{hit.ayah}"}


_PAIRS = {"(": ")", "[": "]", "“": "”"}
# What a sentence carried on past the ayah leaves at the cut: a dash, a comma, a colon.
_CUT_RE = re.compile(r"[\s,;:\-\u2013\u2014]+$")


def standing(text: str) -> str:
    """One ayah's slice of a running translation, made to stand on its own.

    The translation is prose cut at each ayah's end, so a sentence that runs on
    leaves its comma or dash at the cut, and a quote opened in one ayah closes in
    another. The cut is trimmed, and each mark left open, or closed with no
    opening, gets its partner at the other end.
    """
    text = _CUT_RE.sub("", text.strip())
    opened = []
    head = ""
    for c in text:
        if c in _PAIRS:
            opened.append(c)
        elif c in _PAIRS.values():
            if opened and _PAIRS[opened[-1]] == c:
                opened.pop()
            else:
                head = next(o for o, shut in _PAIRS.items() if shut == c) + head
    tail = "".join(_PAIRS[o] for o in reversed(opened))
    if text.count('"') % 2:
        # The odd quote opens when words follow it, else it closes one from before.
        last = text.rindex('"')
        tail, head = (tail + '"', head) if text[last + 1:].strip() else (tail, '"' + head)
    text = head + text + tail
    return text[:1].upper() + text[1:]


def _model_sense(text: str, rows: list[dict], words_source: str = "camel", ref: str | None = None) -> dict:
    """The model's one sentence over the words' facts; no sense when it is unreachable."""
    try:
        meaning = _asked(text, _QUESTION, lambda: ai.translate_sentence(text, _facts(rows))["english"])
    except Exception as exc:  # noqa: BLE001, a dead model leaves the word-by-word standing
        logger.info("sentence meaning  model failed: %s", exc)
        meaning = None
    return {"meaning": meaning, "source": "ai" if meaning else None, "ref": ref,
            "words": rows, "words_source": words_source}


def _facts(pairs: list[dict]) -> str:
    """One line per word: what the grammar read, and its English senses for the model to choose from."""
    return "\n".join(
        f"{n}. {p['arabic']} — {p['lemma'] or p['base']} ({p['pos'] or '-'}, {p['role'] or '-'}, {p['case'] or '-'}): "
        f"{p.get('senses') or p['english'] or '-'}" for n, p in enumerate(pairs, 1))


def _asked(text: str, question: str, ask) -> str:
    """One model answer per text, filed on disk under `question`: the server runs several
    processes, and a cache in each gave the same sentence two wordings by turns. A failure
    or an empty answer raises and is not filed. Two first askings at once both ask, and
    both return the one the store kept first."""
    if not (kept := _kept(text, question)):
        if not (answer := str(ask() or "").strip()):
            raise ValueError("the model answered with nothing")
        progress_store.keep_questions(module=_KEPT, sentence=text, source="ai",
                                      questions=[{"question": question, "answer": answer}])
        kept = _kept(text, question)
    return kept


def _kept(text: str, question: str) -> str | None:
    return next((r["answer"] for r in progress_store.kept_questions(_KEPT, text) if r["question"] == question), None)


def translate_english(text: str) -> dict:
    """English into Arabic: each word's candidates from the dictionary, always, and the
    whole as the model renders it, filed once like the other direction, and None when
    it is unreachable. The model never touches the word rows, so a wrong rendering
    cannot change a lookup."""
    rows = [{"arabic": (w["entries"][0]["arabic"] if w["entries"] else ""), "english": w["english"], "base": w["lemma"]}
            for w in dictionary_service.english_words(text)]
    try:
        meaning = _asked(text, _ARABIC, lambda: ai.render_in_arabic(text)["arabic"])
    except Exception as exc:  # noqa: BLE001, a dead model leaves the word-by-word standing
        logger.info("sentence meaning  model failed: %s", exc)
        meaning = None
    return {"kind": "sentence", "direction": "en", "meaning": meaning, "source": "ai" if meaning else None,
            "ref": None, "words": rows, "words_source": "wiktionary"}
