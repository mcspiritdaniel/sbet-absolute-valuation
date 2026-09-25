"""Task 1: ETH/USD at NYSE close for every XNYS session 2025-06-02 .. latest completed session."""
import os, sys, time, statistics
from pathlib import Path
import pandas as pd
import pandas_market_calendars as mcal
import requests

OUT = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "data" / "eth_usd_at_nyse_close.csv"
START = "2025-06-02"
ET = "America/New_York"
CG_URL = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart/range"
CB_URL = "https://api.exchange.coinbase.com/products/ETH-USD/candles"
CG_HEADERS = {"x-cg-demo-api-key": os.environ["COINGECKO_API_KEY"], "accept": "application/json"}
FLAG_MIN = 30

now_utc = pd.Timestamp.now(tz="UTC")

# ---------- Session calendar ----------
cal = mcal.get_calendar("XNYS")
sched = cal.schedule(start_date=START, end_date=now_utc.tz_convert(ET).date().isoformat())
sched = sched[sched["market_close"] <= now_utc]  # completed sessions only
sessions = pd.DataFrame({
    "session_date": sched.index.date,
    "close_utc": sched["market_close"].dt.tz_convert("UTC").values,
})
sessions["close_utc"] = pd.to_datetime(sessions["close_utc"], utc=True)
sessions["close_et"] = sessions["close_utc"].dt.tz_convert(ET)
bad = sessions[~sessions["close_et"].dt.strftime("%H:%M").isin(["16:00", "13:00"])]
assert bad.empty, f"Unexpected close times:\n{bad}"


