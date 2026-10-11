"""Export CAMeL's BERT disambiguator to ONNX, so the parser runs without torch.

    python -m backend.scripts.build_disambig_onnx [--int8]

The only place in the project that imports torch and transformers: they are
needed here once, to read CAMeL's fine-tuned weights (camel_data
"disambig-bert-unfactored-msa", ~440 MB) and write them as a graph that
onnxruntime can run. The app itself (services/syntax/disambiguator_onnx.py)
never imports either.

Writes into the folder named by `catib_disambig_dir` in backend/config.py:

  model.onnx      BERT token classifier (input_ids, attention_mask -> logits).
                  Over GitHub's size limit, so .gitignore keeps it out of git.
  tokenizer.json  the WordPiece tokenizer, in the `tokenizers` library's format
  labels.json     {"itos": [...]} the label for each logit, as CAMeL names them
  config.json     the analyzer database, backoff, scorer, tie breaker and
                  feature list CAMeL ships for this model (default_config.json)
  mle_model.json  CAMeL's tie-breaker probabilities, copied unchanged

`--int8` also quantises the weights (dynamic, 8-bit) to roughly a quarter of the
size. Use it only if backend/scripts/check_disambig_parity.py still reports every
word's chosen analysis identical to CAMeL's own.

CAMeL's own 556 MB ranking cache is deliberately not exported: it only stores
scores that the analyzer recomputes, and loading it is most of the memory cost.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above

DATASET, MODEL_NAME = "DisambigBertUnfactored", "msa"
# ONNX operator set the graph is written in.
OPSET = 17


def _export_fp32(model_dir: Path, out: Path) -> None:
    import torch
    from transformers import BertForTokenClassification

    model = BertForTokenClassification.from_pretrained(str(model_dir)).eval()
    ids = torch.tensor([[2, 100, 101, 102, 3]])
    mask = torch.ones_like(ids)
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
    """The fast tokenizer's file, plus the one step it leaves out: the slow
    BertTokenizer CAMeL uses recomposes each word to Unicode NFC, which joins
    alef + maddah (U+0627 U+0653) into آ (U+0622) before the vocabulary is
    looked up. Without it, about 5% of Qur'anic spellings tokenise differently."""
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

    id2label = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))["id2label"]
    labels = [id2label[str(i)] for i in range(len(id2label))]
    (out_dir / "labels.json").write_text(json.dumps({"itos": labels}), encoding="utf-8")
    shutil.copyfile(model_dir / "default_config.json", out_dir / "config.json")
    shutil.copyfile(model_dir / "mle_model.json", out_dir / "mle_model.json")
    _write_tokenizer(model_dir, out_dir / "tokenizer.json")

    final = out_dir / "model.onnx"
    if args.int8:
        raw = out_dir / "model.fp32.onnx"
        _export_fp32(model_dir, raw)
        _quantise(raw, final)
        raw.unlink()
    else:
        _export_fp32(model_dir, final)
    print(f"wrote {final} ({final.stat().st_size / 2**20:.0f} MB), {len(labels)} labels")


if __name__ == "__main__":
    main()
