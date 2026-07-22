"""
==============================================================
종합실습1 : 데이터 수집 미니 파이프라인
==============================================================
작성자 : 김하연

설명:
    Open-Meteo(서울 3일 기온·강수확률), countries.dev(한국 국가 정보),
    ip-api(IP 기반 지역 정보) 3개 API를 대상으로 아래 파이프라인을 수행한다.
    1. 비동기 수집 (asyncio + httpx, asyncio.gather()로 동시 요청)
    2. 스키마 검증 (Pydantic v2, mission/schemas.py의 모델 사용)
    3. 저장 및 성능 비교 (CSV/Parquet 각각 저장·재읽기, 소요 시간 측정)

변경내역:
    2026-07-20  최초 작성 (fetch_json, collect_all, validate_*, benchmark_formats)
    2026-07-20  validate_weather에 'hourly' 키 누락 방어 추가
                (country/ip는 실패해도 None을 반환하는데 weather만 KeyError로
                죽는 비일관성이 있어서 통일)
    2026-07-20  _check_required_keys / _timed 헬퍼로 중복 로직 통합
                (validate_country/validate_ip의 키 검사, benchmark_formats의
                시간 측정 패턴이 각각 반복되고 있어서 정리)
    2026-07-20  OUTPUT_DIR.mkdir(exist_ok=True) 추가
                (output/는 .gitignore 대상이라 새로 clone하면 폴더가 없어서
                저장이 실패하는 문제 방지)
==============================================================
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Callable

import httpx
import pandas as pd
from pydantic import ValidationError

from schemas import CountryInfo, IpInfo, WeatherRecord

# 서울 좌표(위도/경도) 기준 3일치 시간대별 기온·강수확률, timezone을 명시하지 않으면
# UTC로 내려와서 실제 서울 시간과 9시간 어긋난다
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=37.5665&longitude=126.9780"
    "&hourly=temperature_2m,precipitation_probability"
    "&forecast_days=3&timezone=Asia/Seoul"
)
COUNTRY_URL = "https://countries.dev/alpha/KOR"
IP_URL = "http://ip-api.com/json/8.8.8.8"

# 스크립트 파일 위치 기준으로 경로를 잡아서, 어느 폴더에서 실행하든 찾을 수 있게 함
OUTPUT_DIR = Path(__file__).parent / "output"


# ======================
# 1. 비동기 수집
# ======================

async def fetch_json(client: httpx.AsyncClient, url: str) -> dict:
    """url을 GET 요청해서 JSON(dict)으로 반환한다.

    API 하나가 실패해도 asyncio.gather()로 묶인 나머지 수집이 계속되도록,
    예외를 그대로 던지지 않고 빈 dict를 반환하며 원인만 출력한다.
    """
    try:
        response = await client.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        # 연결 실패, 타임아웃 등 요청 자체가 안 된 경우
        print(f"[오류] 요청 실패: {e}")
        return {}
    except httpx.HTTPStatusError as e:
        # 요청은 갔지만 4xx/5xx 응답을 받은 경우
        print(f"[오류] HTTP 상태 코드 오류: {e.response.status_code} - {e}")
        return {}


async def collect_all() -> tuple[dict, dict, dict]:
    """weather/country/ip 3개 API를 asyncio.gather()로 동시에 수집한다."""
    async with httpx.AsyncClient() as client:
        return await asyncio.gather(
            fetch_json(client, WEATHER_URL),
            fetch_json(client, COUNTRY_URL),
            fetch_json(client, IP_URL),
        )


# ======================
# 2. 스키마 검증
# ======================

def _check_required_keys(raw: dict, keys: list[str], model_name: str) -> bool:
    """raw에 keys가 모두 있는지 확인한다.

    (validate_country/validate_ip에서 동일한 "필수 키 확인" 로직이
    반복되어서 헬퍼로 뽑았다.)
    """
    for key in keys:
        if key not in raw:
            print(f"[오류] {model_name} 검증 실패: '{key}' 키가 없습니다.")
            return False
    return True


def validate_weather(raw: dict) -> list[WeatherRecord]:
    """raw['hourly']의 time/temperature_2m/precipitation_probability 배열을
    같은 index끼리 묶어 WeatherRecord로 검증한다.
    레코드 하나가 검증에 실패해도 나머지는 계속 진행한다(부분 실패 허용).
    """
    if not _check_required_keys(raw, ["hourly"], "WeatherRecord"):
        return []

    records = []
    hourly = raw["hourly"]
    for i in range(len(hourly["time"])):
        try:
            record = WeatherRecord(
                time=hourly["time"][i],
                temperature_2m=hourly["temperature_2m"][i],
                precipitation_probability=hourly["precipitation_probability"][i],
            )
            records.append(record)
        except ValidationError as e:
            # 체크포인트: 범위를 벗어난 값이 있어도 전체가 아니라 해당 시간대만 제외
            print(f"[오류] WeatherRecord 검증 실패: {e}")
    return records


def validate_country(raw: dict) -> CountryInfo | None:
    """raw를 CountryInfo로 검증한다. 실패 시 None을 반환한다."""
    keys = ["name", "capital", "region", "alpha2Code", "population", "area"]
    if not _check_required_keys(raw, keys, "CountryInfo"):
        return None
    try:
        return CountryInfo(**{key: raw[key] for key in keys})
    except ValidationError as e:
        print(f"[오류] CountryInfo 검증 실패: {e}")
        return None


def validate_ip(raw: dict) -> IpInfo | None:
    """raw를 IpInfo로 검증한다. 실패 시 None을 반환한다."""
    keys = ["query", "country", "city", "lat", "lon", "isp"]
    if not _check_required_keys(raw, keys, "IpInfo"):
        return None
    try:
        return IpInfo(**{key: raw[key] for key in keys})
    except ValidationError as e:
        print(f"[오류] IpInfo 검증 실패: {e}")
        return None


# ======================
# 3. 저장 및 성능 비교
# ======================

def _timed(func: Callable[[], None]) -> float:
    """func()를 실행하고 걸린 시간(초)을 반환한다.

    (benchmark_formats에서 CSV/Parquet 쓰기·읽기 4번 모두
    "시작 시각 기록 -> 실행 -> 끝난 시각 - 시작 시각" 패턴이 반복되어서 헬퍼로 뽑았다.)
    """
    start = time.perf_counter()
    func()
    return time.perf_counter() - start


def benchmark_formats(df: pd.DataFrame, name: str) -> dict:
    """df를 CSV/Parquet로 각각 저장·재읽기 하며 걸린 시간(ms)을 측정해 반환한다.

    주의: pyarrow는 프로세스에서 처음 쓰일 때 초기화 비용이 붙어서
    가장 먼저 호출되는 데이터셋의 Parquet 측정치만 비정상적으로 크게 나올 수 있다.
    (main()에서 여러 데이터셋 결과를 표로 모아 출력하기 위해 dict로 반환한다.)
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    csv_path = OUTPUT_DIR / f"{name}.csv"
    parquet_path = OUTPUT_DIR / f"{name}.parquet"

    csv_write_time = _timed(lambda: df.to_csv(csv_path, index=False))
    parquet_write_time = _timed(lambda: df.to_parquet(parquet_path))
    csv_read_time = _timed(lambda: pd.read_csv(csv_path))
    parquet_read_time = _timed(lambda: pd.read_parquet(parquet_path))

    return {
        "dataset": name,
        "rows": len(df),
        "csv_write_ms": csv_write_time * 1000,
        "csv_read_ms": csv_read_time * 1000,
        "parquet_write_ms": parquet_write_time * 1000,
        "parquet_read_ms": parquet_read_time * 1000,
    }


