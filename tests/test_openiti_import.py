"""The OpenITI parser, argued with on text small enough to read.

Every case here is one the real books actually threw, not an invented one. The
verse split across two paragraphs is from the Alfiyya, the two heading schemas
are from Quduri and al-Hidaya, and the mid-sentence page marker is from
Mukhtasar al-Quduri.
"""
from __future__ import annotations

from backend.scripts.import_openiti import parse

_HEADER = "######OpenITI#\n#META# bk: x\n#META#Header#End#\n"


def _parse(body: str):
    return parse(_HEADER + body)


def test_wrapped_lines_become_one_passage():
    """`~~` continues the paragraph above; it is not a passage of its own."""
    result = _parse("# الكلام هو اللفظ المركب المفيد\n~~بالوضع وأقسامه ثلاثة\n")

    assert len(result.passages) == 1
    assert result.passages[0][2] == "الكلام هو اللفظ المركب المفيد بالوضع وأقسامه ثلاثة"


def test_split_verse_is_put_back_together():
    """A half-verse left ending in the separator takes the next line as its other half.

    The Alfiyya sets a line as "صدر ... عجز"; where the digitiser slipped, the
    two halves are two paragraphs and the first keeps the dangling separator.
    Stored apart they are two fragments that rhyme with nothing.
    """
    result = _parse("# بتا فعلت وأتت ويا افعلي ...\n# ونون أقبلن فعل ينجلي\n")

    assert len(result.passages) == 1
    assert result.passages[0][2] == "بتا فعلت وأتت ويا افعلي ... ونون أقبلن فعل ينجلي"


def test_whole_verse_on_one_line_is_left_alone():
    """The ordinary case must not be merged into the line after it."""
    result = _parse(
        "# كلامنا لفظ مفيد كاستقم ... واسم وفعل ثم حرف الكلم\n"
        "# واحده كلمة والقول عم ... وكلمة بها كلام قد يؤم\n"
    )

    assert len(result.passages) == 2


def test_heading_and_page_are_carried_forward():
    """Both are stated once and then apply until the next one."""
    result = _parse(
        "### | AUTO 1 - كتاب الطهارة\n"
        "# PageV01P005\n"
        "# غسل الأعضاء الثلاثة ومسح الرأس والمرفقان والكعبان\n"
        "# والمفروض في مسح الرأس مقدار الناصية لما روى المغيرة\n"
    )

    assert [p[1] for p in result.passages] == ["كتاب الطهارة", "كتاب الطهارة"]
    assert [p[0] for p in result.passages] == ["1/5", "1/5"]


def test_both_heading_schemas_lose_their_bookkeeping():
    """Shamela writes "AUTO", al-Jami' al-Kabir writes the depth at both ends.

    Neither is part of the chapter's name, and both were being printed on the
    citation under the book's name.
    """
    shamela = _parse("### || AUTO باب التيمم\n# ومن لم يجد الماء\n~~فتيمم بالصعيد\n")
    jamic = _parse("# |1 كتاب الطهارات 1\n# الماء الذي يجوز به الوضوء\n~~ومالا يجوز به\n")

    assert shamela.passages[0][1] == "باب التيمم"
    assert jamic.passages[0][1] == "كتاب الطهارات"


def test_file_machinery_is_not_quotable():
    """Page markers, milestones and quote tags are addresses, not words."""
    result = _parse("# وإن حجر عليه لم يصر ms073 محجورا @QB@ عليه @QE@ PageV01P141\n")

    text = result.passages[0][2]
    for machinery in ("ms073", "@QB@", "@QE@", "PageV01P141"):
        assert machinery not in text


def test_a_line_of_almost_nothing_is_dropped():
    """A stray separator is not a passage; a short real sentence is.

    The short sentence is the point. At a thirty-character cut this line of the
    Ajurrumiyya was thrown away as noise, which is how a rule meant to drop
    rubbish started dropping the book.
    """
    result = _parse("# ...\n\n# وللخفض ثلاث علامات الكسرة والياء والفتحة\n")

    assert [p[2] for p in result.passages] == ["وللخفض ثلاث علامات الكسرة والياء والفتحة"]
    assert result.too_short == 1


def test_prose_trailing_off_does_not_swallow_the_next_paragraph():
    """The verse rule must not fire on prose that merely ends in dots.

    Without a length cap it fired on any paragraph ending in the separator,
    took the one below it, and having kept the trailing dots took the one after
    that as well. One stray line could eat a page.
    """
    prose = (
        "وإذا أذن المولى لعبده في التجارة إذنا عاما جاز تصرفه "
        "في سائر التجارات يشتري ويبيع ويرهن ويسترهن ..."
    )
    result = _parse(f"# {prose}\n# وإقرار المأذون بالديون والغصوب جائز\n")

    assert len(result.passages) == 2


def test_the_arabic_is_never_repaired():
    """The spaced hamza is counted and left exactly as the book has it.

    Closing "الأ قسام" up would be a guess: أ ends real words too, and a wrong
    join invents a word the book never had.
    """
    result = _parse("# فلا بد من البحث في كل واحد من هذه الأ قسام ليعلم بذلك\n")

    assert "الأ قسام" in result.passages[0][2]
    assert result.broken_alif == 1
