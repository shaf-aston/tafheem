"""timing.timed: result passed through, one log line, failures untimed."""
import logging

import pytest

from backend.services.timing import timed


def test_result_passes_through_and_the_line_names_fields_and_length(caplog):
    with caplog.at_level(logging.INFO, logger="timing"):
        assert timed("heard", lambda a, b: a + b, "ab", "c", ear="groq") == "abc"
    line = caplog.records[-1].getMessage()
    assert line.startswith("heard  ear=groq  out=3  ")
    assert line.endswith("ms")


def test_a_number_has_no_out_and_a_failure_is_not_logged(caplog):
    with caplog.at_level(logging.INFO, logger="timing"):
        timed("count", lambda: 4)
        assert "out=" not in caplog.records[-1].getMessage()
        with pytest.raises(ValueError):
            timed("bad", lambda: (_ for _ in ()).throw(ValueError("x")))
    assert len(caplog.records) == 1