def cg_get(params, tries=5):
    for i in range(tries):
        r = requests.get(CG_URL, headers=CG_HEADERS, params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(20 * (i + 1)); continue
        if not r.ok:
            # never echo headers; body contains no key
            raise RuntimeError(f"CoinGecko HTTP {r.status_code}: {r.text[:300]}")
        return r.json()["prices"]
    raise RuntimeError("CoinGecko: repeated 429s")


# ---------- CoinGecko hourly (<=90-day chunks, within 365-day Demo window) ----------
cg_floor = now_utc - pd.Timedelta(days=365) + pd.Timedelta(hours=1)
cg_pts = {}
chunk_start = max(cg_floor, sessions["close_utc"].min() - pd.Timedelta(hours=3))
while chunk_start < now_utc:
    chunk_end = min(chunk_start + pd.Timedelta(days=85), now_utc)
    for ms, px in cg_get({"vs_currency": "usd", "from": int(chunk_start.timestamp()), "to": int(chunk_end.timestamp())}):
        cg_pts[int(ms)] = px
    chunk_start = chunk_end
    time.sleep(2.5)
cg = pd.Series(cg_pts).sort_index()
cg.index = pd.to_datetime(cg.index, unit="ms", utc=True)
gaps = cg.index.to_series().diff().dt.total_seconds().div(60).dropna()
print(f"CoinGecko hourly: {len(cg)} points, {cg.index.min()} -> {cg.index.max()}, "
      f"median spacing {gaps.median():.1f} min, max spacing {gaps.max():.1f} min")
if gaps.median() > 70:
    raise RuntimeError("CoinGecko did not return hourly granularity")

# ---------- CoinGecko daily 00:00 UTC (>90-day chunks -> daily granularity) ----------
daily = {}
chunk_start = cg_floor
while chunk_start < now_utc:
    chunk_end = min(chunk_start + pd.Timedelta(days=120), now_utc)
    if chunk_end - chunk_start <= pd.Timedelta(days=90):
        chunk_start = chunk_end - pd.Timedelta(days=91)  # force daily granularity for the tail
    for ms, px in cg_get({"vs_currency": "usd", "from": int(chunk_start.timestamp()), "to": int(chunk_end.timestamp())}):
        ts = pd.Timestamp(int(ms), unit="ms", tz="UTC")
        if ts == ts.normalize():  # exact 00:00:00 UTC points only
            daily[ts.date()] = px
    chunk_start = chunk_end
    time.sleep(2.5)
print(f"CoinGecko 00:00 UTC daily: {len(daily)} points, {min(daily)} -> {max(daily)}")

# ---------- Coinbase hourly candles over the full session range ----------
cb = {}
cb_start = sessions["close_utc"].min().floor("h") - pd.Timedelta(hours=1)
cb_last = sessions["close_utc"].max().floor("h") + pd.Timedelta(hours=1)
while cb_start < cb_last:
    cb_end = min(cb_start + pd.Timedelta(hours=299), cb_last)
    for attempt in range(5):
        r = requests.get(CB_URL, params={"granularity": 3600, "start": cb_start.isoformat(), "end": cb_end.isoformat()},
                         headers={"User-Agent": "sbet-analysis"}, timeout=60)
        if r.status_code == 429:
            time.sleep(2 * (attempt + 1)); continue
        r.raise_for_status(); break
    for t, low, high, opn, close, vol in r.json():
        cb[pd.Timestamp(int(t), unit="s", tz="UTC")] = float(opn)
    cb_start = cb_end
    time.sleep(0.35)
cb = pd.Series(cb).sort_index()
print(f"Coinbase hourly: {len(cb)} candles, {cb.index.min()} -> {cb.index.max()}")

# ---------- Assemble ----------
rows, diffs = [], []
for _, s in sessions.iterrows():
    close = s["close_utc"]
    cb_px = cb.get(close)  # OPEN of candle starting exactly at close
    cg_px = cg_ts = None
    if close >= cg_floor and len(cg):
        pos = cg.index.get_indexer([close], method="nearest")[0]
        cg_ts, cg_px = cg.index[pos], float(cg.iloc[pos])
    flags = []
    if cg_px is not None:
        mins = (cg_ts - close).total_seconds() / 60
        price, src, src_ts = cg_px, "coingecko", cg_ts
        if abs(mins) > FLAG_MIN:
            flags.append(f"nearest_point_{abs(mins):.0f}min_from_close")
        if cb_px is not None:
            diffs.append((s["session_date"], abs(cg_px / cb_px - 1) * 100))
    elif cb_px is not None:
        price, src, src_ts, mins = cb_px, "coinbase", close, 0.0
    else:
        price, src, src_ts, mins = None, None, None, None
        flags.append("no_source_data")
    rows.append({
        "session_date": s["session_date"].isoformat(),
        "close_time_et": s["close_et"].strftime("%Y-%m-%d %H:%M %Z"),
        "eth_usd_at_close": price,
        "source": src,
        "source_timestamp_utc": src_ts.strftime("%Y-%m-%dT%H:%M:%SZ") if src_ts is not None else None,
        "minutes_from_close": round(mins, 2) if mins is not None else None,
        "eth_usd_0000utc": daily.get(s["session_date"]),
        "flag": ";".join(flags) or None,
        "coinbase_eth_usd_at_close": cb_px,
    })
out = pd.DataFrame(rows)
out.to_csv(OUT, index=False)

# ---------- Validation ----------
print("\n=== VALIDATION ===")
print(f"XNYS completed sessions {START}..{sessions['session_date'].max()}: {len(sessions)}; CSV rows: {len(out)}")
print("Nulls per column:\n" + out.isna().sum().to_string())
fl = out[out["flag"].notna()]
print(f"Flagged rows: {len(fl)}")
if len(fl): print(fl[["session_date", "source", "minutes_from_close", "flag"]].to_string(index=False))
for src, g in out.groupby("source"):
    print(f"Source {src}: {len(g)} sessions, {g['session_date'].min()} -> {g['session_date'].max()}")
no_cb = out[out["coinbase_eth_usd_at_close"].isna()]["session_date"].tolist()
print(f"Sessions with no Coinbase candle starting at the close: {len(no_cb)} {no_cb}")
early = out[out["close_time_et"].str.contains(" 13:00 ")]
print("Early-close sessions:", ", ".join(early["session_date"]))
print("minutes_from_close (coingecko) min/median/max:",
      out.loc[out.source == "coingecko", "minutes_from_close"].agg(["min", "median", "max"]).round(2).tolist())
if diffs:
    vals = [d for _, d in diffs]
    worst = max(diffs, key=lambda x: x[1])
    print(f"CoinGecko vs Coinbase overlap: {len(diffs)} sessions, {diffs[0][0]} -> {diffs[-1][0]}; "
          f"abs % diff median {statistics.median(vals):.4f}%, max {worst[1]:.4f}% on {worst[0]}")
