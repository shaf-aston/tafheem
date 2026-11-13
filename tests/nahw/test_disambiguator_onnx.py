"""The ONNX disambiguator feeds BERT as CAMeL 1.6 does (camel_tools/disambig/bert).

Whether it ranks every reading the same is checked against CAMeL itself, over
thousands of sentences, by scripts/nahw/check_disambig_parity.py (run in CI).
These pin the odd corners of how words become model input, with a stand-in
tokenizer and model so they need no files: the model here answers each word
piece with the label numbered as that piece's id, so a word's tag says which
piece it was read from.
"""
from types import SimpleNamespace

import numpy as np

from backend.services.nahw.syntax import disambiguator_onnx
from backend.services.nahw.syntax.disambiguator_onnx import OnnxDisambiguator

CLS, SEP, UNK = 2, 3, 1


class _Tokenizer:
    def __init__(self, pieces):
        self.pieces = pieces

    def encode(self, word, add_special_tokens=False):
        return SimpleNamespace(ids=list(self.pieces.get(word, [])))


class _Model:
    def __init__(self):
        self.calls = []

    def run(self, _outputs, feeds):
        ids, mask = feeds["input_ids"], feeds["attention_mask"]
        self.calls.append((ids.copy(), mask.copy()))
        logits = np.zeros((*ids.shape, 2000), dtype=np.float32)
        for row, col in np.ndindex(ids.shape):
            logits[row, col, ids[row, col]] = 1
        return [logits]


def _disambiguator(pieces):
    d = object.__new__(OnnxDisambiguator)
    d._top = 1
    d._features = ["pos"]
    d._labels = [{"pos": str(i)} for i in range(2000)]
    d._tok = _Tokenizer(pieces)
    d._cls, d._sep, d._unk = CLS, SEP, UNK
    d._sess = _Model()
    d._analyzer = SimpleNamespace(analyze=lambda word: [])  # unread: the tag is the reading
    d._ranking_cache = {}
    d._cache_lock = disambiguator_onnx.threading.Lock()
    return d


def _tags(d, sentence):
    return [w.analyses[0].analysis for w in d.disambiguate(sentence)]


def test_a_word_is_tagged_at_its_first_piece_with_its_bare_letters():
    d = _disambiguator({"كتب": [10, 11], "الولد": [20]})
    assert _tags(d, ["كَتَبَ", "الولد"]) == [
        {"pos": "10", "lex": "كتب", "diac": "كتب"},
        {"pos": "20", "lex": "الولد", "diac": "الولد"},
    ]
    (ids, mask), = d._sess.calls
    assert ids.tolist() == [[CLS, 10, 11, 20, SEP]] and mask.all()


def test_a_blank_word_shifts_the_tags_up_and_drops_the_last_word_as_camel_does():
    d = _disambiguator({"أ": [10], "ب": [20], "ج": [30]})
    words = d.disambiguate(["أ", " ", "ب", "ج"])
    assert [w.word for w in words] == ["أ", " ", "ب"]
    assert [w.analyses[0].analysis["pos"] for w in words] == ["10", "20", "30"]
    assert [w.analyses[0].analysis["lex"] for w in words] == ["أ", " ", "ب"]


def test_no_pieces_or_only_unknown_pieces_is_one_unknown():
    d = _disambiguator({"أ": [], "ب": [UNK, UNK], "ج": [UNK, 30]})
    d.disambiguate(["أ", "ب", "ج"])
    (ids, _), = d._sess.calls
    assert ids.tolist() == [[CLS, UNK, UNK, UNK, 30, SEP]]


def test_a_long_sentence_is_cut_at_a_word_into_segments_run_together_padded():
    # 300 words of two pieces: 255 fit in 510, the rest start a second segment
    pieces = {f"w{i}": [100 + i, 1500] for i in range(300)}
    d = _disambiguator(pieces)
    tags = _tags(d, [f"w{i}" for i in range(300)])
    assert [t["pos"] for t in tags] == [str(100 + i) for i in range(300)]
    (ids, mask), = d._sess.calls
    assert ids.shape == (2, 512)
    assert mask[0].sum() == 512 and mask[1].sum() == 2 + 45 * 2
    assert (ids[1, mask[1] == 0] == 0).all()  # padded with [PAD], 0
    assert ids[1, 45 * 2 + 1] == SEP


def test_nothing_to_read_reads_nothing():
    d = _disambiguator({})
    assert d.disambiguate([]) == [] and d.disambiguate([""]) == []
    assert d._sess.calls == []
