#!/usr/bin/env python3
import asyncio

from app.clients.ccxt_client import CCXTClient


async def main():
    ccxt_client = CCXTClient()
    print(await ccxt_client.get_exchanges())
    print(await ccxt_client.get_exchange('binance'))


if __name__ == '__main__':
    asyncio.run(main())
