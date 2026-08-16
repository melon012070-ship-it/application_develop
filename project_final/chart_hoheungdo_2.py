import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from matplotlib import rcParams

import matplotlib
matplotlib.rcParams['axes.unicode_minus'] = False

# 폰트 설정
rcParams['font.family'] = 'Malgun Gothic'  # Windows
# rcParams['font.family'] = 'NanumGothic'  # Linux
rcParams['axes.unicode_minus'] = False

# ── 데이터 로드 & 세그먼트 분류 ──────────────────────────────
df = pd.read_excel("C:\\Users\\melon\\Downloads\\고객 데이터 셋 (1).xlsx")

근거리_지역 = ['오산', '세교', '동탄', '양산동']
def is_근거리(지역):
    if pd.isna(지역): return False
    return any(k in str(지역) for k in 근거리_지역)

def classify_segment(row):
    동의=row['마케팅동의여부']; 의사=row['청약의사']; 자격=row['청약자격']
    일정=row['분양 일정']; 지역=row['나의거주지역']; 목적장점=str(row['장점'])+str(row['구매목적'])
    if 동의!='동의': return '발송제외'
    if 의사=='있다':
        return 'S1' if 자격 in ['1순위','특별공급(신혼부부)','특별공급(다자녀가구)','특별공급(생애최초)','특별공급(기관추천)','특별공급(노부모부양)'] else 'S2'
    elif '조건' in str(의사):
        q=자격 in ['1순위','특별공급(신혼부부)','특별공급(다자녀가구)','특별공급(생애최초)','특별공급(기관추천)','특별공급(노부모부양)']
        p='S3' if q else 'S4'
        if '브랜드' in 목적장점: return f'{p}-0'
        elif '교육' in 목적장점: return f'{p}-1'
        elif '교통' in 목적장점: return f'{p}-2'
        elif '생활권' in 목적장점 or '생활' in str(row['장점']): return f'{p}-3'
        elif '미래' in 목적장점: return f'{p}-4'
        elif '자연' in 목적장점: return f'{p}-5'
        elif '대출' in 목적장점: return f'{p}-6'
        else: return f'{p}-0'
    else:
        has=자격 in ['1순위','2순위','특별공급(신혼부부)','특별공급(다자녀가구)','특별공급(생애최초)','특별공급(기관추천)','특별공급(노부모부양)']
        if has: return 'S5' if 일정=='알고 있다.' else ('S5-1' if is_근거리(지역) else 'S5-2')
        else: return 'S6' if 일정=='알고 있다.' else ('S6-1' if is_근거리(지역) else 'S6-2')

df['세그먼트'] = df.apply(classify_segment, axis=1)
def seg_to_group(s):
    if s in ('S1','S2'): return 'S1/S2\n(즉시청약)'
    if s.startswith('S3'): return 'S3\n(조건부핵심)'
    if s.startswith('S4'): return 'S4\n(조건부탐색)'
    if s.startswith('S5'): return 'S5\n(잠재수요)'
    if s.startswith('S6'): return 'S6\n(저관심)'
    return '발송제외'
df['그룹'] = df['세그먼트'].apply(seg_to_group)

send = df[df['세그먼트'] != '발송제외'].copy()
group_order   = ['S1/S2\n(즉시청약)', 'S3\n(조건부핵심)', 'S4\n(조건부탐색)', 'S5\n(잠재수요)', 'S6\n(저관심)']
heungdo_order = ['A', 'B', 'C', 'D', 'S']
heungdo_colors = {'A': '#C0392B', 'B': '#E67E22', 'C': '#3498DB', 'D': '#95A5A6', 'S': '#8E44AD'}
heungdo_labels = {'A': 'A (최고관심)', 'B': 'B (관심)', 'C': 'C (보통)', 'D': 'D (낮음)', 'S': 'S (특수)'}

ct     = pd.crosstab(send['그룹'], send['호응도'])
ct     = ct.reindex(index=group_order, columns=[h for h in heungdo_order if h in ct.columns], fill_value=0)
ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

# ── 레이아웃: 1번(위) + 2번(아래) ────────────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
fig.patch.set_facecolor('#F8F9FA')
#fig.suptitle('세그먼트별 호응도 분포\n— 분류 기준의 관심도 반영 검증 —',
#             fontsize=20, fontweight='bold', color='#2C3E50', y=1.01)

# ── ① 100% 누적 가로바 ───────────────────────────────────────
bottom = np.zeros(len(group_order))
for h in [c for c in heungdo_order if c in ct_pct.columns]:
    vals = ct_pct[h].values
    bars = ax1.barh(group_order, vals, left=bottom,
                    color=heungdo_colors[h], edgecolor='white', linewidth=0.8,
                    label=heungdo_labels[h], height=0.55)
    for bar, v, b in zip(bars, vals, bottom):
        if v > 2:
            ax1.text(b + v/2, bar.get_y() + bar.get_height()/2,
                     f'{v:.1f}%', ha='center', va='center',
                     fontsize=10, fontweight='bold', color='white')
    bottom += vals

ax1.set_xlim(0, 100)
ax1.set_xlabel('비율 (%)', fontsize=11)
ax1.set_title('세그먼트별 호응도 구성 비율 (100% 기준)', fontsize=14, fontweight='bold', pad=12)
ax1.legend(loc='lower right', fontsize=10, ncol=5, framealpha=0.9)
ax1.set_facecolor('#F8F9FA')
ax1.spines[['top', 'right']].set_visible(False)
ax1.invert_yaxis()
ax1.tick_params(axis='y', labelsize=11)

# ── ② A+B 비율 꺾은선 ────────────────────────────────────────
ab_pct = []
for g in group_order:
    a = ct_pct.loc[g, 'A'] if 'A' in ct_pct.columns else 0
    b = ct_pct.loc[g, 'B'] if 'B' in ct_pct.columns else 0
    ab_pct.append(a + b)

x = np.arange(len(group_order))
ax2.plot(x, ab_pct, 'o-', color='#C0392B', linewidth=2.5, markersize=12, zorder=3)
for xi, v in zip(x, ab_pct):
    offset = max(ab_pct) * 0.13
    ax2.text(xi, v + offset, f'{v:.1f}%', ha='center', fontsize=12,
             fontweight='bold', color='#C0392B', zorder=5,
             bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                       edgecolor='#C0392B', linewidth=1.8, alpha=1.0))
ax2.fill_between(x, ab_pct, alpha=0.12, color='#C0392B')
ax2.set_xticks(x)
ax2.set_xticklabels(group_order, fontsize=11)
ax2.set_ylabel('비율 (%)', fontsize=11)
ax2.set_title('A+B 등급 합산 비율 (핵심 관심 고객 비율)', fontsize=14, fontweight='bold', pad=12)
ax2.set_ylim(0, max(ab_pct) * 1.65)
ax2.set_facecolor('#FFF8F8')
ax2.spines[['top', 'right']].set_visible(False)
ax2.grid(axis='y', alpha=0.3, linestyle='--')
ax2.axhline(y=np.mean(ab_pct), color='gray', linestyle=':', linewidth=1.2, alpha=0.7)
ax2.text(len(group_order) - 0.05, np.mean(ab_pct) + 0.5, f'평균 {np.mean(ab_pct):.1f}%',
         fontsize=9, color='gray', ha='right')

plt.tight_layout(pad=2.5)
plt.savefig('10_호응도_세그먼트_1_2.png', dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
plt.close()
print("✅ 저장 완료: 10_호응도_세그먼트_1_2.png")
