# 실습 03 : 판다스 EDA, Polars Lazy API, DuckDB SQL, 성능 비교

작성일: 2026-07-21

Sales 데이터(`sales_100k.csv`)를 pandas / Polars / DuckDB 세 가지 도구로 동일하게 전처리(결측치 채움, IQR 이상치 제거)한 뒤 성능을 비교한다.

## 내용

1. 파일 로딩 + 기본 EDA, 이상치 제거 기준값 산출 (세 도구가 공유)
2. Pandas — groupby named aggregation
3. Polars — Lazy API로 동일 집계 구현
4. DuckDB — SQL로 동일 집계 구현
5. `timeit` 기반 3개 도구 성능 비교

## 실행

```bash
python "광주_1반_김하연_practice03.py"
```

세 파이프라인이 동일한 필터링 기준(`BOUNDS`)을 공유하도록 구성해 결과·성능 비교의 공정성을 확보했다.
