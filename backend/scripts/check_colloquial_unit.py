"""Check one written dialect unit against the spine, the same way the app does on load.

    python -m backend.scripts.check_colloquial_unit <dialect-folder> <unit-NN>

Prints "ok" or every fault, so a unit can be fixed before it is added to dialects.json.
"""
import json
import sys

from backend.config import data_path
from backend.services.colloquial import loader


def faults(folder: str, name: str) -> list[str]:
    root = data_path("colloquial_dir")
    spine = json.loads((root / "spine.json").read_text(encoding="utf-8"))["units"]
    written = json.loads((root / folder / f"{name}.json").read_text(encoding="utf-8"))
    outline = next(one for one in spine if one["unit"] == name)
    unit, said = loader._fill(outline, written)
    return said + loader._unit_faults(unit)


if __name__ == "__main__":
    found = faults(*sys.argv[1:3])
    print("\n".join(found) or "ok")
    sys.exit(1 if found else 0)
