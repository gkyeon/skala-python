"""
==============================================================
실습4 : 시각화 4종 · 통계 검정 · sklearn Pipeline
==============================================================
작성자 : 김하연

설명:
    sales_100k.json 데이터를 활용해 아래 기능을 연습한다.
    1. EDA 시각화 4종
    2. 통계 검정 (t-test, 카이제곱)
    3. sklearn pipeline 구성
    4. plotly 인터랙티브 차트 저장

변경내역:
    2026-07-21  최초 작성
                데이터 불러오기 및 전처리, 그래프 4개 그리기기.
                한글 깨짐 이슈 해결, 그래프 

==============================================================
"""

#=================
'''
#fig, axes = plt.subplots(2, 2)로 서브플롯 구성 — 히스토그램+KDE, 박스플롯, 월별 라인, 상관 히트맵 4종을 각 axes에 개별 출력 (plt.show() 여러 번 X, 하나의 figure로)
서울 vs 부산 평균 매출 차이를 scipy.stats.ttest_ind로 검정, t통계량·p-value 출력 후 p<0.05 여부 해석 주석/코드로 표시
지역×카테고리 분할표(pd.crosstab 등)를 만든 뒤 chi2_contingency로 카이제곱 검정, p-value 출력 및 유의성 해석
전처리(ColumnTransformer) + 모델을 하나로 묶은 Pipeline 구성, fit → predict → score 순서로 실행
학습된 Pipeline을 joblib.dump()로 저장하고, 다시 joblib.load()로 재로딩해 정상 작동 확인
Plotly Express로 지역·카테고리별 총매출 막대 차트 생성 후 fig.write_html()로 .html 파일 저장 (fig.show()만으로 끝내지 않기)'''
#=========================

from pathlib import Path

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import platform

# 데이터는 프로젝트 루트의 data/ 폴더에 모아둠 (실습 03, 실습 04가 같은 데이터를 공유)
# -> 스크립트 위치(실습 04/) 기준 한 단계 위(data-project/)로 올라가서 data/를 찾음
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sales_100k.csv"

# ---- 스타일 (기본) ----
sns.set_style('whitegrid')       # 배경 그리드
sns.set_palette('Set2')          # 색상 팔레트

# ---- 한글 폰트 설정 ----
# 주의: sns.set_style()/set_palette()가 font.family를 'sans-serif'로 되돌리기 때문에
# 반드시 그 뒤에 폰트를 지정해야 한글이 깨지지 않는다 (순서 바꾸면 그래프 한글 다 깨짐)
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':  # Mac
    plt.rcParams['font.family'] = 'AppleGothic'
else:  # Linux (Colab 등)
    plt.rcParams['font.family'] = 'NanumGothic'

plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
plt.rcParams['font.size'] = 11


def print_section(title):
    # 콘솔 출력에 구분선 + 제목을 붙여주는 헬퍼 (가독성용)
    print()
    print('=' * 60)
    print(title)
    print('=' * 60)


#=========================================================
# 0. 데이터 불러오기 및 전처리
#=========================================================

df = pd.read_csv(DATA_PATH)  # 원본 1,000,000행 x 11열

# 데이터 결측치 처리
# 결측치 개수(처리 전 기준): amount 5,000개 / region 10,000개 / category 8,000개
df['amount'] = df['amount'].fillna(df['amount'].median())      # 중앙값 채움 (median = 1,948,270.5)
df['region'] = df['region'].fillna(df['region'].mode()[0])     # 최빈값 채움 (mode = '서울')
df['category'] = df['category'].fillna(df['category'].mode()[0])  # 최빈값 채움 (mode = '가구')

# 필요없는 칼럼 열 제거
# -> 사실 컬럼 제거가 아니라 order_id가 결측인 "행"을 제거하는 코드
#    (이번 데이터엔 order_id 결측이 0건이라 실제로는 아무 행도 지워지지 않음)
df = df.dropna(subset=['order_id'])


# IQR 이상치 처리 (반복문으로 여러 컬럼 처리)
before_count = len(df)  # 이상치 제거 전: 1,000,000행

# IQR 수치형 컬럼을 위한 반복문
# IQR 적용할 수치형 컬럼 목록 (컬럼마다 Q1/Q3/IQR을 따로 계산해야 해서 반복문으로 처리)
iqr_columns = ['quantity', 'unit_price', 'customer_age', 'amount']

