# This query returns all tables (in that case the exchanges) which are part of the ccxt_
# ohlcv schema.  In short, it gives all exchanges that are saved in the db.
select_ccxt_ohlcv_exchange_tables = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'ccxt_ohlcv';
"""

select_latest_ccxt_ohlcv_entry = """
    SELECT symbol, timeframe, max(timestamp) as timestamp
    FROM ccxt_ohlcv.{exchange}
    GROUP BY (symbol, timeframe);
"""

select_ohlcv_status = """
    SELECT exchange, symbol, timeframe, latest_timestamp
    FROM methena.ccxt_ohlcv_status
    ORDER BY exchange, symbol, timeframe;
"""

select_ohlcv_entries = """
    SELECT *
    FROM ccxt_ohlcv.{exchange_id}
    WHERE symbol='{symbol}'
    AND timeframe='{timeframe}'
    ORDER BY timestamp DESC
    LIMIT 100;
"""

select_ohlcv_fetcher_state = """
    SELECT config
    FROM methena.ccxt_ohlcv_fetcher_state
    WHERE id = 1;
"""

select_latest_timestamp = """
    SELECT timestamp from {schema}.{exchange}
    WHERE symbol='{symbol}'
    AND timeframe='{timeframe}'
    ORDER BY timestamp DESC
    LIMIT 1;
"""
