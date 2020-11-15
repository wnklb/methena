class FetchError(Exception):
    pass


class NoStateProvidedError(Exception):
    pass


class AsyncioError(Exception):
    pass


class ConfigFileNotFoundError(Exception):
    pass


class DatabaseConfigNotFoundError(Exception):
    pass


class NoConfigProvidedError(Exception):
    pass


class EnvVariableWronglySetError(Exception):
    pass