mask = pd.Series(True, index=df.index)  # 컬럼별 조건을 AND로 누적 (전부 True인 행만 최종적으로 남음)

# 반복문 자동화
# 컬럼별로 각자 다른 Q1/Q3/IQR 경계를 계산해서 mask에 AND로 누적시킴
for col in iqr_columns:
    Q1 = df[col].quantile(0.25)        # 1사분위수
    Q3 = df[col].quantile(0.75)        # 3사분위수
    IQR = Q3 - Q1                      # 사분위 범위
    lower = Q1 - 1.5 * IQR             # 정상범위 하한
    upper = Q3 + 1.5 * IQR             # 정상범위 상한
    mask &= df[col].between(lower, upper)  # 하나라도 범위를 벗어나면 그 행은 이상치로 간주해 제외

df = df[mask]  # 이상치 제거 적용

after_count = len(df)
removed_count = before_count - after_count

# print_section('[0] 이상치 제거 (IQR) 결과')
# print(f'  제거 전 행 수 : {before_count:>10,}행')
# print(f'  제거 후 행 수 : {after_count:>10,}행')
# print(f'  제거된 행 수  : {removed_count:>10,}행  ({removed_count / before_count:.2%})')
# 실행 결과: 제거 전 1,000,000행 -> 제거 후 978,351행 (제거됨 21,649행, 약 2.16%)

print_section('[0] 기초 정보 (df.info())')
df.info()  # 결측치 처리가 끝났으므로 전 컬럼 Non-Null Count가 978,351로 동일하게 찍힘

#=========================================================
# 1. EDA 시각화
# 2x2 서브 플롯 / 히스토그램,박스블록,월별라인,상관 히트뱁
#=========================================================


df['amount_10k'] = df['amount'] / 10000  # 원 -> 만원 단위 (2, 3번 그래프에서 사용)

# 2x2 서브플롯 하나(fig)에 4개 차트를 각각 axes[행,열]에 그림 -> plt.show()는 마지막에 딱 한 번만 호출
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
fig.suptitle('Sales EDA 시각화', fontsize=16)

# 1. 히스토그램 + KDE (amount 분포 자체를 보는 용도라 원 단위 그대로 사용)
# -> 낮은 금액대에 몰려 있고 오른쪽으로 긴 꼬리를 가진 전형적인 우측 비대칭(오른쪽 꼬리) 분포
sns.histplot(data=df, x='amount', kde=True, ax=axes[0, 0])
axes[0, 0].set_title('Amount 분포 (히스토그램 + KDE)', fontsize=12)

# 2. 박스플롯 (카테고리별 비교이므로 만원 단위로 축소해서 보기 편하게)
# -> 8개 카테고리(전자/의류/식품/가구/스포츠/도서/뷰티/완구) 모두 중앙값·분포가 거의 비슷하게 나옴
#    (category와 amount가 서로 무관하게 생성된 데이터라는 뜻)
sns.boxplot(data=df, x='category', y='amount_10k', ax=axes[0, 1])
axes[0, 1].set_title('Category별 Amount 분포', fontsize=12)
axes[0, 1].set_ylabel('매출액(만원)')
axes[0, 1].tick_params(axis='x', rotation=15)

# 3. 월별 라인
# amount_10k(만원)를 한 달치로 다 더하면 다시 천만 단위(1e7)로 커져서 그대로는 소용없음
# -> 월 "합계"는 억원 단위(원 값을 1억으로 나눔)로 따로 환산해야 눈금이 깔끔하게 나옴
df['month'] = pd.to_datetime(df['order_date']).dt.to_period('M')
monthly = df.groupby('month')['amount'].sum() / 1e8  # 원 -> 억원 단위
# -> 월별 총매출이 대략 1,000억원 안팎에서 등락하며 뚜렷한 상승/하락 추세 없이 유지되는 모습
axes[1, 0].plot(monthly.index.astype(str), monthly.values, marker='o')
axes[1, 0].set_title('월별 총매출 추이', fontsize=12)
axes[1, 0].set_ylabel('총매출(억원)')
axes[1, 0].tick_params(axis='x', rotation=45)

