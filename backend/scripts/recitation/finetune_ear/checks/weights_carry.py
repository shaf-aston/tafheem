"""Do ear/weights.py's tools change nothing they should not? CPU, a few minutes, ~450 MB of downloads.

    python backend/scripts/recitation/finetune_ear/checks/weights_carry.py

1. model.bin read then written is the same file, byte for byte.
2. The champion differs from the untuned one only in attention (what a LoRA on q/k/v/out changes).
3. Blend 0 is the champion, blend 1 the untuned one.
4. The champion carried into the trainable model exports back to itself exactly; a copy with one
   tensor reverted (a planted bug) is caught, and a change outside attention is refused."""
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

import transformers.utils.import_utils

HERE = Path(__file__).parents[1]
sys.path.insert(0, str(HERE / 'ear'))
import settings as S  # noqa: E402  (pathlib only)
import weights as W  # noqa: E402  (alone: the package's other modules need a GPU machine's downloads)

transformers.utils.import_utils._torchvision_available = False  # a broken local torchvision must not stop the check
from huggingface_hub import snapshot_download  # noqa: E402
from transformers import WhisperForConditionalGeneration, WhisperTokenizerFast  # noqa: E402

NAME = S.NAME
REPO, REVISION = S.CHAMPION.split('@')
work = Path(tempfile.mkdtemp())


def export(model, folder):
    model.save_pretrained(work / 'hf')
    WhisperTokenizerFast.from_pretrained('openai/whisper-base').save_pretrained(work / 'hf')
    subprocess.run(['ct2-transformers-converter', '--model', str(work / 'hf'), '--output_dir', str(folder), '--force',
                    '--quantization', 'float16'], check=True, capture_output=True)
    return W.read(folder / 'model.bin')


def carried(target, folder):
    return export(W.onto_trainable(WhisperForConditionalGeneration.from_pretrained(NAME), untuned, target), work / folder)


champion_bin = Path(snapshot_download(REPO, revision=REVISION, allow_patterns=['model.bin'])) / 'model.bin'
champion = W.read(champion_bin)
untuned = export(WhisperForConditionalGeneration.from_pretrained(NAME), work / 'untuned')
W.write(champion, work / 'again.bin')
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
moved = W.changed(untuned, champion)
reverted = W.Weights(champion.spec, champion.revision, champion.version, dict(champion.tensors), champion.aliases)
reverted.tensors[moved[5]] = untuned.tensors[moved[5]]
outside = W.Weights(champion.spec, champion.revision, champion.version, dict(champion.tensors), champion.aliases)
outside.tensors['decoder/layer_norm/gamma'] = outside.tensors['decoder/layer_norm/gamma'] + outside.tensors['decoder/layer_norm/gamma'].dtype.type(0.5)
try:
    W.onto_trainable(WhisperForConditionalGeneration.from_pretrained(NAME), untuned, outside)
    refused = False
except ValueError:
    refused = True
checks = {
    'round trip is byte-identical': digest(champion_bin) == digest(work / 'again.bin'),
    f'champion moved only attention ({len(moved)} tensors)': bool(moved) and all('attention' in k for k in moved),
    'blend 0 is champion, 1 is untuned': not W.changed(W.blend(champion, untuned, 0.0), champion) and not W.changed(W.blend(champion, untuned, 1.0), untuned),
    'champion carried exports back exactly': not W.changed(carried(champion, 'carried'), champion),
    'planted revert is caught': W.changed(carried(reverted, 'reverted'), champion) == [moved[5]],
    'change outside attention is refused': refused,
}
for what, ok in checks.items():
    print('ok  ' if ok else 'FAIL', what)
sys.exit(0 if all(checks.values()) else 1)
