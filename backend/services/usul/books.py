"""Split an OpenITI book into its entries, each keeping the page it stands on. Pure: no I/O.

The files use a small markup (data/usul/usul.json `books` names the marker of
each book's entries):

    # text            a paragraph        ~~text    the same paragraph, wrapped
    ### | title       a chapter heading  ### ||    a sub-heading, closing the entry before it
    PageV01P073       the printed page, inline; the text after it is on that page
    PageV00P000       a page the digitiser lost: no page is known after it
    ms012             a word-count marker, meaningless to a reader, dropped
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADER_END = "#META#Header#End#"
_HEADING = re.compile(r"^### \|(?: (.*))?$")
_MARKS = re.compile(r"(PageV\d+P\d+)|\bms\d+\b")
_NO_PAGE = "PageV00P000"
_PAGE = re.compile(r"PageV(\d+)P(\d+)(?:-(\d+))?")


@dataclass
class Entry:
    n: int
    text: str
    head: str = ""
    heading: str = ""
    start_page: str = ""
    pages: list[tuple[int, str]] = field(default_factory=list)   # (offset in text, page from there on)

    def page_at(self, offset: int) -> str:
        """The page marker the text at `offset` stands on, "" where the book lost it."""
        page = self.start_page
        for at, marker in self.pages:
            if at > offset:
                break
            page = marker
        return page

    def where(self, offset: int = 0) -> str:
        """Where the text at `offset` is printed: "p. 73", or "no. 322" (the entry's number in its book's list)
        where the digitised book lost its pages, as al-'Ala'i's Jami' al-Tahsil did for its narrator list."""
        return page_label(self.page_at(offset)) or f"no. {self.n}"


def page_label(marker: str) -> str:
    """PageV01P073 as "p. 73"; a volume other than the first as "v2 p. 73"; PageV01P073-74 as "p. 73-74"; "" for no page."""
    found = _PAGE.fullmatch(marker)
    if not found:
        return ""
    volume, page = int(found[1]), f"{int(found[2])}-{found[3]}" if found[3] else int(found[2])
    return f"p. {page}" if volume == 1 else f"v{volume} p. {page}"


def entries(raw: str, spec: dict) -> list[Entry]:
    """Every entry of a book in order.

    spec: `entry`, a regex for the line that opens one, with groups n and, optionally, head (kept apart) and text
    (the first words of the entry); `end`, a regex for a line that closes one without opening another; `in_heading`,
    keep only entries under a chapter whose title holds this; `stop`, a phrase where the last entry ends."""
    entry_re = re.compile(spec["entry"])
    end_re = re.compile(spec["end"]) if spec.get("end") else None
    found: list[Entry] = []
    state = {"page": "", "heading": "", "cur": None}

    def close() -> None:
        cur = state["cur"]
        state["cur"] = None
        if cur is None or (spec.get("in_heading") and spec["in_heading"] not in cur.heading):
            return
        if spec.get("stop") and spec["stop"] in cur.text:
            cur.text = cur.text[:cur.text.index(spec["stop"])].strip()
        found.append(cur)

    def feed(content: str) -> None:
        cur = state["cur"]
        pos, pieces = 0, []
        for mark in _MARKS.finditer(content):
            pieces.append(content[pos:mark.start()])
            pos = mark.end()
            if mark[1]:
                state["page"] = "" if mark[1] == _NO_PAGE else mark[1]
                if cur is not None:
                    cur.text += _join(cur.text, pieces)
                    pieces = []
                    cur.pages.append((len(cur.text), state["page"]))
        pieces.append(content[pos:])
        if cur is not None:
            cur.text += _join(cur.text, pieces)

    body = raw.split(_HEADER_END, 1)[-1]
    for line in body.split("\n"):
        line = line.rstrip()
        if heading := _HEADING.match(line):
            close()
            state["heading"] = (heading[1] or "").strip()
        elif opens := entry_re.match(line):
            close()
            fields = opens.groupdict()
            state["cur"] = Entry(n=int(opens["n"]), text="", head=(fields.get("head") or "").strip(),
                                 heading=state["heading"], start_page=state["page"])
            feed(fields.get("text") or "")
        elif line.startswith("###") or (end_re and end_re.match(line)):
            close()
        else:
            feed(re.sub(r"^(?:#|~~)\s?", "", line))
    close()
    return found


def _join(text: str, pieces: list[str]) -> str:
    """The pieces as words to add to `text`: single-spaced, with a space first where text already has words."""
    added = " ".join(" ".join(p.split()) for p in pieces if p.strip())
    return (" " + added if text and added else added)
