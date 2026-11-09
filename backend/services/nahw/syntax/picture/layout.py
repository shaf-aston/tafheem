"""One column per written piece (a prefix, the word, its suffix), and the links the parser gave."""
from __future__ import annotations

from backend.services.nahw.syntax.naming import NAMED
from backend.services.text.harakat import letters, own_letters, written_sizes
from backend.services.nahw.syntax.picture.state import Picture


def lay_out(c: Picture) -> None:
    """One column per written piece (a prefix, the word, its suffix), and the links the parser gave."""
    bases, named, tokens, words = c.bases, c.named, c.tokens, c.words
    # بِـ، وَ، ـهُ: written onto a word, yet each a word of its own in the books, so each is
    # drawn in its own column and joins the way a word typed apart does (لِمَنْ is a
    # جار ومجرور); only a verb keeps what is written after it, its doer and object, inside it
    split = {piece["id"]: piece for found in named for piece in found.get("attached", [])
             if piece["before"] or found["role"] != NAMED.fil}
    by_id = {t["id"]: t for t in tokens}
    drawn, columns, written = [], [], []  # written: the typed word each column was cut from
    for i, (word, token, found) in enumerate(zip(words, bases, named)):
        before = [by_id[p["id"]] for p in found.get("attached", []) if p["id"] in split and p["before"]]
        after = [by_id[p["id"]] for p in found.get("attached", []) if p["id"] in split and not p["before"]]
        sizes = written_sizes(before, token, after, word)
        spans = sizes[:len(before)] + [len(letters(word)) - sum(sizes)] + sizes[len(before):]
        drawn += before + [token] + after
        columns += [own_letters(word, sum(spans[:k]), sum(spans[k + 1:])) for k in range(len(spans))]
        written += [i] * len(spans)
    typed_at = {token["id"]: index for index, token in enumerate(bases)}
    role_of = {token["id"]: found["role"] for token, found in zip(bases, named)} | {
        key: piece["role"] for key, piece in split.items()}
    why_of = {token["id"]: found.get("gap") for token, found in zip(bases, named)}
    c.by_id, c.columns, c.drawn, c.role_of, c.split = by_id, columns, drawn, role_of, split
    c.typed_at, c.why_of, c.written = typed_at, why_of, written
