import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib import rcParams
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
#rcParams['font.family'] = 'AppleGothic'  # Mac
rcParams['font.family'] = 'Malgun Gothic'  # Windows
# rcParams['font.family'] = 'NanumGothic'  # Linux
rcParams['axes.unicode_minus'] = False

# ─────────────────────────────────────────────
# 데이터 로드 & 전처리
# ─────────────────────────────────────────────
df = pd.read_excel("C:\\Users\\melon\\Downloads\\고객 데이터 셋 (1).xlsx")

near = ['오산 기타', '세교1, 내심미동', '세교2', '동탄1', '동탄2', '양산동, 외삼미동']
df['지역구분'] = df['나의거주지역'].apply(lambda x: '근거리' if x in near else '원거리')

def clean_intent(x):
    x = str(x)
    if x == '있다': return '청약 있다'
    if x == '없다': return '청약 없다'
    return '조건부 청약'

df['청약의사_구분'] = df['청약의사'].apply(clean_intent)

def clean_qual(x):
    if '특별공급' in str(x): return '특별공급'
    if str(x) in ['무순위', '1순위', '2순위']: return x
    return '기타'

df['청약자격_구분'] = df['청약자격'].apply(clean_qual)

# 색상 팔레트
C_BLUE   = '#2563EB'
C_SKY    = '#60A5FA'
C_GRAY   = '#D1D5DB'
C_PURPLE = '#7C3AED'
C_LPURP  = '#C4B5FD'
C_GREEN  = '#059669'
C_AMBER  = '#D97706'

INTENT_COLORS = {'청약 있다': C_BLUE, '조건부 청약': C_SKY, '청약 없다': C_GRAY}
QUAL_COLORS   = {'1순위': C_PURPLE, '2순위': C_LPURP, '무순위': '#A78BFA', '특별공급': C_AMBER, '기타': C_GRAY}

# ─────────────────────────────────────────────
# Figure 1: 4대 핵심 지표
# ─────────────────────────────────────────────
fig1, axes = plt.subplots(2, 2, figsize=(14, 10))
fig1.suptitle('고객 데이터 EDA — 핵심 4대 지표', fontsize=18, fontweight='bold', y=0.98)
plt.subplots_adjust(hspace=0.4, wspace=0.35)

# 1) 청약의사 분포
ax = axes[0, 0]
intent_cnt = df['청약의사_구분'].value_counts().reindex(['청약 없다', '조건부 청약', '청약 있다'])
colors = [INTENT_COLORS[k] for k in intent_cnt.index]
bars = ax.barh(intent_cnt.index, intent_cnt.values, color=colors, height=0.5, edgecolor='white')
for bar, val in zip(bars, intent_cnt.values):
    pct = val / len(df) * 100
    ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
            f'{val:,}명 ({pct:.1f}%)', va='center', fontsize=10)
ax.set_title('청약의사 분포', fontsize=13, fontweight='bold', pad=10)
ax.set_xlabel('응답자 수')
ax.set_xlim(0, 9000)
ax.spines[['top','right']].set_visible(False)
ax.tick_params(left=False)

# 2) 청약자격 분포
ax = axes[0, 1]
qual_cnt = df['청약자격_구분'].value_counts().reindex(['무순위', '1순위', '2순위', '특별공급', '기타'])
qual_cnt = qual_cnt.dropna()
colors = [QUAL_COLORS[k] for k in qual_cnt.index]
bars = ax.barh(qual_cnt.index, qual_cnt.values, color=colors, height=0.5, edgecolor='white')
for bar, val in zip(bars, qual_cnt.values):
    pct = val / len(df) * 100
    ax.text(bar.get_width() + 30, bar.get_y() + bar.get_height()/2,
            f'{val:,}명 ({pct:.1f}%)', va='center', fontsize=10)
ax.set_title('청약자격 분포', fontsize=13, fontweight='bold', pad=10)
ax.set_xlabel('응답자 수')
ax.set_xlim(0, 6500)
ax.spines[['top','right']].set_visible(False)
ax.tick_params(left=False)

# 3) 분양일정 인지 현황
ax = axes[1, 0]
schedule_cnt = df['분양 일정'].value_counts()
labels = ['알고 있다', '몰랐다']
vals   = [schedule_cnt.get('알고 있다.', 0), schedule_cnt.get('몰랐다.', 0)]
colors = [C_GREEN, C_GRAY]
wedges, texts, autotexts = ax.pie(
    vals, labels=labels, colors=colors,
    autopct='%1.1f%%', startangle=90,
    wedgeprops={'edgecolor': 'white', 'linewidth': 2},
    textprops={'fontsize': 11}
)
for at in autotexts:
    at.set_fontweight('bold')
    at.set_fontsize(12)
ax.set_title('분양일정 인지 현황', fontsize=13, fontweight='bold', pad=10)
# 수치 추가
ax.text(0, -1.45, f'알고 있다: {vals[0]:,}명  |  몰랐다: {vals[1]:,}명',
        ha='center', fontsize=10, color="#000000")

