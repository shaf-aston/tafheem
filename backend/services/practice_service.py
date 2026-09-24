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

    # 2. The role of the most useful word, the subject if the sentence has one.
    key_roles = config["key_roles"]
    key_word = next(
        (w for w in words if any(role in (w.get("role") or "") for role in key_roles)),
        words[0] if words else None,
    )
    if key_word:
        questions.append(_fill(
            templates["key_role"],
            word=key_word["word"],
            role=key_word.get("role"),
            reason=key_word.get("reason", ""),
            case=key_word.get("case"),
        ))

    # 3. Case and its sign, only for a word that actually shows one.
    case_types = config["case_types"]
    if marked := next(
        (w for w in words if w.get("type") in case_types and w.get("sign")), None
    ):
        questions.append(_fill(
            templates["case_sign"],
            word=marked["word"],
            case=marked.get("case"),
            sign=marked.get("sign"),
            reason=marked.get("reason", ""),
        ))

    # 4. The whole sentence, as recall.
    missing = config["missing"]
    breakdown = " | ".join(
        f"{w['word']}: {w.get('role') or missing}, {w.get('case') or missing}" for w in words
    )
    questions.append(_fill(templates["full_iraab"], sentence=sentence, breakdown=breakdown))

    return questions[: config["max_questions"]]
