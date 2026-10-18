#!/usr/bin/env python3
"""Assemble a cinematic trailer MP4 from a cue sheet (JSON).
Two-stage: (1) per-shot Ken Burns render to intermediate mp4 (low memory),
(2) xfade assembly + audio mix (VO + procedural score w/ ducking + SFX).
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
IMG = os.path.join(ROOT, 'assets', 'img')
VOICE = os.path.join(ROOT, 'assets', 'voice')
CARDS = os.path.join(ROOT, 'assets', 'cards')
SCORE = os.path.join(ROOT, 'assets', 'score')
OUT = os.path.join(ROOT, 'out', 'trailers')
WORK = '/tmp/trailerwork'
SR = 48000
FPS = 24

import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
sys.path.insert(0, HERE)
import audio_synth as S  # noqa: E402

GRADES = {
    'noks': 'eq=contrast=1.09:saturation=1.06,colorbalance=bs=0.08:bm=0.04:rm=0.02',
    'bone': 'eq=contrast=1.07:saturation=0.70,colorbalance=bs=0.06:rs=-0.03',
    'strannik': 'eq=contrast=1.15:saturation=0.86,colorbalance=bs=0.05:bm=0.02',
    'razlom': 'eq=contrast=1.10:saturation=0.92,colorbalance=bs=0.07:rs=0.04:rm=0.02',
}


def run(cmd, tag=''):
    r = subprocess.run(cmd, capture_output=True, text=True)
    open(f'/tmp/fflog_{tag}.txt', 'w').write(r.stdout + '\n==== STDERR ====\n' + r.stderr)
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit(f'ffmpeg failed [{tag}]')
    return r


def probe_dur(path):
    r = subprocess.run([FF, '-i', path], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if 'Duration' in line:
            h, m, s = line.split('Duration:')[1].split(',')[0].strip().split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise ValueError(path)


def decode_wav(path, mono=True):
    tmp = '/tmp/_dec.wav'
    run([FF, '-y', '-i', path, '-ar', str(SR), '-ac', '1' if mono else '2', '-f', 'wav', tmp], 'dec')
    with wave.open(tmp) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return data


def resolve_at(at, starts):
    if isinstance(at, str) and at.startswith('shot'):
        idx = at.split('+')[0]
        off = float(at.split('+')[1]) if '+' in at else 0.0
        return starts[int(idx[4:])] + off
    return float(at)


def build(cue_path):
    cue = json.load(open(cue_path))
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SCORE, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    K4 = os.path.join(IMG, '_4k')
    os.makedirs(K4, exist_ok=True)
    shots = cue['shots']
    for sh in shots:
        if sh['kind'] == 'img':
            src = os.path.join(IMG, sh['img'])
            dst = os.path.join(K4, sh['img'])
            if not os.path.exists(dst):
                from PIL import Image
                Image.open(src).resize((3840, 2160), Image.LANCZOS).save(dst)
            sh['_src'] = dst
        else:
            card = sh['card'].replace('.png', '.jpg')
            sh['_src'] = os.path.join(CARDS, card)
    # ---- durations
    for sh in shots:
        if sh['kind'] == 'img':
            d = sh.get('pad_in', 0.8) + sh.get('pad_out', 1.0)
            for i, v in enumerate(sh.get('vo', [])):
                d += probe_dur(os.path.join(VOICE, v))
                if i:
                    d += sh.get('vo_gap', 0.35)
            sh['dur'] = max(d, sh.get('min', 3.0))
        else:
            sh['dur'] = sh.get('dur', 3.0)
    xfs = [sh.get('xf', 0.6) if i else 0.0 for i, sh in enumerate(shots)]
    total = sum(s['dur'] for s in shots) - sum(xfs)
    starts, acc = [], 0.0
    for i, sh in enumerate(shots):
        starts.append(acc)
        acc += sh['dur'] - (xfs[i + 1] if i + 1 < len(shots) else 0.0)
    # ---- stage 1: per-shot video
    shot_files = []
    for i, sh in enumerate(shots):
        dst = os.path.join(WORK, f"{cue['id']}_s{i}.mp4")
        shot_files.append(dst)
        D = sh['dur']
        FR = max(2, int(round(D * FPS)))
        if sh['kind'] == 'img':
            z0, z1 = sh.get('zoom', [1.0, 1.16])
            px, py = sh.get('pan', [0, 0])
            shake = sh.get('shake', 0.0)
            sx = f"+{shake}*exp(-4.5*on/{FPS})*sin(41*on/{FPS})" if shake else ""
            sy = f"+{shake}*exp(-4.5*on/{FPS})*cos(37*on/{FPS})" if shake else ""
            g = GRADES.get(cue.get('grade', 'noks'), '')
            vf = (f"zoompan=z='{z0}+({z1}-{z0})*on/{FR}':"
                  f"x='(iw-iw/zoom)/2+({px})*on/{FR}{sx}':y='(ih-ih/zoom)/2+({py})*on/{FR}{sy}':"
                  f"d=1:s=1920x1080:fps={FPS},{g},vignette,noise=alls=4:allf=t+u,"
                  f"format=yuv420p,setpts=PTS-STARTPTS,fps={FPS},settb=AVTB")
        else:
            vf = (f"scale=1920:1080,setsar=1,noise=alls=3:allf=t+u,"
                  f"format=yuv420p,setpts=PTS-STARTPTS,fps={FPS},settb=AVTB")
        run([FF, '-y', '-loop', '1', '-t', f'{D:.3f}', '-i', sh['_src'], '-vf', vf,
             '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', dst], f'shot{i}')
    # ---- audio
    n = int(SR * (total + 2))
    vo_bus = np.zeros(n)
    vo_events = []
    for i, sh in enumerate(shots):
        if sh['kind'] != 'img':
            continue
        t = starts[i] + sh.get('pad_in', 0.8)
        for v in sh.get('vo', []):
            sig = decode_wav(os.path.join(VOICE, v))
            j = int(t * SR)
            vo_bus[j:j + len(sig)] += sig[:max(0, n - j)]
            vo_events.append((t, v, len(sig) / SR))
            t += len(sig) / SR + sh.get('vo_gap', 0.35)
    sfx_bus = np.zeros(n)
    for ev in cue.get('sfx', []):
        at = resolve_at(ev['at'], starts)
        sig = S.master(getattr(S, ev['fn'])(**ev.get('kw', {})))
        j = int(at * SR)
        if j < n:
            sfx_bus[j:j + len(sig)] += sig[:max(0, n - j)] * ev.get('gain', 1.0)
    hits = sorted({resolve_at(ev['at'], starts) for ev in cue.get('sfx', [])
                   if ev['fn'] in ('impact', 'braam') and resolve_at(ev['at'], starts) < total - 1})
    score_path = os.path.join(SCORE, f"{cue['id']}_score.wav")
    S.render_score(cue['music'], total, hits, score_path)
    music = decode_wav(score_path, mono=True)
    music = music[:n] if len(music) >= n else np.pad(music, (0, n - len(music)))
    env = np.abs(vo_bus)
    k = int(SR * 0.12)
    env = np.convolve(env, np.ones(k) / k, mode='same')
    env = np.maximum.accumulate(env)
    kd = int(SR * 0.6)
    env = np.convolve(env, np.ones(kd) / kd, mode='same')
    duck = 1 - 0.62 * np.clip(env / (np.percentile(env[env > 0], 85) + 1e-9), 0, 1)
    mix = music * 0.82 * duck + vo_bus * 1.0 + sfx_bus * 0.9
    mix = S.master(mix, 0.9)
    st = S.stereo(mix, 0.18)
    mix_path = os.path.join(SCORE, f"{cue['id']}_mix.wav")
    import scipy.io.wavfile as wav
    wav.write(mix_path, SR, (st.T * 32767).astype(np.int16))
    # ---- stage 2: xfade assembly
    args = [FF, '-y']
    for f in shot_files:
        args += ['-i', f]
    filters = [f"[{i}:v]settb=AVTB,fps={FPS}[v{i}]" for i in range(len(shots))]
    for i in range(1, len(shots)):
        a = f'v{i - 1}' if i == 1 else f'x{i - 1}'
        tr = shots[i].get('xfade', 'fade')
        lbl = f'x{i}' if i < len(shots) - 1 else 'vout'
        filters.append(f"[{a}][v{i}]xfade=transition={tr}:duration={xfs[i]:.3f}:offset={starts[i]:.3f}[{lbl}]")
    vo_only = os.path.join(WORK, f"{cue['id']}_video.mp4")
    args += ['-filter_complex', ';'.join(filters), '-map', '[vout]',
             '-c:v', 'libx264', '-preset', 'medium', '-crf', os.environ.get('FCRF', '26'), '-pix_fmt', 'yuv420p', vo_only]
    run(args, 'xfade')
    # ---- mux
    final = os.path.join(OUT, f"{cue['id']}.mp4")
    run([FF, '-y', '-i', vo_only, '-i', mix_path, '-map', '0:v', '-map', '1:a',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
         '-movflags', '+faststart', '-t', f'{total:.3f}', final], 'mux')
    print(f"BUILT {final}  total={total:.1f}s")
    # srt + timeline
    lines = []
    for i, (t, v, d) in enumerate(vo_events, 1):
        txt = cue.get('subtitles', {}).get(v, '')
        if not txt:
            continue

        def ts(x):
            h = int(x // 3600)
            m = int(x % 3600 // 60)
            s = x % 60
            return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.', ',')
        lines.append(f"{i}\n{ts(t)} --> {ts(t + d)}\n{txt}\n")
    open(os.path.join(OUT, f"{cue['id']}.srt"), 'w').write('\n'.join(lines))
    json.dump({'total': total, 'starts': starts, 'vo': vo_events},
              open(os.path.join(OUT, f"{cue['id']}.timeline.json"), 'w'), ensure_ascii=False, indent=1)
    return total


if __name__ == '__main__':
    build(sys.argv[1])
