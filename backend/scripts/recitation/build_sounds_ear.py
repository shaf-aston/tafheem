"""Build what the sounds ear (services/recitation/sounds.py) runs on. This PC only.

    python backend/scripts/recitation/build_sounds_ear.py export      # model -> int8 onnx in recitation_sounds_path
    python backend/scripts/recitation/build_sounds_ear.py verify      # int8 decodes the same as the original?
    python backend/scripts/recitation/build_sounds_ear.py reference   # every ayah's expected sounds, per word

export: loads quran-dev/wav2vec2-ctc-quran-phoneme-run66-iqratts-mix-final-20260909
from the Hugging Face cache, wraps it so the sound is normalised inside the graph
(the server has no transformers), writes an fp32 onnx to a scratch folder and
quantises the weights to int8 into the data folder. Only MatMul is quantised:
the convolutions in front stay fp32, where int8 would cost most accuracy.
Per channel: 98.5% of sounds agreed with torch on 20 clips against 98.0% per tensor.

verify: on N recordings from the marked-recitation downloads, the greedy decode of
the int8 model against the original torch model's. Prints how many clips decode
to exactly the same sounds, and the sound-level agreement over all of them.

reference: runs quranic-phonemizer over all 6,236 ayahs, so the server needs no
phonemizer. A word-count mismatch with the page's words (imlaei) is dropped from
the file, never guessed (sounds.expected_for says the same on the server).

Needs torch, transformers, onnx, onnxruntime and quranic-phonemizer (system
Python; the server needs none of them).
"""
from __future__ import annotations

import argparse
import difflib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.config import data_path  # noqa: E402
from backend.services.recitation import sound_compare, sounds  # noqa: E402
from backend.services.recitation.place import bare_word  # noqa: E402
from backend.services.recitation.spelling import as_heard  # noqa: E402

SCRATCH = Path(tempfile.gettempdir()) / "sounds-ear-fp32"
# The export is traced at this length and told the time axis is free; onnx wants an example.
EXAMPLE_SECONDS = 4
OPSET = 17
# How the phonemizer writes the vocative يَا: a j and a long a.
VOCATIVE = ("j", "a:")


def export(source: str | None) -> None:
    import torch
    from onnxruntime.quantization import QuantType, quantize_dynamic

    from backend.scripts.recitation.score_phoneme_checker import MODEL_ID, SAMPLE_RATE, load_model, vocab_file
    source = source or MODEL_ID

    model, _, _ = load_model(source)

    class Hearing(torch.nn.Module):
        """Raw 16kHz sound in, a score per symbol per 20ms out. The feature
        extractor's normalisation (zero mean, unit variance) is done here."""
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, audio):
            audio = (audio - audio.mean(dim=-1, keepdim=True)) / torch.sqrt(audio.var(dim=-1, unbiased=False, keepdim=True) + 1e-7)
            return self.inner(audio).logits

    SCRATCH.mkdir(exist_ok=True)
    fp32 = SCRATCH / "model.onnx"
    example = torch.randn(1, SAMPLE_RATE * EXAMPLE_SECONDS)
    with torch.no_grad():
        torch.onnx.export(Hearing(model).eval(), example, str(fp32), input_names=["audio"], output_names=["logits"],
                          dynamic_axes={"audio": {1: "samples"}, "logits": {1: "frames"}}, opset_version=OPSET,
                          dynamo=False)
    folder = data_path("recitation_sounds_path")
    folder.mkdir(parents=True, exist_ok=True)
    quantize_dynamic(str(fp32), str(folder / sounds.MODEL), weight_type=QuantType.QInt8, op_types_to_quantize=["MatMul"],
                      per_channel=True)
    shutil.copy(vocab_file(source), folder / sounds.VOCAB)
    for f in sorted(folder.iterdir()):
        print(f"{f.name}  {f.stat().st_size / 1e6:.0f} MB")
    print(f"fp32 kept at {fp32} for verify")


