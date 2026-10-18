#!/usr/bin/env python3
"""Adapt the screenplay «Странник» into an audiobook segment script.
Output: out/audiobook/strannik/script.json — list of chapters, each a list of
segments {speaker, text}, speakers: narrator|walter|dorian|vera|vance|guard|voice.
Camera/sound directions are removed; dialogue cues become speaker assignments.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'source', 'Странник.txt')
OUTD = os.path.join(HERE, '..', 'out', 'audiobook', 'strannik')

NAME_MAP = {
    'Уолтер': 'walter', 'УОЛТЕР': 'walter',
    'Дориан': 'dorian', 'ДОРИАН': 'dorian',
    'Вера': 'vera', 'ВЭРА': 'vera',
    'Вэнс': 'vance', 'ВЭНС': 'vance',
    'Охранник': 'guard',
    'Голос': 'voice',
}

DROP_START = ('Камера', 'Мы видим', 'Чёрный экран', 'Звук:', 'На экране', 'Текст исчезает',
              'Появляется изображение', 'Экран', 'КАМЕРА', 'ЗВУК:', 'МЫ ВИДИМ', 'НА ЭКРАНЕ',
              'Изображение', 'Крупный план', 'Общий план', 'Сплит-экран', 'Титр:', 'ТИТР',
              'Гул ', 'Голос Уолтера обрывается', 'Голос Уолтера — чуть громче', 'Камера')
DROP_EXACT = {'Пауза.', 'Короткая пауза.', 'Тишина.', 'ПАУЗА.', 'ТИШИНА.', '---', '', '📖 ПРОЛОГ'}


def clean_name(s):
    """УОЛТЕР МАРТИН (68 лет) -> Уолтер Мартин, шестьдесят восемь лет"""
    def age(m):
        n = int(m.group(2))
        w = {8: 'восемь', 24: 'двадцать четыре', 68: 'шестьдесят восемь', 30: 'тридцать',
             45: 'сорок пять', 50: 'пятьдесят', 35: 'тридцать пять', 40: 'сорок'}
        return f"{m.group(1).title()}, {w.get(n, str(n))} лет,"
    s = re.sub(r'([А-ЯЁ][А-ЯЁ\s]+?)\s*\((\d+)\s*(?:лет|года)\)', age, s)
    return s


def parse():
    raw = open(SRC, encoding='utf-8').read().replace('\r', '')
    lines = raw.split('\n')
    chapters = []
    cur = {'title': 'ПРОЛОГ', 'segs': []}
    speaker = None
    prev = ''
    for ln in lines:
        s = ln.strip()
        m = re.match(r'^(?:📖\s*)?ПРОЛОГ$', s)
        mc = re.match(r'^ГЛАВА\s+(\d+)\.\s*(.+)$', s)
        if m or mc:
            if cur['segs']:
                chapters.append(cur)
            cur = {'title': s.replace('📖', '').strip(), 'segs': []}
            speaker = None
            continue
        if s in DROP_EXACT or s.startswith(DROP_START):
            continue
        # dialogue cue: "Уолтер:" / "Дориан (тихо):" / "Голос Вэнса (через динамик):"
        mcue = re.match(r'^(Голос\s+)?([А-ЯЁ][а-яё]+)(?:\s+[А-ЯЁ][А-ЯЁ\s]+?)?\s*(\([^)]*\))?\s*:\s*$', s)
        if mcue and mcue.group(2) in NAME_MAP:
            speaker = NAME_MAP[mcue.group(2)]
            continue
        mcue2 = re.match(r'^Голос\s+([А-ЯЁ][а-яё]+)\w*\s*(\([^)]*\))?\s*:\s*$', s)
        if mcue2 and mcue2.group(1) in NAME_MAP:
            speaker = NAME_MAP[mcue2.group(1)]
            continue
        if s.startswith('—') or s.startswith('- '):
            text = s if s.startswith('—') else '— ' + s[2:]
            cur['segs'].append({'speaker': speaker or 'narrator', 'text': text})
            speaker = None
            continue
        # scene slug ALL CAPS like "ВЕЧЕР. КАФЕ." / "ПОЗДНЕЕ. КРЫША КАФЕ." -> narrator bridge
        if re.match(r'^[А-ЯЁ0-9\s\.,-]{6,}$', s) and 'ГЛАВА' not in s:
            bridge = s.lower().capitalize()
            cur['segs'].append({'speaker': 'narrator', 'text': bridge + '.'})
            continue
        mv = re.match(r'^Голос\s+([А-ЯЁa-z][\w-]*)', s)
        if mv and '(' in s:
            prev = s
            continue
        mvoice = re.search(r'Голос\s+([А-ЯЁ][а-яё]*|[А-ЯЁ]{2,})', prev)
        key = mvoice.group(1) if mvoice else ''
        key = key if key in NAME_MAP else key.title()
        if mvoice and s.startswith('«') and key in NAME_MAP:
            cur['segs'].append({'speaker': NAME_MAP[key], 'text': s})
            prev = s
            continue
        # prose narration
        t = clean_name(s)
        t = re.sub(r'\s+', ' ', t).strip()
        if t:
            cur['segs'].append({'speaker': 'narrator', 'text': t})
        prev = s
    if cur['segs']:
        chapters.append(cur)
    return chapters


def main():
    os.makedirs(OUTD, exist_ok=True)
    ch = parse()
    total = sum(len(s['text']) for c in ch for s in c['segs'])
    json.dump(ch, open(os.path.join(OUTD, 'script.json'), 'w'), ensure_ascii=False, indent=1)
    # classic plan: single narrator voice reads everything, merged up to 1500 chars
    plan = []
    for ci, c in enumerate(ch):
        buf = []
        for sgm in c['segs']:
            if len(' '.join(buf + [sgm['text']])) > 1500 and buf:
                plan.append({'chapter': ci, 'speaker': 'narrator', 'chars': sum(len(x) for x in buf),
                             'text': ' '.join(buf)})
                buf = []
            buf.append(sgm['text'])
        if buf:
            plan.append({'chapter': ci, 'speaker': 'narrator', 'chars': sum(len(x) for x in buf),
                         'text': ' '.join(buf)})
    # cast plan: consecutive same-speaker blocks (for radio-play bonus scenes)
    cast = []
    for ci, c in enumerate(ch):
        buf_sp, buf = None, []
        for sgm in c['segs']:
            if sgm['speaker'] != buf_sp:
                if buf:
                    cast.append({'chapter': ci, 'speaker': buf_sp, 'text': ' '.join(buf)})
                buf, buf_sp = [], sgm['speaker']
            buf.append(sgm['text'])
        if buf:
            cast.append({'chapter': ci, 'speaker': buf_sp, 'text': ' '.join(buf)})
    json.dump(plan, open(os.path.join(OUTD, 'clip_plan.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump(cast, open(os.path.join(OUTD, 'cast_blocks.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'chapters={len(ch)} segments={sum(len(c["segs"]) for c in ch)} chars={total}')
    print(f'clips={len(plan)} est_minutes={total/850:.0f}')
    from collections import Counter
    print(Counter(p['speaker'] for p in plan))


if __name__ == '__main__':
    main()
