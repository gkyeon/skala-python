"""데이터 수집 미니 파이프라인.

3개 API(Open-Meteo, countries.dev, ip-api)를 asyncio + httpx로 동시 수집하고,
Pydantic v2로 스키마를 검증한 뒤 CSV/Parquet로 저장하며 읽기/쓰기 성능을 비교한다.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import httpx
import pandas as pd
from pydantic import ValidationError

from schemas import CountryInfo, IpInfo, WeatherRecord

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=37.5665&longitude=126.9780"
    "&hourly=temperature_2m,precipitation_probability"
    "&forecast_days=3&timezone=Asia/Seoul"
)
COUNTRY_URL = "https://countries.dev/alpha/KOR"
IP_URL = "http://ip-api.com/json/8.8.8.8"

OUTPUT_DIR = Path(__file__).parent / "output"


async def fetch_json(client: httpx.AsyncClient, url: str) -> dict:
    response = await client.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


async def collect_all() -> tuple[dict, dict, dict]:
    async with httpx.AsyncClient() as client:
        weather_raw, country_raw, ip_raw = await asyncio.gather(
            fetch_json(client, WEATHER_URL),
            fetch_json(client, COUNTRY_URL),
            fetch_json(client, IP_URL),
        )
    return weather_raw, country_raw, ip_raw


def validate_weather(raw: dict) -> list[WeatherRecord]:
    hourly = raw["hourly"]
    records = []
    for i, time_str in enumerate(hourly["time"]):
        try:
            record = WeatherRecord(
                time=time_str,
                temperature_2m=hourly["temperature_2m"][i],
                precipitation_probability=hourly["precipitation_probability"][i],
            )
        except ValidationError as e:
            print(f"[weather] 검증 실패 (index={i}): {e}")
            continue
        records.append(record)
    return records


def validate_country(raw: dict) -> CountryInfo | None:
    try:
        return CountryInfo(**raw)
    except ValidationError as e:
        print(f"[country] 검증 실패: {e}")
        return None


def validate_ip(raw: dict) -> IpInfo | None:
    try:
        return IpInfo(**raw)
    except ValidationError as e:
        print(f"[ip] 검증 실패: {e}")
        return None


def warm_up_parquet_engine() -> None:
    """pyarrow의 최초 호출 시 초기화 비용이 이후 측정치를 왜곡하지 않도록 미리 소모한다."""
    warm_path = OUTPUT_DIR / "_warmup.parquet"
    OUTPUT_DIR.mkdir(exist_ok=True)
    pd.DataFrame({"x": [0]}).to_parquet(warm_path, index=False)
    pd.read_parquet(warm_path)
    warm_path.unlink()


def benchmark_formats(df: pd.DataFrame, name: str) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    csv_path = OUTPUT_DIR / f"{name}.csv"
    parquet_path = OUTPUT_DIR / f"{name}.parquet"

    start = time.perf_counter()
    df.to_csv(csv_path, index=False)
    csv_write = time.perf_counter() - start

    start = time.perf_counter()
    df.to_parquet(parquet_path, index=False)
    parquet_write = time.perf_counter() - start

    start = time.perf_counter()
    pd.read_csv(csv_path)
    csv_read = time.perf_counter() - start

    start = time.perf_counter()
    pd.read_parquet(parquet_path)
    parquet_read = time.perf_counter() - start

    print(
        f"[{name}] rows={len(df)} | "
        f"CSV write={csv_write * 1000:.2f}ms read={csv_read * 1000:.2f}ms | "
        f"Parquet write={parquet_write * 1000:.2f}ms read={parquet_read * 1000:.2f}ms"
    )


async def main() -> None:
    weather_raw, country_raw, ip_raw = await collect_all()
    print("3개 API 동시 수집 완료")

    weather_records = validate_weather(weather_raw)
    country_record = validate_country(country_raw)
    ip_record = validate_ip(ip_raw)

    print(f"weather: {len(weather_records)}건 검증 통과")
    print(f"country: {'통과' if country_record else '실패'}")
    print(f"ip: {'통과' if ip_record else '실패'}")

    warm_up_parquet_engine()

    if weather_records:
        weather_df = pd.DataFrame([r.model_dump() for r in weather_records])
        benchmark_formats(weather_df, "weather")

    if country_record:
        country_df = pd.DataFrame([country_record.model_dump()])
        benchmark_formats(country_df, "country")

    if ip_record:
        ip_df = pd.DataFrame([ip_record.model_dump()])
        benchmark_formats(ip_df, "ip")


if __name__ == "__main__":
    asyncio.run(main())
