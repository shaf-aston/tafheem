"""Practice questions built from an I'raab analysis, with no AI involved.

This is the offline path: given what the rule engine worked out about a sentence,
turn it into questions a student can answer. It used to live inside the router,
where nothing could test it without starting a web server.

The wording of every question lives in data/practice/templates.json. This module
only decides which questions a given sentence can support, and fills them in.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.services.nahw_book import teacher_rules
from backend.services.rule_engine import UNNAMED

TEMPLATES_FILE = Path(__file__).parent.parent / "data" / "practice" / "templates.json"


@lru_cache(maxsize=1)
def _config() -> dict:
    return json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))


def _fill(template: dict, **values) -> dict:
    """One question, with every blank filled. A blank the analysis could not
    supply prints the placeholder rather than the word "None"."""
    missing = _config()["missing"]
    safe = {key: (value or missing) for key, value in values.items()}
    return {
        "question": template["question"].format(**safe),
        "answer": template["answer"].format(**safe).strip(),
        "hint": template["hint"].format(**safe),
    }


def _said(case: str | None) -> str | None:
    """A case as the cards say it, in the book's Arabic (teacher.json case_said)."""
    return teacher_rules()["case_said"]["word"].get(case, case)


def from_analysis(sentence: str, rule_result: dict) -> list[dict]:
    """Every question this sentence can support, best first."""
    config = _config()
    templates = config["questions"]
    words = [word for word in rule_result.get("words", []) if word.get("word")]
    questions: list[dict] = []

    # 1. What kind of sentence is this, answerable for any sentence at all.
    sentence_type = templates["sentence_type"]
    summary = rule_result.get("summary", "")
    questions.append({
        **_fill(sentence_type, sentence=sentence, summary=summary),
        "answer": (
            sentence_type["answer"].format(summary=summary)
            if summary
            else sentence_type["answer_when_unknown"]
        ),
    })

    # 2. The role of the most useful word, the doer or subject if the sentence has one;
    # only a word the analysis named, so the answer is never a guess or a dash
    named = [w for w in words if w.get("role") not in (None, UNNAMED) and not w.get("gap")]
    if key_word := next((w for w in named if w.get("role_key") in config["key_roles"]), named[0] if named else None):
        questions.append(_fill(
            templates["key_role"],
            word=key_word["word"],
            reason=key_word.get("reason", ""),
            case=_said(key_word.get("case")),
        ))

    # 3. Case and its sign, only for a word whose ending is a case (not built) and shows one.
    if marked := next((w for w in words if w.get("sign") and w.get("case") not in (None, "mabni")), None):
        questions.append(_fill(
            templates["case_sign"],
            word=marked["word"],
            case=_said(marked.get("case")),
            sign=marked.get("sign"),
            reason=marked.get("reason", ""),
        ))

    # 4. The whole sentence, as recall.
    missing = config["missing"]
    breakdown = " | ".join(
        f"{w['word']}: {w.get('role') or missing}, {_said(w.get('case')) or missing}" for w in words
    )
    questions.append(_fill(templates["full_iraab"], sentence=sentence, breakdown=breakdown))

    return questions[: config["max_questions"]]
