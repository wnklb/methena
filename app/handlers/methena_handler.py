import datetime
from collections import OrderedDict

from handlers import BaseHandler
from sql.insert import upsert_ccxt_ohlcv_status_query
from sql.select import (select_ccxt_ohlcv_exchange_tables, select_latest_ccxt_ohlcv_entry,
                        select_ohlcv_status, select_ohlcv_fetcher_state)


class MethenaExchangesHandler(BaseHandler):
    async def get(self):
        records = self.application.pg.fetch_many(select_ccxt_ohlcv_exchange_tables)
        result = [record[0] for record in records]
        self.write_json(result)


class MethenaOHLCVStatusHandler(BaseHandler):
    async def get(self):
        results = self.application.pg.fetch_many(select_ohlcv_status)

        data = OrderedDict()
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
        exchange_tables = self.application.pg.fetch_many(select_ccxt_ohlcv_exchange_tables)
        exchanges = [record[0] for record in exchange_tables]

        data = []
        for exchange in exchanges:

            # This query returns the latest reported timestamp for the given descriptor.
            query = select_latest_ccxt_ohlcv_entry.format(exchange=exchange)
            latest_ohlcv_entries = self.application.pg.fetch_many(query)

            if not latest_ohlcv_entries:
                continue
            for entry in latest_ohlcv_entries:
                data.append((exchange, entry[0], entry[1], entry[2]))

        self.application.pg.insert_many(upsert_ccxt_ohlcv_status_query, data)
        self.set_status(204)


class MethenaOHLCVFetcherStateHandler(BaseHandler):
    async def get(self):
        data = self.application.pg.fetch_one(select_ohlcv_fetcher_state)
        self.write_json(data)
