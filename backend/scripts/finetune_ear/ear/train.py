"""One round of LoRA training on a start model, merged back into plain weights for export."""
import numpy as np
from peft import LoraConfig, get_peft_model
from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments

from . import settings as S
from .sound import augmented, noise_bank, room_bank
from .text import processor


def train(model, taught):
    noises, rooms = noise_bank(), room_bank()
    print(len(noises), 'noise clips,', len(rooms), 'rooms', flush=True)
    rng = np.random.default_rng(3)

    def gather(rows):
        # Features made per batch, not stored: 18,000 clips' features would take 17 GB.
        batch = processor([augmented(r['sound'], noises, rooms, rng) for r in rows], sampling_rate=S.RATE, return_tensors='pt')
        marked = processor.tokenizer([r['said'] for r in rows], padding=True, return_tensors='pt')
        # Padding is not something to say, so it is masked out of the loss.
        labels = marked['input_ids'].masked_fill(marked.attention_mask.ne(1), -100)
        # The model puts the start mark in front itself; left in, it would be there twice.
        if (labels[:, 0] == model.config.decoder_start_token_id).all():
            labels = labels[:, 1:]
        batch['labels'] = labels
        return batch

    tuned = get_peft_model(model, LoraConfig(**S.LORA))
    tuned.print_trainable_parameters()
    Seq2SeqTrainer(
        model=tuned,
        args=Seq2SeqTrainingArguments(
            output_dir=str(S.OUT / 'ear-lora'), learning_rate=S.LEARNING_RATE, num_train_epochs=S.EPOCHS,
            save_strategy='no', remove_unused_columns=False, label_names=['labels'], report_to=[], **S.TRAINER),
        train_dataset=taught.select_columns(['sound', 'said']),
        data_collator=gather,
    ).train()
    return tuned.merge_and_unload()
