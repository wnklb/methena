#!/usr/bin/env python3
import asyncio

from services import CCXTService


async def main():
    ccxt_client = CCXTService()
    print(await ccxt_client.get_exchanges())
    print(await ccxt_client.get_exchange('binance'))


if __name__ == '__main__':
    asyncio.run(main())
