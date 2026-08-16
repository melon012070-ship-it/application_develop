import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import platform

# ---------------------------------------------------------
# 1. 폰트 및 기본 설정
# ---------------------------------------------------------
if platform.system() == 'Darwin': # Mac
    plt.rcParams['font.family'] = 'AppleGothic'
else: # Windows
    plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------
# 2. 데이터 불러오기 (파일명이 다르면 수정해주세요)
# ---------------------------------------------------------
file_name ="C:\\Users\\melon\\Downloads\\고객 데이터 셋 (1).xlsx"
try:
    if file_name.endswith('.csv'):
        # CSV 파일인 경우 한글 깨짐 방지 인코딩 적용
        df = pd.read_csv(file_name, encoding='cp949') 
    else:
        # 엑셀 파일인 경우
        df = pd.read_excel(file_name)
    print("✅ 데이터를 성공적으로 불러왔습니다!")
except FileNotFoundError:
    print(f"❌ [에러] '{file_name}' 파일을 찾을 수 없습니다. 파일 이름과 경로를 확인해 주세요.")
except Exception as e:
    # 혹시 cp949로 안 열리는 utf-8 csv인 경우 재시도
    try:
        df = pd.read_csv(file_name, encoding='utf-8')
        print("✅ 데이터를 성공적으로 불러왔습니다!")
    except:
        print(f"❌ [에러] 데이터를 불러오는 중 문제가 발생했습니다: {e}")

# ---------------------------------------------------------
# 3. 전처리 및 세그먼트 분류 함수
# ---------------------------------------------------------
def is_near(region):
    if pd.isna(region): return False
    return any(kw in str(region) for kw in ['오산', '동탄', '세교', '양산동'])

def has_qualification(q):
    if pd.isna(q): return False
    return any(x in str(q) for x in ['1순위', '2순위', '특별공급'])

def get_qualification_type(q):
    if pd.isna(q): return '기타'
    q_str = str(q)
    if '1순위' in q_str or '특별공급' in q_str: return '1순위/특공'
    elif '2순위' in q_str or '무순위' in q_str: return '무순위/2순위'
    return '기타'

def assign_segment(row):
    if str(row.get('마케팅동의여부', '')).strip() != '동의': return '발송 제외'
    
    intent = str(row.get('청약의사', ''))
    qual = str(row.get('청약자격', ''))
    schedule_known = '알고 있다' in str(row.get('분양 일정', ''))
    near = is_near(row.get('나의거주지역', ''))
    
    if '있다' in intent and '조건' not in intent:
        return 'S1' if get_qualification_type(qual) == '1순위/특공' else 'S2'
    elif '조건' in intent:
        return 'S3' if get_qualification_type(qual) == '1순위/특공' else 'S4'
    elif '없다' in intent:
        if has_qualification(qual):
            return 'S5' if schedule_known else ('S5-1' if near else 'S5-2')
        else:
            return 'S6' if schedule_known else ('S6-1' if near else 'S6-2')
    return '분류 불가'

# 세그먼트 할당 및 분석용 데이터셋(발송 제외 제거) 생성
df['세그먼트'] = df.apply(assign_segment, axis=1)
df_analysis = df[df['세그먼트'] != '발송 제외'].copy()
segment_order = sorted(df_analysis['세그먼트'].unique())


# ---------------------------------------------------------
# 4. 데이터 시각화 (논리적 근거 증명용 4종 세트)
# ---------------------------------------------------------

# [1] 세그먼트별 고객 수 분포
plt.figure(figsize=(10, 5))
sns.countplot(data=df_analysis, x='세그먼트', order=segment_order, palette='Set2')
plt.title('세그먼트별 고객 수 분포', fontsize=15)
plt.xlabel('고객 세그먼트')
plt.ylabel('고객 수(명)')
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()

# [2] 세그먼트별 연령대 비율 (근거: S1/S3은 3040 실수요, S2/S4는 5060 투자수요)
age_cross = pd.crosstab(df_analysis['세그먼트'], df_analysis['나이'], normalize='index') * 100
age_cross = age_cross.loc[segment_order]
age_cross.plot(kind='bar', stacked=True, colormap='viridis', figsize=(10, 5))
plt.title('세그먼트별 연령대 비율 ', fontsize=15)
plt.xlabel('고객 세그먼트')
plt.ylabel('비율(%)')
plt.xticks(rotation=0)
plt.legend(title='나이', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# [3] 세그먼트별 성별 비율 (근거: 고관여/청약의사 집단은 여성의 비율이 압도적임)
gender_cross = pd.crosstab(df_analysis['세그먼트'], df_analysis['성별'], normalize='index') * 100
gender_cross = gender_cross.loc[segment_order]
gender_cross.plot(kind='bar', stacked=True, colormap='Pastel1', figsize=(10, 5))
plt.title('세그먼트별 성별 비율 ', fontsize=15)
plt.xlabel('고객 세그먼트')
plt.ylabel('비율(%)')
plt.xticks(rotation=0)
plt.legend(title='성별', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# [4] 세그먼트별 호응도 비율 (근거: 우리가 나눈 세그먼트가 실제 마케팅 반응률과 직결됨)
interest_cross = pd.crosstab(df_analysis['세그먼트'], df_analysis['호응도'], normalize='index') * 100
interest_cross = interest_cross.loc[segment_order]
# 호응도는 순서형이므로 coolwarm 등의 컬러맵이 잘 어울립니다.
interest_cross.plot(kind='bar', stacked=True, colormap='coolwarm', figsize=(10, 5))
plt.title('세그먼트별 호응도 비율 ', fontsize=15)
plt.xlabel('고객 세그먼트')
plt.ylabel('비율(%)')
plt.xticks(rotation=0)
plt.legend(title='호응도', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()