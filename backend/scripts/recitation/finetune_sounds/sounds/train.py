"""One round of full fine-tuning (CTC, feature encoder frozen) from the start model; the weights are saved for the judge."""
import shutil
from pathlib import Path

import numpy as np
import torch
from ear.sound import augmented, noise_bank, room_bank, sound_of
from transformers import Trainer, TrainingArguments, Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC

from . import settings as S
from . import targets

PAD_LABEL = -100  # what a CTC loss skips


class Clips(torch.utils.data.Dataset):
    """Training items decoded on demand, made harder, normalised, with their ayah's phoneme ids as the answer."""

    def __init__(self, items, fe, labels, hard):
        self.items, self.fe, self.labels, self.hard = items, fe, labels, hard

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        item = self.items[i]
        x = sound_of(Path(item['path']).read_bytes())
        if self.hard:
            x = augmented(x, *self.hard, np.random.default_rng())
        return {'input_values': self.fe(x, sampling_rate=S.RATE).input_values[0], 'labels': self.labels[item['ayah']]}


def collate(batch):
    """Sounds padded with silence and told which part is real (the model's layer norm wants the mask); answers padded with PAD_LABEL."""
    n, m = max(len(b['input_values']) for b in batch), max(len(b['labels']) for b in batch)
    values, mask, labels = np.zeros((len(batch), n), np.float32), np.zeros((len(batch), n), np.int64), np.full((len(batch), m), PAD_LABEL)
    for i, b in enumerate(batch):
        values[i, :len(b['input_values'])], mask[i, :len(b['input_values'])], labels[i, :len(b['labels'])] = 1 * b['input_values'], 1, b['labels']
    return {'input_values': torch.from_numpy(values), 'attention_mask': torch.from_numpy(mask), 'labels': torch.from_numpy(labels)}


def train(start, items, to):
    """Fine-tune the model in folder `start` on `items`; save it (with its feature extractor and vocab) to folder `to`."""
    symbols, fe = targets.vocab(start), Wav2Vec2FeatureExtractor.from_pretrained(start)
    labels = {k: targets.ids(k, symbols) for k in sorted({i['ayah'] for i in items})}
    hard = (noise_bank(), room_bank()) if S.AUGMENT else None
    model = Wav2Vec2ForCTC.from_pretrained(start)
    model.freeze_feature_encoder()
    Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=str(S.OUT / 'sounds-trainer'), learning_rate=S.LEARNING_RATE, num_train_epochs=S.EPOCHS,
            per_device_train_batch_size=S.BATCH, gradient_accumulation_steps=S.ACCUMULATE, warmup_ratio=S.WARMUP,
            dataloader_num_workers=S.WORKERS, seed=S.SEED, fp16=True, gradient_checkpointing=True,
            gradient_checkpointing_kwargs={'use_reentrant': False}, logging_steps=25, save_strategy='no',
            remove_unused_columns=False, label_names=['labels'], report_to=[]),
        train_dataset=Clips(items, fe, labels, hard),
        data_collator=collate,
    ).train()
    model.save_pretrained(to)
    fe.save_pretrained(to)
    shutil.copy(Path(start) / 'vocab.json', to)
    shutil.rmtree(S.OUT / 'sounds-trainer', ignore_errors=True)
