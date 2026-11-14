"""The parser's 8-bit encoder answers the same on every processor (services/nahw/syntax/exact_int8.py)."""
import numpy as np
import pytest

from backend.config import data_path
from backend.services.nahw.syntax import exact_int8

ENCODER = data_path("catib_parser_dir") / "encoder.onnx"
needs_encoder = pytest.mark.skipif(not ENCODER.exists(), reason="encoder.onnx is fetched from the parser-model release")


@needs_encoder
@pytest.mark.skipif(not exact_int8.fast_path_is_exact(), reason="the signed weights are the inexact ones here")
def test_unsigned_weights_give_the_same_numbers():
    """Where the signed products are exact (VNNI, ARM), the unsigned copy matches them to the bit."""
    import onnxruntime as ort
    signed = ort.InferenceSession(str(ENCODER), providers=["CPUExecutionProvider"])
    unsigned = ort.InferenceSession(exact_int8.unsigned_weights(ENCODER), providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(0)
    for length in (3, 40, 120):
        ids = rng.integers(5, 30000, size=(1, length)).astype(np.int64)
        feed = {"input_ids": ids, "attention_mask": np.ones_like(ids)}
        assert np.array_equal(signed.run(None, feed)[0], unsigned.run(None, feed)[0])


@needs_encoder
def test_no_signed_weights_are_left():
    import onnx
    model = onnx.load_from_string(exact_int8.unsigned_weights(ENCODER))
    tensors = {t.name: t.data_type for t in model.graph.initializer}
    multiplies = [n for n in model.graph.node if n.op_type == "MatMulInteger"]
    assert multiplies
    assert all(tensors[n.input[i]] == onnx.TensorProto.UINT8 for n in multiplies for i in (1, 3))


@pytest.mark.parametrize("machine, flags, exact", [
    ("aarch64", "", True),
    ("x86_64", "fpu avx2 fma avx512f avx512_vnni", True),
    ("x86_64", "fpu avx2 fma avx_vnni", True),
    ("x86_64", "fpu avx2 fma", False),
    ("x86_64", "fpu avx2 fma avx512f", False),
])
def test_which_processors_need_it(monkeypatch, tmp_path, machine, flags, exact):
    cpuinfo = tmp_path / "cpuinfo"
    cpuinfo.write_text(f"processor\t: 0\nflags\t\t: {flags}\n")
    real_open = open
    monkeypatch.setattr(exact_int8.platform, "machine", lambda: machine)
    monkeypatch.setattr("builtins.open", lambda p, *a, **k: real_open(cpuinfo if p == "/proc/cpuinfo" else p, *a, **k))
    assert exact_int8.fast_path_is_exact() is exact
