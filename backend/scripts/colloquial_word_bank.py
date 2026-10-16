"""A dialect's words as one plain text file, for a reviewer to read and edit.

    python -m backend.scripts.colloquial_word_bank dump <dialect-folder> > words.txt
    python -m backend.scripts.colloquial_word_bank load <dialect-folder> words.txt

The file walks the course topic by topic: a `## unit-NN lesson-NN <title>` line,
then one `id | english | arabic | transliteration` line for each word the topic
teaches, each word once, where it is first taught. The English is shown, not
edited: it is shared by every dialect and lives in words.json. A word not said
yet has its last two columns empty. A reviewer who knows the dialect can go
through all of it in one sitting, with no JSON to keep valid.
`load` replaces the dialect's words.json with the file, after checking every unit
the way the app does on load, and writes nothing if any of them breaks a rule.
"""
import sys

from backend.config import data_path
from backend.services.colloquial import loader, wordlist


def dump(folder: str) -> str:
    said, meanings, shown, blocks = wordlist.said_in(folder), wordlist.meanings(), set(), []
    for unit in loader.spine():
        for lesson in unit["lessons"]:
            lines = [f"## {unit['unit']} {lesson['lesson']} {lesson['title']}"]
            for one in lesson.get("words") or []:
                if one in shown:
                    continue
                shown.add(one)
                word = said.get(one, {})
                lines.append(f"{one} | {meanings[one]['english']} | {word.get('arabic', '')} | {word.get('transliteration', '')}")
            blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def _read(text: str) -> tuple[dict, list[str]]:
    words, said = {}, []
    for at, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("## "):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 4:
            said.append(f"line {at} is not `id | english | arabic | transliteration`")
            continue
        one, _, arabic, spelling = parts
        if one in words:
            said.append(f"line {at} gives {one!r} a second time")
        elif arabic or spelling:
            words[one] = {"arabic": arabic, "transliteration": spelling}
    return words, said


def load(folder: str, text: str) -> list[str]:
    words, said = _read(text)
    said += wordlist.unknown(words, wordlist.meanings(), folder)
    written = sorted(path.stem for path in (data_path("colloquial_dir") / folder).glob("unit-*.json"))
    said += [f"{name}: {why}" for name in written for why in loader.unit_faults(folder, name, words=words)]
    if not said:  # all or nothing, so a half-loaded dialect never reaches the app
        path = data_path("colloquial_dir") / folder / wordlist.FILE
        path.write_text(wordlist.text(words), encoding="utf-8")
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