# 4) 거주지역 분포
ax = axes[1, 1]
region_cnt = df['지역구분'].value_counts()
colors = [C_PURPLE, C_GRAY]
wedges, texts, autotexts = ax.pie(
    region_cnt.values, labels=region_cnt.index, colors=colors,
    autopct='%1.1f%%', startangle=90,
    wedgeprops={'edgecolor': 'white', 'linewidth': 2},
    textprops={'fontsize': 11}
)
for at in autotexts:
    at.set_fontweight('bold')
    at.set_fontsize(12)
ax.set_title('거주지역 분포 (근거리 vs 원거리)', fontsize=13, fontweight='bold', pad=10)
ax.text(0, -1.45,
        '근거리: 오산·동탄·세교·양산동  |  원거리: 그 외',
        ha='center', fontsize=9, color="#01040A")

plt.savefig('EDA_1_핵심4대지표.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
print("✅ EDA_1_핵심4대지표.png 저장 완료")


'''
# ─────────────────────────────────────────────
# Figure 2: 크로스탭 분석
# ─────────────────────────────────────────────
fig2, axes = plt.subplots(1, 2, figsize=(16, 6))
fig2.suptitle('고객 데이터 EDA — 크로스탭 분석', fontsize=18, fontweight='bold', y=1.01)
plt.subplots_adjust(wspace=0.4)

# 1) 지역구분 × 청약의사 (100% 누적 막대)
ax = axes[0]
ct = pd.crosstab(df['지역구분'], df['청약의사_구분'])
ct = ct[['청약 없다', '조건부 청약', '청약 있다']]
ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

bottom = np.zeros(len(ct_pct))
for col in ct_pct.columns:
    vals = ct_pct[col].values
    bars = ax.bar(ct_pct.index, vals, bottom=bottom,
                  color=INTENT_COLORS[col], edgecolor='white', linewidth=0.5, label=col)
    for i, (bar, v) in enumerate(zip(bars, vals)):
        if v > 4:
            ax.text(bar.get_x() + bar.get_width()/2,
                    bottom[i] + v/2,
                    f'{v:.1f}%', ha='center', va='center',
                    fontsize=10, fontweight='bold', color='white')
    bottom += vals

ax.set_title('지역구분 × 청약의사 비율', fontsize=13, fontweight='bold')
ax.set_ylabel('비율 (%)')
ax.set_ylim(0, 110)
ax.legend(loc='upper right', fontsize=9)
ax.spines[['top','right']].set_visible(False)

# 실제 인원 수 표시
for i, region in enumerate(ct_pct.index):
    total = ct.loc[region].sum()
    ax.text(i, 102, f'n={total:,}', ha='center', fontsize=10, color='#374151', fontweight='bold')

# 2) 분양일정 인지 × 청약의사
ax = axes[1]
ct2 = pd.crosstab(df['분양 일정'], df['청약의사_구분'])
ct2 = ct2[['청약 없다', '조건부 청약', '청약 있다']]
ct2.index = ['알고 있다', '몰랐다']
ct2_pct = ct2.div(ct2.sum(axis=1), axis=0) * 100

bottom = np.zeros(len(ct2_pct))
for col in ct2_pct.columns:
    vals = ct2_pct[col].values
    bars = ax.bar(ct2_pct.index, vals, bottom=bottom,
                  color=INTENT_COLORS[col], edgecolor='white', linewidth=0.5, label=col)
    for i, (bar, v) in enumerate(zip(bars, vals)):
        if v > 4:
            ax.text(bar.get_x() + bar.get_width()/2,
                    bottom[i] + v/2,
                    f'{v:.1f}%', ha='center', va='center',
                    fontsize=10, fontweight='bold', color='white')
    bottom += vals

ax.set_title('분양일정 인지 × 청약의사 비율', fontsize=13, fontweight='bold')
ax.set_ylabel('비율 (%)')
ax.set_ylim(0, 110)
ax.legend(loc='upper right', fontsize=9)
ax.spines[['top','right']].set_visible(False)

for i, idx in enumerate(ct2_pct.index):
    total = ct2.loc[idx].sum()
    ax.text(i, 102, f'n={total:,}', ha='center', fontsize=10, color='#374151', fontweight='bold')

plt.savefig('EDA_2_크로스탭분석.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
print("✅ EDA_2_크로스탭분석.png 저장 완료")
'''

# ─────────────────────────────────────────────
# Figure 3: 청약자격별 청약의사 + 근거리 세부지역
# ─────────────────────────────────────────────
fig3, axes = plt.subplots(1, 2, figsize=(16, 6))
fig3.suptitle('고객 데이터 EDA — 자격별·지역별 세부 분석', fontsize=18, fontweight='bold', y=1.01)
plt.subplots_adjust(wspace=0.4, bottom=0.18)

# 1) 청약자격 × 청약의사
ax = axes[0]
ct3 = pd.crosstab(df['청약자격_구분'], df['청약의사_구분'])
ct3 = ct3[['청약 없다', '조건부 청약', '청약 있다']]
order = ['무순위', '1순위', '2순위', '특별공급']
ct3 = ct3.reindex([o for o in order if o in ct3.index])
ct3_pct = ct3.div(ct3.sum(axis=1), axis=0) * 100

bottom = np.zeros(len(ct3_pct))
for col in ct3_pct.columns:
    vals = ct3_pct[col].values
    bars = ax.barh(ct3_pct.index, vals, left=bottom,
                   color=INTENT_COLORS[col], edgecolor='white', linewidth=0.5, label=col, height=0.5)
    for i, (bar, v) in enumerate(zip(bars, vals)):
        if v > 5:
            ax.text(bottom[i] + v/2, bar.get_y() + bar.get_height()/2,
                    f'{v:.1f}%', ha='center', va='center',
                    fontsize=9, fontweight='bold', color='white')
    bottom += vals

ax.set_title('청약자격별 청약의사 비율', fontsize=13, fontweight='bold')
ax.set_xlabel('비율 (%)')
ax.set_xlim(0, 115)
ax.legend(loc='upper left', bbox_to_anchor=(0, -0.15), ncol=3, fontsize=9,
          frameon=True, framealpha=0.9, edgecolor='#E5E7EB')
ax.spines[['top','right']].set_visible(False)

for i, idx in enumerate(ct3_pct.index):
    total = ct3.loc[idx].sum()
    ax.text(102, i, f'n={total:,}', va='center', fontsize=9, color='#374151', fontweight='bold')

# 2) 근거리 세부지역 분포
ax = axes[1]
near_df = df[df['지역구분'] == '근거리']
region_detail = near_df['나의거주지역'].value_counts()
colors_region = [C_PURPLE, '#7C3AED', '#8B5CF6', '#A78BFA', '#C4B5FD', '#DDD6FE']
bars = ax.barh(region_detail.index[::-1], region_detail.values[::-1],
               color=colors_region[::-1], height=0.5, edgecolor='white')
for bar, val in zip(bars, region_detail.values[::-1]):
    pct = val / len(near_df) * 100
    ax.text(bar.get_width() + 20, bar.get_y() + bar.get_height()/2,
            f'{val:,}명 ({pct:.1f}%)', va='center', fontsize=10)
ax.set_title('근거리 세부지역 분포', fontsize=13, fontweight='bold')
ax.set_xlabel('응답자 수')
ax.set_xlim(0, 4800)
ax.spines[['top','right']].set_visible(False)
ax.tick_params(left=False)

plt.savefig('EDA_3_자격별_지역별분석.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
print("✅ EDA_3_자격별_지역별분석.png 저장 완료")

'''
# ─────────────────────────────────────────────
# Figure 4: 구매목적 + 연령대
# ─────────────────────────────────────────────
fig4, axes = plt.subplots(1, 2, figsize=(14, 6))
fig4.suptitle('고객 데이터 EDA — 구매목적 & 연령대', fontsize=18, fontweight='bold', y=1.01)
plt.subplots_adjust(wspace=0.4)

# 구매목적
ax = axes[0]
purpose_cnt = df['구매목적'].value_counts()
colors_p = [C_GREEN, '#34D399', C_GRAY, '#6EE7B7', '#A7F3D0']
bars = ax.barh(purpose_cnt.index[::-1], purpose_cnt.values[::-1],
               color=colors_p[:len(purpose_cnt)][::-1], height=0.5, edgecolor='white')
for bar, val in zip(bars, purpose_cnt.values[::-1]):
    pct = val / len(df) * 100
    ax.text(bar.get_width() + 30, bar.get_y() + bar.get_height()/2,
            f'{val:,}명 ({pct:.1f}%)', va='center', fontsize=10)
ax.set_title('구매목적 분포', fontsize=13, fontweight='bold')
ax.set_xlabel('응답자 수')
ax.set_xlim(0, 7500)
ax.spines[['top','right']].set_visible(False)
ax.tick_params(left=False)

# 연령대
ax = axes[1]
age_cnt = df['나이'].value_counts().reindex(['20대', '30대', '40대', '50대', '60대 이상'])
age_cnt = age_cnt.dropna()
colors_a = ['#BFDBFE', '#93C5FD', '#60A5FA', C_BLUE, '#1D4ED8']
bars = ax.bar(age_cnt.index, age_cnt.values,
              color=colors_a[:len(age_cnt)], edgecolor='white', linewidth=0.5)
for bar, val in zip(bars, age_cnt.values):
    pct = val / len(df) * 100
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 30,
            f'{val:,}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=10)
ax.set_title('연령대 분포', fontsize=13, fontweight='bold')
ax.set_ylabel('응답자 수')
ax.set_ylim(0, 4500)
ax.spines[['top','right']].set_visible(False)

plt.savefig('EDA_4_구매목적_연령대.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
print("✅ EDA_4_구매목적_연령대.png 저장 완료")
'''

print("\n🎉 전체 EDA 완료! PNG 4장이 저장되었습니다.")
