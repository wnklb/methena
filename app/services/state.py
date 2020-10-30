import asyncio
import logging

from ccxt import async_support as ccxt

from clients.filesystem_client import FilesystemClient

log = logging.getLogger()


class StateService:
    __instance = None
    state = {
        'config': {},
        'exchange_ids': None,
        'exchanges': {},
    }

    def __init__(self):
        if StateService.__instance is not None:
            raise Exception("OHLCVConfigService is a Singleton class. Use its get() function.")
        else:
            StateService.__instance = self
            StateService.state['config'] = FilesystemClient.load_ohlcv_config()
            self.__udpate_state()

    async def __aenter__(self):
        await self.__init_exchange_markets(self.state['exchange_ids'])

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for exchange_id, exchange in self.state['exchanges'].items():
            try:
                log.debug("Trying to close exchange: {}".format(exchange_id))
                await exchange.close()
                log.info("Successfully closed exchange: {}".format(exchange_id))
            except Exception as e:
                log.error("Error during exchange closing!")
                log.error(e)

    # TODO: check classmethod
    @staticmethod
    def get_instance():
        if StateService.__instance is None:
            return StateService()
        return StateService.__instance

    async def __init_exchange_markets(self, exchange_ids):
        tasks = [self.__init_exchange_market(exchange_id) for exchange_id in exchange_ids]
        await asyncio.gather(*tasks)

    async def __init_exchange_market(self, exchange_id):
        try:
            exchange = getattr(ccxt, exchange_id)()
            await exchange.load_markets()
            await asyncio.sleep((exchange.rateLimit / 1000) + 0.5)
            self.state['exchanges'][exchange_id] = exchange
            log.info("Successfully loaded markets for '{}' and added them.".format(exchange_id))
        except Exception as e:  # TODO: find out the correct exception.
            log.info("Couldn't load markets for exchange '{}'.".format(exchange_id))
            log.error(e)

    def add(self, descriptor):
        for exchange, symbols in descriptor.items():
            if exchange in self.state['config']:
                for symbol, timeframes in symbols:
                    if symbol in self.state['config'][exchange]:
                        new_timeframes = list(set(self.state['config'][exchange][symbol] + timeframes))
                        self.state['config'][exchange][symbol] = new_timeframes
                    else:
                        self.state['config'][exchange][symbol] = timeframes
            else:
                self.state['config'][exchange] = {symbol: timeframes for symbol, timeframes in symbols}
        self.__udpate_state()

    def remove(self, descriptor):
        pass

    def __udpate_state(self):
        StateService.state['exchange_ids'] = StateService.state['config'].keys()
