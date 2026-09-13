"""CLI runner for generating and streaming synthetic IoT traffic via HTTP."""

import argparse
import asyncio
import sys
import time
from typing import Any

import httpx
import structlog

from app.modules.simulation.domain.sensors import get_default_urban_sensor_fleet

logger = structlog.get_logger("iot-traffic-generator")


async def run_traffic_generator(
    target_url: str,
    rate_hz: float,
    duration_seconds: float,
) -> None:
    """
    Sends bulk telemetry to target_url/v1/observations/bulk at rate_hz sweeps per second.
    """
    fleet = get_default_urban_sensor_fleet()
    interval = 1.0 / max(0.1, rate_hz)
    endpoint = f"{target_url.rstrip('/')}/v1/observations/bulk"

    print(f"🚀 Starting IoT traffic generator against: {endpoint}")
    print(
        f"📡 Fleet size: {len(fleet)} sensors | Rate: {rate_hz:.1f} sweeps/sec | Duration: {duration_seconds}s"
    )

    total_sent = 0
    total_errors = 0
    start_time = time.time()

    async with httpx.AsyncClient(timeout=10.0) as client:
        while time.time() - start_time < duration_seconds:
            loop_start = time.time()
            bulk_payload: list[dict[str, Any]] = []

            for sensor in fleet:
                _, obs_list = sensor.sample()
                for o in obs_list:
                    bulk_payload.append(
                        {
                            "entity_id": o["entity_id"],
                            "attribute_name": o["attribute_name"],
                            "timestamp": o["timestamp"].isoformat(),
                            "value_numeric": o["value_numeric"],
                            "unit": o["unit"],
                        }
                    )

            try:
                response = await client.post(endpoint, json={"observations": bulk_payload})
                if response.is_success:
                    total_sent += len(bulk_payload)
                else:
                    total_errors += 1
                    print(
                        f"⚠️ Server returned {response.status_code}: {response.text[:100]}",
                        file=sys.stderr,
                    )
            except Exception as exc:
                total_errors += 1
                print(f"❌ Connection error: {exc}", file=sys.stderr)

            elapsed = time.time() - loop_start
            sleep_duration = max(0.001, interval - elapsed)
            await asyncio.sleep(sleep_duration)

    total_time = time.time() - start_time
    print("\n🏁 Traffic generation complete!")
    print(f"📊 Total metrics ingested: {total_sent}")
    print(f"❌ Total request errors: {total_errors}")
    print(f"⏱️ Throughput: {total_sent / total_time:.1f} metrics/sec over {total_time:.1f} seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description="Aegis Platform IoT Traffic Generator")
    parser.add_argument(
        "--target-url",
        default="http://localhost:8080",
        help="Base URL of urban-data-api (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=2.0,
        help="Sensor sweeps per second (default: 2.0)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Duration to run in seconds (default: 30.0)",
    )

    args = parser.parse_args()
    asyncio.run(run_traffic_generator(args.target_url, args.rate, args.duration))


if __name__ == "__main__":
    main()
