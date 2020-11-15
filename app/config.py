from os import getenv

from errors import EnvVariableWronglySetError


def get_list(key, default=None):
    data = getenv(key, default)
    return data.split(',') if data else None


def get_int(key, default):
    return int(getenv(key, default))


def get_bool(key, default):
    value = getenv(key, default)
    if value == 'True':
        return True
    elif value == 'False':
        return False
    else:
        raise EnvVariableWronglySetError(
            'Env variable {} is no boolean but "{}"'.format(key, value))


PSQL_DSN = getenv('PSQL_DSN')

OHLCV_DB_STATE = get_bool('OHLCV_DB_STATE', 'False')
OHLCV_CONFIG_FILE = getenv('OHLCV_CONFIG_FILE', 'ohlcv_config.json')

SCHEMA_CCXT_OHLCV = getenv('SCHEMA_CCXT_OHLCV')
SCHEMA_METHENA = getenv('SCHEMA_METHENA')

MQTT_HOST = getenv('MQTT_HOST')
MQTT_PORT = get_int('MQTT_PORT', '1883')
MQTT_TOPIC_CCXT_OHLCV = getenv('MQTT_TOPIC_CCXT_OHLCV', 'ccxt/ohlcv/#')

APP_HOST = getenv('APP_HOST')
APP_PORT = getenv('APP_PORT')

DEBUG = get_bool('DEBUG', 'True')
AUTORELOAD = get_bool('AUTORELOAD', 'True')
COMPRESS_RESPONSE = get_bool('COMPRESS_RESPONSE', 'True')
SERVE_TRACEBACK = get_bool('SERVE_TRACEBACK', 'True')

CORS_ORIGIN = getenv('CORS_ORIGIN')
