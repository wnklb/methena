# CCXT OHLCV Fetcher

Service for fetching OHLCV data (based on ccxt library).

## 1. Introduction

The primary goal of this service is to download & persist any OHLCV data accessible via the [ccxt library](https://github.com/ccxt/ccxt). It comes with the following features:
* Highly customizable fetch config via *json*.
* Control commands via MQTT (adding/removal of fetch configs, stop, etc.)

---

## 2. Setup

TODO: describe correct setup

### Environment Variables

1. Copy `.env_template` to `.env` and populate values.

If multiple entries can be set for each variable, separate them via ``,`` .

* **PSQL_DSN**: ``postgresql://user:password@host:port/dbname``
* **SHCEMA**: ``ccxt_ohlcv``
* **EXCHANGES**: ``binance,bitfinex``
* **SYMBOLS**: ``BTC/ETH`` (if left empty, all available symbols at each exchange will be taken in
  consideration)
* **TIMEFRAMES**: ``1d,1h``

### Postgres

```bash
sudo su - postgres
psql

create database methena
\c methena

create user methena with password '1234';
GRANT ALL PRIVILEGES ON DATABASE methena to methena;

CREATE SCHEMA IF NOT EXISTS ccxt;
```

### OHLCV Fetch Config

### MQTT Config

### Logging (optional)

---

## 3. Architecture

There are various components at play which interact together:
* OHLCVFetcher
* CCXTService
* StateService
* PostgresClient
* MQTTClient

### 3.1. OHLCVFetcher

Its main and sole purpose is to constantly fetch data for a given OHLCV description and persist it to a database. A base idea hereby is the OHLCV descriptor. It is a combination of exchange, symbol and timeframe, which together make a timeseries unique.

* Start fetching at the timestamp of the last entry of a persisted descriptor (or starts from the beginning)
* Works on multiple exchanges in parallel
* Works only on one descriptor per exchange (in adherence to the exchange's rate limit)
* Has a synchronization point (default 1min) where it process new commands (e.g. new exchange added; stopping the service)

### 3.2. CCXTService

Basically the interface for ccxt. In addition it handles the initialization and closing of markets

### 3.3. StateService

### 3.4. PostgresClient

### 3.5. MQTTClient

#### 3.5.1. Topics

| Base-Path | Path-Extension | Behaviour |
|---|---|---|
| `ccxt/ohlcv/add/` | `exchange/*/symbol/*/timeframe/*` | Adds the given descriptor. `*` can be a single value or a comma-separated list of values (e.g. `binance` or `binance,bitfinex`) |
| `ccxt/ohlcv/remove/` | `exchange/*/symbol/*/timeframe/*` | Removes the given descriptor. Same patterns apply |
| `ccxt/ohlcv/replace/` | `exchange/*/symbol/*/timeframe/*` | Replaces the given descriptor. Depending on its lowest specificity, replaces the whole provided tree (e.g. `*` flag for symbol replaces the timeframes of every currently set symbol. |

### 3.6. 