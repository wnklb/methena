import asyncio
import logging

import ccxt.async_support as ccxt

from clients.postgres_client import PostgresClient
from services.state import StateService
from utils.singleton import Singleton

log = logging.getLogger('methena')


class CCXTService(Singleton):
    exchanges = {}
    postgres_client = PostgresClient()
    state_service = StateService()
    log.debug('Created CCXTService')

    async def close(self, exchanges=None):
        if exchanges is None:
            exchanges = self.exchanges
        else:
            exchanges = {exchange: self.exchanges[exchange] for exchange in exchanges}
        for exchange_id, exchange in exchanges.items():
            try:
                log.debug('Trying to close exchange: {}'.format(exchange_id))
                asyncio.ensure_future(exchange.close())
                log.info('Successfully closed exchange: {}'.format(exchange_id))
            except Exception as e:
                log.error('Error during closing of exchange!')
                log.error(e)
        for exchange_id in exchanges.keys():
            del self.exchanges[exchange_id]

    async def init_exchange_markets(self, exchange_ids=None):
        if exchange_ids is None:
            exchange_ids = self.state_service.get_exchanges()
        log.info('Initializing exchanges {}'.format(list(exchange_ids)))
        tasks = [self.__init_exchange_market(exchange_id) for exchange_id in exchange_ids]
        return await asyncio.gather(*tasks)

    async def get_exchange(self, exchange_id):
        if exchange_id not in self.exchanges:
            await self.__init_exchange_market(exchange_id)
        return self.exchanges.get(exchange_id)

    @staticmethod
    def get_exchanges():
        return ccxt.exchanges

    async def get_exchange_symbols(self, exchange_id):
        exchange = await self.get_exchange(exchange_id)
        return exchange.symbols

    async def get_exchange_bases(self, exchange_id):
        exchange = await self.get_exchange(exchange_id)
        symbols = exchange.symbols
        split_char = '/'
        bases = set()
        for symbol in symbols:
            base = symbol.split(split_char)[0]
            bases.add(base)
        return sorted(bases)

    async def get_exchange_quotes(self, exchange_id):
        exchange = await self.get_exchange(exchange_id)
        symbols = exchange.symbols
        split_char = '/'
        quotes = set()
        for symbol in symbols:
            quote = symbol.split(split_char)[1]
            quotes.add(quote)
        return sorted(quotes)

    async def get_exchange_timeframes(self, exchange_id):
        exchange = await self.get_exchange(exchange_id)
        return exchange.timeframes

    def get_loaded_exchanges(self):
        return self.exchanges.values()

    def build_descriptor(self, raw_descriptor):
        log.debug('Building descriptor from {}'.format(raw_descriptor))
        exchanges, symbols, timeframes = raw_descriptor

        descriptor = {
            exchange: {
                symbol: self.__get_timeframe_level(exchange, timeframes)
                for symbol in self.__get_symbol_level(exchange, symbols)
            } for exchange in self.__get_exchange_level(exchanges)
        }
        log.debug('Created descriptor {}'.format(descriptor))

        return descriptor

    def __get_exchange_level(self, exchanges):
        if '*' == exchanges:
            return ccxt.exchanges

        # Only return exchanges that have been initialized before
        return [exchange for exchange in exchanges if exchange in self.exchanges]

    def __get_symbol_level(self, exchange, symbols):
        if '*' == symbols:
            return self.exchanges[exchange].symbols
        return [symbol for symbol in symbols if self.__validate_symbol(exchange, symbol)]

    def __get_timeframe_level(self, exchange, timeframes):
        if '*' == timeframes:
            return self.exchanges[exchange].timeframes
        return [timeframe for timeframe in timeframes if
                self.__validate_timeframe(exchange, timeframe)]

    async def __init_exchange_market(self, exchange_id):
        if exchange_id in self.exchanges:
            return
        try:
            exchange = getattr(ccxt, exchange_id)()
            await exchange.load_markets()
            await asyncio.sleep((exchange.rateLimit / 1000) + 0.5)
            self.exchanges[exchange_id] = exchange
            log.info('Successfully loaded markets for {} and added them.'.format(exchange_id))

            self.postgres_client.create_exchange_ohlcv_table_if_not_exists(exchange_id)
        except Exception as e:  # TODO: find out the correct exception.
            # TODO: #2 what to do if market init is unsuccessful?
            log.error('Unable to load markets for exchange {}.'.format(exchange_id))
            log.error(e)

    def __validate_symbol(self, exchange, symbol):
        if symbol not in self.exchanges[exchange].symbols:
            log.warning('Validation for {}.{} failed. The symbol is not available at the '
                        'exchange'.format(exchange, symbol))
            return False
        return True

    def __validate_timeframe(self, exchange, timeframe):
        if timeframe not in self.exchanges[exchange].timeframes:
            log.warning('Validation for {}.{} failed. The timeframe is not '
                        'available at the exchange'.format(exchange, timeframe))
            return False
        return True
