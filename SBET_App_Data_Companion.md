# SBET App — Data Companion
Everything Claude Design needs, extracted from the workbook. Source of truth remains `SBET_Absolute_Valuation_Model.xlsx`.

## 1. Snapshot JSON (`App_Export!B9`)

```json
{"schema":"sbet-model-v1","asOf":"2026-08-20","sbetPriceBasis":"prior trading day official close","fundamentals":{"ethNative":634255.0,"ethLsETH":181748.0,"ethWeETH":72935.0,"ethTotal":888938.0,"cash":56195.0,"otherAssets":1911.0,"liabilities":5572.0,"sharesCommon":217031714.0,"prefundedWarrants":80000.0,"sharesBasicEquiv":217111714.0,"rsu":3500417.0,"options":3146.0,"warrants":16232635.0,"sharesDilutedCompany":236847912.0,"fullExerciseProceeds":127030.05066},"assumptions":{"aprNative":0.034,"aprLsETH":0.03,"aprWeETH":0.03,"incentivesY1":10344.0,"incentiveDecay":0.5,"galaxyCommit":100000.0,"galaxyReturn":0.08,"sgaAnnual":36240.0,"affiliate":436.0,"discountRate":0.12,"horizonYears":10.0,"atmOption":0.05,"ecoOption":0.02,"govDiscount":0.05,"riskFree":0.04,"vol":1.0,"ethSupply":120680000.0},"checks":{"navTotal":2067569.76902,"navPerShareBasic":9.5230687,"navPerShareEconomic":9.0837673,"sharesEconomic":220670252.78972,"ethConcentration":4.0943806,"mnavBasic":0.6741524,"mnavEconomic":0.7067552,"lineInSand":10.3317968,"netYieldAnnual":48741.9646364,"ethPrice":2266.79,"sbetPrice":6.42},"warrants":[{"n":1382007,"k":6.15,"t":3.75},{"n":691004,"k":6.77,"t":3.75},{"n":691004,"k":7.38,"t":3.75},{"n":691004,"k":8.0,"t":3.75},{"n":2764013,"k":7.68,"t":3.75},{"n":10013351,"k":8.15,"t":3.85},{"n":252,"k":7.77,"t":3.96}]}
```

## 2. Methodology text (verbatim)
METHODOLOGY - WHY THIS MODEL MEASURES WHAT IT MEASURES
Three choices in this model are non-obvious. Each is defended here, including where it is weak.
A. WHY ECONOMIC mNAV IS THE RIGHT MULTIPLE
All three definitions answer one question: how much am I paying per dollar of NAV? To answer it you must count the claims on that NAV correctly. Basic and fully diluted each get it wrong, in opposite directions.
BASIC mNAV ignores dilution entirely.
If a holder owns 10.0m warrants struck at $8.15 and the stock reaches $20, those shares will exist and will claim NAV. Basic pretends they do not, so it flatters the discount.
FULLY DILUTED mNAV (company method) makes two errors that compound.
1) It counts every warrant and option share regardless of moneyness. The 3,146 options struck at $122.88 will never be exercised; treating them as real shares is fiction.
2) It credits zero exercise proceeds. If the $8.15 warrants are exercised the company receives roughly $81.6m of cash that lands in NAV. You cannot add the shares without adding the money. The 10-K and 10-Q state explicitly that Assumed Diluted Shares Outstanding is not calculated using the treasury stock method.
Overstating the denominator and understating NAV both push the multiple up - so at a discount the company's own fully diluted figure makes the stock look LESS cheap than it is.
ECONOMIC mNAV fixes both, by treating moneyness as a state rather than a fact.
A warrant is a probabilistic claim, so it is handled twice. If it is in the money now, the treasury stock method applies: shares in, exercise proceeds used to retire shares at market, only the net counted. If it might be in the money later, its Black-Scholes value is deducted from NAV, because that option value is real and belongs to the holder rather than to you. Basic captures neither effect; fully diluted double-counts the first and ignores the second.
Live comparison at the current share price
Basic mNAV  **0.67415243962513**
Fully diluted mNAV (company method)  **0.735435204085387**
Economic mNAV (treasury stock method)  **0.706755222774116**
WHERE IT ACTUALLY BITES.
The divergence is WIDEST AT A DISCOUNT and narrows as the stock rises - which is the opposite of the intuition. At $5 the company method overstates the honest share count by roughly 7.4%; by $30 that falls to about 1.8%. The reason: as the price climbs, exercise proceeds shrink relative to the price, so the treasury stock offset gets smaller and the two methods converge on full dilution. Phantom shares are phantom only while they are out of the money.
So the choice of metric matters MOST right now - precisely when an investor is trying to size a discount. See Cap_Structure section E, which runs it across a range of share prices.
ITS OWN WEAKNESS - you should know this before relying on it.
The treasury stock method ASSUMES exercise proceeds are used to repurchase stock at the prevailing price. That is an accounting convention, not a prediction of what management will do. And the Black-Scholes deduction depends on the volatility input, which is an estimate (100% is used here). Best of the three, not perfect.
MARGINAL_ACTION USES THIS BASIS TOO, as of the 22-Aug-2026 fix pass.
The breakeven tests, both issuance/buyback simulations, the gaming table and the opex-leak section all test a hypothetical transaction against TODAY's balance sheet - the same point-in-time question this section argues Economic mNAV answers correctly. They were previously built on basic-equivalent shares (a 4.8% gap in NAV per share at the live price), understating what the tab itself calls the breakeven buyback price. The June-2026 case study and its counterfactual keep the ACTUAL historical share count and NAV/share as reported at the time, deliberately - a historical reconstruction uses the basis that existed on that date, which is a different question from which basis to use for a live test today.

