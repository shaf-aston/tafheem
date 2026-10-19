"""card_wording passes on hand-made cards: no parser, no CAMeL, so each rule is seen alone."""
from __future__ import annotations

from backend.services import card_wording
from backend.services.card_wording import condition, counting, names, pieces
from backend.services.card_wording.reason import Reason


def test_the_sister_names_the_reason():
    cards = [{"role": "اسم كان", "reason": "مرفوع لأنه اسم كان. القاعدة: ..."}]
    card_wording.run([names.sister], cards, [{"name": "اسم ليس"}])
    assert "لأنه اسم ليس" in cards[0]["reason"]


def test_two_khabars_side_by_side_are_counted():
    cards = [{"role": "خبر إن", "reason": "مرفوع لأنه خبر إن"}, {"role": "خبر إن", "reason": "مرفوع لأنه خبر إن"}]
    card_wording.run([counting.counted], cards, [{}, {}])
    assert "خبر أول" in cards[0]["reason"] and "خبر ثانٍ" in cards[1]["reason"]


def test_one_khabar_is_not_counted():
    cards = [{"role": "مبتدأ", "reason": "لأنه مبتدأ"}, {"role": "خبر", "reason": "مرفوع لأنه خبر"}]
    card_wording.run([counting.counted], cards, [{}, {}])
    assert cards[1]["reason"] == "مرفوع لأنه خبر"


def test_an_extra_ba_word_is_jarr_in_letters_and_its_place_in_meaning():
    cards = [{"role": "فاعل", "case": "raf'", "reason": "مرفوع لأنه فاعل. القاعدة: الفاعل مرفوع"}]
    card_wording.run([pieces.extra_ba], cards, [{"extra_ba": "u"}])
    assert cards[0]["case"] == "jarr" and "مرفوع محلًا" in cards[0]["reason"] and cards[0]["reason"].endswith("الفاعل مرفوع")


def test_kaffa_names_the_pair_only_where_naming_found_it():
    cards = [{"word": "إِنَّمَا", "role": "حرف", "reason": "حرف"}, {"word": "إِنَّ", "role": "حرف", "reason": "حرف"}]
    card_wording.run([pieces.kaffa], cards, [{"kaffa": "إن"}, {}])
    assert cards[0]["name"] == "كافة ومكفوفة" and "name" not in cards[1]


def test_every_pass_is_run_and_a_card_with_nothing_found_is_left_alone():
    assert len(card_wording.PASSES) == len(set(card_wording.PASSES)) == 12
    cards = [{"word": "زَيْدٌ", "role": "مبتدأ", "reason": "مرفوع لأنه مبتدأ"}]
    card_wording.word(cards, [{}])
    assert cards == [{"word": "زَيْدٌ", "role": "مبتدأ", "reason": "مرفوع لأنه مبتدأ"}]


def test_a_reason_read_and_written_back_is_the_same_text():
    for text in ["مرفوع لأنه خبر إن. القاعدة: إن وأخواتها ترفع الخبر", "حرف مبني لا محل له من الإعراب",
                 "منصوب لأنه نعت لما قبله", "أ. ب. ج", ""]:
        assert Reason.read(text).text() == text


def test_a_pass_never_rewrites_the_rule():
    cards = [{"role": "خبر", "reason": "مرفوع لأنه خبر. القاعدة: لأنه خبر يرفع"},
             {"role": "خبر", "reason": "مرفوع لأنه خبر. القاعدة: لأنه خبر يرفع"}]
    card_wording.run([counting.counted], cards, [{}, {}])
    assert [c["reason"] for c in cards] == ["مرفوع لأنه خبر أول. القاعدة: لأنه خبر يرفع",
                                           "مرفوع لأنه خبر ثانٍ. القاعدة: لأنه خبر يرفع"]


def test_a_condition_verb_says_its_part_before_the_rule_and_prints_it():
    cards = [{"role": "فعل", "type": "fi'l", "case": "jazm", "reason": "فعل مضارع مجزوم. القاعدة: الفعل المضارع معرب"}]
    card_wording.run([condition.condition], cards, [{"condition": {"part": "verb", "family": "jazm", "tie": None}}])
    assert cards[0]["reason"] == "فعل مضارع مجزوم، وهو فعل الشرط مجزوم. القاعدة: الفعل المضارع معرب"
    assert cards[0]["name"] == "فعل الشرط"


def test_a_tied_answer_names_its_letter_and_a_conditional_noun_says_what_it_is_first():
    cards = [{"role": "مبتدأ", "type": "ism", "reason": "مبني في محل رفع لأنه مبتدأ. القاعدة: المبتدأ مرفوع"},
             {"role": "فعل", "type": "fi'l", "case": "mabni", "reason": "فعل أمر مبني على السكون. القاعدة: فعل الأمر مبني"}]
    card_wording.run([condition.condition], cards, [{"condition": {"part": "opener", "kind": "اسم شرط جازم"}},
                                                    {"condition": {"part": "answer", "family": "jazm", "tie": "ف"}}])
    assert cards[0]["reason"].startswith("اسم شرط جازم، مبني في محل رفع")
    assert "والفاء رابطة لجواب الشرط، وهو جواب الشرط في محل جزم. القاعدة" in cards[1]["reason"]


def test_a_verb_says_its_drawn_doer_and_a_pronoun_written_on_it_says_its_place():
    cards = [{"role": "فعل", "type": "fi'l", "reason": "فعل ماضٍ مبني على الفتح. القاعدة: الفعل الماضي مبني"}]
    found = [{"doer": {"role": "فاعل", "detail": "ضمير مستتر تقديره هو"},
              "attached": [{"before": False, "form": "نا", "role": "مفعول به"}]}]
    card_wording.run([pieces.doer], cards, found)
    assert cards[0]["reason"] == ("فعل ماضٍ مبني على الفتح، وفاعله ضمير مستتر تقديره هو، "
                                  "و«نا» ضمير متصل مبني في محل نصب مفعول به. القاعدة: الفعل الماضي مبني")
