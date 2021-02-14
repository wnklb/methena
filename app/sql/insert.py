INSERT_OHLCV_ENTRIES = """
    INSERT INTO {schema}.{table} VALUES %s;
"""

UPSERT_CCXT_OHLCV_STATUS = """
    INSERT INTO methena.ccxt_ohlcv_status
    (exchange, symbol, timeframe, latest_timestamp, average_duration, estimated_remaining_time, remaining_fetches)
    VALUES %s
    ON CONFLICT ON CONSTRAINT ccxt_ohlcv_pk
    DO UPDATE
    SET
        latest_timestamp = EXCLUDED.latest_timestamp,
        average_duration = EXCLUDED.average_duration,
        estimated_remaining_time = EXCLUDED.estimated_remaining_time,
        remaining_fetches = EXCLUDED.remaining_fetches
    ;
"""

UPSERT_CCXT_OHLCV_FETCHER_STATE = """
    insert into methena.ccxt_ohlcv_fetcher_state (id, config, timestamp)
    values (1, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (id)
    DO UPDATE
    SET
        config = EXCLUDED.config,
        timestamp = EXCLUDED.timestamp
    ;
"""
