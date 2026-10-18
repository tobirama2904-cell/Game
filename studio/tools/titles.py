#!/usr/bin/env python3
"""Cinematic title cards / typographic overlays (PIL, Cyrillic-safe)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, '..', 'fonts')
FONTS = {
    'display': 'RussoOne-Regular.ttf',      # techy display (sci-fi)
    'cond': 'Oswald[wght].ttf',             # condensed (dystopia)
    'serif': 'YesevaOne-Regular.ttf',       # elegant serif (dark fantasy)
    'phil': 'Philosopher-Regular.ttf',      # humanist (thriller)
    'body': 'PT_Sans-Web-Regular.ttf',
    'rubik': 'Rubik[wght].ttf',
}
W, H = 1920, 1080
RNG = np.random.default_rng(3)


def font(key, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, FONTS[key]), size)


def _tracked_w(draw, text, fnt, tracking):
    if not text:
        return 0
    return sum(draw.textlength(c, font=fnt) for c in text) + tracking * (len(text) - 1)


def draw_tracked(draw, cx, y, text, fnt, fill, tracking=0, anchor_top=True):
    w = _tracked_w(draw, text, fnt, tracking)
    x = cx - w / 2
    for c in text:
        draw.text((x, y), c, font=fnt, fill=fill)
        x += draw.textlength(c, font=fnt) + tracking
    return w


def _bg(style='black', tint=(8, 10, 14)):
    img = Image.new('RGB', (W, H), (0, 0, 0))
    arr = np.zeros((H, W, 3), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    glow = np.clip(1 - r, 0, 1) ** 2.2
    for c in range(3):
        arr[:, :, c] = tint[c] * glow * 1.6
    img = Image.fromarray(arr.astype(np.uint8))
    return img


def _grain_vignette(img, grain=7, vig=0.55):
    a = np.asarray(img).astype(np.float32)
    a += RNG.normal(0, grain, a.shape).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    v = 1 - vig * np.clip(r - 0.45, 0, 1.4) ** 1.6
    a *= v[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def card(lines, out_path, tint=(8, 10, 14), grain=7, rule_color=(120, 130, 150), letterbox=0):
    """lines: list of dicts {text, font, size, color, tracking, dy, glow}
       laid out vertically centered."""
    img = _bg(tint=tint)
    d = ImageDraw.Draw(img)
    # measure
    tot = 0
    specs = []
    for ln in lines:
        f = font(ln.get('font', 'cond'), ln['size'])
        hgt = ln['size'] * ln.get('lh', 1.18)
        specs.append((ln, f, hgt))
        tot += hgt + ln.get('gap_after', 0)
    y = (H - tot) / 2
    glow_layer = Image.new('RGB', (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    for ln, f, hgt in specs:
        color = ln.get('color', (235, 238, 245))
        if ln.get('rule'):
            rw = ln.get('rule_w', 520)
            d.line([(W / 2 - rw / 2, y + hgt / 2), (W / 2 + rw / 2, y + hgt / 2)], fill=rule_color, width=2)
            y += hgt + ln.get('gap_after', 0)
            continue
        if ln.get('glow'):
            draw_tracked(gd, W / 2, y, ln['text'], f, color, ln.get('tracking', 0))
        draw_tracked(d, W / 2, y, ln['text'], f, color, ln.get('tracking', 0))
        y += hgt + ln.get('gap_after', 0)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(9))
    garr = np.asarray(glow_layer).astype(np.float32) * 0.9
    iarr = np.asarray(img).astype(np.float32)
    iarr = np.clip(iarr + garr, 0, 255)
    img = Image.fromarray(iarr.astype(np.uint8))
    img = _grain_vignette(img, grain=grain)
    if letterbox:
        dd = ImageDraw.Draw(img)
        dd.rectangle([0, 0, W, letterbox], fill=(0, 0, 0))
        dd.rectangle([0, H - letterbox, W, H], fill=(0, 0, 0))
    if out_path.endswith('.png'):
        img.convert('RGB').save(out_path[:-4] + '.jpg', quality=93)
        os.remove(out_path)
        return out_path[:-4] + '.jpg'
    img.save(out_path)
    return out_path


def credits_block(out_path, small_lines, title_lines=None, tint=(6, 8, 12)):
    """billing-block style end card"""
    img = _bg(tint=tint)
    d = ImageDraw.Draw(img)
    y = H * 0.30
    for ln in (title_lines or []):
        f = font(ln.get('font', 'cond'), ln['size'])
        draw_tracked(d, W / 2, y, ln['text'], f, ln.get('color', (230, 233, 240)), ln.get('tracking', 0))
        y += ln['size'] * 1.25
    y += 30
    f = font('cond', 26)
    for s in small_lines:
        draw_tracked(d, W / 2, y, s, f, (150, 158, 172), 3)
        y += 40
    img = _grain_vignette(img)
    img.save(out_path)
    return out_path


if __name__ == '__main__':
    import sys
    outdir = sys.argv[1] if len(sys.argv) > 1 else '/tmp/cards'
    os.makedirs(outdir, exist_ok=True)
    card([{'text': 'ХРОНИКИ ИСКРЫ', 'font': 'cond', 'size': 150, 'tracking': 18, 'color': (240, 242, 248), 'glow': 1},
          {'text': '', 'size': 20, 'rule': True, 'rule_w': 700, 'gap_after': 10},
          {'text': 'КНИГА ПЕРВАЯ: НОКС. ИГРЫ ТЕНИ', 'font': 'body', 'size': 40, 'tracking': 8, 'color': (170, 180, 196)}],
         f'{outdir}/t_noks.png', tint=(6, 12, 16))
    card([{'text': 'КОСТЯНОЙ ПРИЛИВ', 'font': 'serif', 'size': 140, 'tracking': 6, 'color': (226, 222, 210), 'glow': 1},
          {'text': '', 'size': 20, 'rule': True, 'rule_w': 620, 'gap_after': 10},
          {'text': 'ПАМЯТЬ — ДАР ПРОКЛЯТЫХ', 'font': 'phil', 'size': 42, 'tracking': 10, 'color': (168, 160, 148)}],
         f'{outdir}/t_bone.png', tint=(10, 10, 8))
    print('ok')
