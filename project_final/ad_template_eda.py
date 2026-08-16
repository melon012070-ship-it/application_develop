"""
광고 템플릿 데이터셋 EDA 시각화
파일: 광고_템플릿_데이터셋_정리.xlsx
"""

import pandas as pd
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# ── 한글 폰트 설정 ──────────────────────────────────────────────────────
import platform
if platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
elif platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    try:
        font_path = fm.findfont(fm.FontProperties(family='NanumGothic'))
        plt.rcParams['font.family'] = 'NanumGothic'
    except:
        pass
plt.rcParams['axes.unicode_minus'] = False

# ── 색상 팔레트 ──────────────────────────────────────────────────────────
PURPLE       = '#534AB7'
TEAL         = '#1D9E75'
AMBER        = '#EF9F27'
LIGHT_PURPLE = '#AFA9EC'
MID_PURPLE   = '#7F77DD'
GRAY         = '#888780'
BG           = '#F8F8F6'

# ── 데이터 로드 & 전처리 ─────────────────────────────────────────────────
df = pd.read_excel("C:\\Users\\melon\\Downloads\\광고_템플릿_데이터셋_정리 (1).xlsx")

def count_buttons(btn_str):
    try:
        return len(json.loads(btn_str))
    except:
        return 0

df['버튼수']       = df['버튼정보'].apply(count_buttons)
df['친구톡_길이']  = df['친구톡 내용'].fillna('').apply(len)
df['대체문자_길이']= df['대체문자 내용'].fillna('').apply(len)

KEYWORDS = ['안내', '견본주택', '홈페이지', '계약', '접수', '입주', '당첨', '방문', '공급', '청약', '신청', '분양', '예약']
kw_counts = {kw: df['친구톡 내용'].fillna('').str.contains(kw).sum() for kw in KEYWORDS}
kw_sorted = dict(sorted(kw_counts.items(), key=lambda x: x[1], reverse=True))

cat_단순 = df[df['템플릿 분류'] == '단순알림(공지)']
cat_광고  = df[df['템플릿 분류'] == '광고']

# ── 레이아웃 ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 12), facecolor='white')
#fig.suptitle('광고 템플릿 데이터셋 EDA', fontsize=20, fontweight='bold',
          #   color='#2C2C2A', y=0.98)

gs = fig.add_gridspec(3, 3, hspace=0.45, wspace=0.35,
                      left=0.07, right=0.97, top=0.93, bottom=0.06)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[0, 2])
ax4 = fig.add_subplot(gs[1, :])
ax5 = fig.add_subplot(gs[2, 0])
ax6 = fig.add_subplot(gs[2, 1])
ax7 = fig.add_subplot(gs[2, 2])

def style_ax(ax, title):
    ax.set_facecolor('#FFFFFF')
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['left', 'bottom']].set_color('#D3D1C7')
    ax.tick_params(colors='#5F5E5A', labelsize=9)
    ax.set_title(title, fontsize=11, fontweight='bold', color='#2C2C2A', pad=10)

# ① 도넛 차트 ─────────────────────────────────────────────────────────────
counts = df['템플릿 분류'].value_counts()
wedges, texts, autotexts = ax1.pie(
    counts,
    labels=counts.index,
    autopct='%1.0f%%',
    colors=[PURPLE, TEAL],
    startangle=90,
    wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2),
    textprops={'fontsize': 9, 'color': '#2C2C2A'}
)
for at in autotexts:
    at.set_fontsize(8)
    at.set_fontweight('bold')
    at.set_color('white')
ax1.set_title('템플릿 분류 비율', fontsize=11, fontweight='bold', color='#2C2C2A', pad=10)

# ② 버튼 수 전체 분포 ──────────────────────────────────────────────────────
btn_counts = df['버튼수'].value_counts().sort_index()
bar_colors = [MID_PURPLE, TEAL, AMBER]
bars = ax2.bar(
    [f'{i}개' for i in btn_counts.index],
    btn_counts.values,
    color=bar_colors[:len(btn_counts)],
    width=0.5, edgecolor='white', linewidth=1.5
)
for bar in bars:
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
             f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='#2C2C2A')
style_ax(ax2, '버튼 수 분포')
ax2.set_ylabel('템플릿 수', fontsize=9, color='#5F5E5A')
ax2.set_ylim(0, btn_counts.max() + 6)
ax2.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

# ③ 분류별 버튼 stacked bar ───────────────────────────────────────────────
cats = ['단순알림(공지)', '광고']
b0 = [len(cat_단순[cat_단순['버튼수']==0]), len(cat_광고[cat_광고['버튼수']==0])]
b1 = [len(cat_단순[cat_단순['버튼수']==1]), len(cat_광고[cat_광고['버튼수']==1])]
b2 = [len(cat_단순[cat_단순['버튼수']==2]), len(cat_광고[cat_광고['버튼수']==2])]

