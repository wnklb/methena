class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if len(kwargs) >= 1:
            kwargs = {}
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance
