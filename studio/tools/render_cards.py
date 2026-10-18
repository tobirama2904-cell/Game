#!/usr/bin/env python3
"""Render all title/end cards for the four trailers + teaser."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import titles as T

OUT = os.path.join(HERE, '..', 'assets', 'cards')
os.makedirs(OUT, exist_ok=True)

GREY = (168, 176, 190)
WHT = (238, 241, 247)

# --- НОКС (condensed dystopia)
T.card([{'text': 'СЛЫШИШЬ ШЁПОТ?', 'font': 'cond', 'size': 92, 'tracking': 14, 'color': WHT, 'glow': 1, 'gap_after': 26},
        {'text': 'НЕ БОЙСЯ. ЭТО КЛЮЧ.', 'font': 'cond', 'size': 54, 'tracking': 12, 'color': GREY}],
       f'{OUT}/noks_tag.png', tint=(5, 12, 16))
T.card([{'text': 'ХРОНИКИ ИСКРЫ', 'font': 'cond', 'size': 158, 'tracking': 20, 'color': WHT, 'glow': 1, 'gap_after': 14},
        {'text': '', 'size': 26, 'rule': True, 'rule_w': 760, 'gap_after': 22},
        {'text': 'КНИГА ПЕРВАЯ: НОКС. ИГРЫ ТЕНИ', 'font': 'body', 'size': 42, 'tracking': 9, 'color': GREY}],
       f'{OUT}/noks_title.png', tint=(5, 12, 16))
T.card([{'text': 'СКОРО', 'font': 'cond', 'size': 120, 'tracking': 30, 'color': WHT, 'glow': 1, 'gap_after': 18},
        {'text': '', 'size': 24, 'rule': True, 'rule_w': 420, 'gap_after': 20},
        {'text': 'ХРОНИКИ ИСКРЫ', 'font': 'body', 'size': 34, 'tracking': 10, 'color': GREY}],
       f'{OUT}/end_noks.png', tint=(5, 12, 16))

# --- КОСТЯНОЙ ПРИЛИВ (elegant serif dark fantasy)
T.card([{'text': 'ПАМЯТЬ — ДАР ПРОКЛЯТЫХ.', 'font': 'phil', 'size': 78, 'tracking': 8, 'color': (224, 218, 204), 'glow': 1}],
       f'{OUT}/bone_tag.png', tint=(10, 10, 8))
T.card([{'text': 'КОСТЯНОЙ ПРИЛИВ', 'font': 'serif', 'size': 148, 'tracking': 6, 'color': (230, 225, 212), 'glow': 1, 'gap_after': 14},
        {'text': '', 'size': 26, 'rule': True, 'rule_w': 640, 'rule_color': (140, 132, 116), 'gap_after': 22},
        {'text': 'ТЁМНОЕ ФЭНТЕЗИ О ТЕХ, КТО СЛЫШИТ ЧУЖОЙ СТРАХ', 'font': 'phil', 'size': 38, 'tracking': 7, 'color': (168, 160, 146)}],
       f'{OUT}/bone_title.png', tint=(10, 10, 8))
T.card([{'text': 'СКОРО', 'font': 'serif', 'size': 118, 'tracking': 12, 'color': (230, 225, 212), 'glow': 1, 'gap_after': 18},
        {'text': '', 'size': 24, 'rule': True, 'rule_w': 400, 'rule_color': (140, 132, 116), 'gap_after': 20},
        {'text': 'КОСТЯНОЙ ПРИЛИВ', 'font': 'phil', 'size': 34, 'tracking': 8, 'color': (168, 160, 146)}],
       f'{OUT}/end_bone.png', tint=(10, 10, 8))

# --- СТРАННИК (noir philosopher)
T.card([{'text': 'ГОРОД ПОМНИТ КАЖДУЮ ТРЕЩИНУ.', 'font': 'phil', 'size': 80, 'tracking': 9, 'color': (232, 236, 242), 'glow': 1}],
       f'{OUT}/strannik_tag.png', tint=(7, 9, 13))
T.card([{'text': 'СТРАННИК', 'font': 'phil', 'size': 190, 'tracking': 26, 'color': (240, 243, 248), 'glow': 1, 'gap_after': 14},
        {'text': '', 'size': 26, 'rule': True, 'rule_w': 560, 'gap_after': 22},
        {'text': 'ОН ВИДИТ ГОРОД НАСКВОЗЬ. ГОРОД ВИДИТ ЕГО.', 'font': 'body', 'size': 40, 'tracking': 8, 'color': (160, 170, 186)}],
       f'{OUT}/strannik_title.png', tint=(7, 9, 13))
T.card([{'text': 'СКОРО', 'font': 'phil', 'size': 118, 'tracking': 22, 'color': (240, 243, 248), 'glow': 1, 'gap_after': 18},
        {'text': '', 'size': 24, 'rule': True, 'rule_w': 400, 'gap_after': 20},
        {'text': 'СТРАННИК', 'font': 'body', 'size': 34, 'tracking': 10, 'color': (160, 170, 186)}],
       f'{OUT}/end_strannik.png', tint=(7, 9, 13))

# --- РАЗЛОМ (RussoOne sci-fi)
T.card([{'text': 'МЫ ПОДОШЛИ СЛИШКОМ БЛИЗКО.', 'font': 'display', 'size': 86, 'tracking': 10, 'color': (240, 240, 244), 'glow': 1}],
       f'{OUT}/razlom_tag.png', tint=(12, 6, 7))
T.card([{'text': 'РАЗЛОМ', 'font': 'display', 'size': 210, 'tracking': 18, 'color': (246, 244, 246), 'glow': 1, 'gap_after': 14},
        {'text': '', 'size': 26, 'rule': True, 'rule_w': 520, 'rule_color': (190, 90, 90), 'gap_after': 22},
        {'text': 'РЕАЛЬНОСТЬ ДАЛА ТРЕЩИНУ', 'font': 'display', 'size': 40, 'tracking': 12, 'color': (200, 150, 150)}],
       f'{OUT}/razlom_title.png', tint=(12, 6, 7))
T.card([{'text': 'СКОРО', 'font': 'display', 'size': 120, 'tracking': 26, 'color': (246, 244, 246), 'glow': 1, 'gap_after': 18},
        {'text': '', 'size': 24, 'rule': True, 'rule_w': 400, 'rule_color': (190, 90, 90), 'gap_after': 20},
        {'text': 'РАЗЛОМ', 'font': 'display', 'size': 36, 'tracking': 12, 'color': (200, 150, 150)}],
       f'{OUT}/end_razlom.png', tint=(12, 6, 7))

# --- TEASER
T.card([{'text': 'ЧЕТЫРЕ ИСТОРИИ.', 'font': 'cond', 'size': 96, 'tracking': 16, 'color': WHT, 'glow': 1, 'gap_after': 20},
        {'text': 'ОДНА ТРЕЩИНА.', 'font': 'cond', 'size': 96, 'tracking': 16, 'color': (214, 120, 120), 'glow': 1}],
       f'{OUT}/teaser_tag.png', tint=(8, 8, 10))
print(sorted(os.listdir(OUT)))
