"""
광고 템플릿 유형 분류 시각화 — ①유형별 수 + ④특성 요약
실행: python type_viz_14.py
의존성: pip install pandas matplotlib openpyxl
"""

import pandas as pd
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import platform
import os

# ── 한글 폰트 ─────────────────────────────────────────────────────────
FONT_PATH = None
_candidates = []
if platform.system() == 'Darwin':
    _candidates = ['/System/Library/Fonts/AppleSDGothicNeo.ttc',
                   '/Library/Fonts/AppleGothic.ttf']
elif platform.system() == 'Windows':
    _candidates = ['C:/Windows/Fonts/malgun.ttf',
                   'C:/Windows/Fonts/NanumGothic.ttf']
else:
    _candidates = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
    ]

for path in _candidates:
    if os.path.exists(path):
        FONT_PATH = path
        break

if FONT_PATH:
    fm.fontManager.addfont(FONT_PATH)
    FP   = fm.FontProperties(fname=FONT_PATH)
    FP_B = fm.FontProperties(fname=FONT_PATH, weight='bold')
else:
    FP = FP_B = fm.FontProperties()

def fp(size=10, bold=False):
    base = FP_B if bold else FP
    p = fm.FontProperties(fname=base.get_file() or None)
    p.set_size(size)
    if bold:
        p.set_weight('bold')
    return p

plt.rcParams['axes.unicode_minus'] = False

# ── 색상 ──────────────────────────────────────────────────────────────
BG      = '#FFFFFF'
CARD    = '#F7F7F5'
GRID    = '#E0DED8'
C_TEXT  = '#1A1928'
C_MUTED = '#6B6880'
C_ACC   = '#F5A623'

TYPE_COLORS = {
    '즉시 행동 유도형': '#7B6FE8',
    '실거주 설득형':    '#34C992',
    '즉시 행동 보조형': '#F5A623',
    '정보 제공형':      '#E8636A',
}

TYPE_ORDER = ['즉시 행동 유도형', '실거주 설득형', '즉시 행동 보조형', '정보 제공형']

# ── 유형 정의 (표 기준) ───────────────────────────────────────────────
TYPE_DATA = {
    '즉시 행동 유도형': {'count': 32, 'sub': '특별공급, 1순위 청약안내'},
    '실거주 설득형':    {'count': 15, 'sub': '계약·서류·입주 안내'},
    '즉시 행동 보조형': {'count':  2, 'sub': '예비입주, 무순위·2순위 청약'},
    '정보 제공형':      {'count':  1, 'sub': '관람 안내, 견본주택 운영 안내'},
}
total = sum(v['count'] for v in TYPE_DATA.values())

# ── 레이아웃 ──────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 9), facecolor=BG)

gs = gridspec.GridSpec(2, 1, figure=fig,
    top=0.90, bottom=0.07, left=0.06, right=0.97, hspace=0.42)

ax_bar  = fig.add_subplot(gs[0])
ax_card = fig.add_subplot(gs[1])

# 제목
#fig.text(0.06, 0.96, '광고 템플릿 유형 분류 분석',
    #     fontproperties=fp(20, bold=True), color=C_TEXT, va='top')

fig.add_artist(plt.Line2D([0.06, 0.97], [0.915, 0.915],
    transform=fig.transFigure, color=GRID, lw=0.8))

def style_ax(ax, title):
    ax.set_facecolor(CARD)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=C_MUTED, labelsize=9, length=0)
    ax.set_title(title, fontproperties=fp(12, bold=True),
                 color=C_TEXT, pad=12, loc='left')

# ══════════════════════════════════════════════════════════════════════
# CHART 1 — 유형별 템플릿 수 (가로 막대)
# ══════════════════════════════════════════════════════════════════════
style_ax(ax_bar, '유형별 템플릿 수')

y      = np.arange(len(TYPE_ORDER))
counts = [TYPE_DATA[t]['count'] for t in TYPE_ORDER]
colors = [TYPE_COLORS[t] for t in TYPE_ORDER]

