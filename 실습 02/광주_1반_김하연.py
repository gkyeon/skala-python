"""
==============================================================
실습2 : 파일 I/O, 예외 처리, Pydantic 검증 파이프라인 (Sales 데이터)
==============================================================
작성자 : 김하연

설명:
    Python_Practice1_Data.json 데이터를 활용해 아래 기능을 연습한다.
    1. 예외 처리 + 파일 읽기 (safe_load_csv)
    2. Pydantic v2 스키마 정의 (SalesRecord)
    3. 검증 파이프라인 (raw_data -> valid / errors 분리)
    4. 결과 파일 저장(CSV/JSON) + 재로딩 확인

변경내역:
    2026-07-20  최초 작성 (safe_load_csv, SalesRecord, validate_sales,
                결과 저장/재로딩, mock 데이터 기반 체크포인트 검증)
    2026-07-20  mock 데이터만 처리하는 데서 그치지 않고, 실제 100건 데이터에도
                동일 파이프라인을 적용하는 실사용 예시 추가
    2026-07-20  체크포인트 4개와 각 assert 위치를 명시하는 설명 주석 추가
==============================================================
"""

import csv
import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 입력 데이터는 프로젝트 루트의 data/ 폴더에 모아둠 (여러 실습이 같은 데이터를 공유)
# 출력 파일(valid/errors)은 이 실습 결과물이므로 스크립트와 같은 폴더에 그대로 저장
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "Python_Practice2_Data.json"
VALID_CSV_PATH = Path(__file__).with_name("valid_sales.csv")
ERRORS_JSON_PATH = Path(__file__).with_name("errors.json")


# ======================
# 1. 예외 처리 + 파일 읽기
# ======================

def safe_load_csv(filepath):
    """
    JSON 파일을 안전하게 로드하는 함수.
    성공하면 dict 리스트를 반환하고 logger.info를 남긴다.
    파일이 없거나 JSON 형식이 잘못되면 None을 반환하고 logger.error를 남긴다.
    finally 블록에서는 성공/실패 여부와 상관없이 '로딩 종료'를 출력한다.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"파일 로드 성공: {filepath} ({len(data)}건)")
        return data
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON 형식이 올바르지 않습니다: {e}")
        return None
    finally:
        print("로딩 종료")


# ======================
# 2. Pydantic v2 스키마 정의
# ======================

class SalesRecord(BaseModel):
    """거래 한 건의 데이터 구조와 유효성 조건을 정의하는 스키마."""

    region: str = Field(..., min_length=1)   # 비어있으면 안 됨
    category: Optional[str] = None           # 없어도 됨
    month: str = Field(..., min_length=1)    # 비어있으면 안 됨 (YYYY-MM)
    amount: float = Field(..., gt=0)         # 0 초과여야 함

    @field_validator("region", "month")
    def not_empty(cls, v):
        """공백 문자열(예: '   ')도 빈 값으로 취급해서 막는다."""
        if not v or not v.strip():
            raise ValueError("빈 문자열은 허용되지 않습니다.")
        return v


# ======================
# 3. 검증 파이프라인 (valid / errors 분리)
# ======================

def validate_sales(raw_data):
    """raw_data(dict 리스트)를 SalesRecord로 검증해 valid/errors 리스트로 분리한다."""
    valid = []
    errors = []
    for row_number, row in enumerate(raw_data, start=1):
        try:
            record = SalesRecord(**row)
            valid.append(record)
        except ValidationError as e:
            # 체크포인트: ValidationError 발생 시 오류 내용 출력
            # (Exception으로 뭉뚱그리지 않고 ValidationError만 구체적으로 처리)
            print(f"[검증 오류] {row_number}번째 행: {e}")
            errors.append({"row": row_number, "error": str(e)})
    return valid, errors


# ======================
# 4. 결과 파일 저장 + 재로딩 확인
# ======================

def save_valid_to_csv(valid_records, filepath):
    """valid SalesRecord 리스트를 CSV 파일로 저장한다."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["region", "category", "month", "amount"])
        writer.writeheader()
        for record in valid_records:
            # model_dump(): pydantic 객체를 dict로 변환 (직접 dict를 만들지 않음)
            writer.writerow(record.model_dump())


