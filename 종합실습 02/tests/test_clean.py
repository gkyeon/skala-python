"""
src/clean.py 핵심 함수(clean_nulls, drop_duplicate_rows, load_pandas/polars)에 대한 pytest 테스트.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# 노트북과 동일한 규칙: 상대 경로로 프로젝트 루트를 sys.path에 추가한 뒤 src를 임포트한다
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.clean import clean_nulls, drop_duplicate_rows, load_and_clean, load_pandas, load_polars


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """workclass에 결측치가 섞인 작은 샘플 DataFrame."""
    return pd.DataFrame({
        "workclass": ["Private", None, "Self-emp", "Private", None],
        "age": [25, 30, 35, 25, 40],
    })


def test_clean_nulls_mode_fills_with_most_frequent_value(sample_df):
    result = clean_nulls(sample_df, cols=["workclass"], strategy="mode")
    assert result["workclass"].isnull().sum() == 0
    assert result.loc[1, "workclass"] == "Private"  # 최빈값으로 채워졌는지 확인


def test_clean_nulls_median_fills_numeric_column():
    df = pd.DataFrame({"age": [10, 20, None, 40]})
    result = clean_nulls(df, cols=["age"], strategy="median")
    assert result["age"].isnull().sum() == 0
    assert result.loc[2, "age"] == 20.0  # [10, 20, 40]의 중앙값


def test_clean_nulls_drop_removes_rows_with_null(sample_df):
    result = clean_nulls(sample_df, cols=["workclass"], strategy="drop")
    assert len(result) == 3
    assert result["workclass"].isnull().sum() == 0


def test_clean_nulls_invalid_strategy_raises():
    df = pd.DataFrame({"a": [1, None]})
    with pytest.raises(ValueError):
        clean_nulls(df, cols=["a"], strategy="not-a-real-strategy")


def test_clean_nulls_does_not_mutate_original(sample_df):
    original_na_count = sample_df["workclass"].isnull().sum()
    clean_nulls(sample_df, cols=["workclass"], strategy="mode")
    assert sample_df["workclass"].isnull().sum() == original_na_count  # 원본은 그대로여야 함


def test_drop_duplicate_rows_removes_exact_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    result = drop_duplicate_rows(df)
    assert len(result) == 2


def test_load_pandas_matches_expected_shape():
    df = load_pandas()
    assert df.shape == (32561, 15)
    assert "income" in df.columns


def test_load_pandas_and_polars_agree_on_row_count():
    pandas_df = load_pandas()
    polars_df = load_polars()
    assert pandas_df.shape[0] == polars_df.shape[0]


def test_load_and_clean_has_no_nulls_and_no_duplicates():
    df = load_and_clean()
    assert df.isnull().sum().sum() == 0
    assert df.duplicated().sum() == 0
