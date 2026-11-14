"""An onnxruntime session for an 8-bit model that answers the same on every processor.

The parser's encoder (data/parser/encoder.onnx) multiplies 8-bit numbers: MatMulInteger,
unsigned inputs times signed weights. onnxruntime does that exactly on a processor with
VNNI (one instruction multiplies and adds into 32 bits) and on ARM. On an x86 processor
without it, the fast path adds pairs of products into 16 bits, which can overflow and is
clipped, so the same sentence gets slightly different numbers there and, where two
readings are close, a different parse. CI's runners are of both kinds: the i'raab score
check passed or failed by which machine a run was given.

Weights shifted by 128 (w + 128 as unsigned, its zero point + 128 too) give the same
products, (a - za)(w - zw), and onnxruntime multiplies unsigned by unsigned exactly on
every processor. That is the same as onnxruntime's own Avx2WeightS8ToU8Transformer,
which only covers the other way of writing an 8-bit model (QDQ). It is slower, about
twice for this encoder, so it is done only where the fast path is not exact.
"""
from __future__ import annotations

import platform
from pathlib import Path

import numpy as np
import onnxruntime as ort

# What /proc/cpuinfo calls the instructions that make onnxruntime's fast path exact.
_EXACT_FLAGS = {"avx512_vnni", "avx_vnni", "amx_int8"}


def fast_path_is_exact() -> bool:
    """True on ARM and on x86 with VNNI; False on x86 without it, or when the flags can't be read."""
    if platform.machine().lower() not in {"x86_64", "amd64", "i386", "i686", "x86"}:
        return True
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            flags = next((line.split(":", 1)[1].split() for line in f if line.startswith("flags")), [])
    except OSError:
        return False
    return bool(_EXACT_FLAGS & set(flags))


def unsigned_weights(path: Path) -> bytes:
    """The model at `path` with every MatMulInteger's signed weights and zero point made unsigned."""
    import onnx  # only here: the app imports it on processors that need this, nowhere else
    from onnx import numpy_helper

    model = onnx.load(str(path))
    tensors = {t.name: t for t in model.graph.initializer}
    for node in model.graph.node:
        if node.op_type != "MatMulInteger" or len(node.input) < 4:
            continue
        for name in (node.input[1], node.input[3]):  # the weights and their zero point
            tensor = tensors.get(name)
            if tensor is None or tensor.data_type != onnx.TensorProto.INT8:
                continue
            values = numpy_helper.to_array(tensor).astype(np.int16) + 128
            tensor.CopyFrom(numpy_helper.from_array(values.astype(np.uint8), name))
    return model.SerializeToString()


def session(path: Path) -> ort.InferenceSession:
    """A CPU session for `path` whose 8-bit products are exact on this processor."""
    model = str(path) if fast_path_is_exact() else unsigned_weights(path)
    return ort.InferenceSession(model, providers=["CPUExecutionProvider"])
