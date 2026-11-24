"""When a passage counts as an answer (match/answers): the PBS score gate."""
from backend.services.daleel.match.answers import answered, share_of
from backend.services.daleel.query.expand import Expansion


def gate(fold, english="", typed=(), related=()):
    row = ("corpus", "", "1:1", fold, english, "", fold, 1)
    return share_of(row, Expansion(typed=typed, related=related, roots=(), loose=()), 0.6)


def test_a_word_inside_another_word_is_not_found():
    """mining is not in undermining: the trigram index says it is, the gate must not."""
    assert gate("", "undermining the people", typed=("mining", "rules")) == 0


def test_half_the_question_in_whole_words_answers():
    assert gate("", "kindness to widows", typed=("caring", "widows")) == 0.5


def test_related_words_alone_do_not_answer_a_longer_question():
    assert gate("فيزياء كم مقدار", typed=("quantum", "physics"), related=("فيزياء", "كم", "مقدار")) == 0


def test_a_translation_answers_a_one_word_question():
    """patience asked in English finds الصبر in a book with no English at all."""
    assert gate("بالصبر", typed=("patience",), related=("صبر",)) == 0.6


def test_arabic_prefixes_do_not_hide_the_word():
    assert gate("واستعينوا بالصبر", typed=("صبر",)) == 1


def test_dictionaries_alone_do_not_answer_several_words():
    assert answered([1, 1], ["Dictionary", "Dictionary"], 2, 0.5) == [False, False]
    assert answered([1, 0.2], ["Fiqh", "Dictionary"], 2, 0.5) == [True, False]
    assert answered([1], ["Dictionary"], 1, 0.5) == [True]