def save_errors_to_json(errors, filepath):
    """errors 리스트를 JSON 파일로 저장한다."""
    with open(filepath, "w", encoding="utf-8") as f:
        # ensure_ascii=False: 한글이 유니코드 이스케이프로 깨져서 저장되는 것을 방지
        json.dump(errors, f, ensure_ascii=False, indent=2)


def reload_csv(filepath):
    """저장된 CSV 파일을 다시 읽어 리스트로 반환한다."""
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


if __name__ == "__main__":

    # ---- 1. safe_load_csv 동작 확인 ----
    # 체크포인트: safe_load_csv 동작 + assert None 통과
    # 존재하지 않는 파일 -> None 반환하는지 확인
    missing_result = safe_load_csv(Path(__file__).with_name("없는파일.json"))
    assert missing_result is None, "존재하지 않는 파일에서 None이 반환되지 않았습니다."
    print("safe_load_csv: 없는 파일 -> None 확인\n")

    # 실제 데이터 로드
    sales = safe_load_csv(DATA_PATH)
    if sales is None:
        print("실제 데이터 로드 실패, 프로그램을 종료합니다.")
        raise SystemExit(1)

    # ---- 2, 3. 검증 파이프라인 데모 (mock 데이터: 정상 4건 + 위반 3건) ----
    mock_data = [
        {"region": "서울", "category": "전자", "amount": 1500, "month": "2024-01"},   # 정상
        {"region": "부산", "category": "의류", "amount": 800,  "month": "2024-01"},   # 정상
        {"region": "대구", "category": "전자", "amount": 950,  "month": "2024-01"},   # 정상
        {"region": "인천", "category": "전자", "amount": 1350, "month": "2024-01"},   # 정상
        {"region": "",     "category": "식품", "amount": 450,  "month": "2024-01"},  # 위반: region 빈 문자열
        {"region": "세종", "category": "전자", "amount": -100, "month": "2024-03"},  # 위반: amount 음수
        {"region": "울산", "category": "의류", "amount": 890,  "month": ""},         # 위반: month 빈 문자열
    ]

    valid, errors = validate_sales(mock_data)

    # 체크포인트: valid 4건 / errors 3건 assert 통과
    assert len(valid) == 4, f"valid 건수가 4건이 아닙니다: {len(valid)}"
    assert len(errors) == 3, f"errors 건수가 3건이 아닙니다: {len(errors)}"
    print(f"\n검증 결과 - valid: {len(valid)}건, errors: {len(errors)}건 (assert 통과)")

    # ---- 4. 결과 저장 + 재로딩 확인 ----
    save_valid_to_csv(valid, VALID_CSV_PATH)
    save_errors_to_json(errors, ERRORS_JSON_PATH)
    print(f"저장 완료: {VALID_CSV_PATH.name}, {ERRORS_JSON_PATH.name}")

    # 체크포인트: 재로딩 후 len(reloaded)==4 통과
    reloaded = reload_csv(VALID_CSV_PATH)
    assert len(reloaded) == 4, f"재로딩한 건수가 4건이 아닙니다: {len(reloaded)}"
    print(f"재로딩 확인: {len(reloaded)}건 (assert 통과)")

    print("\n체크포인트 전체 검증 통과")

    # ---- 실사용 예시: 같은 파이프라인을 실제 100건 데이터에도 적용 ----
    # mock_data는 체크포인트(4/3건) 확인용 테스트 케이스일 뿐,
    # validate_sales/save_* 함수 자체는 실제 데이터에도 그대로 재사용 가능하다.
    print("\n--- 실제 데이터(Python_Practice1_Data.json)에 파이프라인 적용 ---")
    real_valid, real_errors = validate_sales(sales)
    print(f"실제 데이터 검증 결과 - valid: {len(real_valid)}건, errors: {len(real_errors)}건")

    real_valid_path = Path(__file__).with_name("real_valid_sales.csv")
    real_errors_path = Path(__file__).with_name("real_errors.json")
    save_valid_to_csv(real_valid, real_valid_path)
    save_errors_to_json(real_errors, real_errors_path)
    print(f"실제 데이터 저장 완료: {real_valid_path.name}, {real_errors_path.name}")