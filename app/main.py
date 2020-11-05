# flake8: noqa E402
import logging

from utils.log.logging import init_logging_config

init_logging_config()
log = logging.getLogger(__name__)  # noqa F841

import asyncio
import sys

from services import OHLCVFetcher


async def main():
    async with OHLCVFetcher() as ohlcv_fetcher:
        await ohlcv_fetcher.main()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit 0 via Keyboard Interrupt')
        sys.exit(0)
