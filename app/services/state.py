import logging
from datetime import timedelta, datetime

from clients.filesystem_client import FilesystemClient
from utils.singleton import Singleton

log = logging.getLogger()


class StateService(Singleton):
    __instance = None
    state = {
        'config': {},
        'next_sync_timestamp': None,
    }

    def __init__(self):
        StateService.state['config'] = FilesystemClient.load_ohlcv_config()

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
        for exchange, symbols in descriptor.items():
            if exchange in self.state['config']:
                for symbol, timeframes in symbols.items():
                    if symbol in self.state['config'][exchange]:
                        new_timeframes = list(
                            set(self.state['config'][exchange][symbol] + timeframes))
                        self.state['config'][exchange][symbol] = new_timeframes
                    else:
                        self.state['config'][exchange][symbol] = timeframes
            else:
                self.state['config'][exchange] = {symbol: timeframes for symbol, timeframes in
                                                  symbols.items()}

    def remove(self, descriptor):
        pass

    def get_next_sync_timestamp(self):
        return self.state['next_sync_timestamp']

    def set_next_sync_timestamp(self):
        self.state['next_sync_timestamp'] = datetime.now() + timedelta(seconds=20)

