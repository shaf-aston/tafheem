"""Export CAMeL's BERT disambiguator to ONNX, so ranking a sentence's readings runs without torch.

    python -m backend.scripts.nahw.build_disambig_onnx [--int8]

Reads CAMeL's fine-tuned weights (camel_data "disambig-bert-unfactored-msa", ~440 MB,
in `camel_data -i defaults`) with torch and transformers, once, and writes them as a
graph onnxruntime can run (services/nahw/syntax/disambiguator_onnx.py, which imports
neither). The server runs this from deploy/sync.sh when the model is missing or this
script has changed, and CI runs it before the parity check, each with its own CAMeL,
so the tokenizer written is the one that CAMeL there uses.

Writes into the folder named by `catib_disambig_dir` in backend/config.py, none of it in git:

  model.onnx      BERT token classifier (input_ids, attention_mask -> logits), ~420 MB
  tokenizer.json  the WordPiece tokenizer, in the `tokenizers` library's format
  labels.json     {"itos": [...]} the label for each logit, as CAMeL names them
  config.json     the analyzer database, backoff, scorer, tie breaker and feature
                  list CAMeL ships for this model (its default_config.json)
  mle_model.json  CAMeL's tie-breaker probabilities, copied unchanged

model.onnx is written last, under another name and then renamed, so a build that
stops part way never leaves a folder the app would load.

`--int8` also quantises the weights (dynamic, 8-bit) to about a quarter of the size.
Use it only if backend/scripts/nahw/check_disambig_parity.py still passes.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from backend.config import data_path

DATASET, MODEL_NAME = "DisambigBertUnfactored", "msa"
# ONNX operator set the graph is written in.
OPSET = 17


def _export_fp32(model_dir: Path, out: Path) -> None:
    import torch
    from transformers import BertForTokenClassification

    model = BertForTokenClassification.from_pretrained(str(model_dir)).eval()
    ids = torch.tensor([[2, 100, 101, 102, 3], [2, 100, 3, 0, 0]])
    mask = (ids != 0).long()
    with torch.no_grad():
        torch.onnx.export(
            model, (ids, mask), str(out),
            input_names=["input_ids", "attention_mask"], output_names=["logits"],
            dynamic_axes={"input_ids": {0: "batch", 1: "seq"},
                          "attention_mask": {0: "batch", 1: "seq"},
                          "logits": {0: "batch", 1: "seq"}},
            opset_version=OPSET, dynamo=False)


def _quantise(src: Path, dst: Path) -> None:
    from onnxruntime.quantization import QuantType, quantize_dynamic
    quantize_dynamic(str(src), str(dst), weight_type=QuantType.QInt8)


def _write_tokenizer(model_dir: Path, out: Path) -> None:
    """The tokenizer CAMeL itself loads (transformers' BertTokenizer), saved as it is.
    transformers 5 builds it on the `tokenizers` library, so it saves unchanged. The
    older pure-Python BertTokenizer has no such file to save; its fast twin does the
    same except one step, the recomposing of each word to Unicode NFC (alef + maddah,
    U+0627 U+0653, to آ), which is added to it."""
    from transformers import BertTokenizer
    tok = getattr(BertTokenizer.from_pretrained(str(model_dir)), "backend_tokenizer", None)
    if tok is None:
        from tokenizers import normalizers
        from transformers import BertTokenizerFast
        tok = BertTokenizerFast.from_pretrained(str(model_dir)).backend_tokenizer
        tok.normalizer = normalizers.Sequence([tok.normalizer, normalizers.NFC()])
    tok.save(str(out))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--int8", action="store_true", help="quantise the weights to 8 bits")
    args = ap.parse_args()

    from camel_tools.data import CATALOGUE
    model_dir = Path(CATALOGUE.get_dataset(DATASET, MODEL_NAME).path)
    out_dir = data_path("catib_disambig_dir")
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / "model.onnx"
    final.unlink(missing_ok=True)

    id2label = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))["id2label"]
    labels = [id2label[str(i)] for i in range(len(id2label))]
    (out_dir / "labels.json").write_text(json.dumps({"itos": labels}), encoding="utf-8")
    shutil.copyfile(model_dir / "default_config.json", out_dir / "config.json")
    shutil.copyfile(model_dir / "mle_model.json", out_dir / "mle_model.json")
    _write_tokenizer(model_dir, out_dir / "tokenizer.json")

    raw = out_dir / "model.fp32.onnx.part"
    _export_fp32(model_dir, raw)
    if args.int8:
        part = out_dir / "model.int8.onnx.part"
        _quantise(raw, part)
        raw.unlink()
        raw = part
    raw.replace(final)
    print(f"wrote {final} ({final.stat().st_size / 2**20:.0f} MB), {len(labels)} labels")


if __name__ == "__main__":
    main()
