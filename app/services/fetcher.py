import asyncio
import logging
from datetime import datetime
from time import time

from clients.ccxt_client import CCXTClient
from clients.mqtt_client import MqttClient
from clients.postgres_client import PostgresClient
from error import FetchError
from services.state import StateService
from utils.postgres import prepare_data_for_postgres

logger = logging.getLogger(__name__)


class OHLCVFetcher:

    def __init__(self):
        self.postgres_client = PostgresClient()
        self.ccxt_client = CCXTClient()
        self.state_service = StateService()
        self.mqtt_client = MqttClient()

    async def __aenter__(self):
        self.mqtt_client.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.mqtt_client.stop()
        await self.ccxt_client.close()

    async def main(self):
        while True:
            self.state_service.set_next_sync_timestamp()
            await self.ccxt_client.init_exchange_markets()
            # Exit condition via mqtt
            await self.__fetch()

    async def __fetch(self):
        # TODO: Why is the cursor closed if this is instantiated via __anter__?
        with self.postgres_client:
            # Fetch OHLCV data asynchronously for each exchange.
            exchanges = self.ccxt_client.get_loaded_exchanges()
            tasks = [self.__process_exchange(exchange) for exchange in exchanges]
            await asyncio.gather(*tasks)

    async def __process_exchange(self, exchange):
        try:
            if exchange.has['fetchOHLCV']:
                symbols_state = self.state_service.get_symbols(exchange.id)
                symbols = symbols_state.keys() if symbols_state else exchange.symbols

                for symbol in symbols:
                    await self.__process_symbol(exchange, symbol)
            else:
                logger.warning(
                    "Exchange '{}' has no OHLCV data available. Skipping entirely.".format(
                        exchange))
        except Exception as e:
            logger.error("Unexpected behaviour when trying to access the exchange. Skipping!")
            logger.error(e)

    async def __process_symbol(self, exchange, symbol):
        timeframes = self.state_service.get_timeframes(exchange.id, symbol)
        if not timeframes:  # If the config holds an empty list, take all timeframes available
            timeframes = exchange.timeframes

        for timeframe in timeframes:
            try:
                await self.__process_timeseries(exchange, symbol, timeframe)
            except Exception as e:
                logger.error(e)

    async def __process_timeseries(self, exchange, symbol, timeframe):
        logger.info(
            "[{}] [{}] [{}] - Attempting to fetch OHLCV timeseries".format(exchange.id, symbol,
                                                                           timeframe))
        since = self.__get_since_timestamp(exchange, symbol, timeframe)
        count = 0
        start_time = time()
        next_sync = self.state_service.get_next_sync_timestamp()

        while True:
            if datetime.now() > next_sync:
                logger.warning('Breaking out of loop to sync - {}'.format(next_sync))
                break
            try:
                ohlcv_data = await self.__fetch_timeseries_chunk(exchange, symbol, timeframe, since)
            except FetchError as e:
                logger.error(e)
                break  # there is something wrong and we skip this OHLCV timeseries for now.

            latest_timestamp = ohlcv_data[-1][0]
            if since == latest_timestamp:  # Fetched most recent result.
                # TODO: check for some exit msg or whatnot
                break
            else:
                count += len(ohlcv_data)
                since = latest_timestamp

            values = prepare_data_for_postgres(symbol, timeframe, ohlcv_data)
            # For now, we don't care why/that this fails und just pop it.
            # TODO: handling of psql error should be implemented later.
            self.postgres_client.insert_many(values, exchange.id)
            logger.debug("[{}] [{}] [{}] - Successfully inserted OHLCV chunk.".format(
                exchange.id, symbol, timeframe))

        duration = time() - start_time
        logger.info(
            "[{}] [{}] [{}] - Completed and fetched {} entrties for taking {:.2f}s.".format(
                exchange.id, symbol, timeframe, count, duration))

    def __get_since_timestamp(self, exchange, symbol, timeframe):
        since = None
        try:
            since = self.postgres_client.fetch_latest_timestamp(exchange.id, symbol, timeframe)
        except Exception as e:
            logger.info(
                "[{}] [{}] [{}] - No latest timestamp available.".format(exchange.id, symbol,
                                                                         timeframe))
            logger.info(e)

        if since is None:
            since = exchange.parse8601('2010-01-01T00:00:00Z')

        return since

    async def __fetch_timeseries_chunk(self, exchange, symbol, timeframe, since):
        for attempt in range(5):
            try:
                await asyncio.sleep((exchange.rateLimit / 1000) + 0.5)  # +0.5 for safety margin.
                return await exchange.fetch_ohlcv(symbol, since=since, timeframe=timeframe)
            except Exception as e:
                if attempt == 4:
                    logger.error(e)
                    raise FetchError(
                        "Unable to fetch OHLCV data for exchange '{}' symbol '{}' timeframe '{}' "
                        "for  5 times in a row given 'since' timestamp: {}".format(
                            exchange, symbol, timeframe, since))

                next_attempt_sec = 40 * (attempt + 1)
                logger.warning(
                    "{} attempt to get OHLCV data for exchange '{}' symbol '{}' timeframe '{}' "
                    "since '{}'  was unsuccessful. Retrying in {} seconds".format(
                        attempt, exchange, symbol, timeframe, since, next_attempt_sec))
                logger.warning(e)

                await asyncio.sleep(next_attempt_sec)


async def main():
    async with OHLCVFetcher() as ohlcv_fetcher:
        await ohlcv_fetcher.main()


if __name__ == '__main__':
    asyncio.run(main())
