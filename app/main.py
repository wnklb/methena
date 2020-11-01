import asyncio
import logging

from clients.mqtt_client import MqttClient
from clients.postgres_client import PostgresClient
from config import SCHEMA
from utils.log.logging import init_logging_config
from services.fetcher import OHLCVFetcher

init_logging_config()
log = logging.getLogger(__name__)  # noqa F841


async def main():
    with PostgresClient() as postgres_client:
        postgres_client.create_schema_if_not_exist(schema=SCHEMA)

    ohlcv_fetcher = OHLCVFetcher()
    with MqttClient() as mqttc:
        await ohlcv_fetcher.main()


if __name__ == '__main__':
    asyncio.run(main())