def session(path: Path):
    import onnxruntime as ort
    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def onnx_decode(sess, sound: np.ndarray, id2sym: dict[int, str]) -> list[str]:
    (logits,) = sess.run(None, {"audio": sound[None, :].astype(np.float32)})
    return sound_compare.collapse(logits[0].argmax(-1).tolist(), id2sym)[0]


def verify(count: int, source: str | None) -> None:
    from backend.scripts.recitation.score_phoneme_checker import LONGEST_S, MODEL_ID, decode, load_model, wav_floats
    from backend.scripts.recitation.score_recitation_checker import recordings, seconds

    ayahs = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    model, fe, id2sym = load_model(source or MODEL_ID)
    int8 = session(data_path("recitation_sounds_path") / sounds.MODEL)
    fp32 = session(SCRATCH / "model.onnx") if (SCRATCH / "model.onnx").is_file() else None
    same8 = same32 = total = agree = sym_total = 0
    # Spread across both sets and all reciters, not the first N of the first file.
    every = max(1, sum(1 for _ in recordings(ayahs)) // count)
    for n, (_rid, audio, _key, _marks) in enumerate(recordings(ayahs)):
        if total >= count:
            break
        if n % every or seconds(audio) > LONGEST_S:
            continue
        total += 1
        want = decode(model, fe, id2sym, audio)[0]
        got = onnx_decode(int8, wav_floats(audio), id2sym)
        same8 += got == want
        if fp32:
            same32 += onnx_decode(fp32, wav_floats(audio), id2sym) == want
        blocks = difflib.SequenceMatcher(a=want, b=got, autojunk=False).get_matching_blocks()
        agree += sum(b.size for b in blocks)
        sym_total += max(len(want), len(got))
    print(f"{total} clips")
    if fp32:
        print(f"fp32 onnx decodes identically to torch: {same32}/{total} = {same32 / total:.0%}")
    print(f"int8 onnx decodes identically to torch: {same8}/{total} = {same8 / total:.0%}")
    print(f"int8 sounds agreeing with torch's, all clips: {agree}/{sym_total} = {agree / sym_total:.1%}")


def unglue_vocative(page: list[str], phonemes: list[tuple]) -> list[tuple]:
    """The phonemizer writes the vocative يَا as the start of the word after it
    ('ja:' + the rest); the page has it as a word of its own. Cut it back out,
    only where the page has a bare يا and the next word's sounds begin ja:."""
    out = list(phonemes)
    for i, word in enumerate(page):
        if len(out) >= len(page):
            break
        if bare_word(word) == "يا" and i < len(out) and tuple(out[i][:2]) == VOCATIVE and len(out[i]) > 2:
            out[i:i + 1] = [VOCATIVE, tuple(out[i][2:])]
    return out


def reference() -> None:
    from quranic_phonemizer import Phonemizer

    hafs = Phonemizer()
    plain = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    out, mismatched = {}, []
    for key, text in plain.items():
        page = as_heard(text)
        words = unglue_vocative(page, hafs.analyse(key).phonemes(by="word"))
        if len(words) == len(page):
            out[key] = [list(w) for w in words]
        else:
            mismatched.append(key)
    path = data_path("recitation_sounds_reference_path")
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(out)} ayahs written to {path} ({path.stat().st_size / 1e6:.1f} MB); "
          f"{len(mismatched)} left out for a word count that differs: {' '.join(mismatched[:12])}...")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="job", required=True)
    sub.add_parser("export").add_argument("--source", help="a trained model folder; the Hugging Face model when left out")
    sub.add_parser("reference")
    verifying = sub.add_parser("verify")
    verifying.add_argument("--clips", type=int, default=20)
    verifying.add_argument("--source")
    args = parser.parse_args()
    {"export": lambda: export(args.source), "reference": reference, "verify": lambda: verify(args.clips, args.source)}[args.job]()


if __name__ == "__main__":
    main()
