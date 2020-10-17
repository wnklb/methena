# CCXT OHLCV Fetcher




## Setup

1. Copy `.env_template` to `.env` and populate values.


## Databes setup

```bash
sudo su - postgres
psql

create database methena
\c methena

create user methena with password '1234';
GRANT ALL PRIVILEGES ON DATABASE methena to methena;

CREATE SCHEMA IF NOT EXISTS ccxt;
```