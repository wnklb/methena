from clients.filesystem_client import FilesystemClient


class OHLCVConfigService:
    __instance = None
    config = None
    exchanges = None

    def __init__(self):
        if OHLCVConfigService.__instance is not None:
            raise Exception("OHLCVConfigService is a Singleton class. Use its get() function.")
        else:
            OHLCVConfigService.__instance = self
            OHLCVConfigService.config = FilesystemClient.load_ohlcv_config()
            self.__udpate_state()

    @staticmethod
    def get_instance():
        if OHLCVConfigService.__instance is None:
            OHLCVConfigService()
        return OHLCVConfigService.__instance

    def add(self, descriptor):
        for exchange, symbols in descriptor.items():
            if exchange in self.config:
                for symbol, timeframes in symbols:
                    if symbol in self.config[exchange]:
                        new_timeframes = list(set(self.config[exchange][symbol] + timeframes))
                        self.config[exchange][symbol] = new_timeframes
                    else:
                        self.config[exchange][symbol] = timeframes
            else:
                self.config[exchange] = {symbol: timeframes for symbol, timeframes in symbols}
        self.__udpate_state()

    def remove(self, descriptor):
        pass

    def __udpate_state(self):
        OHLCVConfigService.exchanges = OHLCVConfigService.config.keys()
