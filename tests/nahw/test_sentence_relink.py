"""Moving a link through the Sentence leaves it reading as a Sentence built fresh on the moved tokens."""
from backend.services.nahw.syntax.facts import Sentence


def _tokens() -> list[dict]:
    word = {"pos": "NOM", "pos_camel": "noun", "lemma": "ك", "form": "ك"}
    return [{**word, "id": i, "head": head, "rel": rel} for i, head, rel in
            [(1, 0, "---"), (2, 1, "OBJ"), (3, 1, "MOD"), (4, 3, "MOD")]]


def _kids(s: Sentence) -> dict[int, list[int]]:
    return {t["id"]: [k["id"] for k in s.kids(t)] for t in s.tokens}


def test_a_relinked_word_hangs_where_a_fresh_sentence_puts_it():
    tokens = _tokens()
    s = Sentence(tokens)
    s.relink(tokens[3], 1, "SBJ")  # 4 moves up to 1, between its new siblings in word order
    s.relink(tokens[1], 4, "OBJ")  # 2 moves down under the word that just moved
    assert _kids(s) == _kids(Sentence(tokens)) == {1: [3, 4], 2: [], 3: [], 4: [2]}
    assert (tokens[3]["head"], tokens[3]["rel"]) == (1, "SBJ")


def test_a_loop_walking_the_old_kids_finishes_on_them():
    tokens = _tokens()
    s = Sentence(tokens)
    seen = []
    for kid in s.kids(tokens[0]):
        seen.append(kid["id"])
        s.relink(kid, 4, "MOD")
    assert seen == [2, 3]
