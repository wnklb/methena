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

create_table_ccxt_ohlcv_fetcher_state_if_not_exists = """
    create table if not exists ccxt_ohlcv_fetcher_state
    (
        config jsonb not null,
        timestamp timestamp with time zone default CURRENT_TIMESTAMP not null,
        id integer not null
            constraint ccxt_ohlcv_fetcher_state_pk
                primary key
    );

    alter table ccxt_ohlcv_fetcher_state owner to methena;
"""

create_exchange_ohlcv_table_if_not_exists = """
    CREATE TABLE IF NOT EXISTS {schema}.{table} (
        symbol varchar(16),
        timeframe varchar(2),
        timestamp timestamp,
        open float,
        high float,
        low float,
        close float,
        volume float
    );
"""
