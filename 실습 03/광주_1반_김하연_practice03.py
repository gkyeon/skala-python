"""
==============================================================
실습3 : 판다스 EDA, Polars Lazy API, DuckDB SQL, 성능 비교
==============================================================
작성자 : 김하연

설명:
    sales_100k.json 데이터를 활용해 아래 기능을 연습한다.
    1. 파일 로딩 + 기본 EDA, 이상치 제거
    2. Pandas groupby named aggregation
    3. Polars Lazy API 활용 동일 집계 작성
    4. DuckDB 동일집계 작성 및 성능 비교

변경내역:
    2026-07-21  최초 작성
                1,2,3 단계 작성 (하단에 이전 코드 보존)
    2026-07-21  Polars/DuckDB도 pandas와 동일한 결측치 채움값·IQR 경계를
                적용하도록 수정 (원본 CSV부터 매번 동일 전처리 재현).
                timeit 비교를 위해 3개 도구 파이프라인을 함수로 분리.
                기존 코드는 삭제하지 않고 주석 처리하여 하단에 보존.
==============================================================
"""

from pathlib import Path

import pandas as pd
import polars as pl
import duckdb
import timeit

# 데이터는 프로젝트 루트의 data/ 폴더에 모아둠 (실습 03, 실습 04가 같은 데이터를 공유)
# -> 스크립트 위치(실습 03/) 기준 한 단계 위(data-project/)로 올라가서 data/를 찾음
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sales_100k.csv"


def print_section(title):
    # 콘솔 출력에 구분선 + 제목을 붙여주는 헬퍼 (가독성용)
    print()
    print('=' * 60)
    print(title)
    print('=' * 60)


#=========================================================
# 0. 공통 전처리 기준값 산출 (fillna 값 / IQR 경계)
#    -> pandas로 한 번만 계산해서 세 도구가 동일 기준으로 필터링하도록 공유
#=========================================================

_ref = pd.read_csv(DATA_PATH)  # 기준값(FILL_VALUES, BOUNDS) 계산 전용 df

print_section('[0-1] 기초 EDA (df.info() / isnull().sum())')
_ref.info()               # 행/열 개수, 컬럼별 타입, 결측 여부 확인
print()
print(_ref.isnull().sum())  # region 10000 , category 8000, amount 5000 결측

#데이터 결측치 채움 기준값 계산 (Polars/DuckDB도 동일 값 사용)
FILL_VALUES = {
    'amount': _ref['amount'].median(),      # 중앙값
    'region': _ref['region'].mode()[0],     # 최빈값
    'category': _ref['category'].mode()[0], # 최빈값
}

_ref['amount'] = _ref['amount'].fillna(FILL_VALUES['amount'])       # 중앙값 채움
_ref['region'] = _ref['region'].fillna(FILL_VALUES['region'])       # 최빈값 채움
_ref['category'] = _ref['category'].fillna(FILL_VALUES['category']) # 최빈값 채움
_ref = _ref.dropna(subset=['order_id'])  # order_id 결측 행 제거

# IQR 적용할 수치형 컬럼 목록 (반복문으로 처리)
IQR_COLUMNS = ['quantity', 'unit_price', 'customer_age', 'amount']

BOUNDS = {}                                # 컬럼별 (하한, 상한) 저장 -> Polars/DuckDB에서 재사용
_mask = pd.Series(True, index=_ref.index)  # 컬럼별 조건을 AND로 누적
for _col in IQR_COLUMNS:
    Q1 = _ref[_col].quantile(0.25)              # 1사분위수
    Q3 = _ref[_col].quantile(0.75)              # 3사분위수
    IQR = Q3 - Q1                               # 사분위 범위
    lo, hi = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR      # 정상범위 하한 / 상한
    BOUNDS[_col] = (lo, hi)
    _mask &= _ref[_col].between(lo, hi)         # 하나라도 범위 밖이면 이상치로 간주

before_count = len(_ref)             # 이상치 제거 전 행 수
after_count = _mask.sum()            # 이상치 제거 후 행 수 (mask == True 개수)
removed_count = before_count - after_count  # 제거된 행 수

