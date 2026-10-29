"""Every knob of a sounds run, in one place. Change a run by editing this file; the code reads only these names.
The word loop's held voices, noise, room and interval settings (ear/settings.py) are shared on purpose."""
from ear import settings as ear

RATE = ear.RATE
OUT = ear.OUT  # everything a run writes; Kaggle hands this folder back

# --- the start model and the marked recordings, both private Kaggle datasets (prepare.py makes them) ---
MODEL_DATASET = 'sounds-model'  # quran-dev/wav2vec2-ctc-quran-phoneme-run66-iqratts-mix-final-20260909; its Hub page now answers 401
MODEL_MARKER = 'model.safetensors'  # finds the attached folder under /kaggle/input
CHECKS_DATASET = 'sounds-checks'  # the reviewer-marked learner recordings; judged on, never trained on
CHECKS_MARKER = 'checks.jsonl'
CHECKS_AUDIO = 'audio.npy'  # every recording's 16-bit numbers in a row, beside CHECKS_MARKER (a dataset keeps files, not folders)

# --- the judge (judge.py) ---
# Per word, flagged when the model's phonemes disagree with the reference in a consonant (articulation) or a
# vowel (length). Words the reviewer marked tajweed-only are left out. Kept only when all hold against the untuned model:
DROP_MIN = 3.0  # correct words flagged fall by at least this many points, and the interval of that fall sits above zero
VOWEL_FALL_MAX = 3.0  # vowel slips caught may fall by at most this many points
# Letter slips (31 words) are reported, not gated: one word is 3 points.
MATCH_FLOOR = 0.7  # a clip the untuned model matches under this share of holds only part of its ayah; left out for both
# The untuned model's numbers from score_phoneme_checker.py (words flagged, %), and how far a rerun may stray before
# the judge calls itself broken: one letter word is 3.2 points, so that group is allowed more.
BASELINE = {'right': 22.9, 'letter': 54.8, 'vowel': 89.6}
BASELINE_TOL = {'right': 1.0, 'letter': 4.0, 'vowel': 2.0}

# --- professional held-out test (sources.py) ---
PRO_TEST = ear.PRO_TEST  # everyayah.com reciters (and their dataset names) no training clip may come from
EVERYAYAH_URL = ear.EVERYAYAH_URL
PRO_AYAHS = 210  # held ayahs, one clip each, reciters in turn; 30 per reciter
PRO_WORDS = (5, 20)  # words an ayah may hold to be tested
TEST_SEED = 11

# --- training data (sources.py) ---
TRAIN_LONGEST_S = 20  # longer clips are left out of training: memory on a 16 GB card
EVERYAYAH = 'tarteel-ai/everyayah'  # professionals, 132 files, mostly one reciter each
EVERYAYAH_SHARDS = 12  # files read, spread evenly; test reciters' files are passed over
PRO_CLIPS = 6000  # professional clips taught, equal per reciter
TARTEEL_V1 = ear.TARTEEL_V1  # learners (attached on Kaggle as dhiauji/user-tarteel); who recited is not recorded
TARTEEL_LISTING = 'tusers_filtered.csv'
LEARNER_CLIPS = 2500  # learner clips taught
LEARNER_PER_AYAH = 3  # at most this many per ayah, so no surah dominates
PLAN_SEED = 17
AUGMENT = True  # speed, room and noise from ear/settings.py on training clips; test clips never

# --- training (train.py) ---
# Full fine-tune with the convolutional feature encoder frozen, as the start model was made (its card: lr 2e-5).
LEARNING_RATE = 1e-5  # half of that: this round only adapts a finished model
EPOCHS = 2
BATCH = 4
ACCUMULATE = 4  # 16 clips per step
WARMUP = 0.1  # share of the steps
WORKERS = 2  # clips decoded and made harder in the background
SEED = 7
