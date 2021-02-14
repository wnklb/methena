import datetime
from collections import OrderedDict

from handlers import BaseHandler
from sql.insert import UPSERT_CCXT_OHLCV_STATUS_QUERY
from sql.select import (SELECT_CCXT_OHLCV_EXCHANGE_TABLES, SELECT_LATEST_CCXT_OHLCV_ENTRY,
                        SELECT_OHLCV_STATUS, SELECT_OHLCV_FETCHER_STATE)


class MethenaExchangesHandler(BaseHandler):
    async def get(self):
        records = self.application.pg.fetch_many(SELECT_CCXT_OHLCV_EXCHANGE_TABLES)
        result = [record[0] for record in records]
        self.write_json(result)


class MethenaOHLCVStatusHandler(BaseHandler):
    async def get(self):
        results = self.application.pg.fetch_many(SELECT_OHLCV_STATUS)

        # data = OrderedDict()
        data = []
        for result in results:
            exchange = result[0]
            symbol = result[1]
            timeframe = result[2]
            timestamp = result[3]

            now = datetime.datetime.now(datetime.timezone.utc)
            now_minus_1d = now - datetime.timedelta(days=1)
            now_minus_1h = now - datetime.timedelta(hours=1)
            now_minus_1m = now - datetime.timedelta(minutes=1)

            status = None
            if timeframe == "1d":
                status = timestamp > now_minus_1d
            elif timeframe == "1h":
                status = timestamp > now_minus_1h
            elif timeframe == "1m":
                status = timestamp > now_minus_1m

            if exchange not in data:
                data[exchange] = {}
            if symbol not in data[exchange]:
                data[exchange][symbol] = {}
            data[exchange][symbol][timeframe] = {
                "timestamp": timestamp,
                "latest": status,
            }

        self.write_json(data)

    # TODO: implemented?
    async def post(self):
        """Updates the status of the latest OHLCV fetch."""
        exchange_tables = self.application.pg.fetch_many(SELECT_CCXT_OHLCV_EXCHANGE_TABLES)
        exchanges = [record[0] for record in exchange_tables]

        data = []
        for exchange in exchanges:

            # This query returns the latest reported timestamp for the given descriptor.
            query = SELECT_LATEST_CCXT_OHLCV_ENTRY.format(exchange=exchange)
            latest_ohlcv_entries = self.application.pg.fetch_many(query)

            if not latest_ohlcv_entries:
                continue
            for entry in latest_ohlcv_entries:
                data.append((exchange, entry[0], entry[1], entry[2]))

        self.application.pg.insert_many(UPSERT_CCXT_OHLCV_STATUS_QUERY, data)
        self.set_status(204)


class MethenaOHLCVFetcherStateHandler(BaseHandler):
    async def get(self):
        data = self.application.pg.fetch_one(SELECT_OHLCV_FETCHER_STATE)
        self.write_json(data)
