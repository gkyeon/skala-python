"""
전체 분석 파이프라인을 한 번에 실행하는 진입점 스크립트.

    python src/run_pipeline.py

실행하면 다음이 순서대로 수행된다:
  1. data/raw/adult.data 로딩 (pandas/polars 비교) + 정제
  2. 기술통계/상관계수/t-test 계산
  3. sklearn Pipeline 학습 -> 평가 -> output/model.pkl 저장 -> 재로딩 검증
  4. Seaborn/Plotly 차트를 output/figures/에 저장
  5. output/report.md 자동 생성
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.report import generate_full_report


def main() -> None:
    report_path = generate_full_report()
    print(f"\n전체 파이프라인 완료. 리포트: {report_path}")


if __name__ == "__main__":
    main()
