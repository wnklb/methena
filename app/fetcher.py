import asyncio
import logging
from time import time

from ccxt import async_support as ccxt

from config import EXCHANGES, SCHEMA, SYMBOLS, TIMEFRAMES
from error import FetchError
from clients.postgres_client import SynchronousPostgresClient
from utils import prepare_data_for_postgres

logger = logging.getLogger()
# handler = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)
# logger.setLevel(logging.INFO)


class OHLCVFetcher:

    def __init__(self):
        self.exchange_ids = set(EXCHANGES)
        self.exchanges = {}
        self.postgres_client = None

    async def __aenter__(self):
        await self._inti_exchange_markets(self.exchange_ids)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for exchange_id, exchange in self.exchanges.items():
            try:
                logger.info("Trying to close exchange: {}".format(exchange_id))
                await exchange.close()
                logger.info("Successfully closed exchange: {}".format(exchange_id))
            except Exception as e:
                logger.error("Error during exchange closing!")
                logger.error(e)

    async def main(self):
        self.init()
        await self._fetch()

    def init(self):
        with SynchronousPostgresClient() as postgres_client:
            postgres_client.create_schema_if_not_exist(schema=SCHEMA)
            for exchange_id in self.exchanges.keys():
                postgres_client.create_table_if_not_exists(schema=SCHEMA, table=exchange_id)
        
    async def _fetch(self):
        with SynchronousPostgresClient() as postgres_client:
            self.postgres_client = postgres_client
            # Fetch OHLCV data asynchronously for each exchange.
            tasks = [self._fetch_ohlcv_for_exchange(exchange) for exchange in self.exchanges.values()]
            await asyncio.gather(*tasks)

    async def _fetch_ohlcv_for_exchange(self, exchange):
        try:
            if exchange.has['fetchOHLCV']:
                symbols = SYMBOLS if SYMBOLS else exchange.symbols
                start_time = time()
                amount_symbols = len(symbols)
                processed_symbols = 0
                logger.info("Exchange '{}' has {} symbols: {}".format(exchange.id, amount_symbols, symbols))

                for symbol in symbols:
                    for timeframe in TIMEFRAMES:
                        try:
                            logger.info("Attempting to fetch OHLCV data for: '{}', '{}', '{}'".format(
                                exchange.id, symbol, timeframe))
                            await self._fetch_whole_ohlcv_timeseries_data(exchange, symbol, timeframe)
                        except Exception as e:
                            logger.error(e)

                    processed_symbols += 1
                    passed_time = time() - start_time
                    if processed_symbols % 10 == 0:
                        logger.info("Processed {}/{} symbols in {:.1f}s."
                                    .format(processed_symbols, amount_symbols, passed_time))
            else:
                logger.warning("Exchange '{}' has no OHLCV data available. Skipping entirely.".format(exchange))
        except Exception as e:
            logger.error("Unexpected behaviour when trying to access the exchange. Skipping!")
            logger.error(e)

    async def _fetch_whole_ohlcv_timeseries_data(self, exchange, symbol, timeframe):
        since = None
        try:
            since = self.postgres_client.fetch_latest_timestamp(SCHEMA, exchange.id, symbol, timeframe)
        except Exception as e:
            logger.info("No latest timestamp available for: {}.{} {} {}".format(SCHEMA, exchange.id, symbol, timeframe))
            logger.info(e)
        if since is None:
            since = exchange.parse8601('2010-01-01T00:00:00Z')
        count = 0
        start_time = time()
        table = exchange.id

        while True:
            try:
                ohlcv_data = await self._fetch_ohlcv_timeseries_part(exchange, symbol, timeframe, since)
            except FetchError as e:
                logger.error(e)
                break  # there is something wrong and we skip this OHLCV timeseries for now.

            latest_timestamp = ohlcv_data[-1][0]
            if since == latest_timestamp:  # Fetched most recent result.
                break
            else:
                count += len(ohlcv_data)
                since = latest_timestamp

            values = prepare_data_for_postgres(symbol, timeframe, ohlcv_data)
            logger.info("Attempting to insert OHLCV data for: '{}', '{}', '{}' into '{}.{}'".format(
                exchange.id, symbol, timeframe, SCHEMA, table))
            # For now, we don't care why/that this fails und just pop it.
            # TODO: handling of psql error should be implemented later.
            self.postgres_client.insert_many(values, table)
            logger.info("Successfully inserted OHLCV data for: '{}', '{}', '{}' into '{}.{}'".format(
                exchange.id, symbol, timeframe, SCHEMA, table))

        duration = time() - start_time
        logger.info("Completed and fetched {} entrties for: '{}', '{}', '{}' taking {:.2f}s.".format(
            count, exchange.id, symbol, timeframe, duration))

    async def _fetch_ohlcv_timeseries_part(self, exchange, symbol, timeframe, since):
        for attempt in range(5):
            try:
                await asyncio.sleep((exchange.rateLimit / 1000) + 0.5)  # +0.5 for safety margin.
                ohlcv_data = await exchange.fetch_ohlcv(symbol, since=since, timeframe=timeframe)
                return ohlcv_data
            except Exception as e:
                if attempt == 4:
                    logger.error(e)
                    raise FetchError("Unable to catch OHLCV data for exchange '{}' symbol '{}' timeframe '{}' for "
                                     "5 times in a row. Since timestamp: {}".format(exchange, symbol, timeframe, since))

                next_attempt_sec = 40 * (attempt + 1)
                logger.warning("{} attempt to get OHLCV data for exchange '{}' symbol '{}' timeframe '{}' since '{}' "
                               "was unsuccessful. Retrying in {} seconds"
                               .format(attempt, exchange, symbol, timeframe, since, next_attempt_sec))
                logger.warning(e)

                await asyncio.sleep(next_attempt_sec)

    async def _inti_exchange_markets(self, exchange_ids):
        tasks = [self._init_exchange_market(exchange_id) for exchange_id in exchange_ids]
        await asyncio.gather(*tasks)

    async def _init_exchange_market(self, exchange_id):
        try:
            exchange = getattr(ccxt, exchange_id)()
            await exchange.load_markets()
            await asyncio.sleep((exchange.rateLimit / 1000) + 0.5)
            self.exchanges[exchange_id] = exchange
            logger.info("Successfully loaded markets for '{}' and added them.".format(exchange_id))
        except Exception as e:  # TODO: find out the correct exception.
            logger.info("Couldn't load markets for exchange '{}'.".format(exchange_id))
            logger.error(e)


async def main():
    async with OHLCVFetcher() as ohlcv_fetcher:
        await ohlcv_fetcher.main()


if __name__ == '__main__':
    asyncio.run(main())
