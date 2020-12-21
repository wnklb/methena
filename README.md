# CCXT OHLCV Fetcher

Service for fetching OHLCV data (based on ccxt library).

## 1. Introduction

The primary goal of this service is to download & persist any OHLCV data accessible via
the [ccxt library](https://github.com/ccxt/ccxt). It comes with the following features:

* Highly customizable fetch config via *json*.
* Control commands via MQTT (adding/removal of fetch configs, stop, etc.)

---

## 2. Setup

Please follow **ALL** steps to setup this service. It is highly recommended to use Linux/Mac/WSL. If you need to use Windows, please make sure to use WSL. Aany complications under windows (e.g. not having uvloop) are up to the user to fix for himself.

### 2.1. Python Dependencies

It is recommended to use virtual environments. One easy and reliable solution is [virtualenwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/).

```bash
pip install -r app/requirements.txt

# and for development
pip install -r app/requirements_dev.txt
```

### 2.2. Environment Variables

I highly advice to use [direnv](https://direnv.net/) for virtual env management, but any other way will do. Just make sure to populate your `.env` file.

Copy `.env_template` to `.env` and populate values.

### 2.3. Postgres

Install postgres:

```bash
# Official doc: https://www.postgresql.org/download/linux/ubuntu/
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
sudo apt-get -y install postgresql
```


Setup your database, schema and user:

```bash
sudo su - postgres
psql

create database methena
\c methena

create user methena with password '1234';
GRANT ALL PRIVILEGES ON DATABASE methena to methena;

CREATE SCHEMA IF NOT EXISTS ccxt;
```

### 2.4. MQTT

In order to use MQTT you need have a broker (and optionally a client) installed on your system. The easiest way (on
Linux) is to run:

```bash
sudo apt install mosquitto mosquitto-clients
```

You may need to start the mosquitto broker manually:

```bash
sudo service mosquitto status
sudo service mosquitto start
```

### 2.5. OHLCV Fetch Config

Copy `ohlcv_config_template.json` to `ohlcv_config.json` and change values if necessary.

### 2.6. Logging (optional)

---

## 3. Architecture

There are various components at play which interact together:

* OHLCVFetcher
* CCXTService
* StateService
* PostgresClient
* MQTTClient

### 3.1. OHLCVFetcher

Its main and sole purpose is to constantly fetch data for a given OHLCV description and persist it to a database. A base
idea hereby is the OHLCV descriptor. It is a combination of exchange, symbol and timeframe, which together make a
timeseries unique.

* Start fetching at the timestamp of the last entry of a persisted descriptor (or starts from the beginning)
* Works on multiple exchanges in parallel
* Works only on one descriptor per exchange (in adherence to the exchange's rate limit)
* Has a synchronization point (default 1min) where it process new commands (e.g. new exchange added; stopping the
  service)

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


#### 3.5.2. Publishing via CLI

```bash
mosquitto_pub -t ccxt/ohlcv/add/exchange/binance/symbol/ETH-BTC/timeframe/1d -m ""
```

### 3.6. 
