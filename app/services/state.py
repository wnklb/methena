import json
import logging

from clients.filesystem_client import FilesystemClient
from clients.postgres_client import PostgresClient
from config import OHLCV_CONFIG_FILE, OHLCV_DB_STATE
from errors import ConfigFileNotFoundError, DatabaseConfigNotFoundError, NoConfigProvidedError
from utils.singleton import Singleton

log = logging.getLogger('methena')


def load_state(source='db'):
    config = {}
    if source == 'db':
        try:
            config = __load_ohlcv_config_from_database()
        except DatabaseConfigNotFoundError as e:
            log.warning('Trying to initialize state from config file. Error: %s' % e)
            try:
                config = __load_ohlcv_config_from_file()
            except ConfigFileNotFoundError as e:
                raise NoConfigProvidedError(
                    'You have neither provided a database ohlcv config nor a ohlcv config file. '
                    'Check your environment variables. Error: %s' % e)
    elif source == 'file':
        config = __load_ohlcv_config_from_file()

    return {
        'config': config,
        'has_new_config': False,
        'exchanges_to_close': set()
    }


def __load_ohlcv_config_from_database():
    try:
        config = PostgresClient().get_ccxt_ohlcv_fetcher_config()
        log.info('StateService initialized config from database.')
        return config
    except TypeError as e:
        log.warning('Unable to load OHLCV config from database - No config is persisted. Please '
                    'load the config from file and check your environment variables. %s' % e)
        raise DatabaseConfigNotFoundError()


def __load_ohlcv_config_from_file():
    try:
        config = FilesystemClient.load_ohlcv_config()
        log.info('StateService initialized config from OHLCV config file.')
        PostgresClient().set_ccxt_ohlcv_fetcher_config(json.dumps(config))
        log.info('Persisted config to postgres')
        return config
    except FileNotFoundError as e:
        log.warning('There is no ohlcv config file provided.')
        log.warning(e)
        raise ConfigFileNotFoundError(
            'Cannot access OHLCV config file at "{}"'.format(OHLCV_CONFIG_FILE))


class StateService(Singleton):
    postgres_client = PostgresClient()
    state = load_state() if OHLCV_DB_STATE else load_state('file')
    log.debug('Created StateService')

    def get_state(self):
        return self.state

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
        log.debug('State :: Adding descriptor {}'.format(descriptor))
        config = self.state['config']
        for exchange, symbols in descriptor.items():
            if exchange in config:
                for symbol, timeframes in symbols.items():
                    if symbol in config[exchange]:
                        unique_new = list(set(timeframes) - set(config[exchange][symbol]))
                        if len(unique_new) == 0:
                            log.debug('State :: {} already set on {}.{}'.format(
                                timeframes, exchange, symbol))
                            continue
                        config[exchange][symbol] = unique_new + config[exchange][symbol]
                        log.debug(
                            'State :: Added {} to {}.{}'.format(unique_new, exchange, symbol))
                    else:
                        config[exchange][symbol] = timeframes
                        log.debug(
                            'State :: Added {} to {}.{}'.format(timeframes, exchange, symbol))
            else:
                config[exchange] = {}
                for symbol, timeframes in symbols.items():
                    config[exchange][symbol] = timeframes
                    log.debug(
                        'State :: Added {} to {} with {}'.format(symbol, exchange, timeframes))
        self.persist_config()
        self.set_has_new_config_flag(True)

    def remove_descriptor(self, descriptor):
        log.info('Removing descriptor {}'.format(descriptor))
        config = self.state['config']
        for exchange, symbols in descriptor.items():
            for symbol, timeframes in symbols.items():
                for timeframe in timeframes:
                    try:
                        config[exchange][symbol].remove(timeframe)
                        log.debug('State :: Removed {}.{}.{}'.format(exchange, symbol, timeframe))
                    except (ValueError, KeyError):
                        pass
                if len(config[exchange][symbol]) == 0:
                    del config[exchange][symbol]
                    log.debug('State :: Removed {}.{}'.format(exchange, symbol))
            if len(config[exchange]) == 0:
                del config[exchange]
                self.add_exchange_to_close(exchange)
                log.debug('State :: Removed {}'.format(exchange))
        self.persist_config()
        self.set_has_new_config_flag(True)

    def add_exchange_to_close(self, exchange):
        log.debug('Set exchange {} to be closed'.format(exchange))
        self.state['exchanges_to_close'].add(exchange)

    def get_exchanges_to_close(self):
        return self.state['exchanges_to_close']

    def clear_exchanges_to_close(self):
        log.debug('Cleared exchanges to be closed')
        self.state['exchanges_to_close'].clear()

    def persist_config(self):
        self.postgres_client.set_ccxt_ohlcv_fetcher_config(json.dumps(self.state['config']))
        log.info('Persisted config to postgres')
