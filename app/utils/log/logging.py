import json
import logging.config
import os


# https://docs.python.org/3/howto/logging-cookbook.html#configuring-filters-with-dictconfig
class MaxLevelFilter(logging.Filter):
    def __init__(self, level=None):
        super().__init__()
        self.level = level

    def filter(self, record):
        if self.level is None:
            return True
        return record.levelno <= self.level


def init_logging_config(
        file_name='logging_local.json',
        path='utils/log/',
        default_level=logging.INFO,
        env_key='LOG_CFG'  # Allows to provide a different log configuration
):
    """Setup log configuration"""
    path = path + file_name
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
            # return config
            logging.config.dictConfig(config)  # this, apparently, does not work with sanic log ...
    else:
        logging.basicConfig(level=default_level)
        # TODO: I have no idea what to return in this case
