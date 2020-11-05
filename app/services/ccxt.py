import asyncio
import logging

import ccxt.async_support as ccxt

from clients.postgres_client import PostgresClient
from services.state import StateService
from utils.singleton import Singleton

logger = logging.getLogger()


class CCXTService(Singleton):
    exchanges = {}
    postgres_client = PostgresClient()
    state_service = StateService()

    async def close(self, exchanges=None):
        if exchanges is None:
            exchanges = self.exchanges.items()
        else:
            exchanges = {exchange: self.exchanges[exchange] for exchange in exchanges}
        for exchange_id, exchange in exchanges.items():
            try:
                logger.debug('Trying to close exchange: {}'.format(exchange_id))
                await exchange.close()
                logger.info('Successfully closed exchange: {}'.format(exchange_id))
            except Exception as e:
                logger.error('Error during exchange closing!')
                logger.error(e)
            del self.exchanges[exchange_id]

    # async def __aenter__(self):
    #     await self.__init_exchange_markets(self.state['exchange_ids'])
    #     return self
    #
    # async def __aexit__(self, exc_type, exc_val, exc_tb):
    #     for exchange_id, exchange in self.exchanges.items():
    #         try:
    #             logger.debug('Trying to close exchange: {}'.format(exchange_id))
    #             await exchange.close()
    #             logger.info('Successfully closed exchange: {}'.format(exchange_id))
    #         except Exception as e:
    #             logger.error('Error during exchange closing!')
    #             logger.error(e)

    async def init_exchange_markets(self, exchange_ids=None):
        if exchange_ids is None:
            exchange_ids = self.state_service.get_exchanges()
        tasks = [self.__init_exchange_market(exchange_id) for exchange_id in exchange_ids]
        return await asyncio.gather(*tasks)

    def build_descriptor(self, raw_descriptor):
        exchanges, symbols, timeframes = raw_descriptor

        return {
            exchange: {
                symbol: self.__get_timeframe_level(exchange, timeframes)
                for symbol in self.__get_symbol_level(exchange, symbols)
            } for exchange in self.__get_exchange_level(exchanges)
        }

    def __get_exchange_level(self, exchanges):
        if '*' == exchanges:
            return ccxt.exchanges
        return exchanges

    def __get_symbol_level(self, exchange, symbols):
        if '*' == symbols:
            return self.exchanges[exchange].symbols
        return symbols

    def __get_timeframe_level(self, exchange, timeframes):
        if '*' == timeframes:
            return self.exchanges[exchange].timeframes
        return timeframes

    def validate_descriptor(self, descriptor):
        descriptor_validated = {exchange: {} for exchange in descriptor.keys()}
        for exchange, symbols in descriptor.items():
            for symbol, timeframes in symbols.items():
                if not self.__validate_symbol(exchange, symbol):
                    logger.warning(
                        'Symbol {} is not available at exchange {}'.format(symbol, exchange))
                    continue
                descriptor_validated[exchange][symbol] = []
                for timeframe in timeframes:
                    if self.__validate_timeframe(exchange, timeframe):
                        descriptor_validated[exchange][symbol].append(timeframe)
                    else:
                        logger.warning('Timeframe {} is not available at {}.{}'.format(
                            timeframe, exchange, symbol))
        return descriptor_validated

    def __validate_symbol(self, exchange, symbol):
        return True if symbol in self.exchanges[exchange].symbols else False

    def __validate_timeframe(self, exchange, timeframe):
        return True if timeframe in self.exchanges[exchange].timeframes else False

    def get_loaded_exchanges(self):
        return self.exchanges.values()

    async def __init_exchange_market(self, exchange_id):
        if exchange_id in self.exchanges:
            return
        try:
            exchange = getattr(ccxt, exchange_id)()
            await exchange.load_markets()
            await asyncio.sleep((exchange.rateLimit / 1000) + 0.5)
            self.exchanges[exchange_id] = exchange
            logger.info('Successfully loaded markets for {} and added them.'.format(exchange_id))

            self.postgres_client.create_exchange_ohlcv_table_if_not_exists(exchange_id)
        except Exception as e:  # TODO: find out the correct exception.
            logger.error('Unable to load markets for exchange {}.'.format(exchange_id))
            logger.error(e)

    @staticmethod
    def get_exchanges():
        return ccxt.exchanges

    async def get_exchange(self, exchange_id):
        if exchange_id not in self.exchanges:
            await self.__init_exchange_market(exchange_id)
        return self.exchanges.get(exchange_id)

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
