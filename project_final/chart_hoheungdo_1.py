import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import warnings
from matplotlib import rcParams
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.rcParams['axes.unicode_minus'] = False

# 폰트 설정
rcParams['font.family'] = 'Malgun Gothic'  # Windows
# rcParams['font.family'] = 'NanumGothic'  # Linux
rcParams['axes.unicode_minus'] = False

# ── 데이터 로드 ───────────────────────────────────────────
df = pd.read_excel("C:\\Users\\melon\\Downloads\\고객 데이터 셋 (1).xlsx")

heungdo_order  = ['A', 'B', 'C', 'D', 'S']
heungdo_colors = {'A': '#C0392B', 'B': '#E67E22', 'C': '#3498DB', 'D': '#95A5A6', 'S': '#8E44AD'}
heungdo_labels = {
    'A': 'A등급\n(최고관심)',
    'B': 'B등급\n(관심)',
    'C': 'C등급\n(보통)',
    'D': 'D등급\n(낮음)',
    'S': 'S등급\n(특수)'
}

counts = df['호응도'].value_counts().reindex(heungdo_order).fillna(0).astype(int)
total  = counts.sum()
pcts   = counts / total * 100

# ── 레이아웃 ──────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18, 7))
fig.patch.set_facecolor('#F8F9FA')
fig.suptitle('호응도 분포 현황', fontsize=22, fontweight='bold', color='#2C3E50', y=1.02)

# ── 차트1: 도넛 ───────────────────────────────────────────
ax1 = axes[0]
colors = [heungdo_colors[h] for h in heungdo_order]
wedges, texts, autotexts = ax1.pie(
    counts.values, colors=colors,
    autopct=lambda p: f'{p:.1f}%' if p > 0.3 else '',
    pctdistance=0.78, startangle=90,
    wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2.5)
)
for at in autotexts:
    at.set_fontsize(10); at.set_fontweight('bold'); at.set_color('white')

ax1.text(0, 0, f'총\n{total:,}명', ha='center', va='center',
         fontsize=13, fontweight='bold', color='#2C3E50')
ax1.set_title('전체 호응도 비율', fontsize=14, fontweight='bold', pad=15)

patches = [plt.matplotlib.patches.Patch(
               color=heungdo_colors[h],
               label=f'{heungdo_labels[h].replace(chr(10)," ")}  {counts[h]:,}명 ({pcts[h]:.1f}%)')
           for h in heungdo_order]
ax1.legend(handles=patches, loc='lower center', bbox_to_anchor=(0.5, -0.22),
           fontsize=9, framealpha=0.9, ncol=2)

# ── 차트2: 수직 바차트 (절대 인원) ────────────────────────
ax2 = axes[1]
x = np.arange(len(heungdo_order))
bars = ax2.bar(x, counts.values, color=colors, edgecolor='white', linewidth=2, width=0.6)
for bar, v, p in zip(bars, counts.values, pcts.values):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
             f'{v:,}명\n({p:.1f}%)', ha='center', va='bottom',
             fontsize=10, fontweight='bold', color='#2C3E50')

ax2.set_xticks(x)
ax2.set_xticklabels([heungdo_labels[h] for h in heungdo_order], fontsize=10)
ax2.set_ylabel('인원 수 (명)', fontsize=11)
ax2.set_title('등급별 절대 인원', fontsize=14, fontweight='bold', pad=15)
ax2.set_facecolor('#F8F9FA')
ax2.spines[['top', 'right']].set_visible(False)
ax2.grid(axis='y', alpha=0.3, linestyle='--')
ax2.set_ylim(0, max(counts.values) * 1.22)

# ── 차트3: A·B 확대 바 ────────────────────────────────────
ax3 = axes[2]
ab_order  = ['A', 'B']
ab_counts = counts[ab_order]
ab_pcts   = pcts[ab_order]
ab_colors = [heungdo_colors[h] for h in ab_order]
x2 = np.arange(len(ab_order))
bars2 = ax3.bar(x2, ab_counts.values, color=ab_colors,
                edgecolor='white', linewidth=2, width=0.45)
for bar, v, p in zip(bars2, ab_counts.values, ab_pcts.values):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
             f'{v:,}명\n({p:.2f}%)', ha='center', va='bottom',
             fontsize=12, fontweight='bold', color='#2C3E50')

ax3.set_xticks(x2)
ax3.set_xticklabels([heungdo_labels[h] for h in ab_order], fontsize=11)
ax3.set_ylabel('인원 수 (명)', fontsize=11)
ax3.set_title('A·B등급 확대\n(핵심 관심 고객)', fontsize=14, fontweight='bold', pad=15)
ax3.set_facecolor('#FFF5F5')
ax3.spines[['top', 'right']].set_visible(False)
ax3.grid(axis='y', alpha=0.3, linestyle='--')
ax3.set_ylim(0, max(ab_counts.values) * 1.3)

ab_total = ab_counts.sum()
ax3.text(0.5, max(ab_counts.values) * 1.18,
         f'A+B 합계: {ab_total:,}명 ({ab_total/total*100:.1f}%)',
         ha='center', fontsize=11, fontweight='bold', color='#C0392B',
         transform=ax3.transData,
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#FADBD8',
                   edgecolor='#C0392B', alpha=0.8))

plt.tight_layout()
plt.savefig('11_호응도_분포.png', dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
plt.close()
print("✅ 저장 완료: 11_호응도_분포.png")
