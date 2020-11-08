# flake8: noqa E402
import asyncio
import logging
import sys

from error import NoStateProvidedError
from utils.log.logging import init_logging_config

init_logging_config()
log = logging.getLogger(__name__)  # noqa F841


try:
    from services import OHLCVFetcher
except NoStateProvidedError as e:
    log.error(e)
    sys.exit(0)


async def main():
    async with OHLCVFetcher() as ohlcv_fetcher:
        await ohlcv_fetcher.main()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info('Exit 0 via Keyboard Interrupt')
    finally:
        sys.exit(0)
