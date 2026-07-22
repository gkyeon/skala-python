"""
시각화 함수 모음.

Seaborn(정적) / Plotly(인터랙티브) 차트를 함수로 분리해서
notebooks 와 src/report.py 양쪽에서 동일한 코드로 재사용할 수 있게 한다.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = PROJECT_ROOT / "output" / "figures"

DEFAULT_NUMERIC_COLS = [
    "age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week",
]


def plot_correlation_heatmap(
    df: pd.DataFrame,
    numeric_cols: list[str] | None = None,
    save_path: str | Path | None = FIGURES_DIR / "correlation_heatmap.png",
) -> plt.Figure:
    """수치형 변수 간 상관관계를 Seaborn 히트맵(정적 차트)으로 그린다.

    Parameters
    ----------
    df : pd.DataFrame
    numeric_cols : list[str] | None
        상관관계를 볼 수치형 컬럼 목록. None이면 기본 6개 컬럼 사용.
    save_path : str | Path | None
        PNG로 저장할 경로. None이면 저장하지 않고 Figure만 반환.

    Returns
    -------
    matplotlib.figure.Figure
    """
    if numeric_cols is None:
        numeric_cols = DEFAULT_NUMERIC_COLS

    corr = df[numeric_cols].corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
    ax.set_title("Numeric Feature Correlation Heatmap")
    fig.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=120, bbox_inches="tight")

    return fig


def plot_income_by_hours(
    df: pd.DataFrame,
    save_path: str | Path | None = FIGURES_DIR / "income_hours_box.html",
    static_save_path: str | Path | None = FIGURES_DIR / "income_hours_box.png",
) -> go.Figure:
    """income 그룹별 주당 근무시간(hours-per-week) 분포를
    Plotly 박스플롯(인터랙티브, 그룹비교)으로 그린다.

    Parameters
    ----------
    df : pd.DataFrame
    save_path : str | Path | None
        인터랙티브 HTML로 저장할 경로. None이면 저장하지 않는다.
    static_save_path : str | Path | None
        Notion 등 인터랙티브 HTML을 직접 못 넣는 곳에 붙여넣을 수 있도록
        kaleido로 렌더링한 정적 PNG 스냅샷 경로. None이면 저장하지 않는다.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    fig = px.box(
        df,
        x="income",
        y="hours-per-week",
        color="income",
        title="Weekly Working Hours by Income Group",
        labels={"income": "Income Group", "hours-per-week": "Hours per Week"},
    )

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(save_path)

    if static_save_path is not None:
        static_save_path = Path(static_save_path)
        static_save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_image(static_save_path, width=900, height=600, scale=2)

    return fig


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(PROJECT_ROOT))
    from src.clean import load_and_clean

    cleaned_df = load_and_clean()
    plot_correlation_heatmap(cleaned_df)
    plot_income_by_hours(cleaned_df)
    print(f"차트 저장 완료: {FIGURES_DIR}")