### B. THE LINE IN THE SAND - ASSET VALUE PLUS NET YIELD
The line is not a price target. It is a decomposition, and it answers one question: what is SBET worth if management never touches the capital markets again? Two components, neither of which requires anything new to happen.
Part 1 - assets that already exist
Total ETH holdings plus cash, less liabilities, divided by basic-equivalent shares. Worth this much whether or not anyone does anything. This is NAV per share.
Asset value per share  **9.523068704713**
Part 2 - cash flows the existing base throws off
Staking, liquid staking and restaking accretion, plus protocol incentives and fund returns, less the SG&A required to run a public company. Discounted over a finite horizon. Hold the ETH, stake it, collect the incentives, pay the bills.
Net yield value per share  **1.24802943558057**
THE LINE  **10.3317967614173**
Everything above that line requires a claim about FUTURE CAPITAL ALLOCATION - specifically, that management will sell equity above NAV and manufacture ETH per share for existing holders. That is the machine. It is real: it took ETH Concentration from 2.00 to 4.03 during 2025. But it needs mNAV back above 1.0x AND a marginal buyer willing to pay the premium. Neither is contractual, neither is within management's control, and both disappeared during 2026.
So the line tells you what you are underwriting. Below it, you are buying assets plus yield at a discount. Above it, you are additionally paying for management's future ability to sell overpriced stock to somebody else.
CAVEATS. The discount rate and horizon are inputs, not facts - at a lower rate in perpetuity the yield component is far larger and the line moves up substantially. The line also excludes the ATM option, ecosystem optionality and the governance discount, which happen to roughly cancel at the current inputs. That near-cancellation is a coincidence of these settings, not a rule.

### C. HOW THE NORTH STAR CAN BE GAMED
ETH Concentration = ETH units divided by shares per thousand. Cash appears nowhere in that formula. So a cash-funded buyback leaves the numerator untouched and shrinks the denominator: the metric rises, arithmetically, always - regardless of the price paid.
The fair objection: cash is fungible with ETH, so spending it has an opportunity cost.
Correct. The right benchmark is not 'do nothing', it is 'buy ETH instead'. Measured against that benchmark the breakeven is ETH NAV per share, not zero. Buying back below ETH NAV per share beats buying ETH; above it, buying ETH wins. Marginal_Action section F runs both, plus every price in between.
ETH NAV per share (the true buyback breakeven)  **9.28110110641013**
But the metric still fails, because it rises at EVERY price.
A repurchase at three times NAV destroys value and the north star still goes up. The direction of the metric carries no information about whether the transaction was good. Only NAV per share does. That is why this model never displays one without the other.
The larger version of the problem is operating expense, not buybacks.
SG&A of roughly $36m a year, funded from cash, reduces NAV per share every year and moves ETH Concentration by exactly zero. The same is true of the ecosystem grants. The entire operating burn is invisible to the north star.
The tell: fund that same $36m by SELLING ETH and the metric falls. Identical economics, different pocket, opposite reported result. A metric whose direction depends on which account you pay from is, by definition, gameable.
In fairness to the company, it does publish basic-equivalent NAV per share on its dashboard, so the antidote is available. The objection is to reading ETH per share ALONE - which is precisely how it is marketed as the north star.

## 3. Chart series (regression reference — the app must RECOMPUTE these)

