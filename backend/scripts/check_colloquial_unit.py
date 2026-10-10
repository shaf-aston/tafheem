"""Check one written dialect unit against the spine, the same way the app does on load.

    python -m backend.scripts.check_colloquial_unit <dialect-folder> <unit-NN>

Prints "ok" or every fault, so a unit can be fixed before it is added to dialects.json.
The check itself is loader.unit_faults.
"""
import sys

from backend.services.colloquial import loader

if __name__ == "__main__":
    found = loader.unit_faults(*sys.argv[1:3])
    print("\n".join(found) or "ok")
    sys.exit(1 if found else 0)
