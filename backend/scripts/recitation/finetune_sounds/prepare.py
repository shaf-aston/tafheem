"""Once, on this PC: make the two private Kaggle datasets a sounds run needs and upload them.

    python backend/scripts/recitation/finetune_sounds/prepare.py              build both, then upload as new datasets
    python backend/scripts/recitation/finetune_sounds/prepare.py --update     build both, then upload as new versions
    python backend/scripts/recitation/finetune_sounds/prepare.py --no-upload  build only

sounds-model   the start model, copied from this PC's Hugging Face cache (its Hub page answers 401 now).
sounds-checks  the reviewer-marked learner recordings (fetch_recitation_checks.py's downloads): one audio.npy of
               16-bit numbers plus checks.jsonl: per recording its ayah, where its sound sits in audio.npy, each
               word's mark (letter or word / vowel / tajweed / none) and each word's reference phonemes.
               The judge listens to these and never trains on them.
Needs fetch_recitation_checks.py run first and `pip install quranic-phonemizer`.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from huggingface_hub import snapshot_download

HERE = Path(__file__).parent
sys.path[:0] = [str(HERE.parents[3]), str(HERE.parent / 'finetune_ear'), str(HERE)]

from sounds import settings as S  # noqa: E402
from sounds import targets  # noqa: E402

from backend.config import data_path  # noqa: E402
from backend.scripts.recitation.paths import DOWNLOADS  # noqa: E402
from backend.scripts.recitation.score_phoneme_checker import LONGEST_S, MODEL_ID, wav_floats  # noqa: E402
from backend.scripts.recitation.score_recitation_checker import marks_to_places, recordings, seconds  # noqa: E402
from backend.services.recitation.spelling import as_heard  # noqa: E402

OWNER = json.loads((HERE / 'kernel-metadata.json').read_text())['id'].split('/')[0]
BUILT = DOWNLOADS / 'sounds'  # gitignored with the rest of downloads/
MODEL_FILES = ('config.json', 'model.safetensors', 'preprocessor_config.json', 'vocab.json', 'README.md')


def describe(folder, name):
    (folder / 'dataset-metadata.json').write_text(json.dumps(
        {'title': name, 'id': f'{OWNER}/{name}', 'licenses': [{'name': 'other'}]}), encoding='utf-8')
    return folder


def model():
    folder = BUILT / S.MODEL_DATASET
    folder.mkdir(parents=True, exist_ok=True)
    cached = Path(snapshot_download(MODEL_ID, local_files_only=True))
    for name in MODEL_FILES:
        shutil.copyfile(cached / name, folder / name)
    return describe(folder, S.MODEL_DATASET)


def checks():
    folder = BUILT / S.CHECKS_DATASET
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    ayahs = json.loads(data_path('quran_imlaei_path').read_text(encoding='utf-8'))
    rows, sounds, at, skipped = [], [], 0, {'longer than the checker hears': 0, 'word count differs from the phonemizer': 0}
    for rid, audio, key, marks in recordings(ayahs):
        expected, ref = as_heard(ayahs[key]), targets.by_word(key)
        if seconds(audio) > LONGEST_S:
            skipped['longer than the checker hears'] += 1
        elif len(ref) != len(expected):
            skipped['word count differs from the phonemizer'] += 1
        else:
            places = marks_to_places(expected, marks)
            sounds.append(np.round(wav_floats(audio) * 32768).astype(np.int16))  # exactly the 16-bit numbers the checker heard
            rows.append({'id': rid, 'start': at, 'stop': at + len(sounds[-1]), 'ayah': key,
                         'kinds': [places.get(i) for i in range(len(expected))], 'ref': [list(w) for w in ref]})
            at += len(sounds[-1])
    np.save(folder / S.CHECKS_AUDIO, np.concatenate(sounds))
    (folder / S.CHECKS_MARKER).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    print(len(rows), 'recordings written; left out:', skipped)
    return describe(folder, S.CHECKS_DATASET)


if __name__ == '__main__':
    built = [model(), checks()]
    if '--no-upload' not in sys.argv:
        for folder in built:
            subprocess.run(['kaggle', 'datasets', *(['version', '-m', 'rebuilt'] if '--update' in sys.argv else ['create']), '-p', str(folder)],
                           check=True, capture_output=True, text=True, encoding='utf-8')  # its progress bars are not worth reading
