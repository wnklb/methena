class MQTTParser:

    def parse_ccxt_ohlcv_topic(self, topic, payload):
        if type(payload) == 'bytes':
            payload = payload.decode()

        config = topic.split('/')[3:]
        if config[0] == 'exchange':
            exchanges = config[1].split(',')
        else:
            raise Exception("exchange token not provided in mqtt topic")

        if config[2] == 'symbol':
            symbols = config[3].split(',')
        else:
            raise Exception("symbol token not provided in mqtt topic")

        if config[4] == 'timeframe':
            timeframes = config[5].replace('-', '/').split(',')
        else:
            raise Exception("timeframe token not provided in mqtt topic")

        return {
            exchange: {
                symbol: timeframes for symbol in symbols
            } for exchange in exchanges
        }