### PANEL 1 (MODE A) - THE THREE mNAV DEFINITIONS vs. SBET PRICE, ETH HELD AT SPOT
> FLOATING RANGE: the x-axis is expressed as a MULTIPLE of NAV per share, so it stays economically sensible as ETH moves and never implies an absurd price. Frozen: ETH price, NAV.
| x: mNAV level | SBET price | Basic mNAV | FD mNAV (company) | Economic mNAV | Economic shares | Spread: FD less econ | Note |
| 0.3 | 2.8569 | 0.3 | 0.3273 | 0.3048 | 220612131 | 0.0736 |  |
| 0.45 | 4.2854 | 0.45 | 0.4909 | 0.4573 | 220612131 | 0.0736 |  |
| 0.6 | 5.7138 | 0.6 | 0.6545 | 0.6097 | 220612131 | 0.0736 |  |
| 0.7 | 6.6661 | 0.7 | 0.7636 | 0.7116 | 220,719,137.3653 | 0.0731 |  |
| 0.8 | 7.6185 | 0.8 | 0.8727 | 0.8142 | 220,977,096.621 | 0.0718 |  |
| 0.9 | 8.5708 | 0.9 | 0.9818 | 0.9205 | 222,068,545.0958 | 0.0666 |  |
| 1 | 9.5231 | 1 | 1.0909 | 1.0296 | 223,546,167.1862 | 0.0595 |  |
| 1.1 | 10.4754 | 1.1 | 1.2 | 1.1387 | 224,755,130.7147 | 0.0538 |  |
| 1.25 | 11.9038 | 1.25 | 1.3636 | 1.3024 | 226,205,886.949 | 0.047 |  |
| 1.4 | 13.3323 | 1.4 | 1.5273 | 1.466 | 227,345,766.8473 | 0.0418 |  |
| 1.6 | 15.2369 | 1.6 | 1.7454 | 1.6842 | 228,533,141.7414 | 0.0364 |  |
| 1.85 | 17.6177 | 1.85 | 2.0182 | 1.9569 | 229,656,334.2088 | 0.0313 |  |
| 2.15 | 20.4746 | 2.15 | 2.3454 | 2.2842 | 230,659,371.2029 | 0.0268 |  |
| 2.5 | 23.8077 | 2.5 | 2.7273 | 2.666 | 231,525,326.4745 | 0.023 |  |
| 3.15 | 29.9977 | 3.15 | 3.4363 | 3.375 | 232,622,988.5988 | 0.0182 |  |
> The spread in column G is widest at a discount and narrows as the stock rises - exercise proceeds shrink relative to price, so the two methods converge on full dilution. 3.15x is the Citizens target.

### PANEL 2 - NAV PER SHARE AND IMPLIED PRICE vs. ETH PRICE
> Frozen: the mNAV regimes and discretionary financing. Warrant exercise IS included, with its proceeds.
| ETH price | Diluted NAV/share | At observed mNAV | At parity | At justified mNAV | The line in the sand |  | Note |
| 750 | 3.573 | 2.4756 | 3.573 | 3.8765 | 4.8211 |  |  |
| 1000 | 4.5113 | 3.1258 | 4.5113 | 4.8945 | 5.7594 |  |  |
| 1250 | 5.4496 | 3.7759 | 5.4496 | 5.9124 | 6.6977 |  |  |
| 1500 | 6.3879 | 4.426 | 6.3879 | 6.9304 | 7.636 |  |  |
| 1750 | 7.3262 | 5.0761 | 7.3262 | 7.9484 | 8.5743 |  |  |
| 2000 | 8.2645 | 5.7262 | 8.2645 | 8.9664 | 9.5126 |  |  |
| 2250 | 9.2028 | 6.3763 | 9.2028 | 9.9844 | 10.4509 |  |  |
| 2500 | 10.1411 | 7.0265 | 10.1411 | 11.0024 | 11.3892 |  |  |
| 3000 | 12.0177 | 8.3267 | 12.0177 | 13.0383 | 13.2658 |  |  |
| 3500 | 13.8943 | 9.6269 | 13.8943 | 15.0743 | 15.1424 |  |  |
| 4000 | 15.7709 | 10.9272 | 15.7709 | 17.1103 | 17.019 |  |  |
| 4500 | 17.6475 | 12.2274 | 17.6475 | 19.1462 | 18.8956 |  |  |
| 5000 | 19.5241 | 13.5276 | 19.5241 | 21.1822 | 20.7722 |  |  |
| 6000 | 23.2774 | 16.1281 | 23.2774 | 25.2541 | 24.5254 |  |  |
| 7000 | 27.0306 | 18.7286 | 27.0306 | 29.3261 | 28.2786 |  |  |
| 8000 | 30.7838 | 21.329 | 30.7838 | 33.398 | 32.0318 |  |  |
> Column F is assets plus the yield component in dollar terms - the floor below which the market is paying nothing at all for the strategy.

