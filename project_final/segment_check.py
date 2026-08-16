import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import numpy as np
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
import matplotlib
matplotlib.rcParams['axes.unicode_minus'] = False

import platform
import matplotlib.font_manager as fm

def set_korean_font():
    os_name = platform.system()
    if os_name == 'Windows':
        plt.rcParams['font.family'] = 'Gulim' 
    elif os_name == 'Darwin':
        plt.rcParams['font.family'] = 'AppleGothic'
    else:
        # Linux: NanumGothic 설치 필요 (pip install koreanize-matplotlib)
        try:
            import koreanize_matplotlib
        except ImportError:
            pass

set_korean_font()

# ─── 데이터 로드 & 세그먼트 분류 ─────────────────────────────────────────────
df = pd.read_excel("C:\\Users\\melon\\Downloads\\고객 데이터 셋 (1).xlsx")

근거리_지역 = ['오산', '세교', '동탄', '양산동']

def is_근거리(지역):
    if pd.isna(지역): return False
    return any(k in str(지역) for k in 근거리_지역)

def classify_segment(row):
    동의 = row['마케팅동의여부']
    의사 = row['청약의사']
    자격 = row['청약자격']
    일정 = row['분양 일정']
    지역 = row['나의거주지역']
    목적장점 = str(row['장점']) + str(row['구매목적'])

    if 동의 != '동의':
        return '발송제외'
    if 의사 == '있다':
        if 자격 in ['1순위', '특별공급(신혼부부)', '특별공급(다자녀가구)', '특별공급(생애최초)', '특별공급(기관추천)', '특별공급(노부모부양)']:
            return 'S1'
        else:
            return 'S2'
    elif '조건' in str(의사):
        q = 자격 in ['1순위', '특별공급(신혼부부)', '특별공급(다자녀가구)', '특별공급(생애최초)', '특별공급(기관추천)', '특별공급(노부모부양)']
        prefix = 'S3' if q else 'S4'
        if '브랜드' in 목적장점: return f'{prefix}-0'
        elif '교육' in 목적장점: return f'{prefix}-1'
        elif '교통' in 목적장점: return f'{prefix}-2'
        elif '생활권' in 목적장점 or '생활' in str(row['장점']): return f'{prefix}-3'
        elif '미래' in 목적장점: return f'{prefix}-4'
        elif '자연' in 목적장점: return f'{prefix}-5'
        elif '대출' in 목적장점: return f'{prefix}-6'
        else: return f'{prefix}-0'
    else:
        has_자격 = 자격 in ['1순위', '2순위', '특별공급(신혼부부)', '특별공급(다자녀가구)', '특별공급(생애최초)', '특별공급(기관추천)', '특별공급(노부모부양)']
        if has_자격:
            if 일정 == '알고 있다.': return 'S5'
            return 'S5-1' if is_근거리(지역) else 'S5-2'
        else:
            if 일정 == '알고 있다.': return 'S6'
            return 'S6-1' if is_근거리(지역) else 'S6-2'

df['세그먼트'] = df.apply(classify_segment, axis=1)

# ─── 색상 팔레트 ─────────────────────────────────────────────────────────────
SEG_COLORS = {
    'S1':   '#C0392B', 'S2':   '#E74C3C',
    'S3-0': '#8E44AD', 'S3-1': '#9B59B6', 'S3-2': '#A569BD',
    'S3-3': '#BB8FCE', 'S3-4': '#D2B4DE', 'S3-5': '#E8DAEF', 'S3-6': '#F4ECF7',
    'S4-0': '#1A5276', 'S4-1': '#2980B9', 'S4-2': '#5DADE2',
    'S4-3': '#85C1E9', 'S4-4': '#AED6F1', 'S4-5': '#D6EAF8', 'S4-6': '#EBF5FB',
    'S5':   '#1E8449', 'S5-1': '#27AE60', 'S5-2': '#58D68D',
    'S6':   '#B7950B', 'S6-1': '#F1C40F', 'S6-2': '#F9E79F',
    '발송제외': '#95A5A6',
}

GROUP_COLORS = {
    'S1/S2 (즉시청약)': '#C0392B',
    'S3 (조건부핵심)': '#8E44AD',
    'S4 (조건부탐색)': '#2980B9',
    'S5 (잠재수요)':   '#1E8449',
    'S6 (저관심)':     '#F1C40F',
    '발송제외':        '#95A5A6',
}

def seg_to_group(s):
    if s in ('S1','S2'): return 'S1/S2 (즉시청약)'
    if s.startswith('S3'): return 'S3 (조건부핵심)'
    if s.startswith('S4'): return 'S4 (조건부탐색)'
    if s.startswith('S5'): return 'S5 (잠재수요)'
    if s.startswith('S6'): return 'S6 (저관심)'
    return '발송제외'

