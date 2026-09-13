"""Domain models for external public data ingestion."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class StationLocation:
    """Pre-configured geographic station in an urban area."""

    station_id: str
    name: str
    latitude: float
    longitude: float

    @property
    def entity_id(self) -> str:
        return f"urn:ngsi-v2:AirQualityObserved:{self.station_id}"


@dataclass(frozen=True)
class AirQualitySnapshot:
    pm25: float | None
    pm10: float | None
    co: float | None
    no2: float | None
    o3: float | None


@dataclass(frozen=True)
class WeatherSnapshot:
    temperature: float | None
    humidity: float | None
    pressure: float | None
    wind_speed: float | None


@dataclass(frozen=True)
class MergedStationReading:
    station: StationLocation
    timestamp: datetime
    air_quality: AirQualitySnapshot
    weather: WeatherSnapshot

    def to_fiware_attributes(self) -> dict[str, Any]:
        """Map raw measurements to FIWARE NGSI-v2 attribute structure."""
        attrs: dict[str, Any] = {
            "location": {
                "type": "geo:json",
                "value": {
                    "type": "Point",
                    "coordinates": [self.station.longitude, self.station.latitude],
                },
            },
            "dataProvider": {
                "type": "Text",
                "value": "Open-Meteo Public API (real-time)",
            },
        }

        if self.air_quality.pm25 is not None:
            attrs["pm25"] = {
                "type": "Number",
                "value": self.air_quality.pm25,
                "metadata": {"unitCode": {"value": "GQ"}},
            }
        if self.air_quality.pm10 is not None:
            attrs["pm10"] = {
                "type": "Number",
                "value": self.air_quality.pm10,
                "metadata": {"unitCode": {"value": "GQ"}},
            }
        if self.air_quality.co is not None:
            attrs["co"] = {
                "type": "Number",
                "value": self.air_quality.co,
                "metadata": {"unitCode": {"value": "GP"}},
            }
        if self.air_quality.no2 is not None:
            attrs["no2"] = {
                "type": "Number",
                "value": self.air_quality.no2,
                "metadata": {"unitCode": {"value": "GQ"}},
            }
        if self.air_quality.o3 is not None:
            attrs["o3"] = {
                "type": "Number",
                "value": self.air_quality.o3,
                "metadata": {"unitCode": {"value": "GQ"}},
            }

        if self.weather.temperature is not None:
            attrs["temperature"] = {
                "type": "Number",
                "value": self.weather.temperature,
                "metadata": {"unitCode": {"value": "CEL"}},
            }
        if self.weather.humidity is not None:
            attrs["humidity"] = {
                "type": "Number",
                "value": self.weather.humidity,
                "metadata": {"unitCode": {"value": "P1"}},
            }
        if self.weather.pressure is not None:
            attrs["atmosphericPressure"] = {
                "type": "Number",
                "value": self.weather.pressure,
                "metadata": {"unitCode": {"value": "A97"}},
            }
        if self.weather.wind_speed is not None:
            attrs["windSpeed"] = {
                "type": "Number",
                "value": self.weather.wind_speed,
                "metadata": {"unitCode": {"value": "KMH"}},
            }

        return attrs


def get_default_hcmc_stations() -> list[StationLocation]:
    """Default real-world urban observation points in Ho Chi Minh City."""
    return [
        StationLocation(
            "HCM-District1-Center", "District 1 (City Center / Ben Thanh)", 10.7769, 106.7009
        ),
        StationLocation(
            "HCM-District3-TurtleLake", "District 3 (Turtle Lake / Vo Van Tan)", 10.7828, 106.6961
        ),
        StationLocation(
            "HCM-District7-PhuMyHung", "District 7 (Phu My Hung Urban Area)", 10.7290, 106.7218
        ),
        StationLocation(
            "HCM-ThuDuc-HiTechPark", "Thu Duc City (Saigon Hi-Tech Park)", 10.8500, 106.7719
        ),
        StationLocation(
            "HCM-TanBinh-Airport", "Tan Binh District (Tan Son Nhat Area)", 10.8015, 106.6565
        ),
        StationLocation(
            "HCM-BinhThanh-HangXanh",
            "Binh Thanh District (Hang Xanh Intersection)",
            10.8015,
            106.7115,
        ),
    ]
