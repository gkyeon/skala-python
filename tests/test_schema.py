"""Pydantic v2 스키마 검증 테스트."""

import pytest
from pydantic import ValidationError

from mission.schemas import CountryInfo, IpInfo, WeatherRecord


def test_weather_record_valid():
    record = WeatherRecord(
        time="2026-07-20T00:00", temperature_2m=25.3, precipitation_probability=40
    )
    assert record.temperature_2m == 25.3
    assert record.precipitation_probability == 40


def test_weather_record_precipitation_out_of_range():
    with pytest.raises(ValidationError):
        WeatherRecord(time="2026-07-20T00:00", temperature_2m=25.3, precipitation_probability=150)


def test_weather_record_temperature_type_error():
    with pytest.raises(ValidationError):
        WeatherRecord(
            time="2026-07-20T00:00", temperature_2m="hot", precipitation_probability=40
        )


def test_country_info_valid():
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
    with pytest.raises(ValidationError):
        CountryInfo(
            name="Korea (Republic of)",
            capital="Seoul",
            region="Asia",
            alpha2Code="KR",
            population=-1,
            area=100210,
        )


def test_ip_info_latitude_out_of_range():
    with pytest.raises(ValidationError):
        IpInfo(
            query="8.8.8.8",
            country="United States",
            city="Ashburn",
            lat=999.0,
            lon=-77.5,
            isp="Google LLC",
        )
