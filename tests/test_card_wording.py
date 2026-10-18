"""card_wording passes on hand-made cards: no parser, no CAMeL, so each rule is seen alone."""
from __future__ import annotations

from backend.services import card_wording
from backend.services.card_wording import counting, names, pieces


def test_the_sister_names_the_reason():
    cards = [{"role": "اسم كان", "reason": "مرفوع لأنه اسم كان. القاعدة: ..."}]
    names.sister(cards, [{"name": "اسم ليس"}])
    assert "لأنه اسم ليس" in cards[0]["reason"]


def test_two_khabars_side_by_side_are_counted():
    cards = [{"role": "خبر إن", "reason": "مرفوع لأنه خبر إن"}, {"role": "خبر إن", "reason": "مرفوع لأنه خبر إن"}]
    counting.counted(cards, [{}, {}])
    assert "خبر أول" in cards[0]["reason"] and "خبر ثانٍ" in cards[1]["reason"]


def test_one_khabar_is_not_counted():
    cards = [{"role": "مبتدأ", "reason": "لأنه مبتدأ"}, {"role": "خبر", "reason": "مرفوع لأنه خبر"}]
    counting.counted(cards, [{}, {}])
    assert cards[1]["reason"] == "مرفوع لأنه خبر"


def test_an_extra_ba_word_is_jarr_in_letters_and_its_place_in_meaning():
    cards = [{"role": "فاعل", "case": "raf'", "reason": "مرفوع لأنه فاعل. القاعدة: الفاعل مرفوع"}]
    pieces.extra_ba(cards, [{"extra_ba": "u"}])
    assert cards[0]["case"] == "jarr" and "مرفوع محلًا" in cards[0]["reason"] and cards[0]["reason"].endswith("الفاعل مرفوع")


def test_kaffa_names_the_pair_only_where_naming_found_it():
    cards = [{"word": "إِنَّمَا", "role": "حرف", "reason": "حرف"}, {"word": "إِنَّ", "role": "حرف", "reason": "حرف"}]
    pieces.kaffa(cards, [{"kaffa": "إن"}, {}])
    assert cards[0]["name"] == "كافة ومكفوفة" and "name" not in cards[1]


def test_every_pass_is_run_and_a_card_with_nothing_found_is_left_alone():
    assert len(card_wording.PASSES) == len(set(card_wording.PASSES)) == 10
    cards = [{"word": "زَيْدٌ", "role": "مبتدأ", "reason": "مرفوع لأنه مبتدأ"}]
    card_wording.word(cards, [{}])
    assert cards == [{"word": "زَيْدٌ", "role": "مبتدأ", "reason": "مرفوع لأنه مبتدأ"}]