x = np.arange(len(cats))
ax3.bar(x, b0, color=MID_PURPLE, label='버튼 0개', width=0.5, edgecolor='white')
ax3.bar(x, b1, bottom=b0, color=TEAL, label='버튼 1개', width=0.5, edgecolor='white')
ax3.bar(x, b2, bottom=[b0[i]+b1[i] for i in range(2)], color=AMBER, label='버튼 2개', width=0.5, edgecolor='white')
ax3.set_xticks(x)
ax3.set_xticklabels(cats, fontsize=9)
ax3.legend(fontsize=8, framealpha=0.5, loc='upper right')
style_ax(ax3, '분류별 버튼 구성')
ax3.set_ylabel('템플릿 수', fontsize=9, color='#5F5E5A')

# ④ 키워드 빈도 ────────────────────────────────────────────────────────────
kw_labels = list(kw_sorted.keys())
kw_vals   = list(kw_sorted.values())
palette   = [PURPLE if v >= 30 else MID_PURPLE if v >= 20 else LIGHT_PURPLE for v in kw_vals]
bars4 = ax4.barh(kw_labels[::-1], kw_vals[::-1], color=palette[::-1],
                  edgecolor='white', linewidth=1.2, height=0.6)
for bar in bars4:
    w = bar.get_width()
    ax4.text(w + 0.3, bar.get_y() + bar.get_height() / 2,
             f'{int(w)}', va='center', fontsize=10, color='#2C2C2A')
style_ax(ax4, '주요 키워드 등장 빈도 (50개 템플릿 기준)')
ax4.set_xlabel('등장 템플릿 수', fontsize=9, color='#5F5E5A')
ax4.set_xlim(0, max(kw_vals) + 8)
ax4.axvline(x=25, color=GRAY, linestyle='--', linewidth=0.8, alpha=0.6)
ax4.text(25.3, -0.7, '50% 기준선', fontsize=8, color=GRAY)

# ⑤ 친구톡 길이 히스토그램 ────────────────────────────────────────────────
bins = [0, 200, 300, 400, 500, 600, 700]
ax5.hist(cat_단순['친구톡_길이'], bins=bins, color=PURPLE, alpha=0.7, label='단순알림', edgecolor='white')
ax5.hist(cat_광고['친구톡_길이'],  bins=bins, color=TEAL,   alpha=0.7, label='광고',     edgecolor='white')
ax5.axvline(df['친구톡_길이'].mean(), color=AMBER, linestyle='--', linewidth=1.5,
            label=f'평균 {df["친구톡_길이"].mean():.0f}자')
ax5.legend(fontsize=8, framealpha=0.5)
style_ax(ax5, '친구톡 내용 길이 분포')
ax5.set_xlabel('글자 수', fontsize=9, color='#5F5E5A')
ax5.set_ylabel('템플릿 수', fontsize=9, color='#5F5E5A')

# ⑥ 대체문자 길이 히스토그램 ─────────────────────────────────────────────
ax6.hist(cat_단순['대체문자_길이'], bins=bins, color=PURPLE, alpha=0.7, label='단순알림', edgecolor='white')
ax6.hist(cat_광고['대체문자_길이'],  bins=bins, color=TEAL,   alpha=0.7, label='광고',     edgecolor='white')
ax6.axvline(df['대체문자_길이'].mean(), color=AMBER, linestyle='--', linewidth=1.5,
            label=f'평균 {df["대체문자_길이"].mean():.0f}자')
ax6.legend(fontsize=8, framealpha=0.5)
style_ax(ax6, '대체문자 내용 길이 분포')
ax6.set_xlabel('글자 수', fontsize=9, color='#5F5E5A')
ax6.set_ylabel('템플릿 수', fontsize=9, color='#5F5E5A')

# ⑦ 분류별 길이 박스플롯 ──────────────────────────────────────────────────
box_data = [cat_단순['친구톡_길이'].values, cat_광고['친구톡_길이'].values]
bp = ax7.boxplot(box_data, patch_artist=True, widths=0.45,
                 medianprops=dict(color='white', linewidth=2),
                 whiskerprops=dict(color=GRAY, linewidth=1),
                 capprops=dict(color=GRAY, linewidth=1),
                 flierprops=dict(marker='o', color=GRAY, markersize=4, alpha=0.6))
for patch, color in zip(bp['boxes'], [PURPLE, TEAL]):
    patch.set_facecolor(color)
    patch.set_alpha(0.8)
ax7.set_xticks([1, 2])
ax7.set_xticklabels(['단순알림(공지)', '광고'], fontsize=9)
style_ax(ax7, '분류별 친구톡 길이 박스플롯')
ax7.set_ylabel('글자 수', fontsize=9, color='#5F5E5A')

plt.savefig('ad_template_eda.png', dpi=150, bbox_inches='tight', facecolor=BG)
print("저장 완료: ad_template_eda.png")
plt.show()
