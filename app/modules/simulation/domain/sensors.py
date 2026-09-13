"""Domain generators for realistic Urban IoT sensors."""

import random
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any


class BaseSensor(ABC):
    """Abstract base sensor."""

    def __init__(self, sensor_id: str, entity_type: str, location: dict[str, float]) -> None:
        self.sensor_id = sensor_id
        self.entity_type = entity_type
        self.location = location  # {"lat": float, "lng": float}

    @abstractmethod
    def sample(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """
        Generate a sample reading.
        Returns:
            (entity_attributes_dict, list_of_observation_dicts)
        """
        raise NotImplementedError


class AirQualitySensor(BaseSensor):
    """Simulates an urban air quality station (PM2.5, PM10, CO2, Temp, Humidity)."""

    def __init__(self, station_id: str, location: dict[str, float]) -> None:
        super().__init__(
            sensor_id=f"urn:ngsi-v2:AirQualityObserved:{station_id}",
            entity_type="AirQualityObserved",
            location=location,
        )
        self.base_pm25 = random.uniform(25.0, 55.0)
        self.base_temp = random.uniform(28.0, 34.0)

    def sample(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        now = datetime.now(UTC)
        # Random fluctuations with bounds
        pm25 = max(5.0, round(self.base_pm25 + random.gauss(0, 5.0), 1))
        pm10 = max(10.0, round(pm25 * random.uniform(1.2, 1.8), 1))
        temp = round(self.base_temp + random.gauss(0, 1.0), 1)
        humidity = round(random.uniform(60.0, 90.0), 1)
        co2 = round(random.uniform(400.0, 850.0), 0)

        attrs = {
            "pm25": {"type": "Number", "value": pm25, "metadata": {"unitCode": {"value": "GQ"}}},
            "pm10": {"type": "Number", "value": pm10, "metadata": {"unitCode": {"value": "GQ"}}},
            "temperature": {
                "type": "Number",
                "value": temp,
                "metadata": {"unitCode": {"value": "CEL"}},
            },
            "humidity": {
                "type": "Number",
                "value": humidity,
                "metadata": {"unitCode": {"value": "P1"}},
            },
            "co2": {"type": "Number", "value": co2, "metadata": {"unitCode": {"value": "59"}}},
            "location": {
                "type": "geo:json",
                "value": {
                    "type": "Point",
                    "coordinates": [self.location["lng"], self.location["lat"]],
                },
            },
        }

        obs = [
            {
                "entity_id": self.sensor_id,
                "attribute_name": "pm25",
                "value_numeric": pm25,
                "unit": "ug/m3",
                "timestamp": now,
            },
            {
                "entity_id": self.sensor_id,
                "attribute_name": "pm10",
                "value_numeric": pm10,
                "unit": "ug/m3",
                "timestamp": now,
            },
            {
                "entity_id": self.sensor_id,
                "attribute_name": "temperature",
                "value_numeric": temp,
                "unit": "CEL",
                "timestamp": now,
            },
            {
                "entity_id": self.sensor_id,
                "attribute_name": "humidity",
                "value_numeric": humidity,
                "unit": "P1",
                "timestamp": now,
            },
            {
                "entity_id": self.sensor_id,
                "attribute_name": "co2",
                "value_numeric": co2,
                "unit": "ppm",
                "timestamp": now,
            },
        ]

        return attrs, obs


class TrafficFlowSensor(BaseSensor):
    """Simulates an urban intersection traffic flow monitor."""

    def __init__(self, intersection_id: str, location: dict[str, float]) -> None:
        super().__init__(
            sensor_id=f"urn:ngsi-v2:TrafficFlowObserved:{intersection_id}",
            entity_type="TrafficFlowObserved",
            location=location,
        )

    def sample(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        now = datetime.now(UTC)
        vehicle_count = max(0, int(random.gauss(65, 20)))
        speed = round(max(5.0, min(80.0, 60.0 - (vehicle_count * 0.3) + random.gauss(0, 3))), 1)
        congestion = round(min(1.0, max(0.0, vehicle_count / 100.0)), 2)

        attrs = {
            "vehicleCount": {"type": "Number", "value": vehicle_count},
            "averageSpeed": {
                "type": "Number",
                "value": speed,
                "metadata": {"unitCode": {"value": "KMH"}},
            },
            "congestionLevel": {"type": "Number", "value": congestion},
            "location": {
                "type": "geo:json",
                "value": {
                    "type": "Point",
                    "coordinates": [self.location["lng"], self.location["lat"]],
                },
            },
        }

        obs = [
            {
                "entity_id": self.sensor_id,
                "attribute_name": "vehicleCount",
                "value_numeric": float(vehicle_count),
                "unit": "count",
                "timestamp": now,
            },
            {
                "entity_id": self.sensor_id,
                "attribute_name": "averageSpeed",
                "value_numeric": speed,
                "unit": "km/h",
                "timestamp": now,
            },
            {
                "entity_id": self.sensor_id,
                "attribute_name": "congestionLevel",
                "value_numeric": congestion,
                "unit": "ratio",
                "timestamp": now,
            },
        ]

        return attrs, obs


def get_default_urban_sensor_fleet() -> list[BaseSensor]:
    """Generates a default fleet of realistic urban sensors located around Ho Chi Minh City."""
    return [
        AirQualitySensor("HCM-District1-BenThanh", {"lat": 10.7725, "lng": 106.6980}),
        AirQualitySensor("HCM-District1-NguyenHue", {"lat": 10.7741, "lng": 106.7032}),
        AirQualitySensor("HCM-District3-TurtleLake", {"lat": 10.7828, "lng": 106.6961}),
        AirQualitySensor("HCM-District7-PhuMyHung", {"lat": 10.7290, "lng": 106.7218}),
        AirQualitySensor("HCM-District2-ThaoDien", {"lat": 10.8035, "lng": 106.7328}),
        AirQualitySensor("HCM-BinhThanh-HangXanh", {"lat": 10.8015, "lng": 106.7115}),
        TrafficFlowSensor("Inter-D1-LeLoi-Pasteur", {"lat": 10.7738, "lng": 106.7001}),
        TrafficFlowSensor("Inter-BinhThanh-HangXanh", {"lat": 10.8015, "lng": 106.7115}),
        TrafficFlowSensor("Inter-ThuDuc-PhamVanDong", {"lat": 10.8256, "lng": 106.7212}),
        TrafficFlowSensor("Inter-D7-NguyenVanLinh-NguyenHuuTho", {"lat": 10.7320, "lng": 106.7050}),
    ]
