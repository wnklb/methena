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

## ToDos:

### General

* Ability to specify a start and end timestamp from which to start fetching
* What data do I want from logging? from monitoring? Or is this all part of the rest service?

### OHLCVFetcher

* Improve logging (what and how frequent; which values?; how does this work with high async count?)
* Exception handling
  * descriptor is not available
  * something went wrong with the chunk?
* Restart / Skip mechanism that is in sync with the synchronization mechanism and doesn't block

### CCXTService

* Refactor it into a service
* Ability to check if a given descriptor is valid (possible with the exchange) and reject/notify if not
* Ability to handle * flags for creation/deletion/modification

### PostgresClient

* Ability to create schema on init
* Pooling

### MQTTClient

* Ability to handle * flags f
* Make Singleton