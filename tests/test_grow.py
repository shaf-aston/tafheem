"""Grow: its paths, the scholar's words it quotes, and checking a phrase that
is not an ayah. The ear itself is stood in for.

The one test here that matters most is the quote test: Grow promises that no
ruling on the page is the app's own, and that is only true while every ruling
is a sentence that is actually in the book it names.

Run: python -m pytest tests/test_grow.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import app
from backend.routers import grow
from backend.services import recitation
from backend.services.recitation import listen
from backend.services.recitation.spelling import as_heard

client = TestClient(app)
WEBM = bytes([0x1A, 0x45, 0xDF, 0xA3]) + bytes(8)
BACKEND = Path(__file__).resolve().parent.parent / "backend"
PRAYER_WORLD = BACKEND / "data" / "grow" / "worlds" / "prayer" / "world.json"


def _levels():
    """The prayer world's levels, in the order they are climbed (its own world.json)."""
    return json.loads(PRAYER_WORLD.read_text(encoding="utf-8"))["levels"]
AYAH_KEY = re.compile(r"(\d{1,3}):(\d{1,3})")
SUNNAH_PAGE = re.compile(r"sunnah\.com/([a-z]+:\d+[a-z]?)")


def _quotes():
    """Every quote in the Prayer world with the step or card that carries it: a step's
    ruling, a ruling card's quote and why, and each position's quote on a difference card."""
    world = grow.world("prayer")
    for path in world.paths:
        for step in path.steps:
            if step.ruling:
                yield step, step.ruling
    for unit in world.units:
        for card in unit.cards:
            for quote in (getattr(card, "ruling", None), getattr(card, "quote", None), getattr(card, "why", None)):
                if quote:
                    yield card, quote
            for position in getattr(card, "positions", []):
                yield card, position.quote


def _as_read(text: str) -> str:
    """The book's text with its file markup gone: line marks, page and
    manuscript markers, and line breaks inside a sentence."""
    text = re.sub(r"PageV\d+P\d+|ms\d+", " ", text)
    text = re.sub(r"^(#+ ?(\|+ )?|~~)", " ", text, flags=re.M)
    return " ".join(text.split())


def test_every_path_loads_and_every_step_has_something_to_say():
    paths = client.get("/api/grow/paths").json()
    assert [p["id"] for p in paths] == [p.id for p in grow.paths()]
    for path in paths:
        ids = [step["id"] for step in path["steps"]]
        assert len(ids) == len(set(ids)), path["id"]
        for step in path["steps"]:
            if step["kind"] == "action":
                assert step["instruction"] and not step["arabic"] and not step["ayahs"], step["id"]
            else:
                assert bool(step["arabic"]) != bool(step["ayahs"]), step["id"]


def test_step_ids_are_unique_across_every_path():
    """One record holds every step by id, so two paths sharing one would share progress."""
    ids = [step.id for path in grow.paths() for step in path.steps]
    assert len(ids) == len(set(ids))


def test_every_ayahs_step_is_one_surah():
    """The card loads one surah's text for a step, so a step may not span two."""
    for path in grow.paths():
        for step in path.steps:
            assert len({key.split(":")[0] for key in step.ayahs}) <= 1, step.id


def test_every_path_names_a_tier_and_every_step_sits_in_one_group():
    tiers = {t["id"] for t in _levels()}
    for path in grow.paths():
        assert path.tier in tiers, path.id
        grouped = [step for group in path.groups for step in group.steps]
        assert sorted(grouped) == sorted(step.id for step in path.steps), path.id


def test_every_posture_is_an_action_that_quotes_its_source():
    """A posture cannot be heard, so it is tapped Done; and since it is a ruling
    on how to pray or purify, it carries al-Quduri's own sentence (held to the book below)."""
    actions = [step for path in grow.paths() for step in path.steps if step.kind == "action"]
    assert {"stand-up", "sit-down", "wudu-face", "wudu-feet", "fs-rise", "fs-salam"} <= {step.id for step in actions}
    for step in actions:
        assert step.ruling and step.ruling.known_as == "al-Quduri", step.id


