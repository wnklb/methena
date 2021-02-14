import logging

import psycopg2
import psycopg2.extras
from config import PSQL_DSN, SCHEMA_CCXT_OHLCV, SCHEMA_METHENA
from sql.ddl import CREATE_TABLE_CCXT_OHLCV_STATUS, CREATE_SCHEMA_CCXT_OHLCV, CREATE_SCHEMA_METHENA, \
    CREATE_TABLE_CCXT_OHLCV_FETCHER_STATE_IF_NOT_EXISTS
from utils.postgres import convert_datetime_to_timestamp
from utils.singleton import Singleton

log = logging.getLogger('methena')


class PostgresClient(Singleton):
    conn = None
    cur = None
    setup_done = False
    log.debug('Created PostgresClient')

    def __init__(self):
        if self.conn is None:
            self.__start()
        if not self.setup_done:
            self.__setup()
        log.debug('Initialized PostgresClient')

    def stop(self):
        self.conn.close()
        log.info('PostgresClient closed connection to {}'.format(PSQL_DSN.split('@')[1]))

    def __start(self):
        self.conn = psycopg2.connect(dsn=PSQL_DSN)
        self.cur = self.conn.cursor()
        log.info('PostgresClient connected to {}'.format(PSQL_DSN.split('@')[1]))
        return self

    def __setup(self):
        self.execute(CREATE_SCHEMA_CCXT_OHLCV)
        self.execute(CREATE_SCHEMA_METHENA)
        self.execute(CREATE_TABLE_CCXT_OHLCV_FETCHER_STATE_IF_NOT_EXISTS)
        self.execute(CREATE_TABLE_CCXT_OHLCV_STATUS)
        self.setup_done = True
        log.info('PostgresClient setup done - initial schemas and tables created.')

    def __execute(self, query, values=None):
        self.cur.execute(query, values)

    def __commit(self):
        self.conn.commit()

    def __execute_and_commit(self, query, values=None):
        self.__execute(query, values)
        self.__commit()

    def insert(self, query, values):
        self.__execute_and_commit(query, values)

    def insert_many(self, query, values, page_size=1000):
        psycopg2.extras.execute_values(self.cur, query, values, page_size=page_size)
        self.__commit()

    def execute(self, query, values=None):
        self.__execute_and_commit(query, values)

    def fetch_one(self, query):
        self.__execute(query)
        return self.cur.fetchone()

    def fetch_many(self, query):
        self.__execute(query)
        return self.cur.fetchall()
