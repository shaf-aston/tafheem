"""Recordings as 16 kHz numbers, and training clips made harder: speed, a room, background noise, a rough channel."""
import io
import math
import os
import shutil
import subprocess
import zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import requests
import soundfile
from huggingface_hub import HfFileSystem, list_repo_files
from scipy.signal import fftconvolve, resample_poly

from . import settings as S


RAW = ['-f', 'f32le', '-ar', str(S.RATE), '-ac', '1']  # 16 kHz mono floats, the shape every clip is held in


def _ffmpeg(data, *args):
    return subprocess.run(['ffmpeg', '-v', 'error', *args], input=data, capture_output=True, check=True).stdout


def sound_of(recording):
    """Any recording's bytes as 16 kHz mono. ffmpeg, not the datasets decoder: RetaSy's WAV
    headers state the wrong length, which torchcodec refuses (328 of 357 clips) and ffmpeg reads."""
    return np.frombuffer(_ffmpeg(recording, '-i', 'pipe:0', *RAW, 'pipe:1'), dtype=np.float32)


def opened(path):
    """A clip on disk as sound: one parquet.saved() kept decoded at 16 bits (.npy), or a recording as it came."""
    path = Path(path)
    if path.suffix == '.npy':
        return np.load(path).astype(np.float32) / 32767
    return sound_of(path.read_bytes())


def readable(recording):
    """sound_of, or None for a damaged file: one bad file is skipped, not fatal to the run."""
    try:
        return sound_of(recording)
    except subprocess.CalledProcessError:
        return None


def decoded(recordings):
    """readable() of each recording, in order, one ffmpeg per CPU at once. One at a time ran 5 clips a second:
    an hour for Tarteel v1 alone (2026-11-05). At most four per CPU are held decoded ahead of the reader."""
    workers = os.cpu_count()
    with ThreadPoolExecutor(workers) as pool:
        ahead = deque()
        for recording in recordings:
            ahead.append(pool.submit(readable, recording))
            if len(ahead) >= 4 * workers:
                yield ahead.popleft().result()
        while ahead:
            yield ahead.popleft().result()


def noise_bank():
    """Background sounds, 16 kHz mono, each cut to NOISE_MAX_S."""
    fs = HfFileSystem()
    files = sorted(f for f in list_repo_files(S.NOISE_SET, repo_type='dataset') if f.startswith('data/'))[:S.NOISE_SHARDS]
    bank = []
    for shard in files:
        for batch in pq.ParquetFile(fs.open(f'datasets/{S.NOISE_SET}/{shard}')).iter_batches(batch_size=20, columns=['audio']):
            bank += [n[:S.NOISE_MAX_S * S.RATE] for audio in batch.column('audio').to_pylist()
                     if (n := readable(audio['bytes'])) is not None]  # cut as read: a whole noise clip can run minutes
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


def _filtered(x, graph):
    return np.frombuffer(_ffmpeg(x.tobytes(), *RAW, '-i', 'pipe:0', '-af', graph, *RAW, 'pipe:1'), dtype=np.float32)


def rough(sound, rng):
    """One clip as a worse channel carries it (ROUGH_KINDS, one drawn)."""
    x = np.asarray(sound, dtype=np.float32)
    kind = S.ROUGH_KINDS[rng.integers(len(S.ROUGH_KINDS))]
    if kind == 'opus':
        kbps = rng.integers(S.OPUS_KBPS[0], S.OPUS_KBPS[1] + 1)
        return sound_of(_ffmpeg(x.tobytes(), *RAW, '-i', 'pipe:0', '-c:a', 'libopus', '-b:a', f'{kbps}k', '-f', 'ogg', 'pipe:1'))
    if kind == 'phone':
        return _filtered(x, f'highpass=f={S.PHONE_HZ[0]},lowpass=f={S.PHONE_HZ[1]},aresample=8000,aresample={S.RATE}')
    if kind == 'tape':
        x = _filtered(x, f'highpass=f={S.TAPE_HZ[0]},lowpass=f={S.TAPE_HZ[1]}')
        hiss = rng.standard_normal(len(x)).astype(np.float32)
        return (x + hiss * rms(x) / rms(hiss) / 10 ** (rng.uniform(*S.TAPE_SNR_DB) / 20)).astype(np.float32)
    peak = float(np.abs(x).max()) or 1.0
    return np.clip(x / peak * 10 ** (rng.uniform(*S.CLIP_DB) / 20), -1, 1).astype(np.float32)


def augmented(sound, noises, rooms, rng):
    """One training clip made harder: speed, room, background noise, then a rough channel. Never run on a test clip."""
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
    if rng.random() < S.ROUGH_P:
        x = rough(x, rng)
    return x
