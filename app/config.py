from os import getenv


def parse_symbols():
    symbols = getenv('SYMBOLS')
    if not symbols:
        return None
    else:
        return symbols.split(',')


PSQL_DSN = getenv('PSQL_DSN')

SCHEMA = getenv('SCHEMA')
EXCHANGES = getenv('EXCHANGES').split(',')
SYMBOLS = parse_symbols()
TIMEFRAMES = getenv('TIMEFRAMES').split(',')
