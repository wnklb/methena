import logging

from clients.filesystem_client import FilesystemClient
from utils.singleton import Singleton

log = logging.getLogger()


class StateService(Singleton):
    state = {
        'config': FilesystemClient.load_ohlcv_config(),
        'has_new_config': False,
        'exchanges_to_close': []
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

    def has_new_config(self):
        return self.state['has_new_config']

    def set_new_config_flag(self, state):
        self.state['has_new_config'] = state

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
        self.set_new_config_flag(True)

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
            if len(config[exchange]) == 0:
                del config[exchange]
                self.add_exchange_to_close(exchange)
                log.info('--> CMD <-- Removed {}'.format(exchange))
        self.set_new_config_flag(True)

    def add_exchange_to_close(self, exchange):
        self.state['exchanges_to_close'].append(exchange)

    def get_exchanges_to_close(self):
        return self.state['exchanges_to_close']

    def clear_exchanges_to_close(self):
        self.state['exchanges_to_close'] = []