print_section('[0-2] 이상치 제거 (IQR) 결과')
print(f'  제거 전 행 수 : {before_count:>10,}행')
print(f'  제거 후 행 수 : {after_count:>10,}행')
print(f'  제거된 행 수  : {removed_count:>10,}행  ({removed_count / before_count:.2%})')

del _ref, _col, _mask  # 기준값(FILL_VALUES, BOUNDS)만 필요, 임시 df/변수는 제거


#=========================================================
# 1. Pandas 파이프라인 (원본 CSV 로딩 -> 결측치 처리 -> IQR 필터 -> 집계)
#=========================================================

def pandas_pipeline():
    df = pd.read_csv(DATA_PATH)                                     # 원본 CSV 매번 새로 로딩
    df['amount'] = df['amount'].fillna(FILL_VALUES['amount'])       # 중앙값 채움
    df['region'] = df['region'].fillna(FILL_VALUES['region'])       # 최빈값 채움
    df['category'] = df['category'].fillna(FILL_VALUES['category']) # 최빈값 채움
    df = df.dropna(subset=['order_id'])                             # order_id 결측 행 제거

    mask = pd.Series(True, index=df.index)   # 컬럼별 조건을 AND로 누적
    for col, (lo, hi) in BOUNDS.items():
        mask &= df[col].between(lo, hi)      # 0번에서 구한 경계값 그대로 재사용
    df = df[mask]                            # IQR 이상치 제거

    # 집계 (named aggregation)
    result = (
        df.groupby(['region', 'category'])
        .agg(
            total=('amount', 'sum'),    # 합계
            mean=('amount', 'mean'),    # 평균
            count=('amount', 'count'),  # 건수
        )
        .sort_values(by='total', ascending=False)  # 총매출 기준 내림차순 정렬
    )
    return result


#=========================================================
# 2. Polars Lazy API 파이프라인 (scan_csv -> filter -> group_by -> agg -> sort -> collect)
#=========================================================

def polars_pipeline():
    lf = (
        pl.scan_csv(DATA_PATH)  # CSV를 lazy하게 스캔 (Eager read_csv 아님)
        .with_columns([
            pl.col('amount').fill_null(FILL_VALUES['amount']),       # 중앙값 채움
            pl.col('region').fill_null(FILL_VALUES['region']),       # 최빈값 채움
            pl.col('category').fill_null(FILL_VALUES['category']),   # 최빈값 채움
        ])
        .drop_nulls(subset=['order_id'])  # order_id 결측 행 제거
    )

    for col, (lo, hi) in BOUNDS.items():
        lf = lf.filter(pl.col(col).is_between(lo, hi))  # IQR 이상치 제거 필터 (컬럼별 누적)

    result = (
        lf.group_by(['region', 'category'])  # region, category별 그룹
        .agg(
            pl.col('amount').sum().alias('total'),    # 합계
            pl.col('amount').mean().alias('mean'),    # 평균
            pl.col('amount').count().alias('count'),  # 건수
        )
        .sort(by='total', descending=True)  # 총매출 내림차순
        .collect()  # Lazy 실행 -> 결과 반환
    )
    return result


#=========================================================
# 3. DuckDB SQL 파이프라인 (GROUP BY, 결과는 DataFrame으로 반환)
#=========================================================

def duckdb_pipeline():
    # 컬럼별 IQR 조건을 "컬럼 BETWEEN 하한 AND 상한" 형태로 이어붙임 (AND로 연결)
    bound_clause = ' AND '.join(
        f'{col} BETWEEN {lo} AND {hi}' for col, (lo, hi) in BOUNDS.items()
    )

    # WITH절(filled)에서 결측치 채움 -> 바깥 SELECT에서 IQR 필터 + 집계
    query = f"""
        WITH filled AS (
            SELECT
                order_id,
                COALESCE(region, '{FILL_VALUES['region']}') AS region,       -- 최빈값 채움
                COALESCE(category, '{FILL_VALUES['category']}') AS category, -- 최빈값 채움
                quantity,
                unit_price,
                customer_age,
                COALESCE(amount, {FILL_VALUES['amount']}) AS amount          -- 중앙값 채움
            FROM '{DATA_PATH}'
        )
        SELECT
            region,
            category,
            SUM(amount) AS total,    -- 합계
            AVG(amount) AS mean,     -- 평균
            COUNT(amount) AS count   -- 건수
        FROM filled
        WHERE order_id IS NOT NULL AND {bound_clause}  -- order_id 결측 제거 + IQR 필터
        GROUP BY region, category
        ORDER BY total DESC  -- 총매출 내림차순
    """
    return duckdb.sql(query).df()  # SQL 결과를 DataFrame으로 변환


