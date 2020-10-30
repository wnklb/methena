import asyncio
import logging

from clients.postgres_client import SynchronousPostgresClient
from config import SCHEMA
from utils.log.logging import init_logging_config
from services.fetcher import OHLCVFetcher
from services.state import StateService

init_logging_config()
log = logging.getLogger(__name__)  # noqa F841


async def main():
    state_service = StateService.get_instance()
    async with state_service:
        with SynchronousPostgresClient() as postgres_client:
            postgres_client.create_schema_if_not_exist(schema=SCHEMA)
            for exchange_id in state_service.state['exchange_ids']:
                postgres_client.create_table_if_not_exists(schema=SCHEMA, table=exchange_id)

        ohlcv_fetcher = OHLCVFetcher()
        await ohlcv_fetcher.main()


if __name__ == '__main__':
    asyncio.run(main())
