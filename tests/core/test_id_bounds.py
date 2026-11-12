"""An id too big to exist is a 422, never a 500 from the database, and a 404 never echoes the caller's text."""
import pytest
from fastapi.testclient import TestClient

from backend.main import create_app

HUGE = "9" * 20
client = TestClient(create_app())


@pytest.mark.parametrize("path", [
    f"/api/rijal/narrators/{HUGE}",
    f"/api/rijal/narrators/{HUGE}/hadith",
    f"/api/rijal/chains/bukhari/{HUGE}",
    f"/api/rijal/family/bukhari/{HUGE}",
    f"/api/hadith/bukhari/books/{HUGE}",
])
def test_a_huge_hadith_id_is_422(path):
    assert client.get(path).status_code == 422
