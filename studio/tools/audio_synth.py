#!/usr/bin/env python3
"""Procedural cinematic score & SFX engine (numpy + scipy). Pure synthesis, no samples."""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
RNG = np.random.default_rng(11)


def T(dur):
    return np.arange(int(SR * dur)) / SR


def _sos(kind, cut, order=4):
    return butter(order, min(max(cut / (SR / 2), 1e-4), 0.999), btype=kind, output='sos')


def lp(x, cut, order=4):
    return sosfilt(_sos('low', cut, order), x)


def hp(x, cut, order=4):
    return sosfilt(_sos('high', cut, order), x)


def bp(x, lo, hi, order=3):
    return sosfilt(butter(order, [max(lo / (SR / 2), 1e-4), min(hi / (SR / 2), .999)], btype='band', output='sos'), x)


def _tvfilt(x, lo_arr, hi_arr, nfft=4096, hop=1024):
    """time-varying band filter via windowed STFT (smooth brickwall masks)"""
    n = len(x)
    xp = np.concatenate([x, np.zeros(nfft)])
    win = np.hanning(nfft)
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    out = np.zeros(len(xp))
    norm = np.zeros(len(xp))
    for i in range(0, len(xp) - nfft + 1, hop):
        lo = max(float(lo_arr[min(i + nfft // 2, n - 1)]), 30.0)
        hi = min(float(hi_arr[min(i + nfft // 2, n - 1)]), SR / 2 - 200)
        hi = max(hi, lo * 1.5)
        mask = (1 / (1 + (freqs / hi) ** 16)) * (1 / (1 + (lo / np.maximum(freqs, 1)) ** 16))
        seg = np.fft.irfft(np.fft.rfft(xp[i:i + nfft] * win) * mask, nfft)
        out[i:i + nfft] += seg * win
        norm[i:i + nfft] += win ** 2
    return (out / np.maximum(norm, 1e-6))[:n]


def lp_tv(x, cut_arr):
    cut = np.broadcast_to(np.asarray(cut_arr, float), (len(x),))
    return _tvfilt(x, np.full(len(x), 20.0), cut)


def bp_tv(x, lo_arr, hi_arr):
    n = len(x)
    lo = np.broadcast_to(np.asarray(lo_arr, float), (n,))
    hi = np.broadcast_to(np.asarray(hi_arr, float), (n,))
    return _tvfilt(x, lo, hi)


def env(dur, a=0.01, d=0.15, sus=0.7, r=0.4, curve=1.6):
    n = int(SR * dur)
    e = np.ones(n)
    ai, di, ri = max(1, int(a * SR)), int(d * SR), int(r * SR)
    if ai < n:
        e[:ai] = np.linspace(0, 1, ai) ** curve
    if di and ai + di < n:
        e[ai:ai + di] = np.linspace(1, sus, di)
    elif ai < n:
        e[ai:] = sus
    if ri and ri < n:
        e[-ri:] *= np.linspace(1, 0, ri) ** 1.4
    return e


def _crossfade_filters(x, bright, dark, t_mix):
    """crossfade between bright/dark filtered versions, t_mix in [0,1] over time"""
    n = len(x)
    m = np.interp(np.linspace(0, 1, n), [0, 1], [t_mix[0], t_mix[1]])
    return dark * (1 - m) + bright * m


def reverb(x, decay=1.1, mix=0.28, predelay=0.02):
    n = len(x)
    ir_n = int(SR * (decay + predelay))
    ir = RNG.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / (SR * decay / 4)) ** 1.5
    ir[:int(SR * predelay)] = 0
    ir[0] = 0.0
    ir = lp(ir, 5000)
    ir /= np.abs(ir).max() + 1e-9
    L = n + ir_n
    X = np.fft.rfft(x, L)
    H = np.fft.rfft(ir, L)
    wet = np.fft.irfft(X * H, L)[:n]
    wet /= np.abs(wet).max() + 1e-9
    return x * (1 - mix) + wet * mix * np.abs(x).max()


def stereo(x, width=0.25):
    n = len(x)
    d = int(SR * 0.012)
    r = np.roll(x, d) * (1 - width) + x * width
    l = np.roll(x, -d) * (1 - width) + x * width
    return np.stack([l, r])


def master(x, peak=0.88):
    x = np.tanh(x * 1.15) / np.tanh(1.15)
    m = np.abs(x).max()
    if m > 0:
        x = x / m * peak
    return x


# ---------------------------------------------------------------- instruments
def braam(dur=2.4, f=55.0, gain=1.0):
    t = T(dur)
    x = np.zeros_like(t)
    for det in (1.0, 1.006, 0.995):
        ph = 2 * np.pi * f * det * (t - 0.10 * np.exp(-t * 2.5) * t)
        x += np.sin(ph) + 0.55 * np.sin(2 * ph) + 0.30 * np.sin(3 * ph) + 0.18 * np.sin(4 * ph) + 0.09 * np.sin(5 * ph)
    bright = lp(x, 2600)
    dark = lp(x, 380)
    x = _crossfade_filters(bright if False else bright, bright, dark, (1.0, 0.12))
    x *= env(dur, a=0.03, d=0.5, sus=0.55, r=dur * 0.45)
    return reverb(x * gain, decay=1.6, mix=0.35)


def sub_drop(dur=2.6, f0=110, f1=27, gain=1.0):
    t = T(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 5.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.3 * np.sin(2 * ph)
    x *= env(dur, a=0.005, d=0.3, sus=0.7, r=dur * 0.5)
    return x * gain


def impact(dur=2.2, gain=1.0):
    t = T(dur)
    n = RNG.standard_normal(len(t))
    crack = hp(n, 900) * np.exp(-t * 38)
    body = lp_tv(n, 300 + 4000 * np.exp(-t * 9)) * np.exp(-t * 7)
    x = 0.7 * body + 0.5 * crack + sub_drop(dur, 90, 26, 0.9)
    return reverb(x * gain, decay=1.8, mix=0.4)


def riser(dur=4.0, gain=0.8, f_lo=180, f_hi=5200):
    t = T(dur)
    n = RNG.standard_normal(len(t))
    f = f_lo * (f_hi / f_lo) ** (t / dur) ** 1.7
    sig = lp_tv(n, np.clip(f, 100, 9000))
    trem = (1 + 0.6 * np.sin(2 * np.pi * (3 + 9 * t / dur) * t))
    x = sig * trem * (t / dur) ** 2.2
    saw_f = 55 * 2 ** (2.2 * (t / dur) ** 2)
    x += 0.25 * np.sin(2 * np.pi * np.cumsum(saw_f) / SR) * (t / dur) ** 3
    return x * gain


def whoosh(dur=1.3, gain=0.7):
    t = T(dur)
    n = RNG.standard_normal(len(t))
    f = 300 + 3500 * np.sin(np.pi * t / dur) ** 2
    x = lp_tv(n, np.clip(f, 100, 10000)) * np.sin(np.pi * t / dur) ** 1.5
    return x * gain


def thunder(dur=5.0, gain=1.0):
    t = T(dur)
    n = RNG.standard_normal(len(t))
    x = lp(n, 240) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * t + 1)) * np.exp(-t * 0.9)
    x += lp(RNG.standard_normal(len(t)), 90) * np.exp(-t * 0.6)
    for _ in range(3):
        st = RNG.uniform(0, dur * 0.5)
        i = int(st * SR)
        ln = min(int(0.35 * SR), len(x) - i)
        if ln > 0:
            x[i:i + ln] += hp(RNG.standard_normal(ln), 1500) * np.exp(-np.arange(ln) / (SR * 0.05)) * 0.6
    return reverb(x * gain, decay=2.6, mix=0.5)


def heartbeat(bpm=58, dur=2.0, gain=1.0):
    t = T(dur)
    x = np.zeros_like(t)
    per = 60.0 / bpm
    k = 0
    while k * per < dur:
        for off, amp in ((0.0, 1.0), (0.28, 0.6)):
            st = k * per + off
            i = int(st * SR)
            ln = int(0.30 * SR)
            if i + ln > len(x):
                break
            tt = np.arange(ln) / SR
            x[i:i + ln] += amp * np.sin(2 * np.pi * (52 - 18 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 16)
        k += 1
    return x * gain


def piano(f, dur=3.2, gain=1.0):
    t = T(dur)
    parts = [(1, 1.0), (2.0, 0.42), (2.98, 0.24), (4.1, 0.13), (5.3, 0.07), (6.6, 0.04)]
    x = np.zeros_like(t)
    for mul, amp in parts:
        dec = np.exp(-t * (1.1 + mul * 0.55))
        x += amp * np.sin(2 * np.pi * f * mul * t * (1 + 0.0004 * mul)) * dec
    x += 0.25 * hp(RNG.standard_normal(len(t)), 2500) * np.exp(-t * 60)
    x *= env(dur, a=0.004, d=0.1, sus=0.9, r=dur * 0.3)
    return reverb(x * gain, decay=2.0, mix=0.4)


def strings_note(f, dur=2.0, gain=1.0, atk=0.25):
    t = T(dur)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(t / 0.6, 1)
    x = np.zeros_like(t)
    for h, a in ((1, 1), (2, 0.5), (3, 0.32), (4, 0.2), (5, 0.12), (6, 0.07)):
        x += a * np.sin(2 * np.pi * f * h * vib * t + h)
    x = lp(x, 3800)
    x *= env(dur, a=atk, d=0.2, sus=0.8, r=dur * 0.35)
    return x * gain


def choir(freqs, dur=4.0, gain=1.0):
    x = np.zeros(int(SR * dur))
    for i, f in enumerate(freqs):
        n = strings_note(f * (1 + 0.002 * (i % 2)), dur, gain=1.0, atk=dur * 0.25)
        n = bp(n, 200, 3000)
        x[:len(n)] += n * (0.8 + 0.2 * np.sin(i))
    x += 0.05 * bp(RNG.standard_normal(len(x)), 800, 4000) * env(dur, a=dur * .3, d=.1, sus=.6, r=dur * .3)
    return reverb(x * gain, decay=2.4, mix=0.45)


def ostinato(f, dur, rate=8, gain=0.8):
    """spiccato 8th/16th pulse"""
    n_out = int(SR * dur)
    x = np.zeros(n_out)
    step = SR // rate
    ln = int(step * 1.7)
    i = 0
    k = 0
    while i + ln < n_out:
        acc = 1.0 if k % 4 == 0 else (0.75 if k % 2 == 0 else 0.55)
        tt = np.arange(ln) / SR
        s = np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(4 * np.pi * f * tt) + 0.25 * np.sin(6 * np.pi * f * tt)
        s = lp(s, 2400) * np.exp(-tt * 14) * acc
        x[i:i + ln] += s
        i += step
        k += 1
    return x * gain


def kick(gain=1.0):
    ln = int(0.5 * SR)
    tt = np.arange(ln) / SR
    f = 48 + 60 * np.exp(-tt * 22)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 11)
    x += 0.3 * hp(RNG.standard_normal(ln), 2000) * np.exp(-tt * 90)
    return x * gain


def tom(f=120, gain=0.9):
    ln = int(0.6 * SR)
    tt = np.arange(ln) / SR
    x = np.sin(2 * np.pi * (f - 20 * np.exp(-tt * 10)) * tt) * np.exp(-tt * 8)
    x += 0.25 * lp(RNG.standard_normal(ln), 500) * np.exp(-tt * 20)
    return x * gain


def cymbal(dur=2.2, gain=0.5):
    t = T(dur)
    x = hp(RNG.standard_normal(len(t)), 5000) * np.exp(-t * 3.2)
    return reverb(x * gain, decay=1.4, mix=0.4)


# ---------------------------------------------------------------- beds / SFX
def rain(dur, gain=0.5):
    t = T(dur)
    n = RNG.standard_normal(len(t))
    x = bp(n, 500, 7000)
    mod = 0.8 + 0.2 * np.sin(2 * np.pi * 0.23 * t) + 0.1 * RNG.standard_normal(len(t)) * 0
    x *= mod
    drops = np.zeros_like(t)
    for _ in range(int(dur * 14)):
        i = RNG.integers(0, len(t) - 400)
        ln = 400
        tt = np.arange(ln) / SR
        drops[i:i + ln] += np.sin(2 * np.pi * RNG.uniform(1800, 4200) * tt) * np.exp(-tt * 60) * 0.25
    return (x * 0.7 + drops) * gain


def sea_wash(dur, gain=0.6):
    t = T(dur)
    n = RNG.standard_normal(len(t))
    x = lp(n, 900) * (0.45 + 0.55 * np.abs(np.sin(2 * np.pi * 0.09 * t + 0.7)) ** 1.5)
    x += 0.3 * lp(RNG.standard_normal(len(t)), 300) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t + 2.2))
    return x * gain


def wind(dur, gain=0.5):
    t = T(dur)
    n = RNG.standard_normal(len(t))
    f = 300 + 500 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t))
    x = bp(n, 120, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t + 1)) ** 2
    return x * gain


def city_hum(dur, gain=0.4):
    t = T(dur)
    x = 0.5 * np.sin(2 * np.pi * 50 * t) + 0.3 * np.sin(2 * np.pi * 100 * t)
    x += lp(RNG.standard_normal(len(t)), 350) * 0.8
    x = lp(x, 500)
    return x * gain


def vinyl_crackle(dur, gain=0.25):
    n = int(SR * dur)
    x = np.zeros(n)
    idx = RNG.integers(0, n, int(dur * 22))
    x[idx] = RNG.standard_normal(len(idx)) * 0.6
    x += lp(RNG.standard_normal(n), 1200) * 0.05
    return x * gain


def siren(dur=6.0, gain=0.3):
    t = T(dur)
    f = 640 + 180 * np.sin(2 * np.pi * 0.22 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    x = lp(x, 1400) * env(dur, a=1.5, d=0.5, sus=0.7, r=2.0)
    return reverb(x * gain, decay=2.0, mix=0.5)


def glitch(dur=0.7, gain=0.8):
    n = int(SR * dur)
    x = np.zeros(n)
    seg = SR // 40
    i = 0
    while i < n:
        ln = min(seg * RNG.integers(1, 4), n - i)
        x[i:i + ln] = RNG.standard_normal() * np.sin(2 * np.pi * RNG.uniform(200, 3000) * np.arange(ln) / SR)
        i += ln
    x = hp(x, 300)
    return x * gain * np.exp(-T(dur) * 3)


def metal_scrape(dur=1.6, gain=0.7):
    t = T(dur)
    n = RNG.standard_normal(len(t))
    w = 1 + 0.3 * np.sin(2 * np.pi * 7 * t)
    x = bp_tv(n, 1800 * w, 4200 * w) * np.sin(np.pi * t / dur) ** 0.7
    return reverb(x * gain, decay=0.9, mix=0.3)


def bell(f, dur=4.0, gain=0.6):
    t = T(dur)
    x = np.zeros_like(t)
    for mul, a, d in ((1, 1, 1.0), (2.76, 0.5, 1.4), (5.4, 0.25, 2.0), (8.9, 0.12, 2.6)):
        x += a * np.sin(2 * np.pi * f * mul * t) * np.exp(-t * d)
    return reverb(x * gain, decay=2.6, mix=0.45)


def whisper_bed(dur, gain=0.35):
    """formant-ish shifting noise, ghostly"""
    t = T(dur)
    n = RNG.standard_normal(len(t))
    f1 = 500 + 350 * np.sin(2 * np.pi * 0.31 * t) + 200 * np.sin(2 * np.pi * 0.77 * t + 1)
    x = bp_tv(n, np.clip(f1 - 150, 80, 6000), np.clip(f1 + 900, 300, 7000))
    x *= (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 1.7 * t + np.sin(t * 3))))
    return reverb(x * gain, decay=1.5, mix=0.5)


