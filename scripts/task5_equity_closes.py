"""Task 5: SBET and S&P 500 daily closes for every XNYS session 2025-06-02 .. END (default: latest completed session).

Primary: Yahoo Finance chart API daily Close (unadjusted for dividends; split-adjusted, so the script
fails if Yahoo reports any split in the window).
Cross-check: Nasdaq historical quotes API (api.nasdaq.com). It serves SBET but not the S&P 500
("Symbol not exists" for SPX), so spx_nasdaq stays empty unless that changes. Nasdaq returns 0 rows
for some narrow date ranges, so the script always requests the full range and checks the row count.

Usage: task5_equity_closes.py [END_DATE] [OUT_CSV]
"""
import os, sys, time
from pathlib import Path
import pandas as pd
import pandas_market_calendars as mcal
import requests

os.chdir(Path(__file__).resolve().parent.parent)
START = "2025-06-02"
ET = "America/New_York"
now = pd.Timestamp.now(tz="UTC")
END = sys.argv[1] if len(sys.argv) > 1 else now.tz_convert(ET).date().isoformat()
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/sbet_spx_closes.csv"
SBET_TOL, SPX_TOL_PCT = 0.01, 0.05
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

sched = mcal.get_calendar("XNYS").schedule(start_date=START, end_date=END)
sched = sched[sched["market_close"] <= now]
sessions = pd.Index(sched.index.date, name="date")


def yahoo(symbol):
    p1 = int(pd.Timestamp(START, tz=ET).timestamp())
    p2 = int((pd.Timestamp(sessions[-1], tz=ET) + pd.Timedelta(days=1)).timestamp())
    r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                     params={"period1": p1, "period2": p2, "interval": "1d", "events": "split,div"},
                     headers=UA, timeout=60)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    splits = res.get("events", {}).get("splits")
    if splits:
        raise RuntimeError(f"{symbol}: Yahoo reports splits in window {splits}; Close would be split-adjusted")
    dates = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert(ET).date
    s = pd.Series(res["indicators"]["quote"][0]["close"], index=dates, dtype="float64")
    if s.index.duplicated().any():
        raise RuntimeError(f"{symbol}: duplicate Yahoo dates {list(s.index[s.index.duplicated()])}")
    return s


def nasdaq(symbol, assetclass):
    time.sleep(1)
    j = requests.get(f"https://api.nasdaq.com/api/quote/{symbol}/historical",
                     params={"assetclass": assetclass, "fromdate": START, "todate": sessions[-1].isoformat(), "limit": 9999},
                     headers=UA, timeout=60).json()
    if j["status"]["rCode"] != 200 or not j.get("data"):
        return None, f"not served ({j['status'].get('bCodeMessage')})"
    rows = j["data"]["tradesTable"]["rows"] or []
    if len(rows) != j["data"]["totalRecords"]:
        raise RuntimeError(f"Nasdaq {symbol}: {len(rows)} rows but totalRecords={j['data']['totalRecords']}")
    s = pd.Series([float(r["close"].replace("$", "").replace(",", "")) for r in rows],
                  index=[pd.to_datetime(r["date"], format="%m/%d/%Y").date() for r in rows], dtype="float64").sort_index()
    if s.index.duplicated().any():
        raise RuntimeError(f"Nasdaq {symbol}: duplicate dates")
    return s, f"{len(s)} rows, {s.index.min()} -> {s.index.max()}"


# Yahoo returns float32-ish noise (9.949999809); round to the instruments' quoting precision
y_sbet, y_spx = yahoo("SBET").round(4), yahoo("^GSPC").round(2)
(n_sbet, sbet_note), (n_spx, spx_note) = nasdaq("SBET", "stocks"), nasdaq("SPX", "index")

out = pd.DataFrame(index=sessions)
out["sbet"] = y_sbet.reindex(sessions)
out["spx"] = y_spx.reindex(sessions)
out["sbet_nasdaq"] = n_sbet.reindex(sessions) if n_sbet is not None else None
out["spx_nasdaq"] = n_spx.reindex(sessions) if n_spx is not None else None
out.reset_index().to_csv(OUT, index=False)

# ---------- Validation ----------
print(f"XNYS sessions {START}..{sessions[-1]}: {len(sessions)}; rows written to {OUT}: {len(out)}")
for name, s in (("Yahoo SBET", y_sbet), ("Yahoo ^GSPC", y_spx), ("Nasdaq SBET", n_sbet), ("Nasdaq SPX", n_spx)):
    if s is not None:
        print(f"{name}: {len(s)} bars; non-session dates: {sorted(set(s.index) - set(sessions)) or 'none'}")
print("Nulls per column:\n" + out.isna().sum().to_string())
print(f"Nasdaq SBET: {sbet_note}\nNasdaq SPX: {spx_note}")
if sessions[-1] == now.tz_convert(ET).date():
    print(f"NOTE: {sessions[-1]} is today; fetched {now.tz_convert(ET):%H:%M %Z}. Closes may still be revised.")

if n_sbet is not None:
    d = (out.sbet - out.sbet_nasdaq).abs()
    bad = out[(d > SBET_TOL + 1e-9) | (out.sbet.notna() != out.sbet_nasdaq.notna())]
    print(f"\nSBET Yahoo vs Nasdaq: {int((d <= 1e-9).sum())} exact matches; "
          f"differing by > ${SBET_TOL} or missing in one source: {len(bad)}")
    if len(bad): print(bad[["sbet", "sbet_nasdaq"]].to_string())
    small = out[(d > 1e-9) & (d <= SBET_TOL + 1e-9)]
    if len(small): print(f"Differing by <= ${SBET_TOL} (not flagged): {len(small)}\n" + small[["sbet", "sbet_nasdaq"]].to_string())
if n_spx is not None:
    d = ((out.spx / out.spx_nasdaq - 1).abs() * 100)
    bad = out[(d > SPX_TOL_PCT) | (out.spx.notna() != out.spx_nasdaq.notna())]
    print(f"\nS&P Yahoo vs Nasdaq differing by > {SPX_TOL_PCT}% or missing in one source: {len(bad)}")
    if len(bad): print(bad[["spx", "spx_nasdaq"]].to_string())

for col in ("sbet", "sbet_nasdaq"):
    if out[col].notna().any():
        same = out[out[col].notna() & (out[col] == out[col].shift(1))]
        print(f"\nSessions where {col} equals the prior session's close: {len(same)}")
        for dte in same.index:
            print(f"  {dte} = {out.index[out.index.get_loc(dte) - 1]}: {same.at[dte, col]}")

chk = pd.Timestamp("2026-04-09").date()
if chk in out.index:
    i = out.index.get_loc(chk)
    print(f"\n2026-04-09 check:\n" + out.iloc[i-1:i+2].to_string())