def test_tiers_unlock_in_order_and_each_has_a_path():
    tiers = [t["id"] for t in _levels()]
    used = [tiers.index(path.tier) for path in grow.paths()]
    assert used == sorted(used), "a path sits after every path of an earlier tier"
    assert set(used) == set(range(len(tiers))), "no tier is left without a path"


def test_wudu_is_learnt_before_salah():
    ids = [path.id for path in grow.paths() if path.tier == "basics"]
    assert ids.index("wudu") < ids.index("salah")


def test_every_group_id_is_unique_across_every_path():
    ids = [group.id for path in grow.paths() for group in path.groups]
    assert len(ids) == len(set(ids))


def test_every_wudu_step_is_cited_and_its_du_a_is_a_hadith_phrase():
    wudu = next(path for path in grow.paths() if path.id == "wudu")
    assert len(wudu.steps) >= 10 and all(step.ruling for step in wudu.steps)
    dua = next(step for step in wudu.steps if step.id == "wudu-dua")
    assert dua.arabic and dua.ruling.known_as == "Muslim"


def test_every_adhkar_step_is_a_phrase_cited_to_a_hadith():
    adhkar = next(path for path in grow.paths() if path.id == "adhkar")
    assert adhkar.steps
    for step in adhkar.steps:
        assert step.arabic and step.ruling.known_as == "Muslim", step.id


def test_every_ruling_says_who_it_is_by():
    for card, quote in _quotes():
        assert quote.known_as, card.id


def test_a_world_is_served_whole_and_only_by_its_name():
    """Its levels are its world.json's; every unit file loads; and an id names one
    thing across the world, paths' steps and cards alike."""
    world = client.get("/api/grow/worlds/prayer").json()
    assert [(level["id"], level["title"]) for level in world["levels"]] == [(t["id"], t["title"]) for t in _levels()]
    assert world["paths"] == client.get("/api/grow/paths").json()
    folder = BACKEND / "data" / "grow" / "worlds" / "prayer"
    assert len(world["units"]) == len(json.loads((folder / "world.json").read_text(encoding="utf-8"))["units"]) >= 1
    levels = {level["id"] for level in world["levels"]}
    ids = [step["id"] for path in world["paths"] for step in path["steps"]]
    for unit in world["units"]:
        assert unit["level"] in levels and unit["cards"], unit["title"]
        ids += [card["id"] for card in unit["cards"]]
        for card in unit["cards"]:
            if card["kind"] == "difference":
                assert len({p["school"] for p in card["positions"]}) >= 2, card["id"]
    assert len(ids) == len(set(ids))
    for name in ("nowhere", "x..y", "Prayer", "prayer%2F..%2Fprayer"):
        assert client.get(f"/api/grow/worlds/{name}").status_code == 404, name


def test_the_pillars_unit_is_four_fard_rulings_from_al_quduri():
    unit = next(u for u in grow.world("prayer").units if u.title == "Pillars of the prayer")
    assert [card.kind for card in unit.cards] == ["ruling"] * 4
    assert {card.category for card in unit.cards} == {"fard"}
    assert all(card.quote.known_as == "al-Quduri" for card in unit.cards)
    assert [card.order for card in unit.cards] == [1, 2, 3, 4]


def test_every_ruling_is_the_books_own_sentence():
    """Each book in sources.json is read once; every ruling that names it must be a sentence in it."""
    books = {name: _as_read((BACKEND / source["file"]).read_text(encoding="utf-8"))
             for name, source in grow.sources().items() if source["kind"] == "book"}
    quoted = 0
    for card, quote in _quotes():
        if quote.source in books:
            sentence = " ".join(quote.arabic.split())
            assert sentence in books[quote.source], f"{card.id}: not in {quote.known_as} as written"
            quoted += 1
    assert quoted >= 44


def test_every_hadith_ruling_is_the_hadiths_own_words_and_its_phrase_is_in_it():
    """A hadith is quoted vowels and all, so the quote and the phrase it teaches must both
    be in the hadith as sunnah.com prints it (hadith-sources.json), and the page named must exist there."""
    collections = {name: json.loads((BACKEND / source["file"]).read_text(encoding="utf-8"))["hadith"]
                   for name, source in grow.sources().items() if source["kind"] == "hadith"}
    cited = 0
    for card, quote in _quotes():
        if quote.source in collections:
            sources = collections[quote.source]
            key = SUNNAH_PAGE.search(quote.where).group(1)
            assert sources[key]["page"] == f"https://sunnah.com/{key}", card.id
            said = " ".join(sources[key]["arabic"].split())
            assert " ".join(quote.arabic.split()) in said, f"{card.id}: not in {key}"
            phrase = getattr(card, "arabic", "")
            assert not phrase or " ".join(phrase.split()) in said, f"{card.id}: phrase not in {key}"
            cited += 1
    assert cited == 6


