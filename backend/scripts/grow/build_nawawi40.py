"""Build frontend/public/grow/nawawi40.json for Grow's Hadith world.

    python backend/scripts/grow/build_nawawi40.py

Fetches an-Nawawi's Forty (Arabic + English) from fawazahmed0/hadith-api (the
source sources.json "hadith" credits), cleans the text, and pairs each hadith
with its key line from data/grow/nawawi40_keys.json. Fails if a key line is
not an exact quote of its hadith.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
KEYS = ROOT / "backend/data/grow/nawawi40_keys.json"
OUT = ROOT / "frontend/public/grow/nawawi40.json"
MIRRORS = (
    "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions",
    "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions",
)
SOURCE = "https://github.com/fawazahmed0/hadith-api"


def clean(text: str) -> str:
    """Drop bidi marks and <br>, collapse spaces."""
    text = re.sub("[‪-‮]", "", text).replace("<br>", " ")
    return re.sub(r"\s+", " ", text).strip()


def edition(client: httpx.Client, name: str) -> list[dict]:
    for base in MIRRORS:
        try:
            reply = client.get(f"{base}/{name}.json", timeout=120)
            reply.raise_for_status()
            return reply.json()["hadiths"]
        except httpx.HTTPError:
            continue
    raise SystemExit(f"Could not fetch {name} from any mirror")


def build(arabic: list[dict], english: list[dict], keys: dict) -> tuple[list[dict], list[str]]:
    """The hadiths with their key lines, and every key line that is not an exact quote."""
    hadiths, wrong = [], []
    for ar, en in zip(arabic, english, strict=True):
        n = ar["hadithnumber"]
        key_ar, key_en = keys[str(n)]
        text_ar, text_en = clean(ar["text"]), clean(en["text"])
        if key_ar not in text_ar:
            wrong.append(f"{n} ar: {key_ar}")
        if key_en not in text_en:
            wrong.append(f"{n} en: {key_en}")
        hadiths.append({"n": n, "arabic": text_ar, "english": text_en, "key": {"ar": key_ar, "en": key_en}})
    return hadiths, wrong


def main() -> None:
    keys = json.loads(KEYS.read_text(encoding="utf-8"))["keys"]
    with httpx.Client(follow_redirects=True) as client:
        arabic, english = edition(client, "ara-nawawi"), edition(client, "eng-nawawi")
    hadiths, wrong = build(arabic, english, keys)
    if wrong:
        raise SystemExit("Key lines not found in their hadith:\n" + "\n".join(wrong))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "_comment": "Built by backend/scripts/grow/build_nawawi40.py. Do not edit by hand.",
        "source": {"name": "Forty Hadith of an-Nawawi", "url": SOURCE},
        "hadiths": hadiths,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {len(hadiths)} hadiths to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
