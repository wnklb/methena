import asyncio
import logging
from time import time

from clients.mqtt_client import MqttClient
from clients.postgres_client import PostgresClient
from error import FetchError, AsyncioError
from services.ccxt import CCXTService
from services.state import StateService
from utils.postgres import prepare_data_for_postgres

log = logging.getLogger()


class OHLCVFetcher:
    postgres_client = PostgresClient()
    ccxt_service = CCXTService()
    state_service = StateService()
    mqtt_client = None
    cycles = 0
    log.debug('Created OHLCVFetcher')

    def __init__(self):
        self.loop = asyncio.get_running_loop()
        if self.mqtt_client is None:
            OHLCVFetcher.mqtt_client = MqttClient(loop=self.loop)
        log.debug('Initialized OHLCVFetcher')

    async def __aenter__(self):
        self.mqtt_client.start()
        await self.ccxt_service.init_exchange_markets()
        log.debug('Entered OHLCVFetcher')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.mqtt_client.stop()
        self.postgres_client.stop()
        try:
            await self.ccxt_service.close()
        except RuntimeError as e:
            log.warning('Handled runtime error caught during exchange closing: {}'.format(e))
        log.debug('Exited OHLCVFetcher')

    async def main(self):
        ok = True
        while ok:
            self.state_service.set_has_new_config_flag(False)
            try:
                await self.__fetch()
            except AsyncioError:
                ok = False
            exchanges_to_close = self.state_service.get_exchanges_to_close()
            await self.ccxt_service.close(exchanges_to_close)
            self.state_service.clear_exchanges_to_close()

    async def __fetch(self):
        # Fetch OHLCV data asynchronously for each exchange.
        self.cycles += 1
        log.info('')
        log.info('============================================================================')
        log.info('')
        log.info('Fetch in cycle: {}'.format(self.cycles))
        exchanges = self.ccxt_service.get_loaded_exchanges()
        tasks = [self.__process_exchange(exchange) for exchange in exchanges]
        try:
            await asyncio.gather(*tasks)
        except asyncio.exceptions.CancelledError as e:
            log.warning('Caught asyncio.exceptions.CancelledError. Shutting down. ({})'.format(e))
            raise AsyncioError()

    async def __process_exchange(self, exchange):
        log.info('Started fetching {}'.format(exchange.id))
        try:
            if exchange.has['fetchOHLCV']:
                symbols_state = self.state_service.get_symbols(exchange.id)
                symbols = symbols_state.keys() if symbols_state else exchange.symbols

                for symbol in symbols:
                    if self.state_service.has_new_config():
                        log.warning(
                            '[{}] - Breaking out of symbol loop to sync'.format(exchange.id))
                        break
                    await self.__process_symbol(exchange, symbol)
            else:
                log.debug(
                    '[{}] - Exchange has no OHLCV data available. Skipping entirely.'.format(
                        exchange))
        except RuntimeError as e:
            log.info(
                'RuntimeError: [{}] - still trying to access deleted exchange. Skipping'.format(
                    exchange.id))
            log.info(e)
        except Exception as e:
            log.error('[{}] - Unexpected behaviour when trying to access the exchange. '
                      'Skipping till next sync.'.format(exchange.id))
            log.error(e)

    async def __process_symbol(self, exchange, symbol):
        log.info('Started fetching {}.{}'.format(exchange.id, symbol))
        timeframes = self.state_service.get_timeframes(exchange.id, symbol)
        if not timeframes:  # If the config holds an empty list, take all timeframes available
            timeframes = exchange.timeframes

        for timeframe in timeframes:
            if self.state_service.has_new_config():
                log.debug('[{}] [{}] - Breaking out of timeframe loop to sync'.format(
                    exchange.id, symbol))
                break
            try:
                await self.__process_timeseries(exchange, symbol, timeframe)
            except Exception as e:
                log.error(e)

    async def __process_timeseries(self, exchange, symbol, timeframe):
        log.info('[{}] [{}] [{}] - Fetching OHLCV timeseries'.format(
            exchange.id, symbol, timeframe))
        since = self.__get_since_timestamp(exchange, symbol, timeframe)
        count = 0
        start_time = time()

        while True:
            if self.state_service.has_new_config():
                log.debug('[{}] [{}] [{}] - Breaking out of loop to sync'.format(
                    exchange.id, symbol, timeframe))
                break
            try:
                ohlcv_data = await self.__fetch_timeseries_chunk(exchange, symbol, timeframe, since)
            except FetchError as e:
                log.error(e)
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
            log.debug('[{}] [{}] [{}] - Successfully inserted OHLCV chunk.'.format(
                exchange.id, symbol, timeframe))

        duration = time() - start_time
        log.info('[{}] [{}] [{}] - Completed and fetched {} entries taking {:.2f}s.'.format(
            exchange.id, symbol, timeframe, count, duration))

    def __get_since_timestamp(self, exchange, symbol, timeframe):
        since = None
        try:
            since = self.postgres_client.fetch_latest_timestamp(exchange.id, symbol, timeframe)
        except Exception as e:
            log.info('[{}] [{}] [{}] - No previous timestamp available. Fetching from start'.format(
                exchange.id, symbol, timeframe))
            log.info(e)

        if since is None:
            since = exchange.parse8601('2010-01-01T00:00:00Z')

        return since

    async def __fetch_timeseries_chunk(self, exchange, symbol, timeframe, since):
        for attempt in range(5):
            try:
                await asyncio.sleep((exchange.rateLimit / 1000) + 0.5)  # +0.5 for safety margin.
                return await exchange.fetch_ohlcv(symbol, since=since, timeframe=timeframe)
            except Exception as e:
                if self.state_service.has_new_config():
                    log.debug('[{}] [{}] [{}] - Breaking out of fetch to sync'.format(
                        exchange.id, symbol, timeframe))
                    break
                if attempt == 4:
                    log.error(e)
                    raise FetchError(
                        '[{}] [{}] [{}] - Unable to fetch OHLCV data 5 times in a row given '
                        'since timestamp: {}'.format(exchange, symbol, timeframe, since))

                next_attempt_sec = 20 * (attempt + 1)
                log.warning(
                    '[{}] [{}] [{}] - {} attempt to get OHLCV data since {} was unsuccessful. '
                    'Retrying in {} seconds'.format(attempt, exchange, symbol, timeframe, since,
                                                    next_attempt_sec))
                log.warning(e)

                await asyncio.sleep(next_attempt_sec)


async def main():
    async with OHLCVFetcher() as ohlcv_fetcher:
        await ohlcv_fetcher.main()


if __name__ == '__main__':
    asyncio.run(main())
