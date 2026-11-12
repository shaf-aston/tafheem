"""One round of LoRA training on a start model, merged back into plain weights for export."""
import math

import numpy as np
import torch
from peft import LoraConfig, get_peft_model
from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments

from . import settings as S
from .sound import augmented, noise_bank, room_bank
from .text import processor

tokenizer = processor.tokenizer


def pieces(words):
    """Each word's tokens as the app asks about them: the first bare, the rest after a space."""
    return [tokenizer.encode(('' if i == 0 else ' ') + w, add_special_tokens=False) for i, w in enumerate(words)]


def slip_mark(page, said):
    """(page tokens as labels, which of them the slip makes untrue) for a clip whose said text differs from the
    page in one word, or None. Marked: the slipped word's tokens from the first one the said word does not share,
    the pieces the app's `worst` rule reads when it asks the ear about the page word."""
    p, s = page.split(), said.split()
    k = next((i for i, (a, b) in enumerate(zip(p, s)) if a != b), None)
    if k is None or len(p) != len(s):
        return None
    full = tokenizer(page).input_ids
    asked = pieces(p)
    start = len(full) - 1 - sum(map(len, asked))  # start marks before the text, end mark after it
    if full[start:-1] != [t for w in asked for t in w]:
        return None  # pieces as the app asks do not line up with the sentence's own: mark nothing rather than guess
    own, heard = asked[k], pieces(s)[k]
    j = next((i for i, (a, b) in enumerate(zip(own, heard)) if a != b), min(len(own), len(heard)))
    at = start + sum(map(len, asked[:k])) + min(j, len(own) - 1)
    return full, list(range(at, start + sum(map(len, asked[:k + 1]))))


class SlipTrainer(Seq2SeqTrainer):
    """The usual loss on what was said, plus a push on each slipped clip: asked about the page word, the ear's
    least sure piece should fall below SLIP_BELOW. The said text alone stops teaching once the said word wins,
    with the page word still far above the app's cut (v33: surer everywhere, slips missed more)."""

    def compute_loss(self, model, inputs, return_outputs=False, **more):
        page, mark = inputs.pop('page'), inputs.pop('mark')
        loss, out = super().compute_loss(model, inputs, return_outputs=True, **more)
        rows = mark.any(1)
        if rows.any():
            asked = model(encoder_outputs=(out.encoder_last_hidden_state[rows],), labels=page[rows])
            sure = asked.logits.float().log_softmax(-1).gather(-1, page[rows].clamp(min=0).unsqueeze(-1)).squeeze(-1)
            worst = sure.masked_fill(~mark[rows], 0.0).min(1).values
            push = (worst - math.log(S.SLIP_BELOW)).clamp(min=0)
            loss = loss + S.SLIP_WEIGHT * push.sum() / inputs['labels'].ne(-100).sum()
        return (loss, out) if return_outputs else loss


def train(model, taught):
    noises, rooms = noise_bank(), room_bank()
    print(len(noises), 'noise clips,', len(rooms), 'rooms', flush=True)
    rng = np.random.default_rng(3)
    start = model.config.decoder_start_token_id

    def labels_of(ids):
        """Token lists as one padded label block; padding is not something to say, so it is masked out."""
        block = torch.full((len(ids), max(map(len, ids))), -100, dtype=torch.long)
        for i, row in enumerate(ids):
            block[i, :len(row)] = torch.tensor(row)
        # The model puts the start mark in front itself; left in, it would be there twice.
        return block[:, 1:] if (block[:, 0] == start).all() else block

    def gather(rows):
        # Features made per batch, not stored: 18,000 clips' features would take 17 GB.
        batch = processor([augmented(r['sound'], noises, rooms, rng) for r in rows], sampling_rate=S.RATE, return_tensors='pt')
        said = [tokenizer(r['said']).input_ids for r in rows]
        batch['labels'] = labels_of(said)
        marks = [slip_mark(r['page'], r['said']) if r['page'] else None for r in rows]
        batch['page'] = labels_of([m[0] if m else s for m, s in zip(marks, said)])
        mark = torch.zeros_like(batch['page'], dtype=torch.bool)
        for i, m in enumerate(marks):
            if m:
                mark[i, [t - 1 for t in m[1]]] = True  # minus the start mark labels_of dropped
        batch['mark'] = mark
        return batch

    tuned = get_peft_model(model, LoraConfig(**S.LORA))
    tuned.print_trainable_parameters()
    SlipTrainer(
        model=tuned,
        args=Seq2SeqTrainingArguments(
            output_dir=str(S.OUT / 'ear-lora'), learning_rate=S.LEARNING_RATE, num_train_epochs=S.EPOCHS,
            save_strategy='no', remove_unused_columns=False, label_names=['labels'], report_to=[], **S.TRAINER),
        train_dataset=taught.select_columns(['sound', 'said', 'page']),
        data_collator=gather,
    ).train()
    return tuned.merge_and_unload()
