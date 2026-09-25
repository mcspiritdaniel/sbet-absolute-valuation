"""Task 4: download primary doc + EX-99 exhibits for SBET 8-K/8-K/A filings with items 7.01, 8.01 or 2.02."""
import os, re, time
from html.parser import HTMLParser
from pathlib import Path
import pandas as pd
import requests

os.chdir(Path(__file__).resolve().parent.parent)  # outputs go to <repo>/data/
CIK = 1981535
UA = {"User-Agent": "Dan McSpirit mcspiritdaniel@gmail.com", "Accept-Encoding": "gzip, deflate"}
ITEMS = {"7.01", "8.01", "2.02"}
OUT = Path("data/filings")
_last = [0.0]
# sec.gov's CDN appends a bot-management <script> tag to HTML responses; it is not part of the filing.
INJECTED = re.compile(rb'<script type="text/javascript"  src="/[A-Za-z0-9_/+=-]+"></script>')


def get(url):
    wait = 0.2 - (time.time() - _last[0])  # <= 5 req/s
    if wait > 0: time.sleep(wait)
    _last[0] = time.time()
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return r


class DocTable(HTMLParser):
    """Rows of the 'Document Format Files' table on <accession>-index.html: (document name, type)."""
    def __init__(self):
        super().__init__(); self.rows, self.row, self.cell, self.href, self.in_td = [], None, "", None, False
        self.table_no = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table": self.table_no += 1
        elif tag == "tr": self.row, self.href = [], None
        elif tag == "td": self.in_td, self.cell = True, ""
        elif tag == "a" and self.in_td and a.get("href"): self.href = a["href"]
    def handle_endtag(self, tag):
        if tag == "td" and self.row is not None:
            self.row.append(self.cell.strip()); self.in_td = False
        elif tag == "tr" and self.row and self.table_no == 1 and len(self.row) >= 4 and self.href:
            name = self.href.split("?doc=")[-1].rsplit("/", 1)[-1]
            self.rows.append((name, self.row[3]))
            self.row = None
    def handle_data(self, d):
        if self.in_td: self.cell += d


f = pd.read_csv("data/sbet_edgar_filings.csv", dtype=str)
k = f[f.form.isin(["8-K", "8-K/A"])]
sel = k[k["items"].fillna("").apply(lambda s: bool(ITEMS & {x.strip() for x in s.split(",")}))]
print(f"{len(k)} 8-K/8-K/A filings; {len(sel)} with items {sorted(ITEMS)}")
# Incremental: skip filings already in the manifest and append new ones.
prior = pd.read_csv(OUT / "manifest.csv", dtype=str) if (OUT / "manifest.csv").exists() else pd.DataFrame()
if len(prior):
    sel = sel[~sel.accession_number.isin(prior.accession)]
    print(f"{prior.accession.nunique()} already in manifest; {len(sel)} new to download")

manifest, no_ex99, problems = [], [], []
for _, r in sel.iterrows():
    acc, nodash = r.accession_number, r.accession_number.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{nodash}"
    listing = {i["name"]: i["size"] for i in get(f"{base}/index.json").json()["directory"]["item"]}
    idx_name = f"{acc}-index.html"
    if idx_name not in listing:
        problems.append((acc, "no -index.html in index.json")); continue
    p = DocTable(); p.feed(get(f"{base}/{idx_name}").text)
    types = dict(p.rows)
    primary = r.primary_document_url.rsplit("/", 1)[-1]
    if primary not in types:
        problems.append((acc, f"primary {primary} not in filing index table"))
    wanted = [(primary, types.get(primary, r.form))] + [(n, t) for n, t in p.rows if t.upper().startswith("EX-99")]
    if len(wanted) == 1:
        no_ex99.append((r.filing_date, acc, r.form, r["items"]))
    d = OUT / f"{r.filing_date}_{acc}"
    d.mkdir(parents=True, exist_ok=True)
    full_txt = None
    for name, typ in wanted:
        raw = get(f"{base}/{name}").content
        body = INJECTED.sub(b"", raw)
        if listing.get(name):
            ok = int(listing[name]) == len(body)
            check = "index.json size" if ok else f"MISMATCH vs index.json size {listing[name]}"
        else:
            # not in the directory listing (or no size given): compare with the full submission .txt
            if full_txt is None:
                full_txt = get(f"{base}/{acc}.txt").content.replace(b"\r\n", b"\n")
            ok = body.replace(b"\r\n", b"\n").strip() in full_txt
            check = "full submission .txt" if ok else "MISMATCH vs full submission .txt"
            problems.append((acc, f"{name} not listed in index.json; downloaded directly, checked vs full submission: {ok}"))
        if not ok:
            body = raw  # leave the response untouched rather than guess
            problems.append((acc, f"{name}: {check}"))
        (d / name).write_bytes(body)
        manifest.append({"filing_date": r.filing_date, "accession": acc, "form": r.form,
                         "file_name": name, "exhibit_type": typ, "size_bytes": len(body),
                         "verified_against": check})

new = pd.DataFrame(manifest)
m = pd.concat([prior, new.astype(str)], ignore_index=True) if len(new) else prior
m.to_csv(OUT / "manifest.csv", index=False)
m = m.astype({"size_bytes": int})
if len(new): print("New files:\n" + new.to_string(index=False))
print(f"\nManifest now lists {len(m)} files for {m.accession.nunique()} filings "
      f"({(m.exhibit_type.str.upper().str.startswith('EX-99')).sum()} EX-99 exhibits, {m.size_bytes.sum():,} bytes)")
print("Exhibit types:", m.exhibit_type.value_counts().to_dict())
print(f"\nFilings with no EX-99 exhibit: {len(no_ex99)}")
for row in no_ex99: print("  ", *row)
print(f"\nProblems: {len(problems)}")
for row in problems: print("  ", *row)
