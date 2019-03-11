# CCXT OHLCV Fetcher
Service for fetching OHLCV data (based on ccxt library).

## Environment Variables

If multiple entries can be set for each variable, separate them via ``,`` .

* **PSQL_DSN**: ``postgresql://user:password@host:port/dbname``
* **SHCEMA**: ``ccxt_ohlcv``
* **EXCHANGES**: ``binance,bitfinex``
* **SYMBOLS**: ``BTC/ETH`` (if left empty, all available symbols at each exchange will be taken in consideration)
* **TIMEFRAMES**: ``1d,1h``