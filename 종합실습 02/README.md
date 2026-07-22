# Adult Census Income 분석 파이프라인

UCI [Adult Census Income](https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data) 데이터셋을 이용해
데이터 준비 → 시각화 → 통계분석 → ML Pipeline → 리포트 자동 생성까지 이어지는 분석 프로젝트.

## 폴더 구조

```
teamproject/
├── data/
│   ├── raw/            # 원본 데이터 (adult.data). 절대 수정하지 않음
│   ├── processed/      # 전처리 완료 데이터를 저장할 위치 (필요 시 사용)
│   └── external/
├── notebooks/
│   ├── 01_eda.ipynb                 # 로딩 비교, 기초 EDA, 시각화
│   └── 02_feature_exploration.ipynb # 기술통계, 상관관계, t-test, ML Pipeline
├── src/
│   ├── clean.py       # pandas/polars 로딩, 결측치·중복 처리
│   ├── viz.py          # Seaborn/Plotly 시각화 함수
│   ├── stats.py        # 기술통계, 상관계수, t-test
│   ├── pipeline.py     # sklearn Pipeline 정의/학습/평가/저장
│   ├── report.py       # Jinja2 리포트 생성
│   └── run_pipeline.py # 전체 파이프라인 실행 진입점
├── templates/
│   └── report.md.j2    # 리포트 템플릿
├── output/
│   ├── figures/         # 저장된 차트 (PNG, HTML)
│   ├── report.md        # 자동 생성된 분석 리포트
│   └── model.pkl        # 학습된 모델
├── tests/
│   └── test_clean.py
├── requirements.txt
└── README.md
```

## 개발 환경 설정

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 데이터

`data/raw/adult.data`가 이미 포함되어 있다. 없다면 아래 명령으로 다시 받는다 (원본은 절대 덮어쓰지 않음).

```bash
curl -o data/raw/adult.data \
  "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
```

## 실행 방법

### 전체 파이프라인 한 번에 실행 (권장)

```bash
python src/run_pipeline.py
```

데이터 로딩/정제 → 기술통계·t-test → ML Pipeline 학습/평가/저장 → 차트 저장 →
`output/report.md` 생성까지 한 번에 수행한다.

### 모듈 개별 실행

각 모듈은 `python src/<모듈>.py`로 단독 실행해 결과를 바로 확인할 수 있다.

```bash
python src/clean.py      # pandas/polars 로딩 비교 + 기초 EDA + 이상치/결측치 처리 결과
python src/viz.py         # output/figures/에 차트 저장
python src/stats.py       # 기술통계 / 상관계수 / t-test 출력
python src/pipeline.py    # 모델 학습/평가 + output/model.pkl 저장
python src/report.py      # output/report.md 생성
```

### 노트북

```bash
jupyter notebook notebooks/01_eda.ipynb
jupyter notebook notebooks/02_feature_exploration.ipynb
```

노트북은 `sys.path.insert(0, '..')`로 프로젝트 루트를 경로에 추가한 뒤 `src` 모듈을 그대로 import한다.

### 테스트

```bash
pytest
```

## 주요 결과 요약

(최신 수치는 `output/report.md`를 참고. `src/run_pipeline.py` 실행 후 자동 갱신됨)

- t-test: `>50K` vs `<=50K` 그룹의 주당 근무시간(hours-per-week) 평균 차이는 통계적으로 유의함 (p < 0.05)
- ML Pipeline (LogisticRegression): Accuracy ≈ 0.86, F1-score ≈ 0.68
- 상관관계: `education-num`과 `hours-per-week`가 수치형 변수 중 가장 높은 상관관계를 보임

## 데이터 출처

Dua, D. and Graff, C. (2019). UCI Machine Learning Repository — Adult Data Set.
Irvine, CA: University of California, School of Information and Computer Science.
