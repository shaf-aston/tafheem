"""Give a Colloquial word a picture from Twemoji where its English is an emoji's own name.

    python -m backend.scripts.emoji_pictures --twemoji <dir of svgs> --emojibase <en/data.json>

Photo search matches loose tags, so a picture found that way needs a person to
look at it. An emoji's name is exact: the emoji named "carrot" is a carrot. So a
word is matched only when its English, give or take "a"/"the" or a plural s, IS
an emoji's name, and a verb ("to watch") never is, whatever emoji shares its
spelling. One style everywhere, no rate limit, nothing to review one by one.

Twemoji graphics are CC-BY 4.0 (Twitter, Inc. and other contributors), credited
once in images/emoji/attribution.json. The SVGs and the names come from npm
(`npm pack @twemoji/svg emojibase-data`), passed in as paths.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from backend.config import data_path
from backend.services.colloquial import wordlist

CREDIT = {
    "creator": "Twitter, Inc. and other contributors (Twemoji)",
    "license": "by", "license_version": "4.0",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "foreign_landing_url": "https://github.com/jdecked/twemoji",
}


def names(emojibase: Path, svgs: Path) -> dict[str, str]:
    """Each emoji's English name to its SVG file, for the emoji Twemoji draws."""
    have = {one.name for one in svgs.glob("*.svg")}
    found: dict[str, str] = {}
    for emoji in json.loads(emojibase.read_text(encoding="utf-8")):
        code = emoji["hexcode"].lower()
        file = next((f for f in (f"{code}.svg", f"{code.replace('-fe0f', '')}.svg") if f in have), None)
        if file:
            found.setdefault(emoji["label"].lower().removeprefix("flag: "), file)
    return found


# Names that are an emoji's but not the word's meaning: "dizzy" is drawn as a
# star, "bald" as a blank head shape. Found by looking at every match once.
NOT_THE_MEANING = {"dizzy", "bald"}
FLAG = re.compile(r"^1f1(e[6-9a-f]|f[0-9a-f])-")

# Words whose emoji has another name, chosen by hand and looked at once, so that
# every topic has a picture of one of its own words. Only where the emoji shows
# that word; nothing for God, angels or prophets.
CHOSEN = {
    "price": "label", "week": "spiral calendar", "fever": "face with thermometer",
    "message": "speech balloon", "email": "e-mail", "letter": "envelope",
    "happy": "smiling face with smiling eyes", "sad": "disappointed face", "angry": "angry face",
    "scared": "fearful face", "worried": "worried face", "tired": "tired face",
    "surprised": "hushed face", "confused": "confused face",
    "right-correct": "check mark button", "wrong": "cross mark", "ok": "OK hand",
    "advice": "light bulb", "medicine": "pill", "what": "red question mark",
    "under": "down arrow", "above": "up arrow", "again": "repeat button", "metre": "straight ruler",
    "to-run": "person running", "to-climb": "person climbing", "to-clap": "clapping hands",
    "to-wave": "waving hand", "to-sneeze": "sneezing face", "to-laugh": "face with tears of joy",
    "to-study": "books", "to-print": "printer", "to-sign": "writing hand", "to-calculate": "abacus",
    "to-repair": "wrench", "to-build": "building construction", "to-paint": "paintbrush",
    "to-sew": "sewing needle", "to-dig": "pick", "to-saw": "carpentry saw", "to-lock": "locked",
    "to-plant": "seedling", "to-burn": "fire",
    "to-love": "red heart", "love": "red heart", "to-think": "thinking face", "to-hug": "people hugging",
    "quiet": "shushing face", "loud": "speaker high volume", "asleep": "sleeping face",
    "male": "male sign", "female": "female sign", "liar": "lying face", "hajj": "kaaba",
}


def match(english: str, group: str | None, emoji: dict[str, str]) -> str | None:
    word = english.lower().strip()
    if word.startswith("to ") or word in NOT_THE_MEANING:
        return None
    for name in (word, re.sub(r"^(a|an|the) ", "", word), word.removesuffix("s")):
        file = emoji.get(name)
        # A country is its flag, never a namesake ("Turkey" the bird).
        if file and (group != "countries" or FLAG.match(file)):
            return file
    return None


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--twemoji", type=Path, required=True)
    ap.add_argument("--emojibase", type=Path, required=True)
    args = ap.parse_args(argv)

    emoji = names(args.emojibase, args.twemoji)
    root = data_path("colloquial_dir")
    folder = root / "images" / "emoji"
    folder.mkdir(parents=True, exist_ok=True)
    words_file = root / wordlist.FILE
    whole = json.loads(words_file.read_text(encoding="utf-8"))
    given = 0
    for key, meaning in whole["words"].items():
        if meaning.get("image"):
            continue
        file = emoji[CHOSEN[key].lower()] if key in CHOSEN else match(meaning["english"], meaning.get("group"), emoji)
        if not file:
            continue
        shutil.copyfile(args.twemoji / file, folder / file)
        meaning["image"] = f"emoji/{file}"
        given += 1
    (folder / "attribution.json").write_text(json.dumps({"*": CREDIT}, indent=2) + "\n", encoding="utf-8")
    words_file.write_text(wordlist.text(whole["words"], whole.get("_about", "")), encoding="utf-8")
    print(given, "words given an emoji picture")


if __name__ == "__main__":
    main()
