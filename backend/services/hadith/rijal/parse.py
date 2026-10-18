"""sunnah.com pages to plain dicts. Pure: no file, no network.

Two pages are read: a book's (which narrator sits in which chain, with the
words the hadith shows for him) and a narrator's own. Written against the
pages as sunnah.com prints them; a field the page lacks comes back empty.
place() then finds those words in our own copy of the hadith.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString

_REFERENCE = re.compile(r"^/\w+:(\d+)([a-z]*)$")
_NARRATOR = re.compile(r"^/narrator/(\d+)$")
_GRADE = re.compile(r"pill-grade--grade-(\d+)")
_TOTAL = re.compile(r"^([\d,]+) Hadith Narrated")
# The page's own Arabic labels, mapped to our field names. A label not here is left out.
_LABELS = {
    "الكنية": "kunya_ar", "الطبقة": "generation_ar", "الاسم الكامل": "lineage_ar",
    "النسب والنسبة": "nisba_ar", "بلد الإقامة": "city_ar", "الصنعة": "profession_ar", "المذهب": "school_ar",
}


# A name starts a word: nothing word-like (a letter or its vowel marks) before it, or only the particles Arabic writes
# on to the next word: و or ف, then ب ل ك (وبمالك, لمالك).
_NOT_WORD = r"(?<![\w\u064B-\u065F\u0670])"
_WORD_START = "(?:" + "|".join((_NOT_WORD, *(f"(?<={_NOT_WORD}{p})" for p in ("[وف]", "[بلك]", "[وف][بلك]")))) + ")"


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _text(tag) -> str:
    return tag.get_text(" ", strip=True) if tag else ""


def _en(text: str) -> str:
    """sunnah.com's English, its ayn written as a backtick (`Abd) set as ʿ. English only: the Arabic is copied untouched."""
    return text.replace("`", "ʿ")


def _paired(en: list, ar: list) -> list[tuple]:
    """The two languages' lists of one thing side by side. They are matched by place, so only where both pages show the
    same number: a thing one language lacks would shift every later pair, so then each stands alone, (en, None) or (None, ar)."""
    if len(en) == len(ar):
        return list(zip(en, ar))
    return [(e, None) for e in en] + [(None, a) for a in ar]