# ---------------------------------------------------------------- scores
MIN = {'A': 55.0, 'C': 65.41, 'D': 73.42, 'E': 82.41, 'F': 87.31, 'G': 98.0, 'Bb': 116.54}


def _chord(root, kind='m'):
    r = MIN[root] * 4
    iv = {'m': (0, 3, 7), 'M': (0, 4, 7), 'sus': (0, 5, 7), 'dim': (0, 3, 6)}[kind]
    return [r * 2 ** (i / 12) for i in iv]


def _place(out, sig, t0, gain=1.0):
    i = int(t0 * SR)
    j = min(len(out), i + len(sig))
    if i < len(out):
        out[i:j] += sig[:j - i] * gain


def _score_common(style, dur, hits):
    out = np.zeros(int(SR * dur))
    t = T(dur)
    if style == 'noks':
        prog = [('A', 'm'), ('A', 'm'), ('F', 'M'), ('G', 'M')]
        root = 55.0
        out[:len(t)] += (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 27.5 * t)) * 0.16 * np.minimum(t / 4, 1)
        out += lp(RNG.standard_normal(len(t)), 220) * 0.05
        out += vinyl_crackle(dur, 0.10)
        _place(out, ostinato(110, dur * 0.55, 8, 0.5), dur * 0.24)
        _place(out, choir(_chord('A'), dur * 0.4, 0.35), dur * 0.18)
        _place(out, ostinato(110, dur * 0.45, 16, 0.7), dur * 0.55)
        _place(out, choir(_chord('F'), dur * 0.35, 0.5), dur * 0.5)
        _place(out, choir(_chord('G'), dur * 0.3, 0.55), dur * 0.72)
        for i, h in enumerate(hits):
            _place(out, braam(2.6, 55 * (1 if i % 2 == 0 else 1.5), 1.0), h)
            _place(out, kick(1.0), h)
        _place(out, riser(dur * 0.22, 0.9), dur * 0.66)
        _place(out, piano(440, 3.5, 0.5), 0.2)
        _place(out, piano(329.63, 4.0, 0.55), dur - 5.0)
        for i in range(int(dur * 0.9)):
            _place(out, kick(0.5), dur * 0.55 + i * (60 / 100))
    elif style == 'bone':
        out[:len(t)] += (np.sin(2 * np.pi * 36.7 * t) + 0.4 * np.sin(2 * np.pi * 73.4 * t)) * 0.15 * np.minimum(t / 5, 1)
        out += sea_wash(dur, 0.5)
        out += wind(dur, 0.35)
        _place(out, strings_note(146.83, dur * 0.5, 0.4, atk=2.0), 0.3)
        _place(out, choir(_chord('D'), dur * 0.45, 0.45), dur * 0.2)
        _place(out, choir(_chord('Bb'), dur * 0.4, 0.5), dur * 0.55)
        _place(out, choir(_chord('C'), dur * 0.35, 0.5), dur * 0.78)
        # tribal pulse
        i = dur * 0.45
        k = 0
        while i < dur - 2:
            _place(out, tom(110 if k % 4 else 82, 0.9), i)
            i += 60 / 76
            k += 1
        for h in hits:
            _place(out, impact(2.6, 0.9), h)
            _place(out, thunder(4.0, 0.5), h + 0.05)
        _place(out, bell(293.66, 5.0, 0.5), 0.5)
        _place(out, bell(220.0, 6.0, 0.5), dur - 6.5)
        _place(out, riser(dur * 0.2, 0.7), dur * 0.68)
    elif style == 'strannik':
        out += rain(dur, 0.45)
        out += city_hum(dur, 0.30)
        out[:len(t)] += np.sin(2 * np.pi * 65.41 * t) * 0.12 * np.minimum(t / 4, 1)
        _place(out, siren(8.0, 0.22), dur * 0.1)
        _place(out, piano(261.63, 3.5, 0.55), 0.4)
        _place(out, piano(311.13, 3.5, 0.5), dur * 0.16)
        _place(out, piano(233.08, 3.5, 0.5), dur * 0.3)
        _place(out, heartbeat(56, dur * 0.7, 0.7), dur * 0.25)
        _place(out, ostinato(130.81, dur * 0.5, 8, 0.45), dur * 0.42)
        _place(out, strings_note(196.0, dur * 0.4, 0.35, atk=2.5), dur * 0.5)
        _place(out, choir(_chord('C'), dur * 0.3, 0.35), dur * 0.62)
        for h in hits:
            _place(out, impact(2.4, 0.8), h)
            _place(out, glitch(0.6, 0.5), h - 0.1)
        _place(out, riser(dur * 0.2, 0.75), dur * 0.7)
        _place(out, piano(130.81, 5.0, 0.6), dur - 6.0)
    elif style == 'razlom':
        out[:len(t)] += np.sin(2 * np.pi * 41.2 * t) * 0.18 * np.minimum(t / 4, 1)
        out += lp(RNG.standard_normal(len(t)), 400) * 0.06
        _place(out, ostinato(82.41, dur * 0.8, 16, 0.5), dur * 0.15)
        _place(out, choir(_chord('E'), dur * 0.5, 0.4), dur * 0.2)
        _place(out, choir(_chord('C'), dur * 0.4, 0.5), dur * 0.52)
        _place(out, choir(_chord('D'), dur * 0.4, 0.55), dur * 0.74)
        _place(out, bell(659.25, 4.0, 0.35), dur * 0.3)
        i = dur * 0.5
        k = 0
        while i < dur - 2:
            _place(out, kick(0.8 if k % 4 else 1.0), i)
            if k % 4 == 2:
                _place(out, cymbal(1.2, 0.25), i)
            i += 60 / 96
            k += 1
        for h in hits:
            _place(out, braam(2.4, 41.2, 0.9), h)
            _place(out, impact(2.2, 0.8), h)
        _place(out, riser(dur * 0.24, 0.9), dur * 0.68)
        _place(out, piano(329.63, 4.0, 0.5), dur - 5.0)
    return out