df['그룹'] = df['세그먼트'].apply(seg_to_group)
seg_counts = df['세그먼트'].value_counts()
group_counts = df['그룹'].value_counts()

# 발송 대상만
send_df = df[df['세그먼트'] != '발송제외']


# ══════════════════════════════════════════════════════════════════════════════
# 차트 1 : 전체 세그먼트 분포 - 도넛 + 바 차트 콤보
# ══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 8))
fig.patch.set_facecolor('#F8F9FA')
fig.suptitle('고객 세그먼트 전체 분포', fontsize=20, fontweight='bold', y=1.01)

# 왼쪽: 도넛 - 그룹별
ax1 = axes[0]
gc = group_counts.reindex(['S1/S2 (즉시청약)', 'S3 (조건부핵심)', 'S4 (조건부탐색)',
                            'S5 (잠재수요)', 'S6 (저관심)', '발송제외']).dropna()
colors_g = [GROUP_COLORS[g] for g in gc.index]
wedges, texts, autotexts = ax1.pie(
    gc.values, labels=None, colors=colors_g,
    autopct=lambda p: f'{p:.1f}%' if p > 2 else '',
    pctdistance=0.75, startangle=90,
    wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2)
)
for at in autotexts:
    at.set_fontsize(10); at.set_fontweight('bold'); at.set_color('white')
ax1.set_title('그룹별 비율', fontsize=14, fontweight='bold', pad=15)
legend_patches = [mpatches.Patch(color=GROUP_COLORS[g], label=f'{g}\n({gc[g]:,}명)')
                  for g in gc.index]
ax1.legend(handles=legend_patches, loc='lower center', bbox_to_anchor=(0.5, -0.22),
           ncol=2, fontsize=9, framealpha=0.8)
ax1.text(0, 0, f'총\n{len(df):,}명', ha='center', va='center',
         fontsize=13, fontweight='bold', color='#2C3E50')

# 오른쪽: 수평 바 - 세부 세그먼트
ax2 = axes[1]
seg_order = ['S1','S2','S3-0','S3-1','S3-2','S3-3','S3-4','S3-5','S3-6',
             'S4-0','S4-1','S4-2','S4-3','S4-4','S4-5','S4-6',
             'S5','S5-1','S5-2','S6','S6-1','S6-2','발송제외']
seg_order = [s for s in seg_order if s in seg_counts.index]
vals = [seg_counts.get(s, 0) for s in seg_order]
colors_s = [SEG_COLORS.get(s, '#BDC3C7') for s in seg_order]

bars = ax2.barh(seg_order, vals, color=colors_s, edgecolor='white', linewidth=0.5, height=0.7)
for bar, v in zip(bars, vals):
    ax2.text(bar.get_width() + 20, bar.get_y() + bar.get_height()/2,
             f'{v:,}', va='center', fontsize=9, color='#2C3E50')
ax2.set_xlim(0, max(vals)*1.18)
ax2.set_xlabel('고객 수', fontsize=11)
ax2.set_title('세부 세그먼트별 인원', fontsize=14, fontweight='bold', pad=15)
ax2.set_facecolor('#F8F9FA')
ax2.spines[['top','right']].set_visible(False)
ax2.grid(axis='x', alpha=0.3)
ax2.invert_yaxis()

plt.tight_layout()
plt.savefig('01_전체_세그먼트_분포.png', dpi=150, bbox_inches='tight',
            facecolor='#F8F9FA')
plt.close()
print("✅ 차트1 저장 완료")


# ══════════════════════════════════════════════════════════════════════════════
# 차트 2 : 핵심 고객 (S1/S2) 상세 - 연령·성별·지역·평형
# ══════════════════════════════════════════════════════════════════════════════
core_df = df[df['세그먼트'].isin(['S1','S2'])].copy()

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.patch.set_facecolor('#FFF5F5')
fig.suptitle('S1/S2 핵심 고객 (즉시 청약 의사) 상세 분석\n총 146명', 
             fontsize=18, fontweight='bold', color='#C0392B')

# 연령 분포
ax = axes[0,0]
age_order = ['10대','20대','30대','40대','50대','60대 이상']
age_cnt = core_df['나이'].value_counts().reindex(age_order).fillna(0)
bars = ax.bar(age_cnt.index, age_cnt.values, color='#E74C3C', edgecolor='white', linewidth=1.5)
for bar, v in zip(bars, age_cnt.values):
    if v > 0:
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, f'{int(v)}명',
                ha='center', fontsize=10, fontweight='bold', color='#C0392B')
ax.set_title('연령대 분포', fontsize=13, fontweight='bold')
ax.set_facecolor('#FFF5F5'); ax.spines[['top','right']].set_visible(False)
ax.set_ylabel('인원수')

