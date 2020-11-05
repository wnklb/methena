import json

from config import OHLCV_CONFIG_FILE


class FilesystemClient:

    @staticmethod
    def save_ohlcv_config(config, file=OHLCV_CONFIG_FILE):
        with open(file, 'w') as json_file:
            json.dump(config, json_file, indent=2, sort_keys=True)

    @staticmethod
    def load_ohlcv_config(file=OHLCV_CONFIG_FILE):
        with open(file) as json_file:
            return json.load(json_file)
