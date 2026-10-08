"""Split an OpenITI book into its entries, each keeping the page it stands on. Pure: no I/O.

The files use a small markup (data/usul/usul.json `books` names the marker of
each book's entries):

    # text            a paragraph        ~~text    the same paragraph, wrapped
    ### | title       a chapter heading  ### ||    a sub-heading, closing the entry before it
    PageV01P073       the printed page, inline, at its END: the text before it, back to the marker before, is on
                      page 73 (OpenITI mARkdown: "Page number tags are inserted at the end of the corresponding page")
    PageV00P000       a page the digitiser lost: the text before it has no known page
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
    end_page: str = ""   # the page the entry's last words are on: the first marker after it, in this entry or a later one
    pages: list[tuple[int, str]] = field(default_factory=list)   # (offset in text, the page the text before it ends)
    breaks: list[int] = field(default_factory=list)   # offsets in text where the book starts a new paragraph

    def page_at(self, offset: int) -> str:
        """The page marker the text at `offset` stands on: the first marker after it. "" where the book lost it."""
        return next((marker for at, marker in self.pages if at > offset), self.end_page)

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

    spec keys:
      entry        a regex for the line that opens one, with groups n (a book that numbers nothing leaves it out and
                   its entries are numbered 1, 2 ... as they come), head (kept apart) and text (the entry's first
                   words). It is tested before the chapter heading, for a book that numbers its entries `### | N -`.
      end          a regex for a line that closes one without opening another.
      skip         a regex for a line that is neither (a page printed as a sub-heading, `### | [ص: 37]`): dropped,
                   the entry runs on.
      in_heading   keep only entries under a chapter whose title holds this.
      from_heading drop every entry before the first chapter whose title holds this (an editor's introduction
                   numbered the same way).
      stop         a phrase where the last entry ends.
      inline       a regex (group n) for an entry number printed mid-line, which opens a new entry only when it is
                   the next number."""
    entry_re = re.compile(spec["entry"])
    end_re = re.compile(spec["end"]) if spec.get("end") else None
    found: list[Entry] = []
    state = {"heading": "", "cur": None, "seq": 0, "started": not spec.get("from_heading")}
    waiting: list[Entry] = []   # kept entries whose last page no marker has closed yet

    def turn(marker: str) -> None:
        """A page ends here: it closes the text read so far that no earlier marker closed."""
        page = "" if marker == _NO_PAGE else marker
        if state["cur"] is not None:
            state["cur"].pages.append((len(state["cur"].text), page))
        for entry in waiting:
            entry.end_page = page
        waiting.clear()

    def turns(content: str) -> None:
        """The page ends in a line that is no entry's text (a heading, a closing line)."""
        for marker in _PAGE.finditer(content):
            turn(marker[0])

    def close() -> None:
        cur = state["cur"]
        state["cur"] = None
        if cur is None or not state["started"] or (spec.get("in_heading") and spec["in_heading"] not in cur.heading):
            return
        if spec.get("stop") and spec["stop"] in cur.text:
            cur.text = cur.text[:cur.text.index(spec["stop"])].strip()
        found.append(cur)
        waiting.append(cur)

    def feed(content: str) -> None:
        cur = state["cur"]
        pos, pieces = 0, []
        for mark in _MARKS.finditer(content):
            pieces.append(content[pos:mark.start()])
            pos = mark.end()
            if mark[1]:
                if cur is not None:
                    cur.text += _join(cur.text, pieces)
                    pieces = []
                turn(mark[1])
        pieces.append(content[pos:])
        if cur is not None:
            cur.text += _join(cur.text, pieces)

    inline_re = re.compile(spec["inline"]) if spec.get("inline") else None
    skip_re = re.compile(spec["skip"]) if spec.get("skip") else None
    lines = raw.split(_HEADER_END, 1)[-1].split("\n")[::-1]   # a stack, so a split line's rest is read next
    while lines:
        line = lines.pop().rstrip()
        if inline_re:
            # A book numbered in sequence can open the next entry mid-line: "(81)" right after entry 80.
            opening = entry_re.match(line)
            at = int(opening["n"]) if opening else state["cur"].n if state["cur"] else None
            nxt = at and next((m for m in inline_re.finditer(line) if line[:m.start()].strip(" #~")
                               and int(m["n"]) == at + 1), None)
            if nxt:
                lines.append("# " + line[nxt.start():])
                line = line[:nxt.start()].rstrip()
        if skip_re and skip_re.match(line):
            turns(line)
            continue
        if opens := entry_re.match(line):
            close()
            fields = opens.groupdict()
            turns(line[:opens.start("text")] if fields.get("text") is not None else line)
            state["seq"] += 1
            state["cur"] = Entry(n=int(fields["n"]) if "n" in fields else state["seq"], text="", head=(fields.get("head") or "").strip(),
                                 heading=state["heading"])
            feed(fields.get("text") or "")
        elif heading := _HEADING.match(line):
            close()
            turns(line)
            state["heading"] = " ".join(_MARKS.sub("", heading[1] or "").split())
            state["started"] = state["started"] or spec["from_heading"] in state["heading"]
        elif line.startswith("###") or (end_re and end_re.match(line)):
            close()
            turns(line)
        else:
            if line.startswith("#") and state["cur"] is not None:
                state["cur"].breaks.append(len(state["cur"].text))
            feed(re.sub(r"^(?:#|~~)\s?", "", line))
    close()
    return found


def _join(text: str, pieces: list[str]) -> str:
    """The pieces as words to add to `text`: single-spaced, with a space first where text already has words."""
    added = " ".join(" ".join(p.split()) for p in pieces if p.strip())
    return (" " + added if text and added else added)
