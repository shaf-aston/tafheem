"""Every knob of an ear run, in one place. Change a run by editing this file; the code reads only these names."""
from pathlib import Path

# The run, in order. Each step makes one candidate ear; the judge keeps it only if it beats the ear held so far
# (the served one to begin with), and the next step starts from whatever is held. ('blend', s): the held ear
# moved s of the way back toward the untuned model, no training. ('train', None): LoRA on the held ear.
PLAN = [('blend', 0.25), ('blend', 0.5), ('blend', 0.75), ('train', None)]

SIZE = 'base'  # 'tiny': two thirds the time at home, pros 1.2 points worse; tuned on 45 ayahs it slipped 3 more
NAME = f'tarteel-ai/whisper-{SIZE}-ar-quran'  # the untuned model every ear descends from
RATE = 16000
LONGEST = 30 * RATE  # Whisper hears 30 seconds at most; a longer clip's text would be cut short
OUT = Path.cwd()  # everything a run writes; Kaggle hands this folder back

# The served ear (champion) is the one master's config.py pins; cloud.py --ship moves that pin on a win.
SERVED = 'https://raw.githubusercontent.com/shaf-aston/tafheem/master/backend/config.py'
SERVED_PIN = r'recitation_trial_model: str = "(.+?)@(.+?)"'

# --- the judge (judge.py) ---
# A group's margin is the smallest change that counts, either way. A candidate is kept when it is better than the
# held ear by its margin on some group (and the bootstrap interval of that gain sits above zero), worse by more
# than its margin on none, and has not forgotten (FORGET). New ayahs is the only proof it learnt listening rather
# than text; professional is the proof it kept what it had.
MARGIN = {'new ayahs': 1.5, 'professional': 1.0}
# Points more wrong on professionals than the untuned model, at most; an ear already past that may not slip
# further. Anchored to the untuned model, not the held ear, so small slips cannot pile up run after run.
FORGET = 1.0
RESAMPLES = 2000  # bootstrap draws for each interval
SURE = 0.95  # width of the interval
TESTED = 600  # clips per test group at most: 3,000 held clips heard twice would cost an hour

# --- held clips (split.py) ---
HELD = 5  # one voice, one ayah and one Tadabur reciter in HELD are never trained on
PER_AYAH = 40  # two thirds of the clips are al-Ikhlas; uncapped it teaches that one surah
LEARNER_SHARE = 1.0  # share of learner clips kept, picked before decoding; a quarter-size pilot ended 6 points behind
PROS = 200  # professional test clips, 5 to 20 words each; 40 gave ~500 words, so one word was 0.2 points
# The professional test's reciters, as everyayah.com folders, each with every name it has in tarteel-ai/everyayah
# (all 36 listed 2026-10-21: Minshawy is there twice, as minshawi and menshawi; Hudhaify not at all), so replay
# can leave them out: the test must hear voices training never replayed.
PRO_TEST = {'Alafasy_128kbps': ('alafasy',), 'Husary_128kbps': ('husary',), 'Abdul_Basit_Murattal_192kbps': ('abdul_basit',),
            'Minshawy_Murattal_128kbps': ('minshawi', 'menshawi'), 'Saood_ash-Shuraym_128kbps': ('saood_ash-shuraym',),
            'Abdurrahmaan_As-Sudais_192kbps': ('abdurrahmaan_as-sudais',), 'Hudhaify_128kbps': ('hudhaify',)}
EVERYAYAH_URL = 'https://everyayah.com/data/{who}/{surah:03d}{ayah:03d}.mp3'

# --- training data (sources.py) ---
TARTEEL_V1 = 'tarteel-v1'  # attached on Kaggle as dhiauji/user-tarteel
# Tadabur: 384k ayahs by 600+ reciters, 938 GB, CC BY-NC 4.0. Only a few files are read.
TADABUR = 'FaisaI/tadabur'
TADABUR_SHARDS = 8  # of ~390 files, 1,000 ayahs and 2.4 GB each, spread evenly; 3 gave 2,796 usable
TADABUR_SHARE = 0.25  # of the training clips
TADABUR_TEST = 300  # clips of those reciters, at most
TADABUR_SURAH_BASE = 1  # its surah_id counts from 0; checked against the printed ayah text
# Replay: professional recitation mixed into training so the ear keeps hearing what it was first taught
# (CL-MASR, arXiv 2310.16931: replay kept Whisper's old languages where plain fine-tuning and EWC lost them).
# tarteel-ai/everyayah: 132 train files of 0.3 to 1.7 GB, mostly one reciter each, sorted by reciter.
REPLAY = 'tarteel-ai/everyayah'
REPLAY_SHARDS = 8  # files read, spread evenly; files holding only test reciters are skipped first
REPLAY_SHARE = 0.15  # of the training clips

# --- making clips harder (sound.py); training clips only, test clips never ---
# Recipe: Muno459/zipformer_p-arabic-v2 card.
NOISE_SET = 'obadx/freesound-commercial-50k-noise-only'  # per-clip CC0 / CC-BY
NOISE_SHARDS = 1  # of 104 files, 265 clips and half a gigabyte each
NOISE_P = 0.5  # chance a clip gets background noise
NOISE_SNR_DB = (10, 20)  # noise this far under the voice, drawn evenly between
NOISE_MAX_S = 30  # seconds kept of each noise clip
RIR_ZIP = 'https://www.openslr.org/resources/28/rirs_noises.zip'  # OpenSLR 28, Apache 2.0
RIR_LIST = 'RIRS_NOISES/real_rirs_isotropic_noises/rir_list'  # the 325 real room recordings in the zip
REVERB_P = 0.3  # chance a clip gets a room
RIR_MAX_S = 1.0  # seconds of a room's tail kept
SPEEDS = (0.9, 1.0, 1.1)  # one drawn per clip

# --- training (train.py) ---
# LoRA, not a full retrain: a few hundred clips must not wash out thousands of hours. Attention only: swept
# 2026-10-02, 7 plans on 45 ayahs, all within noise on new ayahs; this kept pros best and trains fastest.
LORA = dict(r=32, lora_alpha=64, lora_dropout=0.05, bias='none', target_modules=['q_proj', 'k_proj', 'v_proj', 'out_proj'])
EPOCHS = 2  # 18,000 clips: two passes is already ten times the steps four passes over 45 ayahs took
# Half the from-scratch run's 5e-4: training now starts from a tuned ear, not the untuned one. Untested; the judge decides.
LEARNING_RATE = 2.5e-4
TRAINER = dict(per_device_train_batch_size=8, gradient_accumulation_steps=2, warmup_steps=40, fp16=True, logging_steps=25)
