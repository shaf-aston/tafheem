"""The Jawhara file build (scripts/build_jawhara.py) is sound and its text is clean.

The poem is the one book not from OpenITI, so this is where its shape is held: 144 bayts of two
halves under plain headings, no tatweel, no editor's brackets, no doubled haraka and no sukun
straight before a vowel (the slips the Wikisource copy had)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from backend.scripts import build_jawhara as build

HARAKA = "[ً-ْ]"


@pytest.fixture(scope="module")
def body() -> str:
    text = build.build(build.SOURCE.read_text(encoding="utf-8"))
    assert text.startswith("######OpenITI#")
    return text.split("#META#Header#End#", 1)[1]


def test_144_bayts_of_two_halves(body):
    bayts = [line[2:] for line in body.splitlines() if line.startswith("# ")]
    assert len(bayts) == build.BAYTS
    assert all(bayt.count(" % ") == 1 for bayt in bayts)
    assert bayts[0].startswith("الحَمْدُ لِلّهِ")
    assert bayts[-1].endswith("مِنْ أُمَّتِهْ")


def test_headings_are_plain(body):
    headings = [line[6:] for line in body.splitlines() if line.startswith("### | ")]
    assert len(headings) == len(build.SECTIONS)
    assert headings[0] == "المقدمة"
    assert not any(re.search(r"ms\d+|PageV|\d", heading) for heading in headings)


def test_text_is_clean(body):
    assert "ـ" not in body
    assert not re.search(r"[\[\]]", body)
    assert not re.search(rf"({HARAKA})\1", body), "a doubled haraka"
    assert not re.search(rf"ْ{HARAKA}", body), "a sukun straight before a vowel"
    assert not re.search(r"  ", body), "a doubled space"


def test_every_fix_is_applied_once():
    raw = "\n".join(build.bayts_of(build.SOURCE.read_text(encoding="utf-8")))
    assert all(raw.count(wrong) == 1 for wrong, _ in build.FIXES)
    text = build.fixed(raw)
    assert all(right in text for _, right in build.FIXES)


def test_the_written_file_matches_the_build(body):
    written = Path(build.OUT).read_text(encoding="utf-8").split("#META#Header#End#", 1)[1]
    assert written == body


def test_a_bayt_without_two_halves_stops_the_build():
    with pytest.raises(SystemExit):
        build.bayts_of("{{أبيات|نصف واحد}}")


def test_the_wrong_number_of_bayts_stops_the_build():
    many = "{{أبيات|" + "\n".join("أ\\\\ب" for _ in range(145)) + "}}"
    assert len(build.bayts_of(many)) == 145
    with pytest.raises(SystemExit):
        build.build(many)
