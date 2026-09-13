"""Open-Meteo public API client implementation using httpx."""

import asyncio
from datetime import UTC, datetime

import httpx
import structlog

from app.modules.external_ingest.domain.client_interface import IOpenMeteoClient
from app.modules.external_ingest.domain.models import (
    AirQualitySnapshot,
    MergedStationReading,
    StationLocation,
    WeatherSnapshot,
)

logger = structlog.get_logger(__name__)

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


class OpenMeteoClient(IOpenMeteoClient):
    """Concrete client querying Open-Meteo public endpoints."""

    def __init__(self, timeout_seconds: float = 8.0) -> None:
        self._timeout = timeout_seconds

    async def fetch_reading(self, station: StationLocation) -> MergedStationReading | None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            headers = {"User-Agent": "AegisPlatform-UrbanData/1.0"}

            aq_params: dict[str, str | float] = {
                "latitude": station.latitude,
                "longitude": station.longitude,
                "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone",
            }
            weather_params: dict[str, str | float] = {
                "latitude": station.latitude,
                "longitude": station.longitude,
                "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m",
            }

            try:
                aq_resp, weather_resp = await asyncio.gather(
                    client.get(AIR_QUALITY_URL, params=aq_params, headers=headers),
                    client.get(WEATHER_URL, params=weather_params, headers=headers),
                    return_exceptions=True,
                )

                aq_data = (
                    aq_resp.json().get("current", {})
                    if isinstance(aq_resp, httpx.Response) and aq_resp.is_success
                    else {}
                )
                weather_data = (
                    weather_resp.json().get("current", {})
                    if isinstance(weather_resp, httpx.Response) and weather_resp.is_success
                    else {}
                )

                air_quality = AirQualitySnapshot(
                    pm25=aq_data.get("pm2_5"),
                    pm10=aq_data.get("pm10"),
                    co=aq_data.get("carbon_monoxide"),
                    no2=aq_data.get("nitrogen_dioxide"),
                    o3=aq_data.get("ozone"),
                )

                weather = WeatherSnapshot(
                    temperature=weather_data.get("temperature_2m"),
                    humidity=weather_data.get("relative_humidity_2m"),
                    pressure=weather_data.get("surface_pressure"),
                    wind_speed=weather_data.get("wind_speed_10m"),
                )

                return MergedStationReading(
                    station=station,
                    timestamp=datetime.now(UTC),
                    air_quality=air_quality,
                    weather=weather,
                )
            except Exception as exc:
                logger.warning(
                    "failed to query Open-Meteo for station",
                    station_id=station.station_id,
                    error=str(exc),
                )
                return None

    async def fetch_all_readings(
        self, stations: list[StationLocation]
    ) -> list[MergedStationReading]:
        tasks = [self.fetch_reading(station) for station in stations]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
