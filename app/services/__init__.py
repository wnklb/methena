# flake8: noqa F841
import sys

import psycopg2

try:
    from .ccxt import *
    from .fetcher import *
    from .state import *
except psycopg2.OperationalError as e:
    print('Error: Cannot connect to postgres. Have you started postgres?')
    print(e)
    sys.exit(0)
