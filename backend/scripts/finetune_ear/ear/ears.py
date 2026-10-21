"""Ears as folders faster-whisper loads (CTranslate2): the served one, the untuned one, blends, and a trained one."""
import re
import shutil
import subprocess
import urllib.request

from huggingface_hub import snapshot_download
from transformers import GenerationConfig, WhisperForConditionalGeneration, WhisperTokenizerFast

from . import settings as S
from . import weights
from .text import processor


def served():
    """(repo, revision) of the ear master's config.py pins: the one the app serves and the judge must beat."""
    return re.search(S.SERVED_PIN, urllib.request.urlopen(S.SERVED).read().decode()).groups()


def download(repo, revision, folder):
    return snapshot_download(repo, revision=revision, local_dir=folder, allow_patterns=['*.json', '*.bin'])


def trainable():
    """The untuned model, ready to train or export."""
    model = WhisperForConditionalGeneration.from_pretrained(S.NAME).cuda()
    # tarteel ships no generation_config.json, so it lacks the language table; its base model has it.
    model.generation_config = GenerationConfig.from_pretrained(f'openai/whisper-{S.SIZE}')
    model.generation_config.language = 'ar'
    model.generation_config.task = 'transcribe'
    model.generation_config.forced_decoder_ids = None
    return model


def export(model, folder):
    """A model as the CTranslate2 folder faster-whisper loads, made the way the served ear was.
    tokenizer.json from openai/whisper-SIZE: same words as Tarteel's, plus the timestamp marks theirs
    lacks; without the file faster-whisper silently fetches openai/whisper-tiny's."""
    merged = S.OUT / 'ear-merged'
    model.save_pretrained(merged)
    WhisperTokenizerFast.from_pretrained(f'openai/whisper-{S.SIZE}').save_pretrained(merged)
    processor.feature_extractor.save_pretrained(merged)  # the processor alone no longer writes this file
    subprocess.run(['ct2-transformers-converter', '--model', str(merged), '--output_dir', str(folder), '--force',
                    '--copy_files', 'preprocessor_config.json', 'tokenizer.json', '--quantization', 'float16'], check=True)
    shutil.rmtree(merged)  # 280 MB that would otherwise be downloaded for nothing
    return folder


def blend(untuned, tuned, share, folder):
    """`tuned` moved `share` of the way back toward `untuned`: share 0 is tuned, 1 is untuned. Same files as tuned."""
    shutil.copytree(tuned, folder, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.cache'))
    weights.write(weights.blend(weights.read(f'{tuned}/model.bin'), weights.read(f'{untuned}/model.bin'), share),
                  f'{folder}/model.bin')
    return folder


def as_trainable(untuned, ear):
    """The trainable model carrying `ear`'s attention: the start a new round trains from, so rounds stack."""
    return weights.onto_trainable(trainable(), weights.read(f'{untuned}/model.bin'), weights.read(f'{ear}/model.bin'))