# S1 vs S2 비율
ax = axes[0,1]
s12 = core_df['세그먼트'].value_counts()
labels = [f'S1\n즉시청약 핵심\n(1순위/특공)\n{s12.get("S1",0)}명',
          f'S2\n즉시청약 일반\n(무순위/2순위)\n{s12.get("S2",0)}명']
colors12 = ['#C0392B','#E74C3C']
wedges, texts, autotexts = ax.pie(
    [s12.get('S1',0), s12.get('S2',0)], labels=labels,
    colors=colors12, autopct='%1.1f%%', pctdistance=0.6,
    wedgeprops=dict(edgecolor='white', linewidth=2), startangle=90
)
for at in autotexts: at.set_color('white'); at.set_fontweight('bold')
ax.set_title('S1 vs S2 구성', fontsize=13, fontweight='bold')

# 성별
ax = axes[1,0]
gender_cnt = core_df['성별'].value_counts()
colors_gen = ['#3498DB','#E91E63']
wedges, texts, autotexts = ax.pie(
    gender_cnt.values, labels=[f'{g}\n{v}명' for g,v in gender_cnt.items()],
    colors=colors_gen[:len(gender_cnt)], autopct='%1.1f%%',
    wedgeprops=dict(edgecolor='white', linewidth=2), startangle=90
)
for at in autotexts: at.set_fontweight('bold')
ax.set_title('성별 구성', fontsize=13, fontweight='bold')

# 선호 평형
ax = axes[1,1]
평형_cnt = core_df['선호하는 평형'].value_counts().head(6)
colors_p = plt.cm.Reds(np.linspace(0.4, 0.9, len(평형_cnt)))
bars = ax.barh(평형_cnt.index, 평형_cnt.values, color=colors_p, edgecolor='white')
for bar, v in zip(bars, 평형_cnt.values):
    ax.text(bar.get_width()+0.3, bar.get_y()+bar.get_height()/2,
            f'{v}명', va='center', fontsize=10, color='#C0392B')
ax.set_title('선호 평형', fontsize=13, fontweight='bold')
ax.set_facecolor('#FFF5F5'); ax.spines[['top','right']].set_visible(False)
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('02_S1S2_핵심고객_상세.png', dpi=150, bbox_inches='tight',
            facecolor='#FFF5F5')
plt.close()
print("✅ 차트2 저장 완료")


# ══════════════════════════════════════════════════════════════════════════════
# 차트 3 : 조건부 고객 (S3/S4) - 관심사별 세분화 비교 (파이+바 콤보)
# ══════════════════════════════════════════════════════════════════════════════
interest_labels = ['브랜드', '교육', '교통', '생활권', '미래가치', '자연환경', '대출']

s3_colors = ['#9B59B6','#A569BD','#BB8FCE','#C39BD3','#D2B4DE','#E8DAEF','#F4ECF7']
s4_colors = ['#2980B9','#3498DB','#5DADE2','#7FB3D3','#AED6F1','#D6EAF8','#EBF5FB']

s3_vals = [seg_counts.get(f'S3-{i}', 0) for i in range(7)]
s4_vals = [seg_counts.get(f'S4-{i}', 0) for i in range(7)]
s3_total = sum(s3_vals)
s4_total = sum(s4_vals)

fig = plt.figure(figsize=(18, 15))
fig.patch.set_facecolor('#F8F4FD')
fig.suptitle('S3/S4 조건부 고객 관심사 분포 비교', fontsize=22, fontweight='bold', y=0.98)

# 파이: 위쪽, 바: 아래쪽 — 충분한 간격 확보
ax_pie_s3 = fig.add_axes([0.04, 0.52, 0.42, 0.42])
ax_pie_s4 = fig.add_axes([0.54, 0.52, 0.42, 0.42])
ax_bar_s3 = fig.add_axes([0.06, 0.05, 0.38, 0.38])
ax_bar_s4 = fig.add_axes([0.56, 0.05, 0.38, 0.38])

def draw_simple_pie(ax, vals, colors, total, title, title_color, bg):
    ax.set_facecolor(bg)
    brand_val = vals[0]
    others_val = sum(vals[1:])
    wedges, texts, autotexts = ax.pie(
        [brand_val, others_val],
        colors=[colors[0], '#D5D8DC'],
        autopct='%1.1f%%',
        pctdistance=0.65,
        startangle=90,
        wedgeprops=dict(edgecolor='white', linewidth=3),
        textprops=dict(fontsize=14)
    )
    autotexts[0].set_color('white'); autotexts[0].set_fontweight('bold'); autotexts[0].set_fontsize(16)
    autotexts[1].set_color('#2C3E50'); autotexts[1].set_fontweight('bold'); autotexts[1].set_fontsize(14)
    # 범례를 파이 하단 여백에 표시 (y값을 -1.2/-1.38로 타이트하게)
    ax.text(0, -1.20, f'■ 브랜드  {brand_val:,}명 ({brand_val/total*100:.1f}%)',
            ha='center', fontsize=12, color=colors[0], fontweight='bold')
    ax.text(0, -1.38, f'■ 기타 관심사  {others_val:,}명 ({others_val/total*100:.1f}%)',
            ha='center', fontsize=12, color='#7F8C8D', fontweight='bold')
    ax.set_title(f'{title}\n(총 {total:,}명)', fontsize=14, fontweight='bold',
                 color=title_color, pad=12)

