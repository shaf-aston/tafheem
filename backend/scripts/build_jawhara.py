"""Write Jawharat al-Tawhid as an OpenITI-shaped text file, from the Wikisource copy.

    python backend/scripts/build_jawhara.py

Al-Laqani's 144-bayt creed poem is not in OpenITI, so the Grow book world (public/grow/jawhara.json)
could not be checked word for word against a book file like the others. Arabic Wikisource has the
poem, vowelled, public domain (the author died 1041 AH). Its wikitext is kept as it was fetched in
data/books/wikisource/jawhara.wikitext; this script turns it into the shape every other book file
has (`### | ` headings, one `# ` line per bayt, the two hemistichs joined by OpenITI's ` % ` verse
mark), so lib/bookLesson.test.js and import_openiti.py read it unchanged.

The Wikisource copy has typing slips. Each is corrected here, by hand, as a pair the file must
contain exactly once (FIXES), so a fix that stops matching is noticed rather than silently skipped.
Tatweel (ـ), the editor's square brackets, doubled spaces and the sukun some copies put on hamzat al-wasl
(اْل → ال) are taken out; nothing else changes. The slips were found by reading the whole poem against
the printed editions (critic review, 2026-10-21).
tests/test_jawhara.py holds the result to 144 bayts of two halves, no tatweel, no doubled harakat
and no sukun straight before a vowel.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend" / "data" / "books" / "wikisource" / "jawhara.wikitext"
OUT = ROOT / "backend" / "data" / "books" / "openiti" / "1041BurhanDinLaqani.JawharatTawhid.Wikisource-ara1"

BAYTS = 144

# The poem's parts, as its own blocks of verses run: first bayt of the part → its heading.
# The names are the standard ones commentaries use for these runs of verses.
SECTIONS = {
    1: "المقدمة",
    5: "سبب التأليف",
    9: "حكم التقليد ووجوب النظر",
    19: "الإيمان والإسلام وزيادته",
    23: "ما يجب لله تعالى من الصفات",
    38: "الأسماء والصفات",
    45: "أفعال العباد والقدر",
    57: "إرسال الرسل وما يجب لهم",
    63: "النبوة فضل لا كسب",
    65: "فضل نبينا ﷺ ومعجزاته",
    75: "الصحابة وفضلهم",
    83: "الكرامات والدعاء والحفظة",
    88: "الموت والأرواح",
    96: "القبر والبعث والحساب",
    103: "اليوم الآخر",
    111: "الحوض والشفاعة",
    119: "الرزق والكسب",
    122: "الموجود والمعدوم",
    124: "الذنوب والتوبة",
    127: "الكليات الخمس",
    130: "الإمامة",
    134: "آداب الطريق وآفات القلب",
    140: "الخاتمة",
}

# wrong → right; every pair must be found exactly once after tatweel is removed.
FIXES = [
    ("وَصْحِبِهِ", "وَصَحْبِهِ"),
    ("مُحَتَمٌ", "مُحَتَّمٌ"),
    ("التَّطْوِيِل", "التَّطْوِيلِ"),
    ("كُلَّفَ شَرْعًا", "كُلِّفَ شَرْعًا"),
    ("وَالجَائزََ", "وَالجَائِزَ"),
    ("سِبِيلَ الحَقِّ", "سَبِيلَ الحَقِّ"),
    ("أًوْ لاَ", "أَوْ لاَ"),
    ("اللَّفْظِ الذَّي", "اللَّفْظِ الَّذِي"),
    ("لِعَبَدْه", "لِعَبْدِهِ"),
    ("لِلْمُؤُمِنِينَ", "لِلْمُؤْمِنِينَ"),
    ("هذِا وَلِلْمُخْتَارِ", "هذَا وَلِلْمُخْتَارِ"),
    ("مَعْنَى الذَّيِ", "مَعْنَى الَّذِي"),
    ("بَغْضَهُ", "بَعْضَهُ"),
    ("حَتِّمَا", "حُتِّمَا"),
    ("كَرِامٌ", "كِرَامٌ"),
    ("كَذَا حكا", "كَذَا حَكَى"),
    ("ضُوعَفتَ", "ضُوعِفَتْ"),
    ("وَأَمُرْ بِعُرْفٍ", "وَأْمُرْ بِعُرْفٍ"),
    ("الرَّيَاءٍ", "الرِّيَاءِ"),
    ("يْمنحَنَا", "يَمْنَحَنَا"),
    ("مَنْ أَمَّتِهْ", "مِنْ أُمَّتِهْ"),
    ("أَوْحِتْ", "أَوْجِبْ"),
    ("نَقَاهَا", "نَفَاهَا"),
    ("التَّشَاجُرَ الذَّيِ", "التَّشَاجُرَ الَّذِي"),
    ("ابْتدَاعِ مِنْ خَلَفْ", "ابْتدَاعِ مَنْ خَلَفْ"),
    ("مِنْ وُلِّيَ", "مَنْ وُلِّيَ"),
    ("مَعَرِفَةٌ", "مَعْرِفَةٌ"),
    ("لِلْعَالمَ", "لِلْعَالَمِ"),
    ("وَفَسِّرَ الإِيمَانُ", "وَفُسِّرَ الإِيمَانُ"),
    ("فِيهِ الخَلْفُ", "فِيهِ الخُلْفُ"),
    ("وَالاسْلاَمِ", "وَالإِسْلاَمَ"),
    ("وَنَقَصُهُ بِنَقْصهَا. وَقِيلَ: لاَ % وَقِيلَ لاَ. خُلْفَ", "وَنَقْصُهُ بِنَقْصهَا. وَقِيلَ: لاَ % وَقِيلَ: لاَ خُلْفَ"),
    ("وَوَالَدٍ", "وَوَالِدٍ"),
    ("بَذِي أَتَانَا", "بِذِي أَتَانَا"),
    ("مُتْكَلِّمٌ", "مُتَكَلِّمٌ"),
    ("السَّمْعْيَّةْ", "السَّمْعِيَّةْ"),
    ("وَأحْذَرِ انِتْقَامَهْ", "وَاحْذَرِ انْتِقَامَهْ"),
    ("أَنْ يَصِلُ", "أَنْ يَصِلْ"),
    ("الأَزّلِ", "الأَزَلِ"),
    ("الشَّقُّيِ", "الشَّقِيُّ"),
    ("فَبِمَحْص الْعَدْلِ", "فَبِمَحْضِ الْعَدْلِ"),
    ("خَلْقُ الشِّرِّ", "خَلْقُ الشَّرِّ"),
    ("نُبْوَّةٌ", "نُبُوَّةٌ"),
    ("الِمِنَنْ", "المِنَنْ"),
    ("بِالْبَعَضِ", "بِالْبَعْضِ"),
    ("أُحْدٍ", "أُحُدٍ"),
    ("وَقِلَّ الأَمَلاَ", "وَقَلِّلِ الأَمَلاَ"),
    ("السُّبْكِى", "السُّبْكِيُّ"),
    ("فَاُطْلُبْ", "فَاطْلُبْ"),
    ("قَدْ لخَصُوا", "قَدْ لَخَّصُوا"),
    ("الأَعيْان", "الأَعْيَانِ"),
    ("بَحوْضِ", "بِحَوْضِ"),
    ("حَتْمُ كما", "حَتْمٌ كما"),
    ("لاَ تَمْنَعٍ", "لاَ تَمْنَعِ"),
    ("نُكَفَّرْ", "نُكَفِّرْ"),
    ("تَعَذِيبُ", "تَعْذِيبُ"),
    ("الْقَبْولِ", "الْقَبُولِ"),
    ("أَوِ اَسْتَبَاحَ كالزَّنَا", "أَوِ اسْتَبَاحَ كَالزِّنَا"),
    ("بَغِيْرِ", "بِغَيْرِ"),
    ("لِلنَّبِّي", "لِلنَّبِيِّ"),
    ("دَأَبُهُ", "دَأْبُهُ"),
]

HEADER = """######OpenITI#


