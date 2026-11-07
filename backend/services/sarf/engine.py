"""The morphology engines, loaded once. None means that engine is not installed.

morphology.py reads these and nothing else touches the libraries, so a test swaps
one (`monkeypatch.setattr(engine, "camel", fake)`) instead of reaching into
morphology's privates. Qalsadi is the fallback and loads only when CAMeL is absent;
PyArabic, the third, is looked for by arabic_text.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

camel = None      # CAMeL analyzer: every reading of one word
mle = None        # CAMeL MLE disambiguator: sentence-level, more accurate
bw2ar = None      # CAMeL's Buckwalter-to-Arabic mapper
qalsadi = None    # lemmatizer, only when CAMeL is absent

try:
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    from camel_tools.utils.charmap import CharMapper

    _analyzer = Analyzer(MorphologyDB.builtin_db())  # v1.5+: no 'top' param; all analyses returned
    bw2ar = CharMapper.builtin_mapper("bw2ar")
    camel = _analyzer  # set last: a failure above leaves CAMeL wholly absent
    logger.info("CAMeL Tools morphological analyzer ready")

    # Sentence-level disambiguation. Word-level selection cannot resolve
    # undiacritised homographs (ذهب = "gold" or "he went") because the evidence
    # that decides it lives in the neighbouring words, not the word itself.
    try:
        from camel_tools.disambig.mle import MLEDisambiguator
        # Every reading, ranked, not just the top one: the typed vowels then
        # choose among them (harakat.best_reading), which a single pick cannot allow.
        mle = MLEDisambiguator.pretrained(top=1_000_000)
        logger.info("CAMeL Tools MLE disambiguator ready")
    except Exception as exc:
        logger.warning("MLE disambiguator unavailable (%s), sentences fall back to word-level analysis", exc)

except Exception as exc:
    logger.warning("CAMeL Tools not available (%s), falling back to Qalsadi", exc)

if camel is None:
    try:
        import qalsadi.lemmatizer as _ql
        qalsadi = _ql.Lemmatizer()
        logger.info("Qalsadi lemmatizer ready")
    except Exception as exc:
        logger.warning("Qalsadi not available (%s), using PyArabic/bare only", exc)
