"""
Jinja2 기반 분석 리포트 자동 생성 모듈.

src/clean, src/stats, src/pipeline, src/viz의 결과를 모아
templates/report.md.j2 템플릿에 주입해서 output/report.md로 렌더링한다.
"""

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORT_PATH = OUTPUT_DIR / "report.md"


def _find_top_correlation(corr: pd.DataFrame) -> dict:
    """상관계수 행렬에서 자기 자신을 제외하고 절댓값이 가장 큰 변수 쌍을 찾는다."""
    diagonal_mask = np.eye(len(corr), dtype=bool)
    corr_no_diag = corr.mask(diagonal_mask)
    col_a, col_b = corr_no_diag.abs().stack().idxmax()
    return {"col_a": col_a, "col_b": col_b, "value": corr.loc[col_a, col_b]}


def build_report_context(
    raw_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    descriptive_df: pd.DataFrame,
    correlation_df: pd.DataFrame,
    ttest_result: dict,
    pipeline_result: dict,
    correlation_heatmap_path: str,
    income_hours_chart_path: str,
    income_hours_chart_static_path: str,
) -> dict:
    """리포트 템플릿(templates/report.md.j2)에 주입할 context 딕셔너리를 구성한다."""
    descriptive_records = (
        descriptive_df.reset_index().rename(columns={"index": "column"}).to_dict("records")
    )

    return {
        "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "raw_shape": raw_df.shape,
        "cleaned_shape": cleaned_df.shape,
        "descriptive_stats": descriptive_records,
        "top_correlation": _find_top_correlation(correlation_df),
        "ttest": ttest_result,
        "pipeline": pipeline_result,
        "correlation_heatmap_path": correlation_heatmap_path,
        "income_hours_chart_path": income_hours_chart_path,
        "income_hours_chart_static_path": income_hours_chart_static_path,
    }


def render_report(
    context: dict,
    template_name: str = "report.md.j2",
    output_path: str | Path = REPORT_PATH,
) -> Path:
    """템플릿을 렌더링해서 output_path(기본 output/report.md)에 저장한다."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template(template_name)
    rendered = template.render(**context)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    return output_path


def generate_full_report() -> Path:
    """데이터 로딩부터 리포트 렌더링까지 전체 파이프라인을 한 번에 실행한다.

    src/run_pipeline.py와 이 파일의 __main__ 블록 양쪽에서 재사용한다.
    """
    from src.clean import load_and_clean, load_pandas
    from src.pipeline import train_and_evaluate
    from src.stats import correlation_matrix, descriptive_stats, income_ttest
    from src.viz import plot_correlation_heatmap, plot_income_by_hours

    raw_df = load_pandas()
    cleaned_df = load_and_clean()

    desc_df = descriptive_stats(cleaned_df)
    corr_df = correlation_matrix(cleaned_df)
    ttest_result = income_ttest(cleaned_df)
    pipeline_result = train_and_evaluate(cleaned_df)

    plot_correlation_heatmap(cleaned_df)
    plot_income_by_hours(cleaned_df)

    context = build_report_context(
        raw_df,
        cleaned_df,
        desc_df,
        corr_df,
        ttest_result,
        pipeline_result,
        correlation_heatmap_path="figures/correlation_heatmap.png",
        income_hours_chart_path="figures/income_hours_box.html",
        income_hours_chart_static_path="figures/income_hours_box.png",
    )
    return render_report(context)


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(PROJECT_ROOT))
    report_path = generate_full_report()
    print(f"리포트 생성 완료: {report_path}")
