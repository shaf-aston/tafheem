"""Hearing: the model on the card, and recordings as the phoneme symbols it writes (greedy CTC, one clip at a time)."""
import numpy as np
import torch
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC

from . import settings as S
from . import targets
from .words import collapse


def load(folder):
    """(model, feature extractor, id to symbol) of a model folder, on the card, ready to listen. Full precision: the
    numbers it writes must match the ones score_phoneme_checker.py wrote on the CPU."""
    model = Wav2Vec2ForCTC.from_pretrained(folder).cuda().eval()
    return model, Wav2Vec2FeatureExtractor.from_pretrained(folder), {i: s for s, i in targets.vocab(folder).items()}


def hear(ear, sounds):
    """The symbols each sound reads as, in order."""
    model, fe, id2sym = ear
    out = []
    for x in sounds:
        values = fe(np.asarray(x, dtype=np.float32), sampling_rate=S.RATE, return_tensors='pt').input_values
        with torch.no_grad():
            ids = model(values.cuda()).logits[0].argmax(-1).tolist()
        out.append(collapse(ids, id2sym)[0])
    return out
