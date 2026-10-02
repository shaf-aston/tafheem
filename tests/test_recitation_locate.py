"""Where in the Qur'an a reading is (services/recitation/locate.py), on a typed
stretch of the Qur'an, so no corpus or microphone is needed."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import recitation
from backend.services.recitation import locate

AYAHS = {
    (1, 1): "بسم الله الرحمن الرحيم",
    (1, 2): "الحمد لله رب العالمين",
    (1, 3): "الرحمن الرحيم",
    (1, 4): "مالك يوم الدين",
    (1, 5): "إياك نعبد وإياك نستعين",
    (1, 6): "اهدنا الصراط المستقيم",
    (1, 7): "صراط الذين أنعمت عليهم غير المغضوب عليهم ولا الضالين",
    (2, 255): "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ",
    (2, 256): "لا إكراه في الدين قد تبين الرشد من الغي",
    (3, 1): "الم",
    (3, 2): "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ",
    (3, 3): "نزل عليك الكتاب بالحق مصدقا لما بين يديه",
}
LINE = locate.build(sorted(AYAHS.items()))
FATIHAH = locate.span(LINE, (1, 1), (1, 6))
MARGIN = 0.1
FIT = 0.9


def place(heard, near=None):
    return locate.find(heard, LINE, MARGIN, FIT, near)


def test_words_two_ayahs_share_are_not_sure_until_more_is_said():
    assert not place("الله لا إله إلا هو الحي القيوم").sure
    found = place("الله لا إله إلا هو الحي القيوم لا تأخذه سنة ولا نوم")
    assert (found.surah, found.ayah, found.sure, found.home) == (2, 255, True, False)


def test_reciting_elsewhere_while_al_fatihah_is_open_is_sure_and_not_home():
    found = place("لا تأخذه سنة ولا نوم له ما في السماوات", FATIHAH)
    assert (found.surah, found.ayah, found.sure, found.home) == (2, 255, True, False)


def test_the_open_page_wins_a_tie_and_a_misheard_word_does_not_lose_it():
    found = place("الحمد لله رب العالمين الرحمان الرحيم", FATIHAH)
    assert (found.surah, found.ayah, found.home) == (1, 2, True)


def test_the_ayah_after_the_page_is_home_since_that_is_the_page_turning():
    found = place("غير المغضوب عليهم ولا الضالين", FATIHAH)
    assert (found.surah, found.ayah, found.home) == (1, 7, True)
    assert FATIHAH[1] == LINE.where.index((2, 255))


@pytest.mark.parametrize("heard", ["", "موسيقى", "الله", "اشتريت سيارة جديدة امس"])
def test_one_shared_word_or_none_is_no_place(heard):
    assert place(heard) is None


def test_a_reading_that_runs_from_one_ayah_into_the_next_is_found_where_it_starts():
    found = place("وما في الأرض لا إكراه في الدين")
    assert (found.surah, found.ayah, found.sure) == (2, 255, True)


def test_a_lone_place_that_fits_poorly_is_not_sure():
    # No rival, so before the fit floor this was sure at any fit (here 0.89).
    found = place("قد تبين الرشد من الغيب والنور")
    assert found and not found.sure


def test_a_right_place_beside_a_near_duplicate_is_sure():
    found = place("لا تأخذه سنة ولا نوم")
    assert (found.surah, found.ayah, found.sure) == (2, 255, True)


@pytest.fixture
def heard(monkeypatch):
    monkeypatch.setattr(recitation, "_line", lambda: LINE)
    monkeypatch.setattr("backend.routers.listen.recitation.hear",
                        lambda *a, **k: ("لا تأخذه سنة ولا نوم له ما في السماوات", []))

    def post(near):
        return TestClient(app).post(
            "/api/listen", params={"recite": True, **({"near": near} if near else {})},
            files={"audio": ("r.webm", b"\x1a\x45\xdf\xa3 sound", "audio/webm")},
        )
    return post


def test_the_reply_says_where_only_when_asked_with_a_page(heard):
    assert heard(None).json()["place"] is None
    assert heard("1:1-1:6").json()["place"] == {"surah": 2, "ayah": 255, "sure": True, "home": False}


@pytest.mark.parametrize("near", ["1:1", "1:1-x", "1:1-1:6;drop", "1:1-1:1234"])
def test_a_malformed_page_is_refused(heard, near):
    assert heard(near).status_code == 422


@pytest.mark.parametrize("near", ["1:1-1:99", "0:0-1:1", "2:255-1:1"])
def test_a_page_the_quran_does_not_have_is_refused_before_anything_is_heard(heard, monkeypatch, near):
    def never(*a, **k):
        raise AssertionError("heard a recording for a page that is not there")
    monkeypatch.setattr("backend.routers.listen.recitation.hear", never)
    assert heard(near).status_code == 422
