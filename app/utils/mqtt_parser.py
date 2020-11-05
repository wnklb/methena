class MQTTParser:

    def parse_ccxt_ohlcv_topic(self, topic, payload):
        if type(payload) == 'bytes':
            payload = payload.decode()

        config = topic.split('/')[3:]
        if config[0] == 'exchange':
            exchanges = config[1].split(',')
            if len(exchanges) == 1 and exchanges[0] == '':  # We want to set * as a flag
                exchanges = '*'
        else:
            raise Exception('exchange token not provided in mqtt topic')

        if config[2] == 'symbol':
            symbols = config[3].upper().replace('-', '/').split(',')
            if len(symbols) == 1 and symbols[0] == '':
                symbols = '*'
        else:
            raise Exception('symbol token not provided in mqtt topic')

        if config[4] == 'timeframe':
            timeframes = config[5].split(',')
            if len(timeframes) == 1 and timeframes[0] == '':
                timeframes = '*'
        else:
            raise Exception('timeframe token not provided in mqtt topic')

        return exchanges, symbols, timeframes
