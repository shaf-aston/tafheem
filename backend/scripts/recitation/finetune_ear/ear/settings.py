"""Every knob of an ear run, in one place. Change a run by editing this file; the code reads only these names."""
from pathlib import Path

# The run, in order. Each step makes one candidate ear; the judge keeps it only if it beats the ear held so far
# (the served one to begin with), and the next step starts from whatever is held. ('blend', s): the held ear
# moved s of the way back toward the untuned model, no training. ('train', None): LoRA on the held ear.
# Blends dropped 2026-11-06: two runs, no blend past the margin, and each cost ~25 min of scoring.
PLAN = [('train', None)]

SIZE = 'base'  # 'tiny': two thirds the time at home, pros 1.2 points worse; tuned on 45 ayahs it slipped 3 more
NAME = f'tarteel-ai/whisper-{SIZE}-ar-quran'  # the untuned model every ear descends from
RATE = 16000
LONGEST = 30 * RATE  # Whisper hears 30 seconds at most; a longer clip's text would be cut short
OUT = Path.cwd()  # everything a run writes; Kaggle hands this folder back
SEED = 7  # torch, numpy and LoRA's starting numbers, set once by run.py

# The champion: the best tuned ear so far, "repo@revision". Every run starts from it and must beat it.
# cloud.py --ship moves it, and points the app's recitation_model at it, only when ear_bench keeps it.
CHAMPION = 'shafTheG/quran-ear@0034c0bd1dc1037b0571a5e8702d90128671fb7a'

# --- the judge (judge.py) ---
# A group's margin is the smallest change that counts, either way. A candidate is kept (handed back for ear_bench
# to judge on slips) when it is worse by more than its margin on no group and has not forgotten (FORGET); better
# by its margin, with the bootstrap interval of that gain above zero, is recorded, not required. Run 26
# (2026-11-06) lost an ear 1.4 points better on new voices and 2.5 on Tadabur for missing the new-ayahs margin.
# Professional is the proof it kept what it had.
MARGIN = {'new ayahs': 0.75, 'professional': 1.0, 'rough professional': 1.0}
# Points more wrong on professionals than the untuned model, at most; an ear already past that may not slip
# further. Anchored to the untuned model, not the held ear, so small slips cannot pile up run after run.
FORGET = 1.0
RESAMPLES = 2000  # bootstrap draws for each interval
SURE = 0.95  # width of the interval
TESTED = 1800  # clips per test group at most; 600 left new ayahs at +-1.0 points, too wide to see one run's gain
# (2026-11-05: 0.46). About 0.25 s a clip an ear on Kaggle's T4, so 1,800 adds ~45 min to a 4-step run.

# --- held clips (split.py) ---
HELD = 5  # one voice, one ayah and one Tadabur reciter in HELD are never trained on
PER_AYAH = 40  # two thirds of the clips are al-Ikhlas; uncapped it teaches that one surah
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
TADABUR_SHARDS = 28  # of 385 files, 1,000 ayahs and 2.4 GB each, spread evenly; 8 gave 7,478 usable, 4,796 taught
TADABUR_SHARE = 0.4  # of the training clips; 0.25 (2026-11-05) gained new ayahs 0.46, within noise. Every ayah, 600+ voices
TADABUR_TEST = 300  # clips of those reciters, at most
TADABUR_SURAH_BASE = 1  # its surah_id counts from 0; checked against the printed ayah text
# Replay: professional recitation mixed into training so the ear keeps hearing what it was first taught
# (CL-MASR, arXiv 2310.16931: replay kept Whisper's old languages where plain fine-tuning and EWC lost them).
# tarteel-ai/everyayah: 132 train files of 0.3 to 1.7 GB, mostly one reciter each, sorted by reciter.
REPLAY = 'tarteel-ai/everyayah'
REPLAY_SHARDS = 8  # files read, spread evenly; files holding only test reciters are skipped first
REPLAY_SHARE = 0.1  # of the training clips; ~3,700, as many as 0.15 gave before Tadabur grew
# tlog: real app users on their own phones, 411 files of ~970 clips, one or two ayahs per file. Gated, and
# Kaggle gives a run sent from the command line no secrets, so cloud.py --tlog copies the clips a run hears
# from this computer into TLOG_COPY, a private Kaggle dataset; change the two numbers below, copy again.
# A file name says the ayah meant, not what was said, so a clip is taught only
# when TLOG_CHECKER, an ear that never trained here, writes exactly that ayah: a slip taught as right teaches
# the ear to hear slips as right. Measured 2026-11-04 on 694 clips: about 4 in 10 were off-ayah or noise.
TLOG = 'tarteel-ai/tlog'
TLOG_COPY = 'shafeinhashmi/tlog-sample'
TLOG_SHARDS = 30  # files copied, spread evenly, so ~60 ayahs
TLOG_TRY = 200  # clips copied per file, picked at random, and heard
TLOG_SHARE = 0.1  # of the training clips: wants ~3,700, the checker passes ~900 either way
TLOG_CHECKER = 'large-v3-turbo'

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
# A rough channel, last, as a microphone and codec come after the room: the browser's Opus at a low rate, a phone
# line, an old tape (narrow band, hiss), or a voice too loud for the microphone. The judge hears the professional
# test through the same channels ('rough professional'), each clip's channel fixed by its place in the test.
ROUGH_P = 0.4  # chance a training clip goes through one
ROUGH_KINDS = ('opus', 'phone', 'tape', 'clipped')
OPUS_KBPS = (8, 24)  # drawn evenly; browsers record 24 to 32
PHONE_HZ = (300, 3400)
TAPE_HZ = (100, 5000)
TAPE_SNR_DB = (15, 30)  # hiss this far under the voice
CLIP_DB = (6, 18)  # pushed this far past full scale, then clipped

# --- training (train.py) ---
# LoRA, not a full retrain: a few hundred clips must not wash out thousands of hours. Attention only: swept
# 2026-10-02, 7 plans on 45 ayahs, all within noise on new ayahs; this kept pros best and trains fastest.
LORA = dict(r=32, lora_alpha=64, lora_dropout=0.05, bias='none', target_modules=['q_proj', 'k_proj', 'v_proj', 'out_proj'])
EPOCHS = 2  # 18,000 clips: two passes is already ten times the steps four passes over 45 ayahs took
# Half the from-scratch run's 5e-4: training now starts from a tuned ear, not the untuned one. Untested; the judge decides.
LEARNING_RATE = 2.5e-4
TRAINER = dict(per_device_train_batch_size=8, gradient_accumulation_steps=2, warmup_steps=40, fp16=True, logging_steps=25)
