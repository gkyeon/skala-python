"""
==============================================================
종합실습 : Pydantic v2 스키마 모델
==============================================================
작성자 : 김하연

설명:
    3개 API(Open-Meteo, countries.dev, ip-api) 응답에서 필요한 필드만 뽑아
    타입·범위를 검증하는 Pydantic v2 모델을 정의한다.
    1. WeatherRecord - Open-Meteo 시간대별 기온/강수확률 한 건
    2. CountryInfo   - countries.dev 국가 정보
    3. IpInfo        - ip-api IP 기반 지역 정보

변경내역:
    2026-07-20  최초 작성 (3개 모델, Field(ge=/le=/gt=/min_length= 범위 제약)
==============================================================
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class WeatherRecord(BaseModel):
    """Open-Meteo API 응답의 한 시간대(hourly) 레코드 스키마."""

    time: str = Field(..., min_length=1)  # 비어있으면 안 됨
    temperature_2m: float = Field(..., ge=-50, le=60)  # 현실적인 기온 범위로 제한
    precipitation_probability: int = Field(..., ge=0, le=100)  # 확률이므로 0~100 사이


class CountryInfo(BaseModel):
    """countries.dev API 응답 스키마."""

    name: str = Field(..., min_length=1)
    capital: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    alpha2Code: str = Field(..., min_length=2, max_length=2)  # ISO 3166-1 alpha-2
    population: int = Field(..., gt=0)  # 인구는 양수여야 함
    area: float = Field(..., gt=0)  # 면적(km^2)도 양수여야 함


class IpInfo(BaseModel):
    """ip-api API 응답 스키마."""

    query: str = Field(..., min_length=1)  # 조회한 IP 주소
    country: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    lat: float = Field(..., ge=-90, le=90)  # 위도 범위 제한
    lon: float = Field(..., ge=-180, le=180)  # 경도 범위 제한
    isp: str = Field(..., min_length=1)