def print_benchmark_table(results: list[dict]) -> None:
    """benchmark_formats() 결과들을 한눈에 비교할 수 있는 표로 출력한다."""
    header = f"{'dataset':<10} {'rows':>5} {'csv_write':>10} {'csv_read':>10} {'parquet_write':>14} {'parquet_read':>13}"
    print("\n=== 저장 형식별 성능 비교 (ms) ===")
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['dataset']:<10} {r['rows']:>5} "
            f"{r['csv_write_ms']:>10.2f} {r['csv_read_ms']:>10.2f} "
            f"{r['parquet_write_ms']:>14.2f} {r['parquet_read_ms']:>13.2f}"
        )


async def main() -> None:
    weather_raw, country_raw, ip_raw = await collect_all()
    print("3개 API 동시 수집 완료")

    weather_records = validate_weather(weather_raw)
    country_record = validate_country(country_raw)
    ip_record = validate_ip(ip_raw)

    print("\n=== 수집 및 검증 결과 ===")
    print(f"weather : {len(weather_records)}건 검증 통과")
    print(f"country : {'통과' if country_record else '실패'}")
    print(f"ip      : {'통과' if ip_record else '실패'}")

    # model_dump(): pydantic 객체를 dict로 변환해 DataFrame으로 바로 만들 수 있게 함
    results = []
    if weather_records:
        weather_df = pd.DataFrame([r.model_dump() for r in weather_records])
        results.append(benchmark_formats(weather_df, "weather"))

    if country_record:
        country_df = pd.DataFrame([country_record.model_dump()])
        results.append(benchmark_formats(country_df, "country"))

    if ip_record:
        ip_df = pd.DataFrame([ip_record.model_dump()])
        results.append(benchmark_formats(ip_df, "ip"))

    print_benchmark_table(results)


if __name__ == "__main__":
    asyncio.run(main())
