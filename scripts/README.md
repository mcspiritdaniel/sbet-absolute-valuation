# Data scripts

Rebuild the files in `../data/` for the SBET analysis.

| Script | Output |
|---|---|
| `task1_eth.py` | `data/eth_usd_at_nyse_close.csv`: ETH/USD at the NYSE close for every XNYS session from 2025-06-02 to the latest completed session |
| `task23_edgar.py` | `data/sbet_edgar_filings.csv` (SBET filings since 2025-06-01) and `data/SBET_FORM_10Q_3Q25.html` (10-Q for the quarter ended 2025-09-30) |
| `task4_8k_exhibits.py` | `data/filings/<filing_date>_<accession>/`: primary document and EX-99 exhibits for each 8-K/8-K/A with item 7.01, 8.01 or 2.02, plus `data/filings/manifest.csv`. Run it after `task23_edgar.py`, which it reads. |

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
.venv/bin/python scripts/task4_8k_exhibits.py
```

Both scripts write to `data/` and overwrite the existing files. `task1_eth.py` also takes an optional output path as its first argument. Each script prints a validation summary: row counts, nulls, flagged rows, and source coverage.

## Notes

- The CoinGecko Demo plan only serves the past 365 days. Sessions older than that use the open of the Coinbase ETH-USD hourly candle that starts at the close. So each rerun shifts the CoinGecko/Coinbase boundary forward, and the `source` column changes for the oldest CoinGecko rows.
- `coinbase_eth_usd_at_close` is filled for every session so you can compare the two sources.
- sec.gov's CDN adds a bot-management `<script>` tag to HTML responses. The EDGAR scripts remove it, and keep the change only if the file then matches the size in the filing's `index.json`. Documents that `index.json` doesn't list are checked against the filing's full-submission `.txt` instead.
- EDGAR requests send the User-Agent `Dan McSpirit mcspiritdaniel@gmail.com` and are throttled to 5 requests per second.
