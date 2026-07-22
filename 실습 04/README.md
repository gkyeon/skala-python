# 실습 04 : 시각화 4종 · 통계 검정 · sklearn Pipeline

작성일: 2026-07-21

Sales 데이터(`sales_100k.csv`)를 활용한 EDA 시각화, 통계 검정, 머신러닝 파이프라인, 인터랙티브 시각화 실습.

## 내용

1. EDA 시각화 4종 — 히스토그램+KDE, 박스플롯, 월별 라인, 상관 히트맵 (subplot 하나로 구성)
2. 통계 검정 — 서울 vs 부산 평균 매출 t-test, 지역×카테고리 카이제곱 검정 (p<0.05 해석 포함)
3. sklearn `Pipeline` — `ColumnTransformer` + 모델 구성, `joblib`로 저장/재로딩 검증
4. Plotly — 지역·카테고리별 총매출 인터랙티브 차트, `.html`로 저장

## 실행

```bash
python "광주_1반_김하연.py"
```
