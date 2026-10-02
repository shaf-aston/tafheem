"""How well recitation/locate.py finds a reading's place in the whole Qur'an.

    python -m backend.scripts.score_place [ear] [margin] [fit]

Readings are the saved ones in frontend/scripts/ears-heard.json (ear
"hosted-groq" by default: 150 ayahs by 7 reciters), each cut into pieces the
size a pause makes. A sure place that is not where the piece came from is
wrong, unless that ayah has the very same words (55:13 is said 31 times).
Everyday Arabic should never be a sure place. Sets recitation_place_margin
and recitation_place_fit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from backend.config import get_settings
from backend.services import recitation
from backend.services.recitation import locate

HEARD = Path(__file__).resolve().parents[2] / "frontend" / "scripts" / "ears-heard.json"
EVERYDAY = [
    "اهلا وسهلا كيف حالك اليوم", "انا ذاهب الى السوق لشراء الخبز", "شكرا جزيلا يا اخي",
    "هذا الكتاب جميل جدا", "السلام عليكم ورحمة الله وبركاته", "ما اسمك يا صديقي", "موسيقى",
    "ذهبت الى المدرسة في الصباح الباكر", "الجو حار جدا في الصيف", "هل تريد ان تشرب الشاي",
    "اين المحطة القريبة من هنا", "كان ابي يعمل في المستشفى", "سافرنا الى مكة في رمضان",
    "الطالب يكتب الدرس في الدفتر", "الحمد لله على كل حال", "ان شاء الله نلتقي غدا",
    "قال المعلم للطلاب اجلسوا", "يوم الجمعة يوم مبارك", "اشتريت سيارة جديدة امس",
    "لا اعرف ماذا اقول لك",
]


def pieces(text: str, size: int | None) -> list[str]:
    words = [w for w in text.split() if locate.letters(w)]
    if size is None:
        return [" ".join(words)]
    return [" ".join(words[i:i + size]) for i in range(0, len(words) - size + 1, size)]


def main() -> None:
    ear = sys.argv[1] if len(sys.argv) > 1 else "hosted-groq"
    margin = float(sys.argv[2]) if len(sys.argv) > 2 else get_settings().recitation_place_margin
    fit = float(sys.argv[3]) if len(sys.argv) > 3 else get_settings().recitation_place_fit
    line, plain = recitation._line(), recitation._plain()
    key = lambda k: tuple(map(int, k.split(":")))
    rows = [(key(k.split(" ")[2]), v if isinstance(v, str) else v["text"])
            for k, v in json.loads(HEARD.read_text(encoding="utf-8")).items() if k.startswith(ear + " ")]
    same = lambda a, b: plain[f"{a[0]}:{a[1]}"] == plain[f"{b[0]}:{b[1]}"]

    def tally(name, cases):
        right = wrong = unsure = 0
        for truth, text, near in cases:
            found = locate.find(text, line, margin, fit, near)
            if not found or not found.sure:
                unsure += 1
            elif same((found.surah, found.ayah), truth):
                right += 1
            else:
                wrong += 1
        print(f"{name:<28} right {right:5}  wrong {wrong:3}  not sure {unsure:5}  of {len(cases)}")

    print(f"{len(rows)} {ear} readings, margin {margin}, fit {fit}")
    for size in (None, 8, 4, 3):
        tally(f"{size or 'whole'} words", [(t, p, None) for t, x in rows for p in pieces(x, size)])
    fatihah = locate.span(line, (1, 1), (1, 7))
    tally("4 words, al-Fatihah open", [(t, p, fatihah) for t, x in rows if t[0] != 1 for p in pieces(x, 4)])
    sure = [s for s in EVERYDAY if (f := locate.find(s, line, margin, fit)) and f.sure]
    print(f"everyday Arabic taken as a sure place: {len(sure)} of {len(EVERYDAY)} {sure}")


if __name__ == "__main__":
    main()