### PANEL 3 (MODE B) - ETH-LINKED: SBET IS DERIVED, NOT INDEPENDENT
> Frozen: NOTHING, when the beta toggle is on. SBET price = regime mNAV x NAV per share, so both prices move together. Uses the beta and floor set on Implied_Price.
> EXPECTED RESULT - not a bug: Basic mNAV returns a FLAT line equal to the regime (the NAV terms cancel), and FD mNAV is flat at a fixed 9.1% above it. Only the ECONOMIC line curves, because share count and the out-of-the-money deduction respond to the derived share price. That is the finding: the company's two definitions carry no information about the warrant stack.
| ETH price | Diluted NAV/share | mNAV regime applied | Derived SBET price | Basic mNAV | FD mNAV (company) | Economic mNAV | Spread |
| 1000 | 4.5113 | 0.6929 | 3.1258 | 0.6351 | 0.6929 | 0.6454 | 0.0736 |
| 1250 | 5.4496 | 0.6929 | 3.7759 | 0.6351 | 0.6929 | 0.6454 | 0.0736 |
| 1500 | 6.3879 | 0.6929 | 4.426 | 0.6351 | 0.6929 | 0.6454 | 0.0736 |
| 1750 | 7.3262 | 0.6929 | 5.0761 | 0.6351 | 0.6929 | 0.6454 | 0.0736 |
| 2000 | 8.2645 | 0.6929 | 5.7262 | 0.6351 | 0.6929 | 0.6454 | 0.0736 |
| 2250 | 9.2028 | 0.6929 | 6.3763 | 0.6351 | 0.6929 | 0.6455 | 0.0734 |
| 2500 | 10.1411 | 0.6929 | 7.0265 | 0.6351 | 0.6929 | 0.6459 | 0.0726 |
| 2750 | 11.0794 | 0.6929 | 7.6766 | 0.6351 | 0.6929 | 0.6465 | 0.0717 |
| 3000 | 12.0177 | 0.6929 | 8.3267 | 0.6351 | 0.6929 | 0.6484 | 0.0686 |
| 3500 | 13.8943 | 0.6929 | 9.6269 | 0.6351 | 0.6929 | 0.6544 | 0.0588 |
| 4000 | 15.7709 | 0.6929 | 10.9272 | 0.6351 | 0.6929 | 0.659 | 0.0515 |
| 4500 | 17.6475 | 0.6929 | 12.2274 | 0.6351 | 0.6929 | 0.6626 | 0.0457 |
| 5000 | 19.5241 | 0.6929 | 13.5276 | 0.6351 | 0.6929 | 0.6655 | 0.0412 |
| 6000 | 23.2774 | 0.6929 | 16.1281 | 0.6351 | 0.6929 | 0.6699 | 0.0343 |
| 7000 | 27.0306 | 0.6929 | 18.7286 | 0.6351 | 0.6929 | 0.6731 | 0.0294 |
| 8000 | 30.7838 | 0.6929 | 21.329 | 0.6351 | 0.6929 | 0.6755 | 0.0257 |
> Set Implied_Price toggle 2 to 1 to make the regime drift with ETH - then nothing is flat, and the chart traces a realistic path rather than a frozen multiple.
> APP HANDOFF NOTES
> - Chart mode should be a segmented control (A / B-flat / B-beta) with a caption that NAMES what is frozen. Never show a line without saying what is held still.
> - Panel 1's x-axis floats as a multiple of NAV per share - recompute the dollar prices whenever ETH or holdings change, so the range never implies an economically absurd price.
> - Recompute every series from the input state via a single computeState(inputs) function. If the app renders these static rows, the assumption sliders will silently stop working.
> - Black-Scholes needs a normal CDF; JavaScript has none. Use an Abramowitz-Stegun approximation. 8 tranches x ~16 points per panel is trivial to recompute on every redraw.
> - Do not auto-rescale the y-axis during slider drag - the line appears frozen and the control feels broken. Rescale on discrete changes only.
> - Mark 'today' on every panel, and label the regime lines as conditional ('if the discount persists'), never as forecasts.
> - Prices live (CoinGecko: ETH always; SBET real quote in market hours, SBETON as the labelled after-hours proxy). Fundamentals stay a dated snapshot pasted from App_Export. Show the SBETON-vs-SBET basis as a data-quality signal and distrust it beyond ~2%.
> - Guard every denominator and never let a failed fetch write a zero - a null NAV yields an infinite mNAV and the whole card grid goes to garbage.
