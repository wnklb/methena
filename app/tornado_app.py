import logging

import tornado.ioloop
import tornado.locks
import tornado.web
from config import APP_PORT, AUTORELOAD, COMPRESS_RESPONSE, DEBUG, SERVE_TRACEBACK
from handlers import (CCXTExchangeBasesHandler, CCXTExchangeHandler, CCXTExchangeQuotesHandler,
                      CCXTExchangesHandler, CCXTExchangeSymbolsHandler, MethenaExchangesHandler,
                      MethenaOHLCVStatusHandler, MethenaOHLCVFetcherStateHandler)
from services import CCXTService, PostgresClient, StateService
from tornado.options import define, options
from tornado.routing import HostMatches

log = logging.getLogger('methena')

define("port", default=APP_PORT, help="run on the given port", type=int)

handlers = [
    (
        HostMatches(r'(localhost|127\.0\.0\.1)'),
        [
            # https://www.tornadoweb.org/en/stable/httputil.html#tornado.httputil.HTTPServerRequest
            (r"/ccxt/exchanges", CCXTExchangesHandler),
            (r"/ccxt/exchanges/([^/]+)", CCXTExchangeHandler),
            (r"/ccxt/exchanges/([^/]+)/symbols", CCXTExchangeSymbolsHandler),
            (r"/ccxt/exchanges/([^/]+)/bases", CCXTExchangeBasesHandler),
            (r"/ccxt/exchanges/([^/]+)/quotes", CCXTExchangeQuotesHandler),
            (r"/methena/exchanges/", MethenaExchangesHandler),
            (r"/methena/ohlcv-status/", MethenaOHLCVStatusHandler),
            (r"/methena/ohlcv-fetcher-state/", MethenaOHLCVFetcherStateHandler)
        ]
    )
]


class Application(tornado.web.Application):
    ccxt = CCXTService()
    pg = PostgresClient()
    state = StateService()

    def __init__(self):
        settings = dict(
            debug=DEBUG,
            autoreload=AUTORELOAD,
            compress_response=COMPRESS_RESPONSE,
            serve_traceback=SERVE_TRACEBACK,
            # login_url=
            # default_handler_class  # in case route is not found
        )
        super(Application, self).__init__(handlers, **settings)


async def main():
    tornado.options.parse_command_line()

    # Create the global connection pool.
    app = Application()
    app.listen(options.port)
    log.info('Tornado started at port {}  -  Debug: {}  -  Autoreload: {}'.format(APP_PORT, DEBUG,
                                                                                  AUTORELOAD))

    # In this demo the server will simply run until interrupted
    # with Ctrl-C, but if you want to shut down more gracefully,
    # call shutdown_event.set().
    # shutdown_event = tornado.locks.Event()
    # await shutdown_event.wait()


if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)
