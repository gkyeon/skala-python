"""
데이터 로딩 및 정제 모듈.

Adult Census Income 원본 CSV(data/raw/adult.data)를 pandas/polars로 각각
로딩하고, 결측치 처리·중복 제거·기초 EDA를 수행하는 함수를 제공한다.
notebooks, tests, src/report.py 등에서 공통으로 재사용한다.
"""

from pathlib import Path

import pandas as pd
import polars as pl

# 이 파일(src/clean.py) 기준 상위 폴더가 프로젝트 루트
# -> 어디서 import해서 실행하든(노트북, 테스트, src/run_pipeline.py) 항상 같은 경로를 찾는다
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "adult.data"

# UCI adult.data는 헤더가 없어서 컬럼명을 직접 지정해야 한다
COLUMN_NAMES = [
    "age", "workclass", "fnlwgt", "education", "education-num",
    "marital-status", "occupation", "relationship", "race", "sex",
    "capital-gain", "capital-loss", "hours-per-week", "native-country", "income",
]

# 원본에 " ?"로 표기된 결측치가 몰려있는 컬럼 (workclass, occupation, native-country)
DEFAULT_NULL_COLS = ["workclass", "occupation", "native-country"]

# 원래 수치형이어야 하는 컬럼 (polars 로딩 시 문자열 -> 정수 캐스팅에 사용)
NUMERIC_COLUMNS = ["age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week"]


def load_pandas(path: str | Path = RAW_DATA_PATH) -> pd.DataFrame:
    """adult.data를 pandas DataFrame으로 로딩한다.

    skipinitialspace=True가 ", " 구분자 뒤 공백을 먼저 제거하기 때문에,
    그 뒤에 na_values가 매칭해야 할 값은 " ?"가 아니라 공백이 빠진 "?"여야 한다.
    (na_values=" ?"로 두면 skipinitialspace가 공백을 지운 뒤라 아무 것도 매칭되지 않아
     "?"가 NaN 처리되지 않고 그대로 문자열 값으로 남는 버그가 생긴다.)
    """
    return pd.read_csv(
        path,
        header=None,
        names=COLUMN_NAMES,
        na_values="?",
        skipinitialspace=True,
    )


def load_polars(path: str | Path = RAW_DATA_PATH) -> pl.DataFrame:
    """adult.data를 polars DataFrame으로 로딩한다.

    원본 CSV가 ", " 형태라 값 앞에 공백이 남아있는데, 공백이 붙은 채로는
    polars의 숫자 파서가 "  77516" 같은 값을 숫자로 인식하지 못해 전 컬럼이
    문자열로 읽히는 문제가 있다. 그래서:
      1) schema_overrides로 일단 전부 문자열로 읽고
      2) str.strip_chars()로 공백을 제거한 뒤
      3) NUMERIC_COLUMNS만 다시 정수로 캐스팅한다.
    또한 파일 끝의 빈 줄이 전부 null인 행으로 읽히는 것을
    age가 null인 행을 걸러내는 방식으로 제거한다 (pandas는 이 빈 줄을 자동으로 건너뜀).
    """
    df = pl.read_csv(
        path,
        has_header=False,
        new_columns=COLUMN_NAMES,
        null_values=" ?",
        schema_overrides={col: pl.Utf8 for col in COLUMN_NAMES},
    )
    df = df.with_columns([pl.col(c).str.strip_chars() for c in COLUMN_NAMES])
    df = df.filter(pl.col("age").is_not_null())  # 파일 끝 빈 줄(전부 null) 제거
    df = df.with_columns([pl.col(c).cast(pl.Int64) for c in NUMERIC_COLUMNS])
    return df


def compare_loaders(pandas_df: pd.DataFrame, polars_df: pl.DataFrame) -> None:
    """pandas/polars 로딩 결과의 shape와 컬럼별 dtype을 나란히 출력해 비교한다."""
    print(f"[Pandas] shape: {pandas_df.shape}")
    print(f"[Polars] shape: {polars_df.shape}")
    print()
    print(f'{"컬럼":<16}{"pandas dtype":<14}{"polars dtype":<14}')
    print('-' * 44)
    for col in pandas_df.columns:
        print(f'{col:<16}{str(pandas_df[col].dtype):<14}{str(polars_df.schema[col]):<14}')


def clean_nulls(df: pd.DataFrame, cols: list[str], strategy: str = "mode") -> pd.DataFrame:
    """지정한 컬럼들의 결측치를 strategy 방식으로 채운 새 DataFrame을 반환한다.

    원본 df는 변경하지 않고 복사본에 적용한다 (side-effect 방지).

    Parameters
    ----------
    df : pd.DataFrame
    cols : list[str]
        결측치를 처리할 대상 컬럼 목록
    strategy : {"mode", "median", "drop"}, default "mode"
        - "mode"   : 최빈값으로 채움 (범주형 컬럼에 적합)
        - "median" : 중앙값으로 채움 (수치형 컬럼에 적합)
        - "drop"   : 결측치가 있는 행 자체를 제거

    Returns
    -------
    pd.DataFrame
        결측치가 처리된 새 DataFrame
    """
    df = df.copy()

    if strategy == "drop":
        return df.dropna(subset=cols)

    for col in cols:
        if strategy == "mode":
            fill_value = df[col].mode()[0]
        elif strategy == "median":
            fill_value = df[col].median()
        else:
            raise ValueError(f"알 수 없는 strategy: {strategy!r} (mode/median/drop 중 하나여야 함)")
        df[col] = df[col].fillna(fill_value)

    return df


def drop_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """완전히 동일한 중복 행을 제거하고, 제거 전/후 행 수를 출력한다."""
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    print(f"중복 제거 전: {before:,}행 -> 제거 후: {after:,}행 (제거됨: {before - after:,}행)")
    return df


def basic_eda(df: pd.DataFrame) -> None:
    """info(), describe(수치형/범주형), 범주형 컬럼 value_counts를 순서대로 출력한다."""
    print("=== df.info() ===")
    df.info()

    print("\n=== df.describe() (수치형) ===")
    print(df.describe())

    print("\n=== df.describe(include='str') (범주형) ===")
    print(df.describe(include="str"))

    categorical_cols = df.select_dtypes(include="str").columns
    for col in categorical_cols:
        print(f"\n--- {col} value_counts (상위 10개) ---")
        print(df[col].value_counts().head(10))


def load_and_clean(
    path: str | Path = RAW_DATA_PATH,
    null_cols: list[str] | None = None,
    strategy: str = "mode",
) -> pd.DataFrame:
    """원본 로딩 -> 결측치 처리 -> 중복 제거까지 마친 DataFrame을 반환하는 전체 파이프라인.

    notebooks, src/pipeline.py, src/report.py 등 정제된 데이터가 필요한
    모든 곳에서 이 함수 하나만 호출하면 된다.
    """
    if null_cols is None:
        null_cols = DEFAULT_NULL_COLS

    df = load_pandas(path)
    df = clean_nulls(df, null_cols, strategy=strategy)
    df = drop_duplicate_rows(df)
    return df


if __name__ == "__main__":
    pandas_df = load_pandas()
    polars_df = load_polars()
    compare_loaders(pandas_df, polars_df)

    print()
    basic_eda(pandas_df)

    cleaned = load_and_clean()
    print(f"\n최종 정제 데이터 shape: {cleaned.shape}")
