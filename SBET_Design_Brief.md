# Claude Design Brief — SBET Absolute Valuation App

## What this is

An interactive valuation model for Sharplink, Inc. (NASDAQ: SBET), a digital asset treasury company holding ~889,000 ETH. Built from a 16-tab, 1,049-formula Excel model audited to zero defects.

**The app's differentiator is that it shows its work.** Several outputs are actively misleading without their explanation, so explanation gets permanent screen real estate — not tooltips.

**Governing principle, stated in the model:** you cannot get something for nothing. Capital-markets activity redistributes value; only yield creates it.

---

## Layout

Two-pane, matching the companion ETH app (eth-valuation-analysis.vercel.app):

- **Sticky header** — one framing line plus the data-as-of line
- **Left 1/3** — explanatory notes, **re-rendering per view**
- **Right 2/3** — inputs and outputs

### Header

Framing line, e.g. *"SBET trades at 0.67× the value of the ETH it holds."* Recomputes.

Data-as-of line, three components inline, one status dot driven by the **worst** of the three:

> Data as of — fundamentals 20 Aug 2026 · SBET close 20 Aug · ETH live 14:32 UTC

### Notes panel behaviour

The strongest version of this format: when a user moves an assumption, the panel says what it affects **and what it doesn't**.

- Discount rate / horizon → line-in-the-sand only; **nothing** in the asset arithmetic
- Volatility / risk-free → economic mNAV only
- mNAV beta → chart curvature only
- ETH price, holdings, shares → everything

This teaches the golden rule directly: valuation assumptions don't touch what the company owns.

**One source of prose.** Notes panel = short context tied to the adjacent output. Drawer = the full argument, linked from the note. Never explain the same concept in both.

---

## Views

| View | Question | Excel source |
|---|---|---|
| **Overview** | What is it worth right now? | Control_Panel + NAV_Calculator |
| **Value creation** | Where does value come from, and where does it leak? | Yield_Engine + Marginal_Action |
| **Valuation** | What should it trade at, and what am I underwriting? | Justified_mNAV + Implied_Price + Scenarios |
| **Capital structure** | Who else has a claim? | Cap_Structure + the three-mNAV chart |

Methodology is a drawer reachable from anywhere, not a fifth view.

---

## Data contract

**Fundamentals — pasted snapshot.** One JSON string from `App_Export!B9`. Schema `sbet-model-v1`. Contains `asOf`, `sbetPriceBasis`, `fundamentals` (15), `assumptions` (17), `checks` (11), `warrants` (7 tranches with `n`, `k`, `t`).

Updated weekly. Show `asOf` prominently. Warn on schema mismatch.

**Prices — live from CoinGecko** (the companion ETH app already does this successfully):

- **ETH** — `/simple/price`. 24/7, reliable.
- **SBET** — real quote during market hours; **SBETON** (Ondo tokenized) as a clearly labelled after-hours proxy. SBETON turns over ~$102k/day against a $1.35bn market cap, so display the SBETON-vs-SBET **basis as a data-quality signal** and distrust it beyond ~2%.

**Seed-then-update:** ship with the snapshot hardcoded so the app renders instantly and works offline. Fetch after first paint, never block. On failure keep the snapshot and say why. Manual override always available, with reset-to-live.

**Market-hours asymmetry:** ETH trades 24/7, SBET does not. Computing live-ETH NAV against a stale close moves mNAV ~15% on an 18% ETH day. Flag mNAV as provisional outside RTH. NAV and ETH-per-share stay valid 24/7 — neither depends on the share price.

---

## Architecture — the critical requirement

**Recompute every value and series from input state via a single `computeState(inputs)` function. Do not render the `Chart_Data` rows as static data.** If the app renders static rows, the assumption sliders will appear to work while doing nothing.

`computeState` returns: NAV, three share counts, three mNAVs, yield strip, the line, all chart series.

**Black-Scholes needs a normal CDF; JavaScript has none.** Use an Abramowitz-Stegun approximation. 8 tranches × ~40 points is trivial per redraw.

