import json
import traceback
from typing import Awaitable, Optional

from tornado.web import RequestHandler

from config import CORS_ORIGIN
from errors import HTTPBadRequestError
from utils.tornado import json_encode


class BaseHandler(RequestHandler):
    json_args = None

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def prepare(self):
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            body = self.request.body
            if body:
                self.json_args = json.loads(body)
            else:
                reason = "Bad Request. JSON requests require a body. Please provide one."
                log_message = "400: Bad Request - Content-Type 'application/json' requires a body."
                raise HTTPBadRequestError(reason=reason, log_message=log_message)
        else:
            self.json_args = None

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", CORS_ORIGIN)
        self.set_header("Access-Control-Allow-Headers", 'x-requested-with')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, DELETE, PATCH, OPTIONS')
        self.set_header("Access-Control-Allow-Headers", 'authorization,content-type')
        # self.set_header("Access-Control-Allow-Headers", "*")

    def write_error(self, status_code, **kwargs):
        err_cls, err, tb = kwargs['exc_info']
        status_code = 500
        reason = "Internal Server Error"
        if not isinstance(err, TypeError):
            if err.status_code:
                status_code = err.status_code
                reason = err.reason

        self.set_header('Content-Type', 'application/json')
        self.set_status(status_code)

        response = {
            'code': status_code,
            'message': reason
        }
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            lines = []
            for line in traceback.format_exception(*kwargs["exc_info"]):
                lines.append(line)
            response['traceback'] = lines
        self.write_json_error(response)
        self.finish()

    # def get_current_user(self) -> Any:
    #     pass

    # def on_connection_close(self) -> None:
    #     pass

    async def post(self):
        self.write('some post')

    async def get(self):
        self.write('some get')

    async def patch(self):
        self.write('some patch')

    async def delete(self):
        self.write('some delete')

    async def put(self):
        self.write('put')

    async def options(self):
        # for preflight CORS requests
        self.set_status(204)
        await self.finish()

    def write_json_error(self, response: dict):
        self.write(json.dumps({'error': response}))

    def write_json(self, data):
        self.write(json_encode(data))
