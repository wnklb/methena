import asyncio
import logging

from utils.log.logging import init_logging_config

init_logging_config()
log = logging.getLogger(__name__)  # noqa F841

from services.fetcher import OHLCVFetcher


async def main():
    async with OHLCVFetcher() as ohlcv_fetcher:
        # pass
        await ohlcv_fetcher.main()


if __name__ == '__main__':
    asyncio.run(main())
