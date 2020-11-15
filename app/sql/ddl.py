create_schema_ccxt_ohlcv = """
    CREATE SCHEMA IF NOT EXISTS ccxt_ohlcv;
"""

create_schema_methena = """
    CREATE SCHEMA IF NOT EXISTS methena;
"""

create_table_ccxt_ohlcv_status = """
    create table if not exists methena.ccxt_ohlcv_status
    (
        exchange varchar not null,
        symbol varchar not null,
        timeframe varchar not null,
        latest_timestamp timestamptz not null,
        constraint ccxt_ohlcv_pk
            primary key (exchange, symbol, timeframe)
    );
"""