def draw_bar(ax, vals, colors, total, title, title_color, bg):
    ax.set_facecolor(bg)
    y = np.arange(len(interest_labels))
    bars = ax.barh(y, vals, color=colors, edgecolor='white', linewidth=1.2, height=0.65)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_width() + max(vals)*0.01, bar.get_y() + bar.get_height()/2,
                f'{v:,}명  {v/total*100:.1f}%',
                va='center', ha='left', fontsize=11, color='#2C3E50', fontweight='bold')
    ax.set_yticks(y)
    ax.set_yticklabels(interest_labels, fontsize=12, fontweight='bold')
    ax.set_xlim(0, max(vals) * 1.32)
    ax.set_xlabel('인원 수', fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold', color=title_color, pad=10)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.invert_yaxis()

draw_simple_pie(ax_pie_s3, s3_vals, s3_colors, s3_total,
                'S3 조건부 핵심고객\n(1순위/특별공급)', '#6C3483', '#F5EEF8')
draw_simple_pie(ax_pie_s4, s4_vals, s4_colors, s4_total,
                'S4 조건부 탐색고객\n(무순위/2순위)', '#1A5276', '#EBF5FB')
draw_bar(ax_bar_s3, s3_vals, s3_colors, s3_total, '관심사별 세부 인원', '#6C3483', '#F9F5FD')
draw_bar(ax_bar_s4, s4_vals, s4_colors, s4_total, '관심사별 세부 인원', '#1A5276', '#EEF6FC')

fig.add_artist(plt.Line2D([0.03, 0.97], [0.49, 0.49], transform=fig.transFigure,
                           color='#BDC3C7', linewidth=1.2, linestyle='--'))

plt.savefig('03_S3S4_관심사_분포.png', dpi=150, bbox_inches='tight', facecolor='#F8F4FD')
plt.close()
print("✅ 차트3 저장 완료")


# ══════════════════════════════════════════════════════════════════════════════
# 차트 4 : S5/S6 잠재·저관심 고객 - 근거리/원거리/인지 비교
# ══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 8))
fig.patch.set_facecolor('#EAF7EF')
fig.suptitle('S5/S6 잠재·저관심 고객 세분화 (근거리·원거리·인지 여부)', 
             fontsize=18, fontweight='bold', color='#1A5631')

for ax, segs, labels, title, colors, base_color in [
    (axes[0],
     ['S5', 'S5-1', 'S5-2'],
     ['S5\n인지형 잠재수요', 'S5-1\n잠재수요-근거리', 'S5-2\n잠재수요-원거리'],
     'S5 잠재수요 (자격 있음)', ['#1E8449','#27AE60','#58D68D'], '#1E8449'),
    (axes[1],
     ['S6', 'S6-1', 'S6-2'],
     ['S6\n인지형 저관심', 'S6-1\n저관심-근거리', 'S6-2\n저관심-원거리'],
     'S6 저관심 (자격 없음)', ['#B7950B','#F1C40F','#F9E79F'], '#B7950B'),
]:
    vals = [seg_counts.get(s, 0) for s in segs]
    total = sum(vals)
    bars = ax.bar(labels, vals, color=colors, edgecolor='white', linewidth=2, width=0.55)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+15,
                f'{v:,}명\n({v/total*100:.1f}%)', ha='center', fontsize=11, fontweight='bold',
                color='#2C3E50')
    ax.set_title(f'{title}\n(총 {total:,}명)', fontsize=13, fontweight='bold', color=base_color)
    ax.set_ylim(0, max(vals)*1.25)
    ax.set_facecolor('#EAF7EF')
    ax.spines[['top','right']].set_visible(False)
    ax.set_ylabel('인원 수')

plt.tight_layout()
plt.savefig('04_S5S6_근거리원거리_분포.png', dpi=150, bbox_inches='tight',
            facecolor='#EAF7EF')
plt.close()
print("✅ 차트4 저장 완료")

print("\n🎉 모든 시각화 완료! /mnt/user-data/outputs/ 에 저장되었습니다.")
