"""An ear's weights as numbers: read and write CTranslate2's model.bin, blend two ears, carry an ear back into
the trainable (Hugging Face) model. Layout mirrors ctranslate2.specs.model_spec._serialize (binary version 6), packed
little-endian without padding: one struct.pack('BI') would pad to four bytes and shift every tensor.
Pure numpy, no torch, except `onto_trainable`, which takes the torch model it edits."""
import struct
from dataclasses import dataclass, field

import numpy as np

KINDS = ('float32', 'int8', 'int16', 'int32', 'float16')  # CTranslate2's DataType order; bfloat16 is never written here


@dataclass
class Weights:
    spec: str
    revision: int
    version: int
    tensors: dict = field(default_factory=dict)  # name -> array, in file order
    aliases: list = field(default_factory=list)  # (alias, name)


def read(path):
    data = memoryview(open(path, 'rb').read())
    at = 0

    def take(fmt):
        nonlocal at
        out = struct.unpack_from('<' + fmt, data, at)
        at += struct.calcsize('<' + fmt)
        return out[0]

    def text():
        nonlocal at
        size = take('H')
        out = bytes(data[at:at + size - 1]).decode('utf-8')
        at += size
        return out

    version, spec = take('I'), text()
    w = Weights(spec, take('I'), version)
    for _ in range(take('I')):
        name = text()
        shape = [take('I') for _ in range(take('B'))]
        kind, size = KINDS[take('B')], take('I')
        w.tensors[name] = np.frombuffer(data[at:at + size], dtype=kind).reshape(shape).copy()
        at += size
    w.aliases = [(text(), text()) for _ in range(take('I'))]
    if at != len(data):
        raise ValueError(f'{path}: {len(data) - at} bytes left after the last alias')
    return w


def write(w, path):
    with open(path, 'wb') as out:
        def text(s):
            out.write(struct.pack('<H', len(s) + 1) + s.encode('utf-8') + b'\0')

        out.write(struct.pack('<I', w.version))
        text(w.spec)
        out.write(struct.pack('<II', w.revision, len(w.tensors)))
        for name, x in w.tensors.items():
            text(name)
            out.write(struct.pack('<B', x.ndim) + struct.pack(f'<{x.ndim}I', *x.shape))
            out.write(struct.pack('<BI', KINDS.index(x.dtype.name), x.nbytes))
            out.write(np.ascontiguousarray(x).tobytes())
        out.write(struct.pack('<I', len(w.aliases)))
        for alias, name in w.aliases:
            text(alias)
            text(name)


def same_layout(a, b):
    if a.spec != b.spec or a.aliases != b.aliases or a.tensors.keys() != b.tensors.keys():
        raise ValueError('the two ears are not the same model shape')
    bad = [k for k in a.tensors if a.tensors[k].shape != b.tensors[k].shape or a.tensors[k].dtype != b.tensors[k].dtype]
    if bad:
        raise ValueError(f'tensors differ in shape or type: {bad[:3]}')


def blend(start, tuned, share):
    """start + share * (tuned - start), tensor by tensor: share 0 is start, 1 is tuned. Sums in float32."""
    same_layout(start, tuned)
    out = Weights(start.spec, start.revision, start.version, aliases=list(start.aliases))
    for k, a in start.tensors.items():
        if not np.issubdtype(a.dtype, np.floating):
            out.tensors[k] = a.copy()  # integer tensors (none in a float16 Whisper) are left as the start had them
            continue
        a32 = a.astype(np.float32)
        out.tensors[k] = (a32 + share * (tuned.tensors[k].astype(np.float32) - a32)).astype(a.dtype)
    return out


def changed(start, tuned):
    """Names of the tensors the two ears disagree on."""
    same_layout(start, tuned)
    return [k for k in start.tensors if not np.array_equal(start.tensors[k], tuned.tensors[k])]


def _attention(prefix, module, self_attention):
    """Which CTranslate2 tensor each projection of one attention block was fused into, as
    (ct2 tensor, row start, row end, torch linear). Mirrors the converter's set_attention."""
    q, k, v, o = module.q_proj, module.k_proj, module.v_proj, module.out_proj
    d = q.weight.shape[0]
    if self_attention:
        return [(f'{prefix}/linear_0', 0, d, q), (f'{prefix}/linear_0', d, 2 * d, k),
                (f'{prefix}/linear_0', 2 * d, 3 * d, v), (f'{prefix}/linear_1', 0, d, o)]
    return [(f'{prefix}/linear_0', 0, d, q), (f'{prefix}/linear_1', 0, d, k),
            (f'{prefix}/linear_1', d, 2 * d, v), (f'{prefix}/linear_2', 0, d, o)]


def attention_map(model):
    """Every attention projection of a Hugging Face Whisper, located in the CTranslate2 export."""
    parts = []
    for i, layer in enumerate(model.model.encoder.layers):
        parts += _attention(f'encoder/layer_{i}/self_attention', layer.self_attn, True)
    for i, layer in enumerate(model.model.decoder.layers):
        parts += _attention(f'decoder/layer_{i}/self_attention', layer.self_attn, True)
        parts += _attention(f'decoder/layer_{i}/attention', layer.encoder_attn, False)
    return parts


def onto_trainable(model, start, tuned):
    """Give a Hugging Face Whisper loaded as `start` the attention of `tuned`, copied from its export, so the
    model exports back to `tuned` bit for bit (adding the difference instead was one float16 step off).
    Only attention moves: it is all a LoRA on q/k/v/out changes. Raises if anything else differs, since
    that change would be silently lost."""
    import torch
    parts = attention_map(model)
    reachable = {p[0] + s for p in parts for s in ('/weight', '/bias')}
    lost = [k for k in changed(start, tuned) if k not in reachable]
    if lost:
        raise ValueError(f'the tuned ear changed tensors outside attention, which cannot be carried: {lost[:3]}')
    with torch.no_grad():
        for name, lo, hi, linear in parts:
            for end, param in (('/weight', linear.weight), ('/bias', linear.bias)):
                if param is None:
                    continue  # k_proj has no bias; the converter fills zeros there
                param.copy_(torch.from_numpy(tuned.tensors[name + end][lo:hi].astype(np.float32)))
    return model
