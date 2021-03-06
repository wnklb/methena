import json
import logging

from config import OHLCV_CONFIG_FILE

log = logging.getLogger('methena')


class FilesystemClient:
    log.debug('Created FilesystemClient')

    @staticmethod
    def save_ohlcv_config(config, file=OHLCV_CONFIG_FILE):
        with open(file, 'w') as json_file:
            json.dump(config, json_file, indent=2, sort_keys=True)
        log.debug('Successfully saved OHLCV config into {}'.format(OHLCV_CONFIG_FILE))

    @staticmethod
    def load_ohlcv_config(file=OHLCV_CONFIG_FILE):
        with open(file) as json_file:
            config = json.load(json_file)
        log.debug('Successfully loaded OHLCV config from {}'.format(OHLCV_CONFIG_FILE))
        return config
