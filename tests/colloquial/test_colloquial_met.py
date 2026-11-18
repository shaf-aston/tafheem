"""No word is taught as new twice: a topic's word is `met` when an earlier topic (course order) taught it."""
import collections

from backend.services.colloquial import loader


def test_every_word_is_new_in_exactly_one_topic_its_first():
    first = loader._first_taught()
    new_in = collections.Counter()
    for unit in loader.spine():
        for lesson in unit["lessons"]:
            where = f"{unit['unit']}/{lesson['lesson']}"
            for word in loader._mark_met([{"id": i} for i in lesson.get("words") or []], where):
                if not word["met"]:
                    new_in[word["id"]] += 1
                    assert first[word["id"]] == where
    assert set(new_in) == set(first) and set(new_in.values()) == {1}


def test_the_catalogue_counts_each_topics_new_words():
    for dialect in loader.catalogue()["dialects"]:
        lessons = [lesson for unit in dialect["units"] for lesson in unit["lessons"] if lesson["written"]]
        assert all(0 <= lesson["new_words"] <= lesson["words"] for lesson in lessons)
        assert sum(lesson["new_words"] for lesson in lessons) == len(loader._first_taught())


def test_a_word_unknown_to_the_spine_is_new_where_it_stands():
    assert loader._mark_met([{"id": "not-a-spine-word"}], "unit-01/lesson-01") == [{"id": "not-a-spine-word", "met": False}]
