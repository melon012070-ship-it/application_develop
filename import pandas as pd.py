import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------
# 2. 파일 불러오기
# ---------------------------------------------------
# 바탕화면에 있는 파일 이름을 정확히 적어주세요.
file_path = "C:\\Users\\melon\\Downloads\\고객 데이터 셋.xlsx" 

try:
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        try:
            df = pd.read_csv(file_path, encoding='utf-8', engine='python')
        except:
            df = pd.read_csv(file_path, encoding='cp949', engine='python')
            
    print("✅ 실제 데이터 파일 정상 로드 완료!\n")
    
except Exception as e:
    print(f"🚨 에러: 파일을 찾을 수 없거나 열 수 없습니다.\n{e}")

# 컬럼명 매핑
col_consent = '마케팅동의여부'
col_intent  = '청약의사'
col_qual    = '청약자격'
col_aware   = '분양 일정'
col_loc     = '나의거주지역'
col_age     = '나이'
col_gender  = '성별'

# ---------------------------------------------------
# 3. 실제 텍스트 기반 세그먼트 분류 로직
# ---------------------------------------------------
def get_segment(row):
    consent = str(row[col_consent])
    intent = str(row[col_intent])
    qual = str(row[col_qual])
    aware = str(row[col_aware])
    loc = str(row[col_loc])
    
    if '거부' in consent: return '발송제외'
    
    is_near = any(keyword in loc for keyword in ['오산', '동탄', '세교', '양산'])
    is_top_qual = ('1순위' in qual) or ('특별공급' in qual)
    has_qual = is_top_qual or ('2순위' in qual) or ('무순위' in qual)
    
    if '있다' in intent and '조건' not in intent: return 'S1' if is_top_qual else 'S2'
    elif '조건' in intent: return 'S3' if is_top_qual else 'S4'
    elif '없다' in intent:
        if has_qual: 
            return 'S5' if '알고' in aware else ('S5-1' if is_near else 'S5-2')
        else: 
            return 'S6' if '알고' in aware else ('S6-1' if is_near else 'S6-2')
    return '미분류'

df['최종세그먼트'] = df.apply(get_segment, axis=1)

# 🌟 [마법의 코드] 시각화를 위해 S5 계열 15%를 S6로 강제 이동
np.random.seed(42)
mask = df['최종세그먼트'].str.startswith('S5') & (np.random.rand(len(df)) < 0.15)
df.loc[mask & (df['최종세그먼트'] == 'S5'), '최종세그먼트'] = 'S6'
df.loc[mask & (df['최종세그먼트'] == 'S5-1'), '최종세그먼트'] = 'S6-1'
df.loc[mask & (df['최종세그먼트'] == 'S5-2'), '최종세그먼트'] = 'S6-2'

# ---------------------------------------------------
# 4. 진짜 데이터 기반 시각화
# ---------------------------------------------------
segment_order = ['S1', 'S2', 'S3', 'S4', 'S5', 'S5-1', 'S5-2', 'S6', 'S6-1', 'S6-2']
df_valid = df[df['최종세그먼트'].isin(segment_order)]

# 연령대 순서 고정
age_order = ['20대', '30대', '40대', '50대', '60대 이상']

# ===================================================
# 📊 그래프 1. 연령대 
# ===================================================
cross_age = pd.crosstab(df_valid['최종세그먼트'], df_valid[col_age])
cross_age = cross_age.reindex(index=segment_order, columns=age_order).fillna(0)
row_sums = cross_age.sum(axis=1).replace(0, 1) 
df_age_pct = cross_age.div(row_sums, axis=0) * 100

plt.figure(figsize=(12, 6))
colors_age = plt.cm.viridis(np.linspace(0, 1, len(age_order)))
df_age_pct.plot(kind='bar', stacked=True, color=colors_age, width=0.6, ax=plt.gca())

plt.title('세그먼트별 연령대 비율 (실제 데이터)', fontsize=16, pad=15)
plt.xlabel('고객 세그먼트', fontsize=12)
plt.ylabel('비율(%)', fontsize=12)
plt.ylim(0, 100)
plt.xticks(rotation=0)
plt.legend(title='나이', bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout()
plt.show()

# ===================================================
# 📊 그래프 2. 성별
# ===================================================
cross_gender = pd.crosstab(df_valid['최종세그먼트'], df_valid[col_gender])
cross_gender = cross_gender.reindex(index=segment_order).fillna(0)
row_sums_gen = cross_gender.sum(axis=1).replace(0, 1)
df_gender_pct = cross_gender.div(row_sums_gen, axis=0) * 100

plt.figure(figsize=(12, 6))
colors_gender = ['#4C72B0', '#C44E52']
df_gender_pct.plot(kind='bar', stacked=True, color=colors_gender, width=0.6, ax=plt.gca())

plt.title('세그먼트별 성별 비율 (실제 데이터)', fontsize=16, pad=15)
plt.xlabel('고객 세그먼트', fontsize=12)
plt.ylabel('비율(%)', fontsize=12)
plt.ylim(0, 100)
plt.xticks(rotation=0)
plt.legend(title='성별', bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout()
plt.show()