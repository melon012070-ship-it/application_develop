"""
세그먼트 분류 근거 분석 코드
────────────────────────────
분석 1: 나이 × 세그먼트
분석 2: 성별 × 세그먼트
분석 3: S5/S6 근거리·원거리 분포
분석 4: S3/S4 관심사 서브세그먼트
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import platform, warnings
warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════
# 0. 한글 폰트 설정
# ══════════════════════════════════════════════
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    candidates = [f.name for f in fm.fontManager.ttflist
                  if any(k in f.name for k in ['Nanum', 'Gothic', 'Malgun', 'CJK'])]
    if candidates:
        plt.rcParams['font.family'] = candidates[0]
plt.rcParams['axes.unicode_minus'] = False

# ══════════════════════════════════════════════
# 1. 데이터 로드
# ══════════════════════════════════════════════
df = pd.read_excel("C:\\Users\\melon\\Downloads\\고객 데이터 셋 (1).xlsx")

# ══════════════════════════════════════════════
# 2. 전처리 함수 정의
# ══════════════════════════════════════════════
def map_자격(v):
    v = str(v)
    if '1순위' in v:    return '1순위'
    if '특별공급' in v:  return '특별공급'
    if '2순위' in v:    return '2순위'
    if '무순위' in v:   return '무순위'
    return '기타'

def map_의사(v):
    v = str(v).strip()
    if v == '있다':  return '있다'
    if v == '없다':  return '없다'
    if '조건' in v:  return '조건부'
    return '기타'

# 근거리 기준: 오산 / 동탄 / 세교 / 양산동 포함 지역
NEAR_KEYWORDS = ['오산', '동탄', '세교', '양산동']
def map_거리(v):
    return '근거리' if any(k in str(v) for k in NEAR_KEYWORDS) else '원거리'

# 장점(관심사) → 서브코드 매핑 (첫 번째 매칭 기준)
INTEREST_MAP = {
    '브랜드': '0', '교육': '1', '교통': '2',
    '생활권': '3', '미래가치': '4', '자연환경': '5', '대출': '6'
}
INTEREST_LABEL = {
    '0': '브랜드', '1': '교육', '2': '교통',
    '3': '생활권', '4': '미래가치', '5': '자연환경', '6': '대출'
}
def map_관심코드(v):
    for kw, code in INTEREST_MAP.items():
        if kw in str(v):
            return code
    return '0'

# ══════════════════════════════════════════════
# 3. 파생 컬럼 생성
# ══════════════════════════════════════════════
df['자격그룹'] = df['청약자격'].apply(map_자격)
df['의사그룹'] = df['청약의사'].apply(map_의사)
df['핵심자격'] = df['자격그룹'].isin(['1순위', '특별공급'])
df['거리']    = df['나의거주지역'].apply(map_거리)
df['관심코드'] = df['장점'].apply(map_관심코드)

def assign_segment(row):
    if row['마케팅동의여부'] == '거부':
        return '거부'
    의사 = row['의사그룹']
    자격 = row['자격그룹']
    코드 = row['관심코드']
    거리 = row['거리'][0]  # '근' or '원'

    if 의사 == '있다':
        return 'S1' if row['핵심자격'] else 'S2'

    elif 의사 == '조건부':
        prefix = 'S3' if row['핵심자격'] else 'S4'
        return f'{prefix}-{코드}'

    elif 의사 == '없다':
        has_qual = 자격 in ['1순위', '특별공급', '2순위']
        knows_schedule = '알고' in str(row['분양 일정'])
        if has_qual:
            return 'S5' if knows_schedule else f'S5-{거리}'
        else:
            return 'S6' if knows_schedule else f'S6-{거리}'
    return '기타'

df['세그먼트'] = df.apply(assign_segment, axis=1)

# 분석용: 거부 제외
dv = df[df['세그먼트'] != '거부'].copy()

# ══════════════════════════════════════════════
# 공통 스타일
# ══════════════════════════════════════════════
AGE_ORDER = ['20대', '30대', '40대', '50대', '60대 이상']
INTENT_COLORS = {'있다': '#185FA5', '조건부': '#3B6D11', '없다': '#B4B2A9'}

def add_bar_labels(ax, bars_data, bottoms, threshold=4, text_color='white'):
    """100% stacked bar 위 퍼센트 레이블"""
    for i, (val, bot) in enumerate(zip(bars_data, bottoms)):
        if val >= threshold:
            ax.text(bot + val / 2, i, f'{val:.1f}%',
                    ha='center', va='center', fontsize=8.5,
                    color=text_color, fontweight='bold')

def style_ax(ax):
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(labelsize=10)


# ══════════════════════════════════════════════
# 분석 1: 나이 × 세그먼트
# ══════════════════════════════════════════════
fig1, axes = plt.subplots(1, 2, figsize=(17, 6))
fig1.suptitle('나이 × 세그먼트 분석', fontsize=15, fontweight='bold')

# ── 1-1 나이별 청약의사 비율 ────────────────────
ax = axes[0]
ct = pd.crosstab(dv['나이'], dv['의사그룹']).reindex(AGE_ORDER)
ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100
bottom = np.zeros(len(ct_pct))
for col in ['있다', '조건부', '없다']:
    if col not in ct_pct: continue
    vals = ct_pct[col].values
    ax.barh(ct_pct.index, vals, left=bottom,
            color=INTENT_COLORS[col], label=col, height=0.6)
    add_bar_labels(ax, vals, bottom,
                   text_color='white' if col != '없다' else '#444')
    bottom += vals

ax.set_xlim(0, 100)
ax.set_xlabel('비율 (%)', fontsize=11)
ax.set_title('나이별 청약의사 비율', fontsize=12, pad=10)
ax.legend(fontsize=10, framealpha=0.8)
style_ax(ax)

# ── 1-2 나이별 청약자격 비율 ─────────────────────
ax2 = axes[1]
QUAL_ORDER  = ['1순위', '특별공급', '2순위', '무순위']
QUAL_COLORS = {'1순위': '#185FA5', '특별공급': '#73726c',
               '2순위': '#3B6D11', '무순위': '#E24B4A'}
ct2 = pd.crosstab(dv['나이'], dv['자격그룹']).reindex(AGE_ORDER)
ct2_pct = ct2.div(ct2.sum(axis=1), axis=0) * 100
bottom2 = np.zeros(len(ct2_pct))
for col in QUAL_ORDER:
    if col not in ct2_pct: continue
    vals = ct2_pct[col].values
    ax2.barh(ct2_pct.index, vals, left=bottom2,
             color=QUAL_COLORS[col], label=col, height=0.6)
    add_bar_labels(ax2, vals, bottom2)
    bottom2 += vals

# 핵심자격(1순위+특공) 구분선
ax2.axvline(0, color='none')
ax2.set_xlim(0, 100)
ax2.set_xlabel('비율 (%)', fontsize=11)
ax2.set_title('나이별 청약자격 비율', fontsize=12, pad=10)
ax2.legend(fontsize=10, framealpha=0.8)

# 핵심자격 합계 주석
for i, age in enumerate(AGE_ORDER):
    core = ct2_pct.loc[age, ['1순위','특별공급']].sum() if age in ct2_pct.index else 0
    ax2.text(101, i, f'핵심 {core:.0f}%', va='center', fontsize=8, color='#185FA5')

style_ax(ax2)

plt.tight_layout()
plt.savefig('나이x세그먼트.png', dpi=150, bbox_inches='tight')
plt.close()
print('저장 완료: 나이x세그먼트.png')


# ══════════════════════════════════════════════
# 분석 2: 성별 × 세그먼트
# ══════════════════════════════════════════════
# 표시할 대표 세그먼트 (서브세그먼트 합산)
dv2 = dv.copy()
dv2['세그먼트_대표'] = dv2['세그먼트'].apply(
    lambda x: x.split('-')[0] if x.startswith(('S3','S4')) else
              ('S5-근거리' if x == 'S5-근' else
               'S5-원거리' if x == 'S5-원' else
               'S6-근거리' if x == 'S6-근' else
               'S6-원거리' if x == 'S6-원' else x)
)
SEG_REPR_ORDER = ['S1','S2','S3','S4','S5','S5-근거리','S5-원거리','S6','S6-근거리','S6-원거리']
SEG_COLORS_REPR = {
    'S1':'#185FA5','S2':'#378ADD',
    'S3':'#3B6D11','S4':'#639922',
    'S5':'#854F0B','S5-근거리':'#BA7517','S5-원거리':'#E8A44A',
    'S6':'#A32D2D','S6-근거리':'#E24B4A','S6-원거리':'#F09595'
}

fig2, axes2 = plt.subplots(1, 2, figsize=(17, 7))
fig2.suptitle('성별 × 세그먼트 분석', fontsize=15, fontweight='bold')

# ── 2-1 세그먼트별 성별 구성비 ───────────────────
ax3 = axes2[0]
GENDER_COLORS = {'남자': '#378ADD', '여자': '#D85A30'}
ct3 = pd.crosstab(dv2['세그먼트_대표'], dv2['성별'])
ct3 = ct3.reindex([s for s in SEG_REPR_ORDER if s in ct3.index])
ct3_pct = ct3.div(ct3.sum(axis=1), axis=0) * 100
bottom3 = np.zeros(len(ct3_pct))
for g in ['남자', '여자']:
    if g not in ct3_pct: continue
    vals = ct3_pct[g].values
    ax3.barh(ct3_pct.index, vals, left=bottom3,
             color=GENDER_COLORS[g], label=g, height=0.65)
    for i, (val, bot) in enumerate(zip(vals, bottom3)):
        if val >= 8:
            ax3.text(bot + val / 2, i, f'{val:.0f}%',
                     ha='center', va='center', fontsize=8.5,
                     color='white', fontweight='bold')
    bottom3 += vals

ax3.axvline(50, color='#555', linewidth=0.9, linestyle='--', alpha=0.5, label='50% 기준선')
ax3.set_xlim(0, 100)
ax3.set_xlabel('비율 (%)', fontsize=11)
ax3.set_title('세그먼트별 성별 구성비', fontsize=12, pad=10)
ax3.legend(fontsize=10, framealpha=0.8)
style_ax(ax3)

# ── 2-2 성별 청약의사 비율 ───────────────────────
ax4 = axes2[1]
ct4 = pd.crosstab(dv['성별'], dv['의사그룹'])
ct4_pct = ct4.div(ct4.sum(axis=1), axis=0) * 100
bottom4 = np.zeros(len(ct4_pct))
for col in ['있다', '조건부', '없다']:
    if col not in ct4_pct: continue
    vals = ct4_pct[col].values
    ax4.barh(ct4_pct.index, vals, left=bottom4,
             color=INTENT_COLORS[col], label=col, height=0.5)
    add_bar_labels(ax4, vals, bottom4,
                   text_color='white' if col != '없다' else '#444')
    bottom4 += vals

ax4.set_xlim(0, 100)
ax4.set_xlabel('비율 (%)', fontsize=11)
ax4.set_title('성별 청약의사 비율', fontsize=12, pad=10)
ax4.legend(fontsize=10, framealpha=0.8)
style_ax(ax4)

plt.tight_layout()
plt.savefig('성별x세그먼트.png', dpi=150, bbox_inches='tight')
plt.close()
print('저장 완료: 성별x세그먼트.png')


# ══════════════════════════════════════════════
# 분석 3: S5 / S6 근거리·원거리 분포
# ══════════════════════════════════════════════
fig3, axes3 = plt.subplots(1, 2, figsize=(16, 5))
fig3.suptitle('S5 / S6 세그먼트: 근거리 vs 원거리 분포', fontsize=14, fontweight='bold')

DIST_COLORS = {'근거리': '#185FA5', '원거리': '#E24B4A'}

for ax_i, (prefix, title) in enumerate(zip(['S5','S6'], ['S5 잠재수요','S6 저관심'])):
    ax = axes3[ax_i]

    # 미인지자(근거리/원거리) + 인지자 3개 그룹
    sub = dv[dv['세그먼트'].str.startswith(prefix)].copy()
    sub['그룹'] = sub['세그먼트'].map({
        prefix: f'{prefix} 인지자',
        f'{prefix}-근': f'{prefix}-1 근거리',
        f'{prefix}-원': f'{prefix}-2 원거리'
    })
    counts = sub['그룹'].value_counts().reindex(
        [f'{prefix} 인지자', f'{prefix}-1 근거리', f'{prefix}-2 원거리'], fill_value=0
    )
    colors = ['#73726c', DIST_COLORS['근거리'], DIST_COLORS['원거리']]
    bars = ax.barh(counts.index, counts.values, color=colors, height=0.55)

    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_width() + 30, bar.get_y() + bar.get_height()/2,
                f'{val:,}명 ({val/len(sub)*100:.1f}%)',
                va='center', fontsize=10, color='#333')

    ax.set_xlabel('고객 수 (명)', fontsize=11)
    ax.set_title(f'{title} 세부 분포 (총 {len(sub):,}명)', fontsize=12, pad=10)
    ax.set_xlim(0, counts.max() * 1.45)
    style_ax(ax)

    # 근거리/원거리 지역 설명 텍스트
    ax.text(0.98, 0.04,
            '근거리: 오산·동탄·세교·양산동\n원거리: 그 외 경기·서울 등',
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=8.5, color='#888',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='#ddd', alpha=0.8))

plt.tight_layout()
plt.savefig('S5S6_근거리원거리.png', dpi=150, bbox_inches='tight')
plt.close()
print('저장 완료: S5S6_근거리원거리.png')


# ══════════════════════════════════════════════
# 분석 4: S3 / S4 관심사 서브세그먼트
# ══════════════════════════════════════════════
fig4, axes4 = plt.subplots(1, 2, figsize=(16, 6))
fig4.suptitle('S3 / S4 세그먼트: 관심사(장점) 서브세그먼트 분포', fontsize=14, fontweight='bold')

SUB_COLORS = ['#185FA5','#3B6D11','#854F0B','#D85A30','#A32D2D','#1D9E75','#7F77DD']
SUB_LABELS = {'0':'브랜드','1':'교육','2':'교통','3':'생활권','4':'미래가치','5':'자연환경','6':'대출'}

for ax_i, prefix in enumerate(['S3','S4']):
    ax = axes4[ax_i]
    sub = dv[dv['세그먼트'].str.startswith(prefix)].copy()
    sub['서브'] = sub['세그먼트'].str.split('-').str[1]
    counts = sub['서브'].value_counts().reindex(
        [str(i) for i in range(7)], fill_value=0
    )
    labels = [f"{SUB_LABELS[k]}\n({prefix}-{k})" for k in counts.index]
    colors_used = SUB_COLORS[:len(counts)]

    bars = ax.barh(labels, counts.values, color=colors_used, height=0.6)
    for bar, val in zip(bars, counts.values):
        if val > 0:
            ax.text(bar.get_width() + 8, bar.get_y() + bar.get_height()/2,
                    f'{val:,}명 ({val/len(sub)*100:.1f}%)',
                    va='center', fontsize=9.5, color='#333')

    ax.set_xlabel('고객 수 (명)', fontsize=11)
    seg_name = '조건부 핵심(1순위/특공)' if prefix=='S3' else '조건부 탐색(무순위/2순위)'
    ax.set_title(f'{prefix} {seg_name}\n총 {len(sub):,}명', fontsize=11, pad=10)
    ax.set_xlim(0, counts.max() * 1.5)
    style_ax(ax)

plt.tight_layout()
plt.savefig('S3S4_관심사.png', dpi=150, bbox_inches='tight')
plt.close()
print('저장 완료: S3S4_관심사.png')

print('\n✓ 전체 분석 완료! 생성된 파일:')
print('  - 나이x세그먼트.png')
print('  - 성별x세그먼트.png')
print('  - S5S6_근거리원거리.png')
print('  - S3S4_관심사.png')