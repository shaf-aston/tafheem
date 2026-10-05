"""sunnah.com pages to plain dicts. Pure: no file, no network.

Two pages are read: a book's (which narrator sits in which chain, with the
words the hadith shows for him) and a narrator's own. Written against the
pages as sunnah.com prints them; a field the page lacks comes back empty.
place() then finds those words in our own copy of the hadith.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

_REFERENCE = re.compile(r"^/\w+:(\d+)([a-z]*)$")
_NARRATOR = re.compile(r"^/narrator/(\d+)$")
_GRADE = re.compile(r"pill-grade--grade-(\d+)")
_TOTAL = re.compile(r"^([\d,]+) Hadith Narrated")
# The page's own Arabic labels, mapped to our field names. A label not here is left out.
_LABELS = {
    "الكنية": "kunya_ar", "الطبقة": "generation_ar", "الاسم الكامل": "lineage_ar",
    "النسب والنسبة": "nisba_ar", "بلد الإقامة": "city_ar", "الصنعة": "profession_ar", "المذهب": "school_ar",
}


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _text(tag) -> str:
    return tag.get_text(" ", strip=True) if tag else ""


def book_chains(html: str) -> list[dict]:
    """Every hadith on a book page: its number and letter, and each narrator in its Arabic, in order, as (id, the words shown)."""
    out = []
    for box in _soup(html).select("div.actualHadithContainer"):
        link = box.select_one("table.hadith_reference a[href]")
        ref = _REFERENCE.match(link["href"]) if link else None
        if not ref:
            continue
        names = [(int(m.group(1)), a.get_text().strip())
                 for a in box.select("div.arabic_hadith_full a[href]") if (m := _NARRATOR.match(a["href"]))]
        out.append({"number": int(ref.group(1)), "part": ref.group(2), "names": names})
    return out


def place(arabic: str, names: list[tuple[int, str]]) -> tuple[list[tuple[int, int, int]], list[tuple[int, str]]]:
    """([(start, end, id)] found in our text, [(id, shown)] not found).

    Each search starts where the last name ended, so a name that comes twice in
    one chain lands each time on its own words, in order. A hit must end its
    word (أبيه, not the start of أبيها); its start may carry an attached و or ف.
    """
    placed, lost, at = [], [], 0
    for who, shown in names:
        hit = re.compile(re.escape(shown) + r"(?!\w)").search(arabic, at)
        if hit:
            at = hit.end()
            placed.append((hit.start(), at, who))
        else:
            lost.append((who, shown))
    return placed, lost


def _people(soup: BeautifulSoup, panel: str) -> list[tuple[int, str, str]]:
    """(id, Arabic name, English name) of a panel's narrators, the folded-away rows included, each once."""
    found = {}
    for a in soup.select(f"section.panel--{panel} a.name-en"):
        if m := _NARRATOR.match(a.get("href", "")):
            who = int(m.group(1))
            found.setdefault(who, (who, _text(a.find_next_sibling("a", class_="name-ar")), _text(a)))
    return list(found.values())


def narrator(html: str) -> dict:
    """One narrator page: names, grade, the labelled facts, appraisals, teachers, students and the classical texts."""
    # The site joins book and author with an em dash; the app never prints one.
    soup = _soup(html.replace("—", "-"))
    out = {key: "" for key in _LABELS.values()}
    for label in soup.select("span.label.arabic-label"):
        key = _LABELS.get(_text(label))
        if key:
            out[key] = _text(label.parent.find(class_=["field", "lineage"]))
    grade = soup.select_one("div.pill-grade")
    rank = _GRADE.search(" ".join(grade["class"])) if grade else None
    total = next((m for h in soup.select("h3.section-title") if (m := _TOTAL.match(_text(h)))), None)
    return {
        **out,
        "name_en": _text(soup.select_one("h1.hero-title:not(.arabic)")),
        "name_ar": _text(soup.select_one("h1.hero-title.arabic")),
        "grade_en": _text(soup.select_one("div.pill-grade .pill-text")),
        "grade_ar": _text(soup.select_one("div.pill-grade .arabic")),
        "grade_rank": int(rank.group(1)) if rank else None,
        "years": _text(soup.select_one("span.pill-secondary:not(.arabic)")),
        "books_ar": [_text(p) for p in soup.select("span.pill-outline.arabic")],
        "verdicts": [(_text(v.select_one(".verdict-scholar")), _text(v.select_one(".critic-quote")))
                     for v in soup.select("div.verdict")],
        "teachers": _people(soup, "teachers"),
        "students": _people(soup, "students"),
        "hadith_total": int(total.group(1).replace(",", "")) if total else None,
        "texts": [(_text(a.select_one(".accordion-title")), a.select_one(".accordion-body").get_text("\n", strip=True))
                  for a in soup.select("div.accordion") if a.select_one(".accordion-body")],
    }
