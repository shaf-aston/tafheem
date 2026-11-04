"""Where the marked recitations, their downloads and the reports live."""
from pathlib import Path

CHECKS = Path(__file__).resolve().parents[2] / "data" / "recitation_checks"
DOWNLOADS = CHECKS / "downloads"
