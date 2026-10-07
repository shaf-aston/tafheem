"""A dialect's word banks as one plain text file, for a reviewer to read and edit.

    python -m backend.scripts.colloquial_word_bank dump <dialect-folder> > words.txt
    python -m backend.scripts.colloquial_word_bank load <dialect-folder> words.txt

The file is one block per lesson: a `## unit-NN lesson-NN <category>` line, then
one `arabic | transliteration | english` line per word. A reviewer who knows the
dialect can go through all of it in one sitting, with no JSON to keep valid.
`load` writes the banks back into the unit files, then checks every unit the way
the app does on load, and writes nothing if any of them breaks a rule.
"""
import json
import sys

from backend.config import data_path
from backend.scripts.check_colloquial_unit import faults


def _units(folder: str):
    for path in sorted((data_path("colloquial_dir") / folder).glob("unit-*.json")):
        yield path, json.loads(path.read_text(encoding="utf-8"))


def dump(folder: str) -> str:
    blocks = []
    for _, unit in _units(folder):
        for lesson in unit["lessons"]:
            words = lesson.get("vocabulary") or []
            category = next((w["category"] for w in words if w.get("category")), lesson.get("title", ""))
            lines = [f"## {unit['unit']} {lesson['lesson']} {category}"]
            lines += [f"{w['arabic']} | {w['transliteration']} | {w['english']}" for w in words]
            blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def _read(text: str) -> tuple[dict, list[str]]:
    banks, said, key = {}, [], None
    for at, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if line.startswith("## "):
            unit, lesson, category = (line[3:].split(" ", 2) + [""])[:3]
            key = (unit, lesson)
            banks[key] = (category.strip(), [])
        elif line:
            parts = [part.strip() for part in line.split("|")]
            if key is None or len(parts) != 3:
                said.append(f"line {at} is not `arabic | transliteration | english` under a ## heading")
                continue
            arabic, transliteration, english = parts
            banks[key][1].append({"arabic": arabic, "transliteration": transliteration,
                                  "english": english, "category": banks[key][0]})
    return banks, said


def load(folder: str, text: str) -> list[str]:
    banks, said = _read(text)
    units, seen = [], set()
    for path, unit in _units(folder):
        for lesson in unit["lessons"]:
            key = (unit["unit"], lesson["lesson"])
            if key not in banks:
                continue
            seen.add(key)
            words = banks[key][1]
            if "vocabulary" in lesson:
                lesson["vocabulary"] = words
            else:  # a new bank sits after the drills, where the others do
                items = list(lesson.items())
                at = next((i + 1 for i, (name, _) in enumerate(items) if name == "de_book"), len(items))
                lesson.clear()
                lesson.update(items[:at] + [("vocabulary", words)] + items[at:])
        units.append((path, unit))
    said += [f"{unit} {lesson} is not a lesson of {folder}" for unit, lesson in banks if (unit, lesson) not in seen]
    said += [f"{unit['unit']}: {why}" for _, unit in units for why in faults(folder, unit["unit"], unit)]
    if not said:  # all or nothing, so a half-loaded dialect never reaches the app
        for path, unit in units:
            path.write_text(json.dumps(unit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return said


if __name__ == "__main__":
    command, folder = sys.argv[1:3]
    if command == "dump":
        sys.stdout.write(dump(folder))
    else:
        with open(sys.argv[3], encoding="utf-8") as source:
            found = load(folder, source.read())
        print("\n".join(found) or "ok")
        sys.exit(1 if found else 0)
