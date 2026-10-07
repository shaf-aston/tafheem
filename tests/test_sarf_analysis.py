"""A word's whole Sarf answer, called without the web layer."""
import pytest

from backend.services import morphology, sarf_word


@pytest.mark.skipif(not morphology._CAMEL_AVAILABLE, reason="CAMeL data not installed")
def test_istaqbala_conjugates_as_form_x_not_as_qabala():
    got = sarf_word.analyze("اِسْتَقْبَلَ", None)
    assert got.root and got.table and got.table.rows
    assert got.form == "X" and got.wazn
    assert got.source and got.meaning_source


def test_unknown_form_for_root_gives_reason_not_table():
    got = sarf_word.table_for("كتب", "IQ")
    assert got.table is None and got.table_note and got.form is None
