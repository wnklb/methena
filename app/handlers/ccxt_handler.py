from handlers import BaseHandler
from tornado.escape import json_encode
from utils.ccxt import parse_exchange_to_json


class CCXTExchangesHandler(BaseHandler):
    async def get(self):
        exchanges = self.application.ccxt.get_exchanges()
        self.write(json_encode(exchanges))


class CCXTExchangeHandler(BaseHandler):
    async def get(self, exchange_id):
        exchange = await self.application.ccxt.get_exchange(exchange_id)
        data = parse_exchange_to_json(exchange)
        self.write(data)


class CCXTExchangeSymbolsHandler(BaseHandler):
    async def get(self, exchange_id):
        exchange = await self.application.ccxt.get_exchange_symbols(exchange_id)
        self.write(json_encode(exchange))


class CCXTExchangeBasesHandler(BaseHandler):
    async def get(self, exchange_id):
        bases = await self.application.ccxt.get_exchange_bases(exchange_id)
        self.write(json_encode(bases))


class CCXTExchangeQuotesHandler(BaseHandler):
    async def get(self, exchange_id):
        quotes = await self.application.ccxt.get_exchange_quotes(exchange_id)
        self.write(json_encode(quotes))
