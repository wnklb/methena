import logging

import psycopg2
import psycopg2.extras

from config import PSQL_DSN, SCHEMA_CCXT_OHLCV, SCHEMA_METHENA
from utils.postgres import convert_datetime_to_timestamp
from utils.singleton import Singleton

logger = logging.getLogger()


class PostgresClient(Singleton):
    conn = None
    cur = None

    def __init__(self):
        if self.conn is None:
            self.start()
        self.setup()

    def start(self):
        self.conn = psycopg2.connect(dsn=PSQL_DSN)
        self.cur = self.conn.cursor()
        logger.info('Postgres connected!')
        return self

    def stop(self):
        self.conn.close()

    def setup(self):
        self.create_schema_if_not_exist(SCHEMA_CCXT_OHLCV)
        self.create_schema_if_not_exist(SCHEMA_METHENA)
        self.create_table_ccxt_ohlcv_fetcher_state_if_not_exists()

    def __execute(self, query, values=None):
        self.cur.execute(query, values)

    def __commit(self):
        self.conn.commit()

    def __execute_and_commit(self, query, values=None):
        self.__execute(query, values)
        self.__commit()

    def create_schema_if_not_exist(self, schema: str):
        query = """CREATE SCHEMA IF NOT EXISTS {schema};""".format(schema=schema)
        self.__execute_and_commit(query)

    def create_table_ccxt_ohlcv_fetcher_state_if_not_exists(self):
        query = """
        create table if not exists ccxt_ohlcv_fetcher_state
        (
            state jsonb not null,
            timestamp timestamp with time zone default CURRENT_TIMESTAMP not null,
            id integer not null
                constraint ccxt_ohlcv_fetcher_state_pk
                    primary key
        );

        alter table ccxt_ohlcv_fetcher_state owner to methena;
        """
        self.__execute_and_commit(query)

    def create_exchange_ohlcv_table_if_not_exists(self, table):
        query = """
        CREATE TABLE IF NOT EXISTS {schema}.{table} (
            symbol varchar(16),
            timeframe varchar(2),
            timestamp timestamp,
            open float,
            high float,
            low float,
            close float,
            volume float
        );""".format(schema=SCHEMA_CCXT_OHLCV, table=table)
        self.__execute_and_commit(query)

    def insert(self, query, values):
        self.__execute_and_commit(query, values)

    def insert_many(self, values, table, schema=SCHEMA_CCXT_OHLCV, page_size=1000):
        query = "INSERT INTO {schema}.{table} VALUES %s;".format(schema=schema, table=table)
        psycopg2.extras.execute_values(self.cur, query, values, page_size=page_size)
        self.__commit()

    def fetch_one(self, query):
        self.__execute(query)
        return self.cur.fetchone()

    def fetch_latest_timestamp(self, exchange, symbol, timeframe):
        query = """
        SELECT timestamp from {schema}.{exchange}
        WHERE symbol='{symbol}'
        AND timeframe='{timeframe}'
        ORDER BY timestamp DESC
        LIMIT 1;
        """.format(
            schema=SCHEMA_CCXT_OHLCV,
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe
        )
        datetime_ = self.fetch_one(query)
        if datetime_ is None:
            return
        timestamp = convert_datetime_to_timestamp(datetime_[0])
        return timestamp

    def set_ccxt_ohlcv_fetcher_state(self, state):
        query = """
        insert into methena.ccxt_ohlcv_fetcher_state (id, state, timestamp)
        values (1, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (id)
        DO UPDATE
        SET
            state = EXCLUDED.state,
            timestamp = EXCLUDED.timestamp
        ;
        """
        self.insert(query, (state,))

    def get_ccxt_ohlcv_fetcher_state(self):
        query = """
        SELECT state
        FROM methena.ccxt_ohlcv_fetcher_state
        WHERE id = 1;
        """
        return self.fetch_one(query)[0]
