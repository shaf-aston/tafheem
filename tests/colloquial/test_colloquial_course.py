"""A phrase or example sentence is taught once in the whole course, however it is spelt."""
from backend.services.colloquial import loader


def _course(*lines):
    return [{"unit": f"unit-{n:02}", "lessons": [{"lesson": "lesson-01", "phrases": [{"english": line}]}]}
            for n, line in enumerate(lines, 1)]


def test_a_line_taught_again_in_other_words_is_named_with_both_topics():
    said = loader.course_faults(_course("Where's the lift?", "where is the  LIFT", "This isn't it.", "This is not it!"))
    assert said == ["spine unit-02/lesson-01 teaches 'where is the  LIFT' again, already taught in unit-01/lesson-01",
                    "spine unit-04/lesson-01 teaches 'This is not it!' again, already taught in unit-03/lesson-01"]


def test_a_sentence_counts_as_a_line_too_and_different_lines_pass():
    course = _course("Do you have another colour?", "Do you have another size?")
    course[1]["lessons"].append({"lesson": "lesson-02", "sentences": [{"english": "Do you have another color?"}]})
    assert [f.split(" teaches")[0] for f in loader.course_faults(course)] == ["spine unit-02/lesson-02"]


def test_the_real_course_teaches_every_line_once():
    assert loader.course_faults(loader.spine()) == []
