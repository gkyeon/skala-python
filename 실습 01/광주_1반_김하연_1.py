"""
==============================================================
실습1 : 자료구조 집계, 컴프리헨션, 제너레이터 (Sales 데이터)
==============================================================
작성자 : 김하연

설명:
    Python_Practice2_Data.json 의 sales 데이터를 불러와 아래 기능을 수행한다.
    1. 리스트/딕셔너리 컴프리헨션 (amount 필터링, 지역별 총매출)
    2. Counter / defaultdict (지역별 거래 건수, 카테고리별 amount 리스트)
    3. 제너레이터 (amount > 1000 필터링) vs 리스트 메모리 비교
    4. 종합 - 월별·카테고리별 매출 집계 (컴프리헨션 + defaultdict), top3 정렬

변경내역:
    2026-07-20  최초 작성
    2026-07-20  region_total 필터링 기준(amount_1000) 반영, top3 정렬 추가
    2026-07-20  JSON 파일 로딩 함수 추가, 예외처리 반영, 변수명 중복 정리
    2026-07-20  __file__ 기준 경로 처리(cwd 무관), AMOUNT_THRESHOLD 상수화,
                bool 타입 방어 추가
    2026-07-20  4개 체크포인트 self-check assert 추가
    2026-07-20  region_total/monthly_category_total 그룹핑+합산 로직을
                group_and_sum() 헬퍼로 통합해 중복 제거
==============================================================
"""

import sys
import json
from collections import Counter, defaultdict
from pathlib import Path


AMOUNT_THRESHOLD = 1000
# 데이터는 프로젝트 루트의 data/ 폴더에 모아둠 (여러 실습이 같은 데이터를 공유)
# -> 스크립트 위치(실습 01/) 기준 한 단계 위(data-project/)로 올라가서 data/를 찾음
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "Python_Practice2_Data.json"


