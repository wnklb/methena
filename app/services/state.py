import logging
from datetime import datetime, timedelta

from clients.filesystem_client import FilesystemClient
from utils.singleton import Singleton

log = logging.getLogger()


class StateService(Singleton):
    state = {
        'config': FilesystemClient.load_ohlcv_config(),
        'next_sync_timestamp': None,
    }

    def get_state(self):
        return self.state

    def get_exchanges(self):
        return self.state['config'].keys()

    def get_symbols(self, exchange):
        return self.state['config'][exchange]

    def get_timeframes(self, exchange, symbol):
        return self.state['config'][exchange][symbol]

    def get_config(self):
        return self.state['config']

    def add(self, descriptor):
        config = self.state['config']
        for exchange, symbols in descriptor.items():
            if exchange in config:
                for symbol, timeframes in symbols.items():
                    if symbol in config[exchange]:
                        unique_new = list(set(timeframes) - set(config[exchange][symbol]))
                        if len(unique_new) == 0:
                            log.info('--> CMD <-- {} already set on {}.{}'.format(
                                timeframes, exchange, symbol))
                            continue
                        config[exchange][symbol] = unique_new + config[exchange][symbol]
                        log.info(
                            '--> CMD <-- Added {} to {}.{}'.format(unique_new, exchange, symbol))
                    else:
                        config[exchange][symbol] = timeframes
                        log.info(
                            '--> CMD <-- Added {} to {}.{}'.format(timeframes, exchange, symbol))
            else:
                for symbol, timeframes in symbols.items():
                    config[exchange] = {symbol: timeframes}
                    log.info(
                        '--> CMD <-- Added {} to {} with {}'.format(symbol, exchange, timeframes))

    def remove(self, descriptor):
        config = self.state['config']
        for exchange, symbols in descriptor.items():
            for symbol, timeframes in symbols.items():
                for timeframe in timeframes:
                    config[exchange][symbol].remove(timeframe)
                    log.info('--> CMD <-- Removed {}.{}.{}'.format(exchange, symbol, timeframe))
                if len(config[exchange][symbol]) == 0:
                    del config[exchange][symbol]
                    log.info('--> CMD <-- Removed {}.{}'.format(exchange, symbol))
            if len(config[exchange]):
                del config[exchange]
                log.info('--> CMD <-- Removed {}'.format(exchange))

    def get_next_sync_timestamp(self):
        return self.state['next_sync_timestamp']

    def set_next_sync_timestamp(self):
        self.state['next_sync_timestamp'] = datetime.now() + timedelta(seconds=20)
