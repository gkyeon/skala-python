"""
통계 분석 함수 모음.

기술통계, 상관계수, income 그룹 간 t-test를 계산하는 함수를 제공한다.
결과를 dict/DataFrame으로 반환해서 src/report.py의 Jinja2 템플릿에
그대로 주입할 수 있게 한다.
"""

import pandas as pd
from scipy import stats

DEFAULT_NUMERIC_COLS = [
    "age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week",
]


def descriptive_stats(df: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    """평균·표준편차·분위수 등 기술통계를 계산한다.

    반환값은 (컬럼) x (통계량) 형태로 전치해서, 컬럼이 많아져도 보기 편하게 한다.
    """
    if cols is None:
        cols = DEFAULT_NUMERIC_COLS
    return df[cols].describe().T


def correlation_matrix(df: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    """수치형 변수 간 피어슨 상관계수 행렬을 계산한다."""
    if cols is None:
        cols = DEFAULT_NUMERIC_COLS
    return df[cols].corr()


def income_ttest(
    df: pd.DataFrame,
    value_col: str = "hours-per-week",
    group_col: str = "income",
    group_a: str = ">50K",
    group_b: str = "<=50K",
    alpha: float = 0.05,
) -> dict:
    """income 두 그룹(기본: >50K vs <=50K) 간 value_col 평균 차이를 t-test로 검정한다.

    Welch's t-test(equal_var=False)를 사용해 두 그룹의 분산이 같다고
    가정하지 않는다 (표본 크기·분산이 다른 실제 데이터에 더 안전한 방식).

    Returns
    -------
    dict
        t_stat, p_value, alpha, is_significant, interpretation, 그룹별 평균/표본수 등을
        담은 딕셔너리. src/report.py의 Jinja2 템플릿에 그대로 주입 가능한 형태.
    """
    group_a_values = df.loc[df[group_col] == group_a, value_col]
    group_b_values = df.loc[df[group_col] == group_b, value_col]

    t_stat, p_value = stats.ttest_ind(group_a_values, group_b_values, equal_var=False)
    is_significant = p_value < alpha

    # p < 0.05 여부에 따른 해석 문장 (감점 대상 항목이라 반드시 포함)
    significance_phrase = "유의하다" if is_significant else "유의하지 않다"
    interpretation = (
        f"유의수준 {alpha}에서 '{group_a}' 그룹과 '{group_b}' 그룹의 "
        f"'{value_col}' 평균 차이는 통계적으로 {significance_phrase}."
    )

    result = {
        "value_col": value_col,
        "group_col": group_col,
        "group_a": group_a,
        "group_b": group_b,
        "mean_a": group_a_values.mean(),
        "mean_b": group_b_values.mean(),
        "n_a": len(group_a_values),
        "n_b": len(group_b_values),
        "t_stat": t_stat,
        "p_value": p_value,
        "alpha": alpha,
        "is_significant": is_significant,
        "interpretation": interpretation,
    }

    print(f"[t-test] '{group_a}' vs '{group_b}' on '{value_col}'")
    print(f"  {group_a} 평균 : {result['mean_a']:.2f}  (n={result['n_a']:,})")
    print(f"  {group_b} 평균 : {result['mean_b']:.2f}  (n={result['n_b']:,})")
    print(f"  t-statistic : {t_stat:.4f}")
    print(f"  p-value     : {p_value:.4f}")
    print(f"  -> {interpretation}")

    return result


if __name__ == "__main__":
    import sys
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.clean import load_and_clean

    cleaned_df = load_and_clean()

    print("=== 기술통계 ===")
    print(descriptive_stats(cleaned_df))

    print("\n=== 상관계수 행렬 ===")
    print(correlation_matrix(cleaned_df))

    print()
    income_ttest(cleaned_df)
