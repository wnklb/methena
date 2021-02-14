CREATE_SCHEMA_CCXT_OHLCV = """
    CREATE SCHEMA IF NOT EXISTS ccxt_ohlcv;
"""

CREATE_SCHEMA_METHENA = """
    CREATE SCHEMA IF NOT EXISTS methena;
"""

CREATE_TABLE_CCXT_OHLCV_STATUS = """
    create table if not exists methena.ccxt_ohlcv_status
    (
        exchange varchar not null,
        symbol varchar not null,
        timeframe varchar not null,
        latest_timestamp timestamptz not null,
        average_duration real,
        estimated_remaining_time real,
        remaining_fetches integer,
        constraint ccxt_ohlcv_pk
            primary key (exchange, symbol, timeframe)
    );
"""

CREATE_TABLE_CCXT_OHLCV_FETCHER_STATE_IF_NOT_EXISTS = """
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

CREATE_EXCHANGE_OHLCV_TABLE_IF_NOT_EXISTS = """
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
