"""3개 API 응답에 대한 Pydantic v2 검증 모델."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WeatherRecord(BaseModel):
    """Open-Meteo 시간대별 기온/강수확률 레코드."""

    time: str
    temperature_2m: float = Field(ge=-50, le=60)
    precipitation_probability: int = Field(ge=0, le=100)


class CountryInfo(BaseModel):
    """countries.dev 국가 정보."""

    name: str
    capital: str
    region: str
    alpha2Code: str = Field(min_length=2, max_length=2)
    population: int = Field(gt=0)
    area: float = Field(gt=0)


class IpInfo(BaseModel):
    """ip-api IP 기반 지역 정보."""

    query: str
    country: str
    city: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    isp: str
