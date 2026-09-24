"""Outcome tests for the Tamreen build, not structural ones.

`test_tamreen.py` checks the *shape* every exercise must have (a tag, a
sentence, an answer) - it would pass just as happily if a whole exercise's
content quietly changed, as long as the shape held. These tests instead pin
the actual reviewed content: the counts and specific facts a three-lane
review + adjudication pass produced on 2026-09-05, so a future silent edit
(a bad merge, a re-run that drops a picture) is caught even though the shape
still validates.

If a number here changes on purpose - a new form harvested, a doubt
resolved - update the expectation deliberately; don't delete the test.
"""
from backend.services import tamreen

# rules, examples per slug, as the review left them.
SIZES = {
    "mafool-maahu": (17, 15),
    "haal": (22, 28),
    "mafool-lahu-fihi": (15, 18),
    # Harvested 2026-09-16: two readers per picture, an Opus review settling every disagreement.
    "mushabbahat-laysa-la-jins": (18, 24),
    "mafool-mutlaq": (10, 15),
    "naat-sababi": (10, 20),
    "mustasna": (23, 20),
    # Harvested 2026-09-17: one word per picture, read twice blind, 11 settled by a third reader.
    "munsarif": (0, 110),
}
NEW = ("mushabbahat-laysa-la-jins", "mafool-mutlaq", "naat-sababi", "mustasna", "munsarif")


def _by_slug():
    return {ex["key"]: ex for ex in tamreen.exercises()}


def test_exercise_sizes_match_the_reviewed_build():
    exercises = _by_slug()
    assert set(exercises) == set(SIZES)
    for slug, (rules, examples) in SIZES.items():
        assert len(exercises[slug]["rules"]) == rules, slug
        assert len(exercises[slug]["examples"]) == examples, slug


def test_tag_vocabulary_matches_the_reviewed_build():
    # 52, then 11 for munsarif: the two verdicts and the nine causes its answers use
    # (compounding, تركيب, is an option on the form but no answer ticks it).
    assert len(tamreen.tags()) == 63


def test_every_munsarif_question_is_filed_under_its_verdicts_and_its_causes():
    # A word can be both munsarif and ghair munsarif; the form says to tick both then.
    examples = _by_slug()["munsarif"]["examples"]
    for example in examples:
        answer = example["parts"][0]["answer"]
        assert ("munsarif" in example["tags"]) == ("منصرف" in answer), example["id"]
        assert ("ghair-munsarif" in example["tags"]) == ("غير منصرف" in answer), example["id"]
        assert len(example["tags"]) == len(answer), example["id"]


def test_flagged_doubts_are_exactly_the_ones_the_review_left():
    # A part carries a doubt where a reviewer found the teacher's tick and
    # the teacher's own explanation disagree; a picture carries one where
    # three readers could not settle a vowel mark. These counts must not
    # silently grow (an unreviewed answer sneaking in) or shrink (a real
    # doubt getting smoothed over).
    exercises = _by_slug()
    part_doubts = {slug: sum("doubt" in p for e in ex["examples"] for p in e["parts"])
                   for slug, ex in exercises.items()}
    picture_doubts = {slug: sum("doubt" in e for e in ex["examples"])
                      for slug, ex in exercises.items()}
    assert part_doubts == {"mafool-maahu": 0, "haal": 10, "mafool-lahu-fihi": 0, **dict.fromkeys(NEW, 0)}
    # The one new picture doubt: mushabbahat picture 13 disagrees with itself.
    assert picture_doubts == {"mafool-maahu": 1, "haal": 8, "mafool-lahu-fihi": 1,
                              **dict.fromkeys(NEW, 0), "mushabbahat-laysa-la-jins": 1}


def test_haal_e11_keeps_its_flagged_contradiction():
    # The clearest case: the teacher's ruling and their own explanation for
    # it point at different rows. This must stay visible, not resolved by
    # guessing which side is right.
    haal_e11 = next(e for e in _by_slug()["haal"]["examples"] if e["id"] == "haal-e11")
    part_b = next(p for p in haal_e11["parts"] if p["letter"] == "b")
    assert "doubt" in part_b


def test_haal_e24_keeps_the_picture_correction():
    # Verified by directly viewing haal-23.png: the word is yathbutu, not
    # the visually similar yanbuthu an earlier transcription pass read.
    haal_e24 = next(e for e in _by_slug()["haal"]["examples"] if e["id"] == "haal-e24")
    assert "يَثبُتُ" in haal_e24["sentence"]
    assert "يَنبُثُ" not in haal_e24["sentence"]
