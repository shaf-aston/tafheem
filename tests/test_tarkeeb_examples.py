"""The worked examples must be sound before the app is allowed to draw them.

A tree that skips a word still renders, it just renders something untrue, so
that is the case checked hardest here.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""

from backend.services import tarkeeb_examples

TOPICS = {"verbal"}  # the shared topic list; every example is checked against it


def test_every_shipped_example_loads_and_checks_out():
    books = tarkeeb_examples.books()
    assert books, "no example books found"
    assert sum(len(book["examples"]) for book in books) == 47


def test_each_example_carries_the_book_it_came_from():
    assert all(example["book"] for example in tarkeeb_examples.all_examples())


def test_ids_are_unique_across_every_book():
    ids = [example["id"] for example in tarkeeb_examples.all_examples()]
    assert len(ids) == len(set(ids))


def test_a_tree_that_skips_a_word_is_rejected():
    missing = {
        "id": "test", "topic": "verbal", "sentence": "أ ب", "words": ["أ", "ب"],
        "tree": {"children": [{"word": 0}]},
    }
    assert tarkeeb_examples._faults(missing, TOPICS) == [
        "its tree covers words [0], not all 2 of them"
    ]


def test_a_tree_that_uses_a_word_twice_is_rejected():
    doubled = {
        "id": "test", "topic": "verbal", "sentence": "أ ب", "words": ["أ", "ب"],
        "tree": {"children": [{"word": 0}, {"word": 0}]},
    }
    assert tarkeeb_examples._faults(doubled, TOPICS)


def test_words_that_do_not_spell_the_sentence_are_rejected():
    wrong = {
        "id": "test", "topic": "verbal", "sentence": "أ ب", "words": ["أ", "ج"],
        "tree": {"children": [{"word": 0}, {"word": 1}]},
    }
    assert "its words do not spell out its sentence" in tarkeeb_examples._faults(wrong, TOPICS)


def test_a_word_split_into_its_pieces_is_still_accepted():
    # The book draws وَاللهِ as two columns, وَ and اللهِ. That is not a fault.
    split = {
        "id": "test", "topic": "verbal", "sentence": "وَاللهِ", "words": ["وَ", "اللهِ"],
        "tree": {"children": [{"word": 0}, {"word": 1}]},
    }
    assert tarkeeb_examples._faults(split, TOPICS) == []


def test_an_example_filed_under_an_unknown_topic_is_rejected():
    # Browsing is by topic, so a wrong key would hide the example completely.
    stray = {
        "id": "test", "topic": "typo", "sentence": "أ", "words": ["أ"],
        "tree": {"word": 0},
    }
    assert tarkeeb_examples._faults(stray, TOPICS) == [
        "is filed under topic 'typo', which topics.json does not declare"
    ]


def test_every_shipped_example_is_reachable_from_a_topic_chip():
    declared = {topic["key"] for topic in tarkeeb_examples.topics()}
    assert {example["topic"] for example in tarkeeb_examples.all_examples()} <= declared


def test_topics_are_shared_not_per_book():
    # Two books teaching kana must land under one chip, so no book file may
    # declare its own topics.
    assert all("topics" not in book for book in tarkeeb_examples.books())
