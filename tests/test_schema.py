"""
==============================================================
종합실습 : Pydantic v2 스키마 검증 테스트
==============================================================
작성자 : 김하연

설명:
    mission/schemas.py의 3개 모델(WeatherRecord, CountryInfo, IpInfo)이
    정상 값은 통과시키고, 범위를 벗어나거나 타입이 잘못된 값은
    ValidationError로 막는지 pytest로 확인한다.

변경내역:
    2026-07-20  최초 작성 (모델별 정상 케이스 1건 + 위반 케이스 1건 이상)
==============================================================
"""

import pytest
from pydantic import ValidationError

from mission.schemas import CountryInfo, IpInfo, WeatherRecord


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
