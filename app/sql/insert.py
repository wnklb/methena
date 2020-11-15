upsert_ccxt_ohlcv_status_query = """
    INSERT INTO methena.ccxt_ohlcv_status
    (exchange, symbol, timeframe, latest_timestamp)
    VALUES %s
    ON CONFLICT ON CONSTRAINT ccxt_ohlcv_pk
    DO UPDATE
    SET latest_timestamp = EXCLUDED.latest_timestamp;
"""