# 4. 상관 히트맵 (상관계수는 단위에 영향받지 않으므로 원 단위 그대로 사용)
# 실행 결과 상관계수:
#   quantity   - amount : 0.624 (수량이 많을수록 금액도 커짐 - 어느 정도 예상되는 관계)
#   unit_price - amount : 0.659 (단가가 높을수록 금액도 커짐 - 역시 자연스러운 관계)
#   customer_age - amount : 0.000 (고객 나이는 매출액과 거의 무관)
#   quantity   - unit_price : -0.016 (거의 무관, 둘은 독립적으로 생성된 값으로 보임)
corr = df[['quantity', 'unit_price', 'customer_age', 'amount']].corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', ax=axes[1, 1])
axes[1, 1].set_title('수치형 변수 상관관계', fontsize=12)

plt.tight_layout()
plt.show()



#===========================================================================
# 2. 통계 검정 — t-test + 카이제곱
#===========================================================================

from scipy import stats
from scipy.stats import chi2_contingency

# --- t-test: 서울 vs 부산 평균 매출 차이 ---
# 두 지역의 amount 값만 각각 뽑아서 두 그룹의 "평균"이 통계적으로 다른지 검정
seoul = df[df['region'] == '서울']['amount']
busan = df[df['region'] == '부산']['amount']

# equal_var=False -> 두 그룹의 분산이 같다고 가정하지 않는 Welch's t-test
# (표본 크기·분산이 다를 수 있는 실제 데이터에는 이 방식이 더 안전함)
t_stat, p_value = stats.ttest_ind(seoul, busan, equal_var=False)
# 실행 결과: 서울 평균 2,470,691원(n=252,014) vs 부산 평균 2,465,320원(n=116,810)
#           t-statistic = 0.7289, p-value = 0.4661
#           -> p >= 0.05 이므로 두 지역 평균 매출 차이는 통계적으로 유의하지 않음
#              (평균 차이가 5천원 남짓으로 작고, 표본이 커도 이 정도 차이는 우연 범위 안에 있다는 뜻)

print_section('[검정 1] t-test: 서울 vs 부산 평균 매출')
print(f'  서울 평균 : {seoul.mean():>15,.0f}원  (n={len(seoul):,})')
print(f'  부산 평균 : {busan.mean():>15,.0f}원  (n={len(busan):,})')
print(f'  t-statistic : {t_stat:.4f}')  # 두 그룹 평균 차이의 크기 (표준오차 대비)
print(f'  p-value     : {p_value:.4f}')  # 이 정도 차이가 우연히 나올 확률

# p-value < 0.05 면 "차이가 우연이 아니다"라고 해석 (유의수준 5% 기준)
if p_value < 0.05:
    print('  -> 유의수준 0.05에서 서울-부산 평균 매출 차이는 통계적으로 유의하다.')
else:
    print('  -> 유의수준 0.05에서 서울-부산 평균 매출 차이는 통계적으로 유의하지 않다.')


# --- 카이제곱: region x category 독립성 검정 ---
# region별로 category가 어떻게 분포하는지 교차표(분할표)를 만듦
# ex) 서울-전자 몇 건, 서울-의류 몇 건, 부산-전자 몇 건 ...
contingency = pd.crosstab(df['region'], df['category'])

# 관측된 분포(contingency)가 "region과 category가 서로 무관하다"는
# 기대 분포(expected)와 얼마나 다른지를 검정
chi2, p_val, dof, expected = chi2_contingency(contingency)
# 실행 결과: chi2 = 76.4768, dof = 49(=7개 region x 8개 category 조합에서 나온 자유도), p-value = 0.0073
#           -> p < 0.05 이므로 region과 category는 통계적으로 유의한 연관성이 있음 (완전 독립은 아님)
#              단, 위 3번 박스플롯에서 카테고리별 매출 자체는 차이가 거의 없었으니
#              "매출액과 관련 있다"가 아니라 "지역별 카테고리 구성 비율에 약간의 차이가 있다" 정도로 해석해야 함

print_section('[검정 2] 카이제곱: region x category 독립성')
print(f'  chi2 statistic : {chi2:.4f}')  # 관측값과 기대값의 차이 크기
print(f'  자유도(dof)     : {dof}')
print(f'  p-value        : {p_val:.4f}')  # 이 정도 차이가 우연히 나올 확률

