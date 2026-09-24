"""Prompt templates shared by all AI backends.

Identical in content to the original groq/prompts.py but backend-agnostic.
"""
from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


SYSTEM_BASE = (
    "You are an expert classical Arabic grammarian trained in the traditional Islamic seminary (madrasa) method.\n"
    "You specialize in Nahw (syntax) and Sarf (morphology) of Classical and Quranic Arabic.\n"
    "Your analysis follows the proof-based methodology (الإعراب مع الدليل) used in Dars Nizami:\n"
    "  - For every grammatical decision, cite the RULE NAME (e.g. 'الفاعل مرفوع', 'المفعول به منصوب')\n"
    "  - Identify the 'amil (العامل), the operator that causes the case\n"
    "  - Distinguish mabni (مبني) from mu'rab (معرب) words\n"
    "  - Use standard Nahw terminology: mubtada, khabar, fa'il, na'ib al-fa'il, maf'ul bihi, "
    "mudaf, mudaf ilayhi, sifah, haal, tamyiz, etc.\n"
    "You MUST respond with ONLY valid JSON, no markdown, no extra text.\n"
)

IRAAB_USER = """Perform a full proof-based I'raab (الإعراب مع الدليل) of this Arabic sentence, word by word.

Sentence: {sentence}
Morphological hints (from local NLP engine): {qalsadi_tags}

For EACH word provide:
- Its grammatical role (fa'il, maf'ul bihi, mubtada, khabar, mudaf, sifah, haal, etc.)
- Its case (raf' / nasb / jarr / jazm) OR state it is mabni with its fixed harakat
- The sign of its case, in Arabic (ضمة / فتحة / كسرة / سكون / الواو / الألف / الياء / ثبوت النون / حركة مقدرة)
- The PROOF (الدليل): cite the exact Nahw rule by name in Arabic, e.g. 'الفاعل مرفوع',
  'المفعول به منصوب', 'اسم إن منصوب', and identify the 'amil (العامل)
- Whether it is mu'rab (معرب) or mabni (مبني), and why if mabni

Return a JSON object with this exact structure:
{{
  "summary": "sentence type: jumlah fi'liyyah / ismiyyah, and the main predication",
  "words": [
    {{
      "word": "Arabic word exactly as written",
      "type": "ism | fi'l | harf",
      "role": "precise grammatical role in Arabic terminology",
      "role_key": "that same role as ONE of: fil, fail, mubtada, khabar, mafool, sifah, haal, mudaf, harf; or \\"\\" if none of them fits. This is only used to pick a colour, so leave it empty rather than choose a near-miss",
      "case": "raf' | nasb | jarr | jazm | mabni (specify fixed harakat if mabni)",
      "sign": "ضمة | فتحة | كسرة | سكون | الواو | الألف | الياء | ثبوت النون | حركة مقدرة",
      "reason": "cite the Nahw rule by name in Arabic + identify the 'amil. E.g.: مرفوع لأنه فاعل، والعامل فيه الفعل المتقدم. القاعدة: الفاعل مرفوع",
      "notes": "mabni/mu'rab status, any irregular forms, relevant Sarf notes"
    }}
  ]
}}"""

SARF_USER = """Perform a Sarf (morphology) analysis of this Arabic word.

Word: {word}
Morphological hints (from local NLP engine): {qalsadi_tags}

Do not return a conjugation table. The app builds that from its own rule tables and never
from a model, so anything you wrote here would be thrown away; or worse, disagree with it.

Return a JSON object with this exact structure:
{{
  "word": "the input word",
  "root": "3-letter root",
  "wazn": "verb pattern e.g. فَعَلَ or فَاعَلَ",
  "verb_class": "e.g. Sahih Salim / Ajwaf / Naqis / Mudha'af / Mithaal",
  "meaning": "core meaning in English",
  "notes": "any important morphological notes"
}}"""

PRACTICE_USER = """Generate 4 practice questions to test understanding of the I'raab of this Arabic sentence.

Sentence: {sentence}
I'raab analysis: {iraab_summary}

Create questions of varying difficulty:
- 1 identification question (e.g. "What is the grammatical role of X?")
- 1 case/sign question (e.g. "Why is X in the nominative case?")
- 1 fill-in-the-blank (remove a word, ask what it is)
- 1 transformation question (e.g. "Change this jumlah fi'liyyah to jumlah ismiyyah")

Return a JSON object with this exact structure:
{{
  "questions": [
    {{
      "question": "the question text (can be in English or Arabic)",
      "answer": "the correct answer with explanation",
      "hint": "a one-line hint (optional)"
    }}
  ]
}}"""


ROOT_ENTRY_USER = """Put this entry from Ibn Faris's Maqayees al-Lugha into plain English for a
learner who cannot read classical Arabic.

Root: {root}
Entry (Arabic, as printed): {entry}

Rules:
- Say only what the entry says. Do not add meanings, examples or verses of your own.
- Keep his order: the origin sense first, then each branch of it, then his examples.
- Where he quotes the Qur'an or a line of poetry, say so and give the sense of it.
  A line printed in two halves separated by "..." is one line of poetry.
- Copy every reference exactly as it is printed. The surah name and verse number
  are in the entry already: repeat them, never convert a name to a number or
  work one out yourself.
- Write short sentences. No transliteration tables, no grammar jargon.
- If part of the entry is unclear or cut off, say that plainly instead of filling it in.

Return a JSON object with this exact structure:
{{
  "english": "the whole entry retold in plain English, in paragraphs separated by a blank line"
}}"""

ROOT_ENTRY_LINES_USER = """Put this entry from Ibn Faris's Maqayees al-Lugha into plain English for a
learner who cannot read classical Arabic. It is given to you line by line,
numbered, and your answer must keep the numbering: one English line for each
Arabic line, saying what that line and only that line says.

Root: {root}
The entry, line by line:
{numbered}

Rules:
- Say only what each line says. Do not add meanings, examples or verses of your own.
- Do not move anything between lines. If a line is half a sentence, translate the half.
- A line printed in two halves separated by "..." is one line of poetry: give its
  sense as one English line.
- Copy every reference exactly as it is printed. The surah name and verse number
  are in the entry already: repeat them, never convert a name to a number or
  work one out yourself.
- Write short sentences. No transliteration tables, no grammar jargon.
- If a line is unclear or cut off, say that plainly instead of filling it in.

Return a JSON object with this exact structure, with exactly {count} strings in
the same order as the numbering:
{{
  "lines": ["English of line 1", "English of line 2"]
}}"""


_RULES_EXCERPT_CHARS = 3000
_system_prompt: str = SYSTEM_BASE


def system_prompt() -> str:
    return _system_prompt


def load_nahw_rules(rules_json_path: str) -> None:
    """Augment the system prompt with an excerpt from the local rules JSON."""
    global _system_prompt
    with open(rules_json_path, encoding="utf-8") as f:
        rules = json.load(f)
    if not isinstance(rules, list):
        raise ValueError("Rules JSON must contain a list of topics")

    lines: list[str] = []
    for entry in rules:
        if not isinstance(entry, dict):
            continue
        lines.append(f"Topic: {entry.get('topic', '')}")
        lines.extend(f"  - {rule}" for rule in entry.get("rules", []))
    excerpt = "\n".join(lines)[:_RULES_EXCERPT_CHARS]
    _system_prompt = f"{SYSTEM_BASE}\nKey grammar rules reference:\n{excerpt}\n"
    logger.info("Loaded %d grammar rule lines from %s", len(lines), rules_json_path)