#META# 000.SortField	:: Wikisource_JawharatTawhid
#META# 010.AuthorNAME	:: برهان الدين إبراهيم بن هارون اللقاني
#META# 011.AuthorDIED	:: 1041
#META# 020.BookTITLE	:: جوهرة التوحيد
#META# 040.EdPUBLISHER	:: Arabic Wikisource, ضبط جلال علي الجهاني; public domain
#META# 041.EdURL	:: https://ar.wikisource.org/wiki/الجوهرة_في_التوحيد
#META# 090.Note	:: Written by backend/scripts/build_jawhara.py from data/books/wikisource/jawhara.wikitext; the slips it corrects are listed there.
#META#Header#End#
"""


def bayts_of(wikitext: str) -> list[str]:
    """Each bayt as "first half % second half", the tatweel, brackets and doubled spaces gone."""
    blocks = re.findall(r"\{\{أبيات\|(.*?)\}\}", wikitext, re.S)
    lines = [line.strip() for block in blocks for line in block.strip().split("\n") if line.strip()]
    out = []
    for line in lines:
        line = line.replace("ـ", "").replace("اْل", "ال")
        line = re.sub(r"\[([^\]]*)\]", r"\1", line)
        halves = [re.sub(r"\s+", " ", half).strip() for half in line.split("\\\\")]
        if len(halves) != 2:
            raise SystemExit(f"a bayt without two halves: {line}")
        out.append(" % ".join(halves))
    return out


def fixed(text: str) -> str:
    for wrong, right in FIXES:
        if text.count(wrong) != 1:
            raise SystemExit(f"fix {wrong!r} is found {text.count(wrong)} times, not once")
        text = text.replace(wrong, right)
    return text


def build(wikitext: str) -> str:
    bayts = bayts_of(wikitext)
    if len(bayts) != BAYTS:
        raise SystemExit(f"{len(bayts)} bayts, not {BAYTS}")
    body = []
    for n, bayt in enumerate(bayts, 1):
        if n in SECTIONS:
            body.append(f"### | {SECTIONS[n]}")
        body.append(f"# {bayt}")
    return HEADER + fixed("\n".join(body)) + "\n"


def main() -> None:
    text = build(SOURCE.read_text(encoding="utf-8"))
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {BAYTS} bayts, {len(SECTIONS)} sections, {len(FIXES)} slips corrected")


if __name__ == "__main__":
    sys.exit(main())
