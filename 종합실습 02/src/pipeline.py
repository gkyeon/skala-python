"""
income(소득 <=50K / >50K) 분류를 위한 sklearn Pipeline 정의/학습/평가/저장 모듈.

ColumnTransformer로 수치형/범주형 전처리를 하나로 묶고, LogisticRegression으로
분류 모델을 학습한 뒤 joblib으로 저장 -> 재로딩까지 검증한다.
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "output" / "model.pkl"

# 수치형은 스케일링, 범주형은 인코딩이 필요하므로 컬럼을 미리 구분해둔다
NUMERIC_FEATURES = [
    "age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week",
]
CATEGORICAL_FEATURES = [
    "workclass", "education", "marital-status", "occupation",
    "relationship", "race", "sex", "native-country",
]
TARGET = "income"


def build_pipeline() -> Pipeline:
    """전처리(ColumnTransformer) + LogisticRegression을 하나로 묶은 Pipeline을 생성한다.

    - 수치형: StandardScaler로 평균0/분산1 표준화
    - 범주형: OneHotEncoder(handle_unknown="ignore")로 더미변수화
              (학습에 없던 카테고리가 테스트에 나와도 에러 없이 무시)
    """
    preprocessor = ColumnTransformer(transformers=[
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    return Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("model", LogisticRegression(max_iter=1000)),
    ])


def split_data(
    df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
) -> tuple:
    """설명변수/타겟을 분리하고 train/test로 split한다 (stratify로 income 비율 유지)."""
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]
    return train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )


def train_and_evaluate(df: pd.DataFrame, save_path: str | Path = MODEL_PATH) -> dict:
    """Pipeline 학습 -> 평가 -> joblib 저장 -> 재로딩 검증까지 한 번에 수행한다.

    Returns
    -------
    dict
        accuracy, f1, classification_report 등 src/report.py 템플릿에
        그대로 주입 가능한 평가 지표 모음.
    """
    X_train, X_test, y_train, y_test = split_data(df)

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, pos_label=">50K")
    report_text = classification_report(y_test, y_pred)

    # 저장 (전처리 규칙 + 학습된 모델 파라미터를 통째로 직렬화)
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, save_path)

    # 재로딩 확인 (다시 불러온 pipeline이 방금 학습한 것과 동일하게 동작하는지 검증)
    reloaded_pipeline = joblib.load(save_path)
    reload_accuracy = accuracy_score(y_test, reloaded_pipeline.predict(X_test))

    result = {
        "n_train": len(X_train),
        "n_test": len(X_test),
        "accuracy": accuracy,
        "f1": f1,
        "classification_report": report_text,
        "model_path": str(save_path),
        "reload_accuracy": reload_accuracy,
        "reload_matches": reload_accuracy == accuracy,
    }

    print(f"[Pipeline] train={result['n_train']:,} / test={result['n_test']:,}")
    print(f"[Pipeline] accuracy={accuracy:.4f}, f1={f1:.4f}")
    print(report_text)
    print(f"[Pipeline] 모델 저장 완료: {save_path}")
    print(f"[Pipeline] 재로딩 후 accuracy={reload_accuracy:.4f} (원본과 일치: {result['reload_matches']})")

    return result


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(PROJECT_ROOT))
    from src.clean import load_and_clean

    cleaned_df = load_and_clean()
    train_and_evaluate(cleaned_df)