def _letters(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def _names(full) -> list[tuple[int, str, int, bool]]:
    """(id, the words shown, letters before them, in the chain) for each narrator link with a letter in it.

    The page wraps the isnad in span.arabic_sanad and the matn in span.arabic_text_details, so a name linked in the
    story is told apart from the chain by the source itself; a hadith the page does not wrap counts all as chain."""
    names, before = [], 0
    wrapped = bool(full and full.select_one(".arabic_sanad"))
    for node in full.descendants if full else ():
        if node.name == "a" and (m := _NARRATOR.match(node.get("href", ""))):
            shown = node.get_text().strip()
            if any(ch.isalpha() for ch in shown):
                names.append((int(m.group(1)), shown, before, not wrapped or node.find_parent(class_="arabic_sanad") is not None))
        elif isinstance(node, NavigableString):
            before += _letters(node)
    return names


def book_name(html: str) -> str:
    """The book's Arabic name as its page heads it; "" where the page has none."""
    return _text(_soup(html).select_one("div.book_page_arabic_name"))


def book_chains(html: str) -> list[dict]:
    """Every hadith on a book page: its number and letter, and each narrator in its Arabic, in order."""
    out = []
    for box in _soup(html).select("div.actualHadithContainer"):
        link = box.select_one("table.hadith_reference a[href]")
        ref = _REFERENCE.match(link["href"]) if link else None
        if ref:
            out.append({"number": int(ref.group(1)), "part": ref.group(2),
                        "names": _names(box.select_one("div.arabic_hadith_full"))})
    return out


def place(arabic: str, names: list[tuple[int, str, int, bool]]) -> tuple[list[tuple[int, int, int, bool]], list[tuple[int, str]]]:
    """([(start, end, id, in the chain)] found in our text, [(id, shown)] not found).

    Our text is sunnah.com's, so each name goes to the copy of its words whose
    letter count from the start is nearest where sunnah.com links it; a name
    said twice (الحسن in the chain, الحسن in the story) lands on the right one.
    A hit must end its word (أبيه, not the start of أبيها); its start may carry
    an attached و, ف, ب, ل or ك. One place is never given to two names.
    """
    letters = [0]
    for ch in arabic:
        letters.append(letters[-1] + (not ch.isspace()))
    placed, lost, taken = [], [], set()
    for who, shown, before, in_chain in names:
        hits = re.finditer(_WORD_START + re.escape(shown) + r"(?![\w\u064B-\u065F\u0670])", arabic)
        hit = min((h for h in hits if h.start() not in taken), key=lambda h: abs(letters[h.start()] - before), default=None)
        if hit:
            taken.add(hit.start())
            placed.append((hit.start(), hit.end(), who, in_chain))
        else:
            lost.append((who, shown))
    return sorted(placed), lost


def _people(soup: BeautifulSoup, panel: str) -> list[tuple[int, str, str]]:
    """(id, Arabic name, English name) of a panel's narrators, the folded-away rows included, each once."""
    found = {}
    for a in soup.select(f"section.panel--{panel} a.name-en"):
        if m := _NARRATOR.match(a.get("href", "")):
            who = int(m.group(1))
            found.setdefault(who, (who, _text(a.find_next_sibling("a", class_="name-ar")), _en(_text(a))))
    return list(found.values())


def _facts(soup: BeautifulSoup) -> list[dict]:
    """Each labelled fact as the page prints it in both languages: its English and Arabic labels, in page order, paired."""
    def side(labels):
        return [(_text(label), _text(label.parent.find(class_=["field", "lineage"]))) for label in labels]
    en = side(label for label in soup.select("span.label") if "arabic-label" not in label["class"])
    ar = side(soup.select("span.label.arabic-label"))
    return [{"label_en": le, "en": _en(ve), "label_ar": la, "ar": va}
            for (le, ve), (la, va) in ((e or ("", ""), a or ("", "")) for e, a in _paired(en, ar)) if ve or va]


# A run inside a classical text that the page marks: the scholar quoted, his words, a book's letter.
_RUNS = {"tarjama-scholar": "scholar", "tarjama-verdict": "verdict", "sigla-link": "mark", "sigla": "mark"}


def _runs(node) -> list[dict]:
    """A block's text as runs, each {"t": text} with "role" for a marked one and "title" for a book letter's book; plain neighbours joined."""
    runs: list[dict] = []
    for child in node.children:
        role = next((_RUNS[c] for c in (getattr(child, "get", lambda *_: None)("class") or []) if c in _RUNS), None)
        text = child.get_text() if child.name else str(child)
        if role:
            runs.append({"t": text.strip(), "role": role, **({"title": child["title"]} if child.get("title") else {})})
        elif runs and "role" not in runs[-1]:
            runs[-1]["t"] += text
        elif text:
            # Kept even when only a space: it is what parts two marked runs (ثقة يحيى).
            runs.append({"t": text})
    for run in runs:
        run["t"] = re.sub(r"\s+", " ", run["t"])
    while runs and "role" not in runs[0] and not runs[0]["t"].strip():
        runs.pop(0)
    while runs and "role" not in runs[-1] and not runs[-1]["t"].strip():
        runs.pop()
    return [r for r in runs if r["t"]]


def _blocks(body) -> list[dict]:
    """A classical text as the page sets it: {"kind", "runs"}, kind title (a bold opening line), para, label (a heading
    such as روى عن) or item (one row of a list under it)."""
    out = []
    for node in body.find_all(["p", "div", "li"]):
        # A block inside another (a <p> in an <li>) is that block's words, not a line of its own.
        if node.find_parent(["p", "li"]) and body in node.parents:
            continue
        classes = node.get("class") or []
        if node.name == "li":
            out.append({"kind": "item", "runs": _runs(node)})
        elif "sublabel" in classes:
            out.append({"kind": "label", "runs": [{"t": _text(node)}]})
        elif node.name == "p":
            bold = node.find("strong")
            out.append({"kind": "title", "runs": [{"t": _text(bold)}]} if bold and _text(bold) == _text(node)
                       else {"kind": "para", "runs": _runs(node)})
    return [b for b in out if b["runs"]]


def _pairs(soup: BeautifulSoup, selector: str) -> list[dict]:
    """The page's pills of one kind as {"en", "ar"}, each language's own, side by side where both pages agree on how many."""
    return [{"en": _en(_text(e)), "ar": _text(a)} for e, a in
            _paired(soup.select(f"{selector}:not(.arabic)"), soup.select(f"{selector}.arabic"))]


def _body(body) -> str:
    """A classical text's plain words: the page's own buttons ("read more" and its icon's name) are not the book's."""
    for button in body.find_all("button"):
        button.decompose()
    return body.get_text("\n", strip=True)


def narrator(html: str) -> dict:
    """One narrator page: names, grade, the labelled facts, appraisals, teachers, students and the classical texts."""
    soup = _soup(html)
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
        "name_en": _en(_text(soup.select_one("h1.hero-title:not(.arabic)"))),
        "name_ar": _text(soup.select_one("h1.hero-title.arabic")),
        "grade_en": _en(_text(soup.select_one("div.pill-grade .pill-text"))),
        "grade_ar": _text(soup.select_one("div.pill-grade .arabic")),
        "grade_rank": int(rank.group(1)) if rank else None,
        "years": _text(soup.select_one("span.pill-secondary:not(.arabic)")),
        "years_ar": _text(soup.select_one("span.pill-secondary.arabic")),
        "alt_en": _en(_text(soup.select_one("p.hero-alt-name:not(.arabic)"))),
        "alt_ar": _text(soup.select_one("p.hero-alt-name.arabic")),
        "books": _pairs(soup, "span.pill-outline"),
        # The page's warnings beside the grade (Ikhtilat, Tadlis): a grade alone would read as clean.
        "flags": _pairs(soup, "span.pill-flag"),
        "facts": _facts(soup),
        "verdicts": [v for v in ((_text(v.select_one(".verdict-scholar")), _text(v.select_one(".critic-quote")))
                                 for v in soup.select("div.verdict")) if all(v)],
        "teachers": _people(soup, "teachers"),
        "students": _people(soup, "students"),
        "hadith_total": int(total.group(1).replace(",", "")) if total else None,
        # The site joins a book and its author with an em dash; the app never prints one.
        "texts": [(_text(a.select_one(".accordion-title")).replace("—", "-"), _body(body), _blocks(body))
                  for a in soup.select("div.accordion") if (body := a.select_one(".accordion-body"))],
    }