def render_score(style, dur, hits, out_path):
    x = _score_common(style, dur, hits)
    x = master(reverb(x, decay=1.2, mix=0.18))
    n = len(x)
    fi = int(SR * 0.4)
    x[:fi] *= np.linspace(0, 1, fi)
    fo = int(SR * 1.2)
    x[-fo:] *= np.linspace(1, 0, fo) ** 1.2
    import scipy.io.wavfile as wav
    wav.write(out_path, SR, (stereo(x).T * 32767).astype(np.int16))
    return dur


def render_sfx(name, out_path, **kw):
    import scipy.io.wavfile as wav
    fn = {'impact': impact, 'riser': riser, 'whoosh': whoosh, 'thunder': thunder, 'braam': braam,
          'glitch': glitch, 'metal': metal_scrape, 'rain': rain, 'sea': sea_wash, 'wind': wind,
          'city': city_hum, 'siren': siren, 'whisper': whisper_bed, 'bell': bell, 'heartbeat': heartbeat,
          'subdrop': sub_drop, 'cymbal': cymbal, 'kick': kick}
    x = master(fn[name](**kw))
    wav.write(out_path, SR, (stereo(x).T * 32767).astype(np.int16))
    return out_path


def render_theme(style, dur, out_path):
    """Audiobook main theme / chapter stinger."""
    import scipy.io.wavfile as wav
    out = np.zeros(int(SR * dur))
    t = T(dur)
    roots = {'strannik': ('C', 130.81), 'noks': ('A', 110.0), 'bone': ('D', 73.42), 'razlom': ('E', 82.41)}
    key, f = roots[style]
    out += np.sin(2 * np.pi * f / 2 * t) * 0.12 * np.minimum(t / 2, 1) * np.minimum((dur - t) / 2, 1)
    _place(out, piano(f, dur * 0.6, 0.6), 0.1)
    _place(out, piano(f * 1.5, dur * 0.6, 0.5), dur * 0.25)
    _place(out, piano(f * 2 ** (3 / 12), dur * 0.6, 0.5), dur * 0.45)
    _place(out, choir(_chord(key), dur * 0.8, 0.4), dur * 0.15)
    _place(out, strings_note(f * 2, dur * 0.7, 0.3, atk=dur * 0.2), dur * 0.2)
    if style == 'strannik':
        out += rain(dur, 0.25)
    x = master(reverb(out, decay=2.2, mix=0.35))
    fo = int(SR * min(1.5, dur * 0.3))
    x[-fo:] *= np.linspace(1, 0, fo) ** 1.2
    fi = int(SR * 0.3)
    x[:fi] *= np.linspace(0, 1, fi)
    wav.write(out_path, SR, (stereo(x).T * 32767).astype(np.int16))
    return out_path


if __name__ == '__main__':
    import sys, time
    st = sys.argv[1] if len(sys.argv) > 1 else 'noks'
    d = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    hits = [float(v) for v in sys.argv[3].split(',')] if len(sys.argv) > 3 and sys.argv[3] else []
    t0 = time.time()
    render_score(st, d, hits, f'/tmp/test_{st}.wav')
    print(f'{st}: {d}s in {time.time()-t0:.1f}s')