#=========================================================
# 4. 결과 확인 (세 도구가 동일한 결과를 내는지 검증)
#=========================================================

result_pd = pandas_pipeline()
result_pl = polars_pipeline()
result_duckdb = duckdb_pipeline()

print_section('[1] Pandas 집계 결과 (총매출 상위 5개)')
print(result_pd.head())

print_section('[2] Polars 집계 결과 (총매출 상위 5개)')
print(result_pl.head())

print_section('[3] DuckDB 집계 결과 (총매출 상위 5개)')
print(result_duckdb.head())

# 세 도구가 같은 전처리 기준(FILL_VALUES, BOUNDS)을 썼다면 총매출 합계가 완전히 같아야 함
print_section('[검증] 세 도구 결과 일치 여부 (총매출 합계 비교)')
print(f'  Pandas : {result_pd["total"].sum():>20,.0f}')
print(f'  Polars : {result_pl["total"].sum():>20,.0f}')
print(f'  DuckDB : {result_duckdb["total"].sum():>20,.0f}')


#=========================================================
# 5. timeit 성능 비교 (세 도구 모두 동일한 반복 횟수 사용)
#=========================================================

N = 5  # 반복 횟수 (세 도구 동일 -> 공정 비교)

pandas_time = timeit.timeit(pandas_pipeline, number=N)  # pandas 파이프라인 N회 총 실행시간
polars_time = timeit.timeit(polars_pipeline, number=N)  # polars 파이프라인 N회 총 실행시간
duckdb_time = timeit.timeit(duckdb_pipeline, number=N)  # duckdb 파이프라인 N회 총 실행시간

avg_times = {
    'Pandas': pandas_time / N,  # 1회 평균 실행시간
    'Polars': polars_time / N,
    'DuckDB': duckdb_time / N,
}
fastest_tool = min(avg_times, key=avg_times.get)  # 평균시간이 가장 짧은 도구

print_section(f'[성능 비교] timeit 결과 ({N}회 반복 평균)')
print(f'  {"도구":<10}{"평균 실행시간(초)":>16}{"기준 대비 배수":>16}')
print(f'  {"-" * 42}')
for tool, avg_time in avg_times.items():
    ratio = avg_time / avg_times[fastest_tool]  # 가장 빠른 도구 대비 몇 배 걸리는지
    print(f'  {tool:<10}{avg_time:>16.4f}{ratio:>15.1f}x')
print(f'\n  가장 빠른 도구: {fastest_tool}')


# ==============================================================
# ==============================================================
# 이하는 이전 버전 코드 (2026-07-21 작성, 2026-07-21 리팩터링 전 보존용 주석)
# ==============================================================

