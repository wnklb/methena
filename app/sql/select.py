# This query returns all tables (in that case the exchanges) which are part of the ccxt_
# ohlcv schema.  In short, it gives all exchanges that are saved in the db.
SELECT_CCXT_OHLCV_EXCHANGE_TABLES = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'ccxt_ohlcv';
"""

SELECT_LATEST_CCXT_OHLCV_ENTRY = """
    SELECT symbol, timeframe, max(timestamp) as timestamp
    FROM ccxt_ohlcv.{exchange}
    GROUP BY (symbol, timeframe);
"""

SELECT_OHLCV_STATUS = """
    SELECT exchange, symbol, timeframe, latest_timestamp, average_duration, estimated_remaining_time, remaining_fetches
    FROM methena.ccxt_ohlcv_status
    ORDER BY exchange, symbol, timeframe;
"""

SELECT_OHLCV_ENTRIES = """
    SELECT *
    FROM ccxt_ohlcv.{exchange_id}
    WHERE symbol='{symbol}'
    AND timeframe='{timeframe}'
    ORDER BY timestamp DESC
    LIMIT 100;
"""

SELECT_OHLCV_FETCHER_STATE = """
    SELECT config
    FROM methena.ccxt_ohlcv_fetcher_state
    WHERE id = 1;
"""

SELECT_LATEST_TIMESTAMP = """
    SELECT timestamp from {schema}.{exchange}
    WHERE symbol='{symbol}'
    AND timeframe='{timeframe}'
    ORDER BY timestamp DESC
    LIMIT 1;
"""
