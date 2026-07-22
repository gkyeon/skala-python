"""
==============================================================
종합실습 : Pydantic v2 스키마 검증 테스트
==============================================================
작성자 : 김하연

설명:
    schemas.py의 3개 모델(WeatherRecord, CountryInfo, IpInfo)이
    정상 값은 통과시키고, 범위를 벗어나거나 타입이 잘못된 값은
    ValidationError로 막는지 pytest로 확인한다.

변경내역:
    2026-07-20  최초 작성 (모델별 정상 케이스 1건 + 위반 케이스 1건 이상)
    2026-07-22  mission/ -> 종합실습 01/ 폴더명 변경(공백 포함)에 맞춰
                패키지 임포트 대신 sys.path 방식으로 변경
==============================================================
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# 폴더명에 공백이 있어 "종합실습 01.schemas"처럼 패키지 경로로 임포트할 수 없음
# -> 이 폴더 자체를 sys.path에 추가하고 schemas를 바로 임포트
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas import CountryInfo, IpInfo, WeatherRecord


# ======================
# WeatherRecord
# ======================

def test_weather_record_valid():
    """정상 값이면 필드가 그대로 들어간다."""
    record = WeatherRecord(
        time="2026-07-20T00:00", temperature_2m=25.3, precipitation_probability=40
    )
    assert record.temperature_2m == 25.3
    assert record.precipitation_probability == 40


def test_weather_record_precipitation_out_of_range():
    """확률은 0~100 사이만 허용 -> 150은 ValidationError."""
    with pytest.raises(ValidationError):
        WeatherRecord(time="2026-07-20T00:00", temperature_2m=25.3, precipitation_probability=150)


def test_weather_record_temperature_type_error():
    """temperature_2m은 숫자여야 함 -> 문자열이면 ValidationError."""
    with pytest.raises(ValidationError):
        WeatherRecord(
            time="2026-07-20T00:00", temperature_2m="hot", precipitation_probability=40
        )


# ======================
# CountryInfo
# ======================

def test_country_info_valid():
    """정상 값이면 필드가 그대로 들어간다."""
    country = CountryInfo(
        name="Korea (Republic of)",
        capital="Seoul",
        region="Asia",
        alpha2Code="KR",
        population=51780579,
        area=100210,
    )
    assert country.alpha2Code == "KR"


def test_country_info_negative_population_rejected():
    """인구는 양수만 허용 -> 음수면 ValidationError."""
    with pytest.raises(ValidationError):
        CountryInfo(
            name="Korea (Republic of)",
            capital="Seoul",
            region="Asia",
            alpha2Code="KR",
            population=-1,
            area=100210,
        )


# ======================
# IpInfo
# ======================

def test_ip_info_latitude_out_of_range():
    """위도는 -90~90 사이만 허용 -> 999는 ValidationError."""
    with pytest.raises(ValidationError):
        IpInfo(
            query="8.8.8.8",
            country="United States",
            city="Ashburn",
            lat=999.0,
            lon=-77.5,
            isp="Google LLC",
        )
