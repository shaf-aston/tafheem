"""Cut al-Tahawi's Sharh Mushkil al-Athar into one issue per bab.

    python -m backend.scripts.build_mushkil                  # read the OpenITI copy, split
    python -m backend.scripts.build_mushkil --from path/file # split a file kept elsewhere
    python -m backend.scripts.build_mushkil --dry-run        # count everything, write nothing

The catalogue is the scholar's own grouping: each bab is a topic where narrations
seem to conflict, with Tahawi's reconciliation after them. Nothing here, and no
model, decides what belongs together. Writes beside the other hadith data:

    data/hadith/mushkil-tahawi.json     the issues
    data/hadith/mushkil-unplaced.json   every paragraph the cutter could not place

The rule itself is backend/services/mushkil_split.py, which is pure and tested.
Ibn Qutaybah's Tawil Mukhtalaf al-Hadith is in the same OpenITI folder and is not
read yet.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services import mushkil_split  # noqa: E402

# Where OpenITI's pri-data sits on this computer.
BOOK_DEFAULT = Path.home() / "Downloads/OpenITI-pri-data_v9/0321Tahawi.SharhMushkilAthar.JK007043-ara1"
# The printed edition carries roughly 6,000 narrations. Far outside this range
# the cutter has broken, rather than the book being unusual.
NARRATIONS_PLAUSIBLE = (1000, 15000)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="source", help="Split this file instead of the OpenITI copy")
    parser.add_argument("--dry-run", action="store_true", help="Count everything, write nothing")
    args = parser.parse_args()

    book_path = Path(args.source) if args.source else BOOK_DEFAULT
    if not book_path.exists():
        raise SystemExit(f"No such file: {book_path}")
    issues, unplaced = mushkil_split.split(book_path.read_text(encoding="utf-8"))

    narrations = sum(len(issue["narrations"]) for issue in issues)
    low, high = NARRATIONS_PLAUSIBLE
    if not low <= narrations <= high:
        raise SystemExit(
            f"{narrations} narrations cut from {book_path.name}; the book has about 6,000. "
            "The file or the split rule is wrong; nothing written."
        )
    average = narrations / len(issues) if issues else 0
    print(f"  {len(issues)} issues, {narrations} narrations ({average:.1f} per issue), {len(unplaced)} unplaced")
    for why, count in Counter(row["why"] for row in unplaced).most_common():
        print(f"    {count:4}  {why}")
    if args.dry_run:
        return 0

    built = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    target = data_path("mushkil_path")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "_comment": "Hadith that seem to conflict, grouped by al-Tahawi's own chapters in Sharh Mushkil al-Athar. Narrations are as the book prints them, each opening with the edition's hadith number where it has one; the discussion is Tahawi's reconciliation.",
        "source": "mushkil-tahawi",
        "built": built,
        "issues": issues,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    other = data_path("mushkil_unplaced_path")
    other.write_text(json.dumps({
        "_comment": "Paragraphs in Sharh Mushkil al-Athar that fit no bab: the preface, or a repeat of the paragraph before. Listed rather than guessed at.",
        "built": built,
        "unplaced": unplaced,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  -> {target.name} and {other.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