bars = ax_bar.barh(y, counts, height=0.52,
                    color=colors, edgecolor=BG, linewidth=0.8, zorder=3)

for i, (bar, cnt) in enumerate(zip(bars, counts)):
    pct = cnt / total * 100
    ax_bar.text(cnt + 0.3, i,
                f'{cnt}개  ({pct:.0f}%)',
                va='center', fontproperties=fp(11, bold=True),
                color=C_TEXT, zorder=4)

ax_bar.set_yticks(y)
ax_bar.set_yticklabels(TYPE_ORDER, fontproperties=fp(11))
for lbl in ax_bar.get_yticklabels():
    lbl.set_color(C_TEXT)
ax_bar.set_xlim(0, max(counts) + 12)
ax_bar.set_xticks([])
ax_bar.invert_yaxis()
for i in range(len(TYPE_ORDER) - 1):
    ax_bar.axhline(i + 0.5, color=GRID, lw=0.5, zorder=1)
ax_bar.text(0.98, -0.10, '즉시 행동 유도형이 전체의 64%',
            transform=ax_bar.transAxes, ha='right',
            fontproperties=fp(9.5), color=C_ACC, style='italic')

# ══════════════════════════════════════════════════════════════════════
# CHART 2 — 유형별 특성 요약 카드
# ══════════════════════════════════════════════════════════════════════
ax_card.set_facecolor(CARD)
for sp in ax_card.spines.values():
    sp.set_visible(False)
ax_card.set_xticks([])
ax_card.set_yticks([])
ax_card.set_title('유형별 특성 요약', fontproperties=fp(12, bold=True),
                   color=C_TEXT, pad=12, loc='left')
ax_card.set_xlim(0, 10)
ax_card.set_ylim(0, len(TYPE_ORDER) + 0.3)

for i, t in enumerate(TYPE_ORDER):
    yc  = len(TYPE_ORDER) - 1 - i
    clr = TYPE_COLORS[t]
    d   = TYPE_DATA[t]

    # 카드 배경
    ax_card.add_patch(plt.Rectangle(
        (0.1, yc + 0.08), 9.8, 0.82,
        facecolor=clr, alpha=0.12,
        edgecolor=clr, linewidth=0.8, zorder=2
    ))
    # 색상 인디케이터 바
    ax_card.add_patch(plt.Rectangle(
        (0.1, yc + 0.08), 0.22, 0.82,
        facecolor=clr, alpha=0.9, zorder=3
    ))
    # 유형명
    ax_card.text(0.55, yc + 0.50, t,
                 va='center', fontproperties=fp(11, bold=True),
                 color=clr, zorder=4)
    # 개수
    ax_card.text(5.3, yc + 0.50, f'{d["count"]}개',
                 va='center', ha='center',
                 fontproperties=fp(13, bold=True), color=C_TEXT, zorder=4)
    # 주요 콘텐츠
    ax_card.text(6.3, yc + 0.50, d['sub'],
                 va='center', fontproperties=fp(9.5), color=C_MUTED, zorder=4)

# 컬럼 헤더
ax_card.text(0.55, len(TYPE_ORDER) + 0.12, '유형',
             va='bottom', fontproperties=fp(9, bold=True), color=C_MUTED)
ax_card.text(5.3,  len(TYPE_ORDER) + 0.12, '개수',
             ha='center', va='bottom',
             fontproperties=fp(9, bold=True), color=C_MUTED)
ax_card.text(6.3,  len(TYPE_ORDER) + 0.12, '주요 콘텐츠',
             va='bottom', fontproperties=fp(9, bold=True), color=C_MUTED)
ax_card.axhline(len(TYPE_ORDER), color=GRID, lw=0.8)

# ── 저장 ──────────────────────────────────────────────────────────────
plt.savefig('type_viz_14.png', dpi=180, bbox_inches='tight', facecolor=BG)
print('저장 완료: type_viz_14.png')
plt.show()
