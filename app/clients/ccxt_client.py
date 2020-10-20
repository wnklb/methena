import asyncio

import ccxt.async_support as ccxt


class CCXTClient:

    def __init__(self):
        self.exchange_ids = set()
        self.exchanges = {}

    def __del__(self):
        for exchange in self.exchanges.values():
            asyncio.ensure_future(exchange.close())

    @staticmethod
    async def get_exchanges():
        return ccxt.exchanges

    async def get_exchange(self, exchange_id):
        if exchange_id not in self.exchange_ids:
            await self._init_exchange(exchange_id)
        return self.exchanges.get(exchange_id)

    async def get_exchange_symbols(self, exchange_id):
        exchange = await self.get_exchange(exchange_id)
        return exchange.symbols

    async def get_exchange_timeframes(self, exchange_id):
        exchange = await self.get_exchange(exchange_id)
        return exchange.timeframes

    async def _init_exchange(self, exchange_id):
        try:
            exchange = getattr(ccxt, exchange_id)()
            await exchange.load_markets()
            self.exchanges[exchange_id] = exchange
            self.exchange_ids.add(exchange_id)
        except Exception as e:
            raise NotImplementedError


async def main():
    ccxt_client = CCXTClient()
    print(await ccxt_client.get_exchanges())
    print(await ccxt_client.get_exchange('binance'))


if __name__ == '__main__':
    asyncio.run(main())