# #=========================================================
# # 1. pandas EDA
# # IQR로 이상치 제거 (Q1 - 1.5IQR ~ Q3 + 1.5IQR 범위 벗어난 행 제거)
# # 제거 전/후 행 수 출력
# #==========================================================
#
# df = pd.read_csv('sales_100k.csv')
#
# # 기초 EDA
# # print(df.shape) # 행,열
# # print(df.info()) #결측치 존재 /  orde_date,region,category,product_name, payment_method, customer_gender -> object type
# # print(df.describe()) # 수치 기술통계
# # print(df.describe(include='all')) # 범주형 포함
#
# print('결측치 처리 전')
# print(df.isnull().sum()) # region 10000 , category 8000, amount 5000
#
# #데이터 결측치 처리
# df['amount'] = df['amount'].fillna(df['amount'].median()) #중앙값 채움
# df['region'] = df['region'].fillna(df['region'].mode()[0]) #최빈값 채움
# df['category'] = df['category'].fillna(df['category'].mode()[0]) #최빈값 채움
#
# # 결측치 처리 확인
# # print(df.info())
# print('결측치 처리 후')
# print(df.isnull().sum())
#
#
#
#  # 필요없는 칼럼 열 제거
# df = df.dropna(subset=['order_id'])
#
#
# # IQR 이상치 처리 (반복문으로 여러 컬럼 처리)
# before_count = len(df) #이상치 제거 전 : 1000000
#
# # IQR 수치형 컬럼을 위한 반복문
# # IQR 적용할 수치형 컬럼 목록
# iqr_columns = ['quantity', 'unit_price', 'customer_age', 'amount']
#
# mask = pd.Series(True, index=df.index)  # 컬럼별 조건을 AND로 누적
#
# # 반복문 자동화
# for col in iqr_columns:
#     Q1 = df[col].quantile(0.25)
#     Q3 = df[col].quantile(0.75)
#     IQR = Q3 - Q1
#     lower = Q1 - 1.5 * IQR
#     upper = Q3 + 1.5 * IQR
#     mask &= df[col].between(lower, upper)
#
# df = df[mask]
#
# after_count = len(df)
#
# print(f'이상치 제거 전 행 수: {before_count}') # 10000000
# print(f'이상치 제거 후 행 수: {after_count}') #978351
# print(f'제거된 행 수: {before_count - after_count}') #21649
#
# #===========================================================================
# # 2. Pandas groupby named aggregation
# # region·category별 total(합계)·mean(평균)·count(건수)를 named aggregation으로 계산
# # 총매출 기준 내림차순 정렬
# #============================================================================
#
# # 집계
# result_pd = df.groupby(['region', 'category']).agg(
#     total=('amount', 'sum'), # 합계
#     mean=('amount', 'mean'), # 평균
#     count=('amount', 'count') # 건수
# ).sort_values( by ='total', ascending= False) # 총매출 기준으로 내림차순 정렬
#
# print(result_pd)
#
#
# #===========================================================================
# # 3. Polars Lazy API 활용 동일 집계 작성
# # 2번과 동일한 집계를 Polars Lazy API로 작성
# # (scan_csv → filter → group_by → agg → sort → collect), collect()포함
# #============================================================================
#
# #Polars Lazy API
#
# result_pl = (
#     pl.scan_csv("sales_100k.csv")  # CSV를 lazy하게 스캔
#     .filter(pl.col('amount').is_between(lower, upper))  # IQR 이상치 제거 필터
#     .group_by(['region', 'category'])  # region, category별 그룹
#     .agg(
#         pl.col('amount').sum().alias('total'),
#         pl.col('amount').mean().alias('mean'),
#         pl.col('amount').count().alias('count'),
#     )
#     .sort(by='total', descending=True)  # 총매출 내림차순
#     .collect()  # Lazy 실행 → 결과 반환
# )
#
# print(result_pl)
#
#
# #=============================================================
# # 4. DuckDB SQL
# # 동일 집계를 DuckDB SQL(GROUP BY)로 작성, 결과를 DataFrame으로 출력
# #=============================================================
#
# # DuckDB SQL로 동일 집계
# result_duckdb = duckdb.sql("""
#     SELECT
#         region,
#         category,
#         SUM(amount) AS total,
#         AVG(amount) AS mean,
#         COUNT(amount) AS count
#     FROM 'sales_100k.csv'
#     WHERE amount BETWEEN {lower} AND {upper}
#     GROUP BY region, categroy
#     ORDER BY total DESC
#     """).df() #sql을 df로 변환
#
# print(result_duckdb)
#
#
# #====================================================
# # 5. 성능비교
# # timeit으로 Pandas·Polars·DuckDB 세 도구 실행 시간 측정
# # (세 도구 모두 동일한 반복 횟수 사용)
# #====================================================
#
# # timeit으로 세 도구 성능 비교
