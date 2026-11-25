"""Repair: إِنْ تَضْرِبْ أَضْرِبْ. A command answers a condition only with فَ written on it, so an
untied verb the parser read as a command, after a جازم condition and its verb, is the present
in jazm: its أ is the speaker's, not a command's hamza."""
from __future__ import annotations

from backend.services.nahw.book import condition_of
from backend.services.nahw.syntax.facts import Sentence, is_prefix, is_verb


def untied_command(s: Sentence) -> None:
    tokens = s.tokens
    words = [t for t in tokens if not t["form"].endswith("+") and not t["form"].startswith("+")]
    for i, opener in enumerate(words[:-2]):
        frame = condition_of(opener["form"])
        if not frame or not frame.get("case") or not is_verb(words[i + 1]):
            continue
        answer = words[i + 2]
        tied = any(is_prefix(t) and t["id"] == answer["id"] - 1 for t in tokens)
        if is_verb(answer) and answer.get("asp") == "c" and not tied:
            answer["asp"] = "i"


def clause_on_its_fa(s: Sentence) -> None:
    """أَيُّمَا امْرَأَةٍ نَكَحَتْ فَنِكَاحُهَا بَاطِلٌ: what a فاء brings is its own clause, hung on the فاء (as جواب
    الشرط or as what it joins), so a فاعل never reaches back over it to a verb before it. The word heading the words
    after a ف, hung past it on the ف's own head (a word before the ف) while the ف holds nothing, hangs on the ف."""
    for fa in s.tokens:
        if fa["form"] != "ف+" or any(k["rel"] == "OBJ" for k in s.kids(fa)):
            continue
        after = next((t for t in s.tokens if t["id"] == fa["id"] + 1), None)
        top = after and s.climb(after, lambda t: t["head"] == fa["head"])
        if top and top["head"] == fa["head"] and top["id"] > fa["id"] and 0 < fa["head"] < fa["id"]:
            s.relink(top, fa["id"], "OBJ")
