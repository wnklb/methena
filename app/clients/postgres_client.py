import logging

import psycopg2
import psycopg2.extras

from config import PSQL_DSN, SCHEMA
from utils import convert_datetime_to_timestamp

logger = logging.getLogger()


class SynchronousPostgresClient:

    def __init__(self):
        self.conn = None
        self.cur = None

    def __enter__(self):
        self.conn = psycopg2.connect(dsn=PSQL_DSN)
        self.cur = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def execute(self, query):
        self.cur.execute(query)

    def commit(self):
        self.conn.commit()

    def create_schema_if_not_exist(self, schema: str):
        query = "CREATE SCHEMA IF NOT EXISTS {schema};".format(schema=schema)
        self.execute(query)
        self.commit()

    def create_table_if_not_exists(self, schema, table):
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
        );""".format(schema=schema, table=table)
        self.execute(query)
        self.commit()

    def insert_many(self, values, table, schema=SCHEMA, page_size=1000):
        query = "INSERT INTO {schema}.{table} VALUES %s;".format(schema=schema, table=table)
        psycopg2.extras.execute_values(self.cur, query, values, page_size=page_size)
        self.conn.commit()

    def fetch_one(self, query):
        self.execute(query)
        return self.cur.fetchone()

    def fetch_latest_timestamp(self, exchange, symbol, timeframe):
        query = """
        SELECT timestamp from {schema}.{exchange}
        WHERE symbol='{symbol}'
        AND timeframe='{timeframe}'
        ORDER BY timestamp DESC
        LIMIT 1;
        """.format(
            schema=SCHEMA,
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe
        )
        datetime_ = self.fetch_one(query)
        if datetime_ is None:
            return
        timestamp = convert_datetime_to_timestamp(datetime_[0])
        return timestamp
