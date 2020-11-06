import json
import logging

from clients.filesystem_client import FilesystemClient
from clients.postgres_client import PostgresClient
from config import OHLCV_DB_STATE
from error import NoStateProvidedError
from utils.singleton import Singleton

log = logging.getLogger()


def load_ohlcv_config_from_file():
    state = {
        'config': FilesystemClient.load_ohlcv_config(),
        'has_new_config': False,
        'exchanges_to_close': []
    }
    log.info('StateService initialized state from config file.')
    return state


class StateService(Singleton):
    postgres_client = PostgresClient()
    log.debug('Created StateService')

    if OHLCV_DB_STATE:
        try:
            state = postgres_client.get_ccxt_ohlcv_fetcher_state()
            log.info('StateService initialized state from database.')
        except TypeError as e:
            log.warning('There is no persisted state in the database. Please load the config from '
                        'file and check your environment variables.')
            log.warning('Trying to initialize state from config file.')
            log.warning(e)
            try:
                state = load_ohlcv_config_from_file()
                postgres_client.set_ccxt_ohlcv_fetcher_state(json.dumps(state))
            except FileNotFoundError as e:
                log.warning('There is no ohlcv config file provided.')
                log.warning(e)
                raise NoStateProvidedError(
                    'You have neither provided a database ohlcv state nor a ohlcv config file. '
                    'Check your environment variables -- Exiting.')
    else:
        state = load_ohlcv_config_from_file()
        postgres_client.set_ccxt_ohlcv_fetcher_state(json.dumps(state))

    def get_exchanges(self):
        return self.state['config'].keys()

    def get_symbols(self, exchange):
        return self.state['config'][exchange]

    def get_timeframes(self, exchange, symbol):
        return self.state['config'][exchange][symbol]

    def has_new_config(self):
        return self.state['has_new_config']

    def set_has_new_config_flag(self, state):
        self.state['has_new_config'] = state

    def add_descriptor(self, descriptor):
        log.info('State :: Adding descriptor {}'.format(descriptor))
        config = self.state['config']
        for exchange, symbols in descriptor.items():
            if exchange in config:
                for symbol, timeframes in symbols.items():
                    if symbol in config[exchange]:
                        unique_new = list(set(timeframes) - set(config[exchange][symbol]))
                        if len(unique_new) == 0:
                            log.info('State :: {} already set on {}.{}'.format(
                                timeframes, exchange, symbol))
                            continue
                        config[exchange][symbol] = unique_new + config[exchange][symbol]
                        log.info(
                            'State :: Added {} to {}.{}'.format(unique_new, exchange, symbol))
                    else:
                        config[exchange][symbol] = timeframes
                        log.info(
                            'State :: Added {} to {}.{}'.format(timeframes, exchange, symbol))
            else:
                for symbol, timeframes in symbols.items():
                    config[exchange] = {symbol: timeframes}
                    log.info(
                        'State :: Added {} to {} with {}'.format(symbol, exchange, timeframes))
        self.persist_state()
        self.set_has_new_config_flag(True)

    def remove_descriptor(self, descriptor):
        log.info('Removing descriptor {}'.format(descriptor))
        config = self.state['config']
        for exchange, symbols in descriptor.items():
            for symbol, timeframes in symbols.items():
                for timeframe in timeframes:
                    config[exchange][symbol].remove(timeframe)
                    log.info('State :: Removed {}.{}.{}'.format(exchange, symbol, timeframe))
                if len(config[exchange][symbol]) == 0:
                    del config[exchange][symbol]
                    log.info('State :: Removed {}.{}'.format(exchange, symbol))
            if len(config[exchange]) == 0:
                del config[exchange]
                self.add_exchange_to_close(exchange)
                log.info('State :: Removed {}'.format(exchange))
        self.persist_state()
        self.set_has_new_config_flag(True)

    def add_exchange_to_close(self, exchange):
        log.debug('Set exchange {} to be closed'.format(exchange))
        self.state['exchanges_to_close'].append(exchange)

    def get_exchanges_to_close(self):
        return self.state['exchanges_to_close']

    def clear_exchanges_to_close(self):
        log.debug('Cleared exchanges to be closed')
        self.state['exchanges_to_close'] = []

    def persist_state(self):
        state = json.dumps(self.state)
        self.postgres_client.set_ccxt_ohlcv_fetcher_state(state)
        log.info('Persisted state to postgres')

    def load_persisted_state(self):
        state = self.postgres_client.get_ccxt_ohlcv_fetcher_state()
        log.info('Loaded state from postgres')
        return state
