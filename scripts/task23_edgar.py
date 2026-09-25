"""Tasks 2 & 3: SBET EDGAR filing index + 3Q25 10-Q download."""
import os, re, time, datetime as dt
from pathlib import Path
import pandas as pd
import requests

UA = {"User-Agent": "Dan McSpirit mcspiritdaniel@gmail.com", "Accept-Encoding": "gzip, deflate"}
FORMS = {"8-K", "8-K/A", "10-Q", "10-K", "424B5", "S-3", "S-3ASR", "S-8", "DEF 14A"}
START, TODAY = "2025-06-01", dt.date.today().isoformat()
_last = [0.0]
os.chdir(Path(__file__).resolve().parent.parent)  # outputs go to <repo>/data/


def get(url):
    wait = 0.2 - (time.time() - _last[0])  # <= 5 req/s
    if wait > 0: time.sleep(wait)
    _last[0] = time.time()
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return r


tickers = get("https://www.sec.gov/files/company_tickers.json").json()
hits = [v for v in tickers.values() if v["ticker"].upper() == "SBET"]
assert len(hits) == 1, hits
cik = int(hits[0]["cik_str"])
print(f"SBET -> CIK {cik:010d} ({hits[0]['title']})")

sub = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()
print(f"EDGAR entity name: {sub['name']}; former names: {[f['name'] for f in sub.get('formerNames', [])]}")
frames = [pd.DataFrame(sub["filings"]["recent"])]
for f in sub["filings"].get("files", []):
    if f["filingTo"] >= START:
        frames.append(pd.DataFrame(get(f"https://data.sec.gov/submissions/{f['name']}").json()))
allf = pd.concat(frames, ignore_index=True).drop_duplicates("accessionNumber")
print(f"Oldest filing in fetched data: {allf['filingDate'].min()}")
win = allf[(allf.filingDate >= START) & (allf.filingDate <= TODAY)]
other = win[~win.form.isin(FORMS)].form.value_counts()
print("Other forms in window (excluded):", other.to_dict())

sel = win[win.form.isin(FORMS)].copy()
sel["primary_document_url"] = sel.apply(
    lambda r: f"https://www.sec.gov/Archives/edgar/data/{cik}/{r.accessionNumber.replace('-', '')}/{r.primaryDocument}", axis=1)
sel["items"] = sel.apply(lambda r: r["items"] if r.form.startswith("8-K") else "", axis=1)
out = sel.rename(columns={"filingDate": "filing_date", "reportDate": "report_date",
                          "accessionNumber": "accession_number", "primaryDocDescription": "description"})[
    ["form", "filing_date", "report_date", "accession_number", "primary_document_url", "items", "description"]
].sort_values(["filing_date", "accession_number"])
out.to_csv("data/sbet_edgar_filings.csv", index=False)
print(f"\nWrote {len(out)} filings; by form: {out.form.value_counts().to_dict()}")
print("Blank report_date:", (out.report_date.fillna('') == '').sum(),
      "| blank description:", (out.description.fillna('') == '').sum(),
      "| 8-Ks with blank items:", ((out.form.str.startswith('8-K')) & (out['items'].fillna('') == '')).sum())
print("Non-HTML primary docs:", out[~out.primary_document_url.str.lower().str.endswith(('.htm', '.html'))][['form', 'filing_date', 'primary_document_url']].to_string(index=False))

# ---------- Task 3 ----------
q = win[(win.reportDate == "2025-09-30") & win.form.str.startswith("10-Q")]
print("\n10-Q filings for period 2025-09-30:\n" + q[["form", "filingDate", "accessionNumber", "primaryDocument"]].to_string(index=False))
orig = q[q.form == "10-Q"]
assert len(orig) == 1, "Expected exactly one original 10-Q"
r = orig.iloc[0]
url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{r.accessionNumber.replace('-', '')}/{r.primaryDocument}"
# sec.gov's CDN appends a bot-management <script> tag to HTML responses; strip it and verify vs index.json size.
html = re.sub(rb'<script type="text/javascript"  src="/[A-Za-z0-9_/+=-]+"></script>', b"", get(url).content)
listing = {i["name"]: i["size"] for i in get(url.rsplit("/", 1)[0] + "/index.json").json()["directory"]["item"]}
assert listing.get(r.primaryDocument) and int(listing[r.primaryDocument]) == len(html), "10-Q size mismatch vs index.json"
open("data/SBET_FORM_10Q_3Q25.html", "wb").write(html)
txt = html.decode("utf-8", "ignore")
print(f"Saved {url} -> {len(html):,} bytes; mentions 'September 30, 2025': {'September 30, 2025' in txt}; "
      f"'QUARTERLY REPORT' present: {'QUARTERLY REPORT' in txt.upper()}")