def test_every_ayah_is_a_real_one():
    for path in grow.paths():
        for step in path.steps:
            for key in step.ayahs:
                surah, ayah = map(int, AYAH_KEY.fullmatch(key).groups())
                assert 1 <= surah <= 114 and ayah >= 1, key


def test_every_ayahs_step_is_a_run_the_check_can_take():
    """One recording is checked as a run of consecutive ayahs, at most as many as the route allows."""
    for path in grow.paths():
        for step in path.steps:
            if step.ayahs:
                numbers = [int(key.split(":")[1]) for key in step.ayahs]
                assert numbers == list(range(numbers[0], numbers[0] + len(numbers))), step.id
                assert len(numbers) <= get_settings().recitation_check_ayahs_max, step.id


def test_every_phrase_is_one_ear_word_per_written_word():
    """The page marks words as written and the ear scores words as it spells
    them; the two lists must be the same length or the marks land on the
    wrong words."""
    for path in grow.paths():
        for step in path.steps:
            if step.arabic:
                assert len(as_heard(step.arabic)) == len(step.arabic.split()), step.id


def test_a_phrase_is_scored_whole(monkeypatch):
    asked = []
    monkeypatch.setattr(listen, "sureness", lambda audio, words, model=None: asked.append(words) or [0.91234] * len(words))
    assert recitation.check_text(b"x", "سبحان ربي", "سُبْحَانَ رَبِّيَ الْعَظِيمِ") == [0.912] * 3
    assert len(asked[0]) == 3


def test_nothing_heard_or_too_long_is_not_scored(monkeypatch):
    monkeypatch.setattr(listen, "sureness", lambda *a: (_ for _ in ()).throw(AssertionError("scored")))
    assert recitation.check_text(b"x", "  ", "اللَّهُ أَكْبَرُ") == []
    monkeypatch.setattr(get_settings(), "recitation_sure_max_words", 1)
    assert recitation.check_text(b"x", "الله اكبر", "اللَّهُ أَكْبَرُ") == []


def test_check_text_route_answers_per_word(monkeypatch):
    monkeypatch.setattr(recitation, "check_text", lambda audio, heard, expected, model=None: [1.0, 0.4])
    resp = client.post(
        "/api/listen/check-text", params={"heard": "الله اكبر", "expected": "اللَّهُ أَكْبَرُ"},
        files={"audio": ("r.webm", WEBM)},
    )
    assert resp.status_code == 200
    assert resp.json() == {"sure": [1.0, 0.4]}


def test_check_text_route_refuses_what_is_not_a_recording(monkeypatch):
    monkeypatch.setattr(recitation, "check_text", lambda *a: (_ for _ in ()).throw(AssertionError("scored")))
    resp = client.post(
        "/api/listen/check-text", params={"heard": "الله", "expected": "اللَّهُ"},
        files={"audio": ("r.webm", b"not a recording at all")},
    )
    assert resp.status_code == 415


def test_check_text_route_with_nothing_heard_answers_empty(monkeypatch):
    monkeypatch.setattr(recitation, "check_text", lambda *a: (_ for _ in ()).throw(AssertionError("scored")))
    resp = client.post(
        "/api/listen/check-text", params={"heard": "", "expected": "اللَّهُ"}, files={"audio": ("r.webm", WEBM)},
    )
    assert resp.json() == {"sure": []}


def test_check_text_route_refuses_an_oversize_phrase(monkeypatch):
    monkeypatch.setattr(get_settings(), "recitation_check_heard_max_chars", 5)
    resp = client.post(
        "/api/listen/check-text", params={"heard": "x", "expected": "اللَّهُ أَكْبَرُ"},
        files={"audio": ("r.webm", WEBM)},
    )
    assert resp.status_code == 422