def load_sales_json(filepath):
    """
    JSON 파일에서 sales 데이터를 읽어 리스트로 반환한다.
    파일이 없거나 JSON 형식이 잘못된 경우 오류 메시지를 출력하고 빈 리스트를 반환한다.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[오류] 파일을 찾을 수 없습니다: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"[오류] JSON 형식이 올바르지 않습니다: {e}")
        return []


def get_valid_amount(sale):
    """
    거래(dict) 하나에서 amount 값을 안전하게 추출한다.
    key가 없거나 숫자가 아니면(bool 포함) 경고를 출력하고 None을 반환한다.
    """
    try:
        amount = sale["amount"]
    except KeyError:
        print(f"[경고] amount 키 없음, 해당 거래 제외: {sale}")
        return None
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        print(f"[경고] amount가 숫자가 아님, 해당 거래 제외: {sale}")
        return None
    return amount


def filter_amount(sales):
    """amount > AMOUNT_THRESHOLD인 거래만 순차적으로 yield하는 제너레이터."""
    for sale in sales:
        amount = get_valid_amount(sale)
        if amount is not None and amount > AMOUNT_THRESHOLD:
            yield sale


def group_and_sum(data, key_func):
    """
    key_func(item) 기준으로 amount를 그룹핑해서 합산한 dict를 반환한다.
    (region_total, monthly_category_total에서 동일하게 재사용해 중복 제거)
    """
    groups = defaultdict(list)
    for item in data:
        groups[key_func(item)].append(item["amount"])
    return {key: sum(amounts) for key, amounts in groups.items()}


if __name__ == "__main__":

    sales = load_sales_json(DATA_PATH)

    if not sales:
        print("불러온 데이터가 없어 프로그램을 종료합니다.")
        sys.exit(1)

    # ======================
    # 1. 리스트/딕셔너리 컴프리헨션
    # ======================

    # amount가 AMOUNT_THRESHOLD 이상인 데이터만 필터링
    amount_1000 = [
        sale for sale in sales
        if (get_valid_amount(sale) or 0) >= AMOUNT_THRESHOLD
    ]

    # 지역별 총매출: group_and_sum으로 그룹핑+합산을 한 번에 처리
    region_total = group_and_sum(amount_1000, key_func=lambda s: s["region"])

    # 체크포인트: region_total 값 정확
    # -> 그룹핑 과정에서 amount_1000의 금액이 하나도 누락/중복되지 않았는지 합계로 검증
    assert sum(region_total.values()) == sum(sale["amount"] for sale in amount_1000), (
        "region_total 합계가 필터링된 거래(amount_1000) 총합과 일치하지 않습니다."
    )

    print("필터링된 거래 수:", len(amount_1000))
    print("지역별 총매출:", region_total)
    print("region_total 검증 통과 (assert)")

    # ======================
    # 2. Counter, defaultdict
    # ======================

    # Counter: 지역명이 몇 번 등장하는지(=거래 건수)를 한 줄로 자동 집계
    region_count = Counter(sale["region"] for sale in sales)
    print("\n지역별 거래 건수:", region_count)
    # most_common(): 건수가 많은 지역부터 내림차순으로 정렬해서 반환
    print("거래 건수 많은 순:", region_count.most_common())

    # 체크포인트: Counter.most_common() 순서 정확
    # -> 반환된 건수들이 실제로 내림차순인지 확인
    counts_only = [count for _, count in region_count.most_common()]
    assert counts_only == sorted(counts_only, reverse=True), (
        "Counter.most_common() 결과가 내림차순으로 정렬되어 있지 않습니다."
    )
    print("Counter.most_common() 순서 검증 통과 (assert)")

    # defaultdict(list): 처음 보는 카테고리 키에 접근해도 KeyError 없이
    # 자동으로 빈 리스트가 생성되므로, 'if key not in dict' 분기 없이 바로 append 가능
    category_amounts = defaultdict(list)
    for sale in sales:
        category_amounts[sale["category"]].append(sale["amount"])
    print("\n카테고리별 amount 리스트:", dict(category_amounts))

    # ======================
    # 3. 제너레이터 메모리 비교
    # ======================

    # list_sales: 조건에 맞는 모든 데이터를 메모리에 한 번에 다 올려놓음
    list_sales = [sale for sale in sales if sale["amount"] > AMOUNT_THRESHOLD]
    # gen_sales: filter_amount()는 값을 미리 계산해두지 않고, 호출될 때마다
    # 하나씩만 만들어내는 제너레이터라서 객체 자체의 크기가 훨씬 작음
    gen_sales = filter_amount(sales)

    list_size = sys.getsizeof(list_sales)
    gen_size = sys.getsizeof(gen_sales)
    print("\nlist_sales 메모리:", list_size, "bytes")
    print("gen_sales 메모리:", gen_size, "bytes")

    # 체크포인트: generator sys.getsizeof < list 확인
    # (list로 변환해서 비교하지 않고, 제너레이터 객체 자체의 크기로 비교)
    assert gen_size < list_size, "제너레이터가 리스트보다 메모리를 더 적게 쓰지 않습니다."
    print("제너레이터 메모리 검증 통과 (assert)")

    # ======================
    # 4. 종합 - 월별 카테고리 매출 집계
    # ======================

    # 월별·카테고리별 총매출: region_total과 동일한 group_and_sum 재사용 (키만 튜플로 변경)
    monthly_category_total = group_and_sum(
        sales, key_func=lambda s: (s["month"], s["category"])
    )

    # item[1](총매출) 기준으로 내림차순 정렬 후 상위 3개만 슬라이싱
    top3 = sorted(monthly_category_total.items(), key=lambda x: x[1], reverse=True)[:3]

    print("\n월별-카테고리별 총매출:", monthly_category_total)
    print("총매출 상위 3개 (월, 카테고리):", top3)

    # 체크포인트: top3 금액 내림차순 정렬 정확
    top3_amounts = [amount for _, amount in top3]
    assert len(top3) == 3, "top3 개수가 3개가 아닙니다."
    assert top3_amounts == sorted(top3_amounts, reverse=True), (
        "top3이 금액 기준 내림차순으로 정렬되어 있지 않습니다."
    )
    print("top3 정렬 검증 통과 (assert)")

    print("\n체크포인트 4개 전체 검증 통과")