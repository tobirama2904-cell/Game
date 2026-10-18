#!/usr/bin/env python3
"""Assemble audiobook chapters from generated TTS clips + themes.
Clips expected at assets/voice/ab/<chapter:02d>_<idx:02d>.mp3 in clip_plan order.
Outputs out/audiobook/strannik/NN_Title.mp3 (mono 44.1k mp3 96k) + full book mp3.
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
AB = os.path.join(ROOT, 'assets', 'voice', 'ab')
SCORE = os.path.join(ROOT, 'assets', 'score')
OUTD = os.path.join(ROOT, 'out', 'audiobook', 'strannik')
SR = 48000
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
sys.path.insert(0, HERE)
import audio_synth as S  # noqa: E402

CH_NAMES = {}


def decode(path):
    tmp = '/tmp/_abd.wav'
    subprocess.run([FF, '-y', '-i', path, '-ar', str(SR), '-ac', '1', '-f', 'wav', tmp],
                   capture_output=True, check=True)
    import wave
    with wave.open(tmp) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def encode_mp3(x, path, br='96k'):
    tmp = '/tmp/_abe.wav'
    import scipy.io.wavfile as wav
    wav.write(tmp, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
    subprocess.run([FF, '-y', '-i', tmp, '-c:a', 'libmp3lame', '-b:a', br, '-ar', '44100', '-ac', '1', path],
                   capture_output=True, check=True)


def gap(sec):
    return np.zeros(int(SR * sec))


def main():
    os.makedirs(OUTD, exist_ok=True)
    plan = json.load(open(os.path.join(OUTD, 'clip_plan.json')))
    script = json.load(open(os.path.join(OUTD, 'script.json')))
    theme = os.path.join(SCORE, 'theme_strannik.wav')
    if not os.path.exists(theme):
        S.render_theme('strannik', 12.0, theme)
    stinger = os.path.join(SCORE, 'stinger_strannik.wav')
    if not os.path.exists(stinger):
        S.render_theme('strannik', 4.0, stinger)
    th = decode(theme)
    st = decode(stinger)
    chapters = {}
    for idx, clip in enumerate(plan):
        ci = clip['chapter']
        f = os.path.join(AB, f'{ci:02d}_{idx:02d}.mp3')
        chapters.setdefault(ci, []).append((idx, f))
    made = []
    for ci in sorted(chapters):
        missing = [f for _, f in chapters[ci] if not os.path.exists(f)]
        if missing:
            print(f'chapter {ci}: waiting on {len(missing)} clips (first: {os.path.basename(missing[0])})')
            continue
        title = script[ci]['title'].replace('📖', '').strip()
        parts = [th * 0.9, gap(0.8)]
        for j, (idx, f) in enumerate(chapters[ci]):
            parts.append(decode(f))
            parts.append(gap(0.55))
            if j < len(chapters[ci]) - 1:
                pass
        parts.append(st * 0.8)
        x = np.concatenate(parts)
        x = S.master(x, 0.85)
        safe = ''.join(c for c in title if c.isalnum() or c in ' -')[:40]
        out = os.path.join(OUTD, f'{ci:02d}_{safe}.mp3')
        encode_mp3(x, out)
        made.append(out)
        print(f'chapter {ci}: {len(x)/SR/60:.1f} min -> {os.path.basename(out)}')
    # whole book concat
    if len(made) == len(chapters):
        parts = []
        for f in made:
            parts.append(decode(f))
            parts.append(gap(1.6))
        x = S.master(np.concatenate(parts), 0.85)
        encode_mp3(x, os.path.join(OUTD, 'FULL_Странник.mp3'), br='96k')
        print('FULL book assembled')


if __name__ == '__main__':
    main()
