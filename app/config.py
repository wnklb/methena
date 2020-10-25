from os import getenv


def get_list(key, default=None):
    data = getenv(key, default)
    return data.split(',') if data else None


def get_int(key, default):
    data = int(getenv(key, default))
    return data


PSQL_DSN = getenv('PSQL_DSN')

SCHEMA = getenv('SCHEMA')
EXCHANGES = get_list('EXCHANGES')
SYMBOLS = get_list('SYMBOLS')
TIMEFRAMES = get_list('TIMEFRAMES')

MQTT_HOST = getenv('MQTT_HOST')
MQTT_PORT = get_int('MQTT_PORT', '1883')
MQTT_TOPIC_CCXT_OHLCV = getenv('MQTT_TOPICS', 'ccxt/ohlcv')
