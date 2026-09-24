"""Extract Nahw grammar rules from PDF files into a structured JSON knowledge base.

Run this script once from the project root:
    python backend/data/nahw_rules/extract_rules.py

It reads all PDFs from the `Nahw yr3` folder and produces `rules.json`.
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

# Force UTF-8 output on Windows to handle Arabic filenames in print().
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF not installed. Run: pip install pymupdf")
    sys.exit(1)

try:
    from bidi.algorithm import get_display

    BIDI_AVAILABLE = True
except ImportError:
    print("WARNING: python-bidi not installed. Arabic text order may be reversed.")
    BIDI_AVAILABLE = False


TOPIC_MAP = {
    "9 Types of I'raab - HN1": "9 Types of I'raab",
    "Alaf`aal Anaaqisa WS": "Af'aal Naqisah (Defective Verbs)",
    "Alhuroof Almushabbaha bilf`il WS": "Huroof Mushabbahah bil-Fi'l",
    "Haal الحالة": "Al-Haal (Circumstantial Expression)",
    "Huroof mushabahah bil fi'l": "Huroof Mushabbahah bil-Fi'l (Revised)",
    "Ism Isharah Yr3": "Ism Isharah (Demonstrative Pronouns)",
    "Maa Laa Laata Laa Nafi Jins": "Maa / Laa / Lata / Laa Nafi al-Jins",
    "Mafool bihi Yr3": "Maf'ul Bihi (Direct Object)",
    "Mafool Ma'ahu Rules": "Maf'ul Ma'ah",
    "Mafool Mutlaq Yr3": "Maf'ul Mutlaq (Cognate Object)",
    "Mawsoolaat Harfyiyyah BTM": "Mawsoolaat Harfiyyah (Particle Relative Pronouns)",
    "Waw Haaliyah": "Waw Haliyyah",
    "Zuroof Year 3": "Zuroof (Adverbials of Time/Place)",
    "Nahw Basics 1": "Nahw Basics - Introduction",
    "Nahw Basics 2": "Nahw Basics - Gender and Number",
    "Nahw Basics 3": "Nahw Basics - States (I'raab)",
    "Nahw Basics 4": "Nahw Basics - Fi'l (Verb)",
    "Nahw Basics 5": "Nahw Basics - Musnad and Musnad Ilayhi",
    "Nahw Basics 6": "Nahw Basics - Jumlah Fi'liyyah",
    "Rules of Fail": "Fa'il and Na'ib al-Fa'il Rules",
    "BTM Tarkeebs": "Tarkeebs (Phrase Structures)",
}


def find_nahw_folder() -> Path | None:
    """Find the `Nahw yr3` folder by searching common locations."""
    repo_root = Path(__file__).resolve().parents[3]
    workspace_root = repo_root.parent

    candidates = [
        workspace_root / "Nahw yr3",
        Path.cwd() / "Nahw yr3",
        repo_root / "Nahw yr3",
    ]

    return next(
        (
            candidate
            for candidate in candidates
            if candidate.exists() and candidate.is_dir()
        ),
        None,
    )


def get_topic(filename: str) -> str:
    stem = Path(filename).stem
    return next(
        (
            topic
            for key, topic in TOPIC_MAP.items()
            if key.lower() in stem.lower()
        ),
        stem,
    )


def extract_text_from_pdf(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    pages: list[str] = []
    for page in doc:
        text = page.get_text("text")
        if BIDI_AVAILABLE:
            fixed_lines = []
            for line in text.split("\n"):
                if line.strip():
                    try:
                        fixed_lines.append(get_display(line))
                    except Exception:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            text = "\n".join(fixed_lines)
        pages.append(text)
    return "\n\n".join(pages)


def text_to_rules(text: str) -> list[str]:
    """Split extracted text into individual rule sentences."""
    rules: list[str] = []
    for line in re.split(r"\n+", text):
        line = line.strip()
        if len(line) < 10:
            continue
        if re.match(r"^\d+$", line):
            continue
        rules.append(line)
    return rules[:100]


def main() -> None:
    nahw_folder = find_nahw_folder()
    if not nahw_folder:
        print("ERROR: 'Nahw yr3' folder not found.")
        print("Please ensure the folder is in one of these locations:")
        repo_root = Path(__file__).resolve().parents[3]
        workspace_root = repo_root.parent
        for candidate in [
            workspace_root / "Nahw yr3",
            Path.cwd() / "Nahw yr3",
            repo_root / "Nahw yr3",
        ]:
            print(f"  {candidate}")
        sys.exit(1)

    output_json = Path(__file__).parent / "rules.json"
    print(f"Reading PDFs from: {nahw_folder}")
    print(f"Output: {output_json}")

    pdf_files = list(nahw_folder.rglob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files")

    all_rules = []
    for pdf_path in sorted(pdf_files):
        print(f"  Processing: {pdf_path.name}")
        try:
            text = extract_text_from_pdf(pdf_path)
            rules = text_to_rules(text)
            all_rules.append(
                {
                    "topic": get_topic(pdf_path.name),
                    "file": pdf_path.name,
                    "rules": rules,
                }
            )
        except Exception as exc:
            print(f"    WARNING: Failed to process {pdf_path.name}: {exc}")

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_rules, f, ensure_ascii=False, indent=2)

    total_rules = sum(len(entry["rules"]) for entry in all_rules)
    print(f"\nDone! Wrote {len(all_rules)} topics, {total_rules} rules to:")
    print(f"  {output_json}")


if __name__ == "__main__":
    main()
