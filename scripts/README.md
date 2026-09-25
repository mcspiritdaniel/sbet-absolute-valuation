# Data scripts

Rebuild the files in `../data/` for the SBET analysis.

| Script | Output |
|---|---|
| `task1_eth.py` | `data/eth_usd_at_nyse_close.csv`: ETH/USD at the NYSE close for every XNYS session from 2025-06-02 to the latest completed session |
| `task23_edgar.py` | `data/sbet_edgar_filings.csv` (SBET filings since 2025-06-01) and `data/SBET_FORM_10Q_3Q25.html` (10-Q for the quarter ended 2025-09-30) |

## Setup

Run these from the repo root. `pandas_market_calendars` is pinned to 4.6.1 because 5.x needs Python 3.10+.

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
```

## Run

`task1_eth.py` reads a CoinGecko Demo API key from the `COINGECKO_API_KEY` environment variable. Set it in your shell; don't commit it or paste it into a file in this repo.

```bash
.venv/bin/python scripts/task1_eth.py
.venv/bin/python scripts/task23_edgar.py
```

Both scripts write to `data/` and overwrite the existing files. `task1_eth.py` also takes an optional output path as its first argument. Each script prints a validation summary: row counts, nulls, flagged rows, and source coverage.

## Notes

- The CoinGecko Demo plan only serves the past 365 days. Sessions older than that use the open of the Coinbase ETH-USD hourly candle that starts at the close. So each rerun shifts the CoinGecko/Coinbase boundary forward, and the `source` column changes for the oldest CoinGecko rows.
- `coinbase_eth_usd_at_close` is filled for every session so you can compare the two sources.
- EDGAR requests send the User-Agent `Dan McSpirit mcspiritdaniel@gmail.com` and are throttled to 5 requests per second.
