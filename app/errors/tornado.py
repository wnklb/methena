from tornado import web


class HTTPBadRequestError(web.HTTPError):
    def __init__(self, reason="Bad Request", log_message=None, *args, **kwargs):
        kwargs["reason"] = reason
        super().__init__(status_code=400, log_message=log_message, *args, **kwargs)
