"""Cutting Sharh Mushkil al-Athar into issues.

A hand-built miniature in OpenITI's marks: each case is a rule in
services/mushkil_split. The real book is checked by the counts build_mushkil.py
prints and by data/hadith/mushkil-unplaced.json.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
from backend.services import mushkil_split

BOOK = """######OpenITI#
#META# 000.SortField :: X
#META#Header#End#

# | بسم الله الرحمن الرحيم
# فاصلة قبل أول باب
# | 1 باب بيان مشكل ما روي عن رسول الله
~~صلى الله عليه وسلم في الصلاة PageV01P005
# 1 حدثنا يونس عن ابن وهب ms0001 الأول
# 2 وما حدثنا فهد الثاني قال أبو جعفر فهذا من كلامه
# قال أبو جعفر فهذا وجه التوفيق
~~بينهما
# | اب بيان ما أشكل علينا في الصوم
# حدثنا بكار حدثنا مسلم الثالث
# حدثنا بكار حدثنا مسلم الثالث
# أخبرنا ابن وهب الرابع
# | 3 باب ثالث
# 5 ومن ذلك ما حدثنا أحمد الخامس
"""


def test_heading_is_cleaned_and_a_damaged_one_is_repaired():
    issues, _ = mushkil_split.split(BOOK)
    assert [i["heading"] for i in issues] == [
        "باب بيان مشكل ما روي عن رسول الله صلى الله عليه وسلم في الصلاة",
        "باب بيان ما أشكل علينا في الصوم",
        "باب ثالث",
    ]
    assert [i["id"] for i in issues] == [1, 2, 3]


def test_narrations_are_counted_and_marks_are_gone():
    issues, _ = mushkil_split.split(BOOK)
    assert [len(i["narrations"]) for i in issues] == [2, 2, 1]
    assert "ms0001" not in issues[0]["narrations"][0]
    assert "PageV" not in issues[0]["heading"]


def test_discussion_is_kept_with_its_wrapped_line():
    issues, _ = mushkil_split.split(BOOK)
    assert issues[0]["discussion"] == "قال أبو جعفر فهذا من كلامه قال أبو جعفر فهذا وجه التوفيق بينهما"


def test_stray_paragraph_is_unplaced_and_listed():
    _, unplaced = mushkil_split.split(BOOK)
    assert [row["why"] for row in unplaced if row["text"] == "فاصلة قبل أول باب"] == ["before the first bab"]


def test_duplicate_consecutive_paragraph_is_not_counted_twice():
    issues, unplaced = mushkil_split.split(BOOK)
    assert issues[1]["narrations"].count("حدثنا بكار حدثنا مسلم الثالث") == 1
    assert any(row["why"] == "repeats the paragraph before it" for row in unplaced)


def test_offset_is_the_headings_line_in_the_source():
    issues, _ = mushkil_split.split(BOOK)
    lines = BOOK.split("\n")
    assert all("اب" in lines[i["offset"] - 1] for i in issues)


def test_tahawis_voice_at_the_end_of_a_narration_paragraph_is_discussion():
    issues, _ = mushkil_split.split(BOOK)
    assert issues[0]["narrations"][1] == "2 وما حدثنا فهد الثاني"