# p-value < 0.05 면 "region과 category는 서로 관련 있다(독립이 아니다)"로 해석
if p_val < 0.05:
    print('  -> region과 category는 통계적으로 유의한 연관성이 있다 (독립 아님).')
else:
    print('  -> region과 category는 통계적으로 독립이다.')


#===========================================================================
# 3. sklearn Pipeline 구성 + 저장
#===========================================================================

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression
import joblib

# 모델 입력으로 쓸 컬럼 구분: 수치형은 스케일링, 범주형은 인코딩이 필요하므로 따로 관리
numeric_features = ['quantity', 'unit_price', 'customer_age']
categorical_features = ['region', 'category', 'payment_method']

X = df[numeric_features + categorical_features]  # 설명변수(입력)
y = df['amount']                                  # 목표변수(예측 대상)

# 학습용 80% / 테스트용 20%로 분리, random_state 고정으로 재현 가능하게
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 컬럼 종류별로 다른 전처리를 적용하는 ColumnTransformer
# - 수치형: StandardScaler로 평균0/분산1로 표준화 (컬럼 간 스케일 차이 제거)
# - 범주형: OneHotEncoder로 더미변수화, handle_unknown='ignore'로 학습에 없던
#           카테고리가 테스트에 나와도 에러 없이 무시
preprocessor = ColumnTransformer(transformers=[
    ('num', StandardScaler(), numeric_features),
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
])

# 전처리 + 모델을 하나로 묶어서 fit/predict를 한 번에 처리
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('model', LinearRegression()),
])

# 훈련 (여기서 preprocessor가 X_train 기준으로 스케일/인코딩 규칙을 학습하고,
#       그 규칙으로 변환한 데이터를 LinearRegression에 넣어 학습까지 한 번에 수행)
pipeline.fit(X_train, y_train)


# 평가 (score()는 회귀모델 기준 R^2 값을 반환: 1에 가까울수록 설명력이 높음)
r2_score = pipeline.score(X_test, y_test)
# 실행 결과: R^2 = 0.8375
# -> quantity/unit_price/customer_age + region/category/payment_method 만으로
#    테스트셋 amount 분산의 약 83.75%를 설명함. 위 히트맵에서 quantity·unit_price가
#    amount와 상관 0.6대였던 걸 감안하면 납득 가능한 수준의 설명력

print_section('[Pipeline] 학습 결과')
print(f'  R^2 score : {r2_score:.4f}')

# 저장 (전처리 규칙 + 학습된 모델 파라미터를 통째로 파일에 직렬화)
joblib.dump(pipeline, 'sales_pipeline.pkl')
print('  모델 저장 완료 : sales_pipeline.pkl')

# 재로딩 확인 (다시 불러온 pipeline이 방금 학습한 것과 동일하게 동작하는지 검증)
loaded_pipeline = joblib.load('sales_pipeline.pkl')
reloaded_r2 = loaded_pipeline.score(X_test, y_test)
print(f'  재로딩 후 R^2 score : {reloaded_r2:.4f}  (일치: {reloaded_r2 == r2_score})')


#===========================================================================
# 4. Plotly 인터랙티브 차트 저장
#===========================================================================

import plotly.express as px

# region, category별 총매출 집계 (막대 차트에 바로 쓸 수 있는 long-format으로 정리)
# region 8개 x category 8개 = 64행짜리 표가 만들어짐 (region_category_sales.shape == (64, 3))
region_category_sales = (
    df.groupby(['region', 'category'], as_index=False)['amount']
    .sum()
    .rename(columns={'amount': 'total_sales'})
)

# region을 x축, category를 색상으로 구분해서 지역 안에서 카테고리별 매출을 비교
fig = px.bar(
    region_category_sales,
    x='region',
    y='total_sales',
    color='category',
    barmode='group',   # 카테고리 막대를 쌓지 않고 옆으로 나란히 배치
    title='지역·카테고리별 총매출',
)

# fig.show()만 하면 매번 실행할 때마다 다시 그려야 하므로,
# 인터랙티브 HTML로 저장해서 브라우저에서 언제든 다시 열어볼 수 있게 함
fig.write_html('region_category_sales.html')

print_section('[Plotly] 차트 저장 완료')
print('  파일 : region_category_sales.html')
