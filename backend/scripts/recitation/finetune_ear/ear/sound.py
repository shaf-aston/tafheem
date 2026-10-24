"""Recordings as 16 kHz numbers, and training clips made harder: speed, a room, background noise."""
import io
import math
import shutil
import subprocess
import zipfile

import numpy as np
import pyarrow.parquet as pq
import requests
import soundfile
from huggingface_hub import HfFileSystem, list_repo_files
from scipy.signal import fftconvolve, resample_poly

from . import settings as S


def sound_of(recording):
    """Any recording's bytes as 16 kHz mono. ffmpeg, not the datasets decoder: RetaSy's WAV
    headers state the wrong length, which torchcodec refuses (328 of 357 clips) and ffmpeg reads."""
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'pipe:0', '-f', 'f32le', '-ac', '1', '-ar', str(S.RATE), 'pipe:1'],
                         input=recording, capture_output=True, check=True)
    return np.frombuffer(out.stdout, dtype=np.float32)


def noise_bank():
    """Background sounds, 16 kHz mono, each cut to NOISE_MAX_S."""
    fs = HfFileSystem()
    files = sorted(f for f in list_repo_files(S.NOISE_SET, repo_type='dataset') if f.startswith('data/'))[:S.NOISE_SHARDS]
    bank = []
    for shard in files:
        for batch in pq.ParquetFile(fs.open(f'datasets/{S.NOISE_SET}/{shard}')).iter_batches(batch_size=20, columns=['audio']):
            for audio in batch.column('audio').to_pylist():
                try:
                    bank.append(sound_of(audio['bytes'])[:S.NOISE_MAX_S * S.RATE])
                except subprocess.CalledProcessError:
                    pass
    return [n for n in bank if len(n) > S.RATE]


def room_bank():
    """Real room impulse responses from the OpenSLR 28 zip, 16 kHz, from the direct sound on, unit energy.
    The zip is downloaded next to the outputs and deleted after: Kaggle would hand it back."""
    path = S.OUT / 'rirs_noises.zip'
    with requests.get(S.RIR_ZIP, stream=True, timeout=60) as r, open(path, 'wb') as f:
        r.raise_for_status()
        shutil.copyfileobj(r.raw, f)
    bank = []
    with zipfile.ZipFile(path) as z:
        for line in z.read(S.RIR_LIST).decode().splitlines():
            wav, rate = soundfile.read(io.BytesIO(z.read(line.split()[-1])), always_2d=True)
            gcd = math.gcd(S.RATE, rate)
            wav = resample_poly(wav[:, 0], S.RATE // gcd, rate // gcd)
            wav = wav[np.argmax(np.abs(wav)):][:int(S.RIR_MAX_S * S.RATE)]
            bank.append((wav / np.linalg.norm(wav)).astype(np.float32))
    path.unlink()
    return bank


def rms(x):
    return float(np.sqrt(np.mean(np.square(x)))) + 1e-9


def augmented(sound, noises, rooms, rng):
    """One training clip made harder: speed, then room, then background noise. Never run on a test clip."""
    x = np.asarray(sound, dtype=np.float32)
    speed = float(rng.choice(S.SPEEDS))
    if speed != 1.0:
        slowed = resample_poly(x, 100, int(round(100 * speed)))  # 0.9 plays slower, so longer
        if len(slowed) <= S.LONGEST:  # a longer clip would lose its end but keep its text
            x = slowed.astype(np.float32)
    if rng.random() < S.REVERB_P:
        wet = fftconvolve(x, rooms[rng.integers(len(rooms))])[:len(x)]
        x = (wet * rms(x) / rms(wet)).astype(np.float32)
    if rng.random() < S.NOISE_P:
        noise = np.resize(noises[rng.integers(len(noises))], len(x))  # repeated if shorter
        snr = rng.uniform(*S.NOISE_SNR_DB)
        x = (x + noise * rms(x) / rms(noise) / 10 ** (snr / 20)).astype(np.float32)
    return x
