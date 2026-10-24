"""Build frontend/public/grow/basics-verbs.json for the Basics world's verb skills.

    python backend/scripts/grow/build_basics_verbs.py          # write it
    python backend/scripts/grow/build_basics_verbs.py --check  # fail if the shipped file is stale

Every Arabic form comes from backend/services/sarf/conjugation.py, the same engine the
Sarf tab draws its tables with; data/grow/basics_verbs.json only names the verbs
(root, باب) and their English. Seven persons, the ones a beginner meets first
(هو هي هم أنتَ أنتم أنا نحن cover 98.9% of the Qur'an's past verbs), each with:

  past      كَتَبَتْ      the ماضي
  present   تَكْتُبُ      the مضارع, مرفوع
  subj      تَكْتُبَ      منصوب, after لَنْ: the last ُ turns to َ, or the ن of ـونَ goes
  juss      تَكْتُبْ      مجزوم, after لَمْ and the لا of "don't": the engine's نهي without its لَا
  command   اُكْتُبْ      أمر, for the two "you" persons only

The particles (سَ سَوْفَ لا لَمْ لَنْ مَا) are put in front by the browser (lib/grow/wordForms.js).
"""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.services.sarf import conjugation  # noqa: E402

SOURCE = ROOT / "backend/data/grow/basics_verbs.json"
OUT = ROOT / "frontend/public/grow/basics-verbs.json"

DAMMA, FATHA = "ُ", "َ"
NAHY = "لَا "
# Our id → the engine's person label (data/sarf/patterns.json "persons").
PERSONS = {"he": "he", "she": "she", "they": "they (m)", "you": "you (m)", "you-all": "you all (m)", "I": "I", "we": "we"}
ADDRESSED = {"you", "you-all"}
# The persons whose present ends in ُ, so ُ → َ makes the منصوب; the others' منصوب is their مجزوم (ـُوا).
SINGLE = {"he", "she", "you", "I", "we"}


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def forms_of(root: str, bab: str) -> dict:
    """The seven persons' forms of one verb."""
    rows = {row["person"]: row["cells"] for row in conjugation.conjugate(root, bab)["rows"]}
    forms = {}
    for ours, label in PERSONS.items():
        cells = rows[label]
        present, nahy = nfc(cells["mudari"]), nfc(cells["nahy"])
        if not nahy.startswith(NAHY):
            raise ValueError(f"{root} {ours}: the نهي does not start with لَا: {nahy}")
        juss = nahy.removeprefix(NAHY)
        if ours in SINGLE:
            if not present.endswith(DAMMA):
                raise ValueError(f"{root} {ours}: the present does not end in ُ: {present}")
            subj = present[:-1] + FATHA
        else:
            subj = juss
        one = {"past": nfc(cells["madi"]), "present": present, "subj": subj, "juss": juss}
        if ours in ADDRESSED:
            one["command"] = nfc(cells["amr"])
        forms[ours] = one
    return forms


def build(source: dict) -> dict:
    verbs = [{**verb, "forms": forms_of(verb["root"], verb["bab"])} for verb in source["verbs"]]
    return {"persons": list(PERSONS), "verbs": verbs}


def text(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=1) + "\n"


def main() -> None:
    fresh = text(build(json.loads(SOURCE.read_text(encoding="utf-8"))))
    if "--check" in sys.argv:
        if OUT.read_text(encoding="utf-8") != fresh:
            raise SystemExit(f"{OUT.relative_to(ROOT)} is stale: run python backend/scripts/grow/build_basics_verbs.py")
        return
    OUT.write_text(fresh, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
