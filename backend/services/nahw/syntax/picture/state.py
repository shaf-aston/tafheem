"""The one state the picture"s phases share, so each phase reads its inputs from here and writes its results back."""
from __future__ import annotations


class Picture:
    """Everything one sentence"s picture has worked out so far.

    `build` makes it from the typed words; each phase in this package reads what it needs off it
    and sets what the later phases read. A name is set by the phase that makes it, never before.
    """

    __slots__ = ("words", "tokens", "named", "bases", "by_id", "columns", "drawn", "role_of", "split",
        "typed_at", "why_of", "written", "joins", "after_noun", "at", "fronted", "hung", "kept", "khabars",
        "mubdal_minhu", "pair_of", "said", "sentence", "understand", "understood", "understood_pair",
        "detail_of", "named_by_unsaid", "opens", "replies", "said_verb", "job_by_place", "job_of",
        "kind_of_ma", "ma_card", "masdar", "nominal", "family_of", "framed", "label_of", "name_of", "place_of",
        "clauses", "described", "in_place", "children_of", "depth", "parent", "pulled", "roots", "opened",
        "root", "chained", "doer_of", "persons_of", "seen")

    def __init__(self, words: list[str], tokens: list[dict], named: list[dict], bases: list[dict]) -> None:
        self.words, self.tokens, self.named, self.bases = words, tokens, named, bases
