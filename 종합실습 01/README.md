# 데이터 수집 미니 파이프라인

3개 API(Open-Meteo, countries.dev, ip-api)를 `asyncio` + `httpx`로 동시 수집하고,
`Pydantic v2`로 스키마를 검증한 뒤 CSV/Parquet로 저장하며 읽기/쓰기 성능을 비교하는 미니 파이프라인.

## 사용 API

| API | 내용 |
|---|---|
| [Open-Meteo](https://open-meteo.com/) | 서울 3일치 시간대별 기온·강수확률 |
| [countries.dev](https://countries.dev/) | 한국(KOR) 국가 정보 |
| [ip-api](https://ip-api.com/) | IP(8.8.8.8) 기반 지역 정보 |

## 프로젝트 구조

```
data-project/
├── mission/
│   ├── requirements.txt   # httpx, pydantic, pandas, pyarrow, pytest, ruff
│   ├── schemas.py          # Pydantic v2 검증 모델 3개
│   ├── 종합실습.py          # 메인 파이프라인 (수집 → 검증 → 저장/성능비교)
│   └── output/             # 실행 시 생성되는 CSV/Parquet (git에는 포함 안 됨)
└── tests/
    └── test_schema.py       # 스키마 검증 pytest
```

## 환경 설정

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r mission/requirements.txt
```

## 실행

```bash
cd mission
python 종합실습.py
```

실행하면 3개 API를 동시에 수집한 뒤, 검증 결과와 CSV/Parquet 저장·읽기 소요 시간을 출력한다.

```
3개 API 동시 수집 완료
weather: 72건 검증 통과
country: 통과
ip: 통과
[weather] rows=72 | CSV write=3.46ms read=1.31ms | Parquet write=44.35ms read=32.72ms
[country] rows=1 | CSV write=0.51ms read=0.36ms | Parquet write=0.97ms read=0.63ms
[ip] rows=1 | CSV write=0.20ms read=0.29ms | Parquet write=0.44ms read=0.45ms
```

> weather의 Parquet 수치가 country/ip보다 유독 큰 건 pyarrow 엔진이 프로세스에서
> 처음 쓰일 때 초기화 비용이 붙기 때문이다(가장 먼저 벤치마크되는 데이터셋이라 그렇다).

## 테스트

```bash
python -m pytest tests/ -v
```

## 코드 스타일 검사

```bash
ruff check mission tests
```
