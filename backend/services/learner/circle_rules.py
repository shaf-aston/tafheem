"""Who may open whose overview inside circles. Pure: circles.py reads the rows and passes them in."""
from __future__ import annotations

ROLES = ("admin", "member")


def can_see(viewer: str, target: str, mine: dict, theirs: dict, kinds: dict) -> bool:
    """Themselves; an admin of a circle `target` is joined in or of any circle above it; or a fellow member
    of a circle whose kind shows members' details.

    `mine`: each circle the viewer has joined -> (role, kind). `theirs`: each circle the target has joined
    -> that circle and every circle above it. `kinds`: kind -> whether its members see each other's details.
    """
    if viewer == target:
        return True
    for circle, chain in theirs.items():
        if any(c in mine and mine[c][0] == "admin" for c in chain):
            return True
        if circle in mine and kinds.get(mine[circle][1]):
            return True
    return False