**Regression test:** at default inputs the app must reproduce the JSON `checks` block exactly — `lineInSand` 10.3317968, `mnavEconomic` 0.7067552, `ethConcentration` 4.0943806. If it can't, the port is wrong.

---

## Controls

**Sliders control judgments. Cells control facts.**

- **Numeric cells** — ETH price, SBET price, share count, holdings, cash. Externally observable; a slider can't hit $2,266.79 and implies false uncertainty.
- **Sliders** — discount rate (6–20%), staking APR (2–5%), horizon (5–20y), ATM option (0–15%), governance discount (0–15%), deployment %, incentive decay, mNAV beta.
- **Toggles** — mNAV regime, buyback funding source (cash vs. ETH sale), instantaneous vs. one-year-forward, chart mode.
- ETH price wants **both**: a cell for the live value, a slider for scenarios. Different jobs.

---

## Charts

**Chart 1 — three mNAV definitions.** Segmented control, three modes, **with a caption naming what is frozen**:

- **Mode A** — x = SBET price, ETH frozen. Divergence widest at a discount (7.4% at $5), narrowing as price rises (1.8% at $30). Kinks at strikes $6.15, $6.77, $7.38, $7.68, $8.00, $8.15.
- **Mode B flat** — x = ETH price, SBET derived = regime × NAV/share. **Basic and FD render as flat lines. This is correct** — the NAV terms cancel. Only economic curves. That is the finding.
- **Mode B beta** — regime drifts with ETH; nothing is flat.

**Mode A's x-axis floats as a multiple of NAV/share** (0.30×–3.15×), recomputed when ETH or holdings change, so the range never implies an absurd price.

**Chart 2 — NAV/share and implied price vs. ETH price**, with the line in the sand as a floor series.

**Do not auto-rescale the y-axis during slider drag** — the line looks frozen and the control feels broken. Rescale on discrete changes only. Mark "today" on every chart. Label regime lines as conditional ("if the discount persists"), never as forecasts.

---

## Notes that prevent misreading — these must be visible, not hidden

1. **ETH per share rises on every buyback, at any price** — even at 3× NAV. Never display it without NAV/share adjacent.
2. **Operating expense is invisible to ETH per share.** ~$36m/yr of SG&A moves it exactly 0.00%.
3. **Fully diluted mNAV (company method) overstates the multiple at a discount** — counts ~19.7m out-of-the-money shares and credits zero exercise proceeds.
4. **On Marginal_Action, ETH value per share sits above NAV per share.** Different numerator, not a cash bridge: NAV/share deducts the Black-Scholes value of OTM warrants, the ETH line doesn't.

---

## Mobile

**Do not attempt the full model on a phone.** But do not hard-gate either — most traffic will arrive from a shared link on mobile.

Read-only summary card, roughly 1.5 screens, no interactivity, no charts:

- The framing line
- NAV/share, ETH per 1,000 shares, economic mNAV, the line in the sand
- Data-as-of line with status dot
- One paragraph on what the discount means
- Invitation to the full model on desktop

Gate at a **phone breakpoint**, not "not desktop" — the two-pane layout works to ~900px, so tablets should get the real thing.

---

## Guards

- **Never let a failed fetch write a zero.** Null NAV → infinite mNAV → the whole card grid is garbage.
- Validate response shape; sanity-band values (reject ETH outside $100–$50,000, SBET outside $0.10–$500).
- Guard every denominator.
- A visibly stale number beats a silently wrong one.

---

## Required disclosure

Visible, not buried: an analytical framework built from public SEC filings; **not investment advice**; **not affiliated with Sharplink**. Note that digital asset treasury companies carry concentration, custody, protocol, regulatory and dilution risk.

---

## Do not "fix" these

- Panel 3's flat lines — correct by construction, and the finding itself
- Economic (TSM) for point-in-time vs. full-dilution-with-proceeds for scenarios — different jobs, ~0.2% apart
- Two ETH Concentration figures exist: **4.094** (basic, the JSON value, the north star) and **4.028** (economic, Marginal_Action). Label both; never show one unlabelled
- Scenarios are deliberately unlabelled — no bear/base/bull
