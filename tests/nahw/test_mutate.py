"""The mutation guard derives each mutant's expected answer from the source key, and tells an
honest miss (the app flagged a reading it had to assume) from a silent one."""
import json
from collections import defaultdict

from backend.scripts.nahw import mutate


def test_a_nominal_sentence_gives_every_mutant_with_its_derived_key():
    ex = {"sentence": "الطَّالِبُ مُجْتَهِدٌ", "key": ["مبتدأ", "خبر"]}
    got = {kind: (s, key) for kind, s, key in mutate.mutations(ex)}
    assert got["bare"] == ("الطالب مجتهد", ["مبتدأ", "خبر"])
    assert got["noun"] == ("المعلمُ مُجْتَهِدٌ", ["مبتدأ", "خبر"])
    assert got["inna"] == ("إِنَّ الطَّالِبَ مُجْتَهِدٌ", ["حرف", "اسم إن", "خبر إن"])
    assert got["kana"] == ("كَانَ الطَّالِبُ مُجْتَهِدًا", ["فعل", "اسم كان", "خبر كان"])


def test_a_three_word_sentence_gets_no_governor_mutant():
    ex = {"sentence": "كَتَبَ زَيْدٌ الدَّرْسَ", "key": ["فعل", "فاعل", "مفعول به"]}
    assert {k for k, _, _ in mutate.mutations(ex)} == {"bare", "rename"}


def test_a_wrong_mutant_is_flagged_only_when_every_wrong_card_says_it_assumed(monkeypatch):
    ex = {"id": "x1", "set": "t", "sentence": "كُتِبَ الدَّرْسُ", "key": ["فعل", "نائب فاعل"]}
    right = {"words": [{"word": "كُتِبَ", "role": "فعل"}, {"word": "الدَّرْسُ", "role": "نائب فاعل"}]}
    bare = {"words": [{"word": "كتب", "role": "فعل"}, {"word": "الدرس", "role": "مفعول به"}]}
    monkeypatch.setattr(mutate, "routed", lambda s, api: right if s == ex["sentence"] else bare)
    stats = mutate.run([ex], defaultdict(list))
    assert (stats["bare"]["wrong"], stats["bare"]["flagged"]) == (1, 0)
    bare["words"][1]["assumed"] = {"vox": "p"}
    stats = mutate.run([ex], defaultdict(list))
    assert (stats["bare"]["wrong"], stats["bare"]["flagged"]) == (1, 1)


def test_the_check_fails_on_a_lost_mutant_or_more_unflagged_misses(monkeypatch, tmp_path):
    base = {"bare": {"right": 2, "wrong": 1, "flagged": 0, "whole": ["a", "b"]}}
    (tmp_path / "b.json").write_text(json.dumps(base))
    monkeypatch.setattr(mutate, "BASELINE", tmp_path / "b.json")
    level = {"bare": {"right": 2, "wrong": 1, "flagged": 0, "crashed": 0, "whole": ["a", "b"]}}
    assert mutate.check(level, {"a", "b"}, partial=False) == 0
    lost = {"bare": {**level["bare"], "right": 1, "whole": ["a"]}}
    assert mutate.check(lost, {"a", "b"}, partial=True) == 1
    worse = {"bare": {**level["bare"], "wrong": 2}}
    assert mutate.check(worse, {"a", "b"}, partial=False) == 1
    flagged = {"bare": {**level["bare"], "wrong": 2, "flagged": 1}}
    assert mutate.check(flagged, {"a", "b"}, partial=False) == 0
