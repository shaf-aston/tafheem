"""Move links the parser drew where the books hang them: a مفعول معه on its verb, a list on its first word, a verb under its مبتدأ."""
from __future__ import annotations

from backend.services.nahw.book import is_one
from backend.services.nahw.syntax.facts import is_prefix, is_verb
from backend.services.nahw.syntax.followers import chain_first
from backend.services.nahw.syntax.naming import NAMED
from backend.services.nahw.syntax.picture.names import ATF, FRAMES
from backend.services.nahw.syntax.picture.state import Picture


def rehang(c: Picture) -> None:
    """Move links the parser drew where the books hang them: a مفعول معه on its verb, a list on its first word, a verb under its مبتدأ."""
    bases, by_id, drawn, named, role_of = c.bases, c.by_id, c.drawn, c.named, c.role_of
    # جاء الأميرُ والجيشَ: the مفعول معه and its و hang on the verb, not inside the فاعل
    for token, found in zip(bases, named):
        if role_of[token["id"]] in FRAMES["on_the_verb"] and (at_gov := found.get("governor")) is not None:
            waw = by_id.get(token["head"])
            moved = waw if waw and is_prefix(waw) else token
            moved = {**moved, "head": bases[at_gov]["id"]}
            drawn[[t["id"] for t in drawn].index(moved["id"])], by_id[moved["id"]] = moved, moved
    # وَإِقَامِ الصَّلَاةِ وَإِيتَاءِ الزَّكَاةِ وَالْحَجِّ: the parser chains a list, each و on the معطوف before it;
    # every معطوف of a chain is joined on its first word, the معطوف عليه, as its card says
    # (card_wording.counting.followed), so each حرف عطف hangs on that word and the معطوفات stand side by side
    def joins(token: dict) -> bool:  # a حرف عطف, still named حرف here: the chart's finer name comes later (finer_name)
        return role_of.get(token["id"]) in (NAMED.harf, ATF) and is_one(token["form"], "atf")
    def joined_on(at: int) -> int | None:  # the word a معطوف's و hangs on
        waw = by_id.get(by_id[at]["head"])
        return waw["head"] if role_of.get(at) == NAMED.matoof and waw and joins(waw) and waw["head"] in by_id else None
    for waw in [t for t in drawn if joins(t) and t["head"] in by_id]:
        if (first := chain_first(waw["head"], joined_on)) != waw["head"]:
            moved = {**waw, "head": first}
            drawn[[t["id"] for t in drawn].index(moved["id"])], by_id[moved["id"]] = moved, moved
    # جاء الولدُ وهو يبكي: the parser can hang the مبتدأ under the verb after it; the verb's sentence
    # is the مبتدأ's khabar, so the verb hangs on the مبتدأ and the مبتدأ where the verb hung
    for verb in [t for t in drawn if is_verb(t)]:
        subject = next((t for t in drawn if t["head"] == verb["id"] and t["id"] < verb["id"]
                        and role_of.get(t["id"]) == NAMED.mubtada), None)
        for moved in ({**subject, "head": verb["head"]}, {**verb, "head": subject["id"]}) if subject else ():
            drawn[[t["id"] for t in drawn].index(moved["id"])], by_id[moved["id"]] = moved, moved
    c.joins = joins
