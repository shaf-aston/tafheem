"""naming.finish: what only the picture works out goes on the cards and comes off the drawing."""
from backend.services.nahw.book import frames
from backend.services.nahw.syntax.naming import CARD_FACTS, NAMED, finish


def test_a_masdar_ma_is_named_on_its_card_and_loses_its_gap():
    found = [{"role": None, "gap": {"rule": "x"}}]
    drawn = {"ma": [(None, None)], "columns": []}
    finish(found, drawn)
    assert found[0]["role"] == NAMED.harf and found[0]["built"] is False
    assert found[0]["named"] == frames()["masdar"]["named_by_word"]["ما"]
    assert "gap" not in found[0]


def test_the_card_facts_come_off_the_drawing():
    drawn = {key: [] for key in CARD_FACTS} | {"columns": []}
    drawn["piece_names"] = {}
    finish([], drawn)
    assert drawn == {"columns": []}
