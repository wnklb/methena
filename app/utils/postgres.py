import logging
from datetime import datetime

log = logging.getLogger()


def prepare_data_for_postgres(symbol: str, timeframe: str, ohlcv_data: list) -> list:
    data = []
    for record in ohlcv_data:
        timestamp, open, high, low, close, volume = record
        timestampTZ = datetime.fromtimestamp(timestamp / 1000)
        new_record = (symbol, timeframe, timestampTZ, open, high, low, close, volume)
        data.append(new_record)
    return data


def convert_datetime_to_timestamp(timestamp: datetime) -> int:
    return int(timestamp.timestamp() * 1000)
