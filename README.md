# The Alchemist Strategy — XAUUSD v5a

> Gold (XAUUSD) Multi-Timeframe SNR Strategy | Daily → H4 → M15 | London Session Only
> **All results verified by Python backtest on 401,431 real M1 bars (Mar 2009 – Mar 2026)**

---

## Verified Backtest Results

### Optimised Version — Ext1.5 + RSI65 ✅ RECOMMENDED

| Metric | Result |
|---|---|
| Period | Mar 2009 – Mar 2026 (17 years) |
| Total Trades | 419 |
| Avg Trades/Month | 2.2 |
| **Win Rate** | **63.5%** |
| **Profit Factor** | **3.42** |
| Net Profit | +$37,369 (+374%) |
| Max Drawdown | **4.3%** |
| Profitable Months | 139/187 (74%) |

> 1% risk per trade · SL = 1×ATR(H4) · TP = 2×ATR(H4) · London only (06:00–09:00 UTC)

**Key filters vs baseline:**
- `Ext ≤ 1.5×ATR` — price must be close to H4 EMA21, not overextended
- `RSI ≥ 65` (bull) / `RSI ≤ 35` (bear) — only trade strong momentum

---

### Year-by-Year (Optimised)

| Year | Trades | Win Rate | P&L | Return |
|---|---|---|---|---|
| 2009 | 20 | 55% | +$1,279 | +12.8% |
| 2010 | 22 | 77% | +$2,903 | +29.0% |
| 2011 | 25 | 68% | +$2,548 | +25.5% |
| 2012 | 23 | 65% | +$2,137 | +21.4% |
| 2013 | 19 | 63% | +$1,674 | +16.7% |
| 2014 | 33 | 58% | +$2,387 | +23.9% |
| 2015 | 26 | 77% | +$3,331 | +33.3% |
| 2016 | 29 | 59% | +$2,180 | +21.8% |
| 2017 | 29 | 69% | +$3,068 | +30.7% |
| 2018 | 16 | 44% | +$475 | +4.8% |
| 2019 | 21 | 52% | +$1,151 | +11.5% |
| 2020 | 31 | 61% | +$2,597 | +26.0% |
| 2021 | 28 | 71% | +$3,151 | +31.5% |
| 2022 | 24 | 50% | +$1,190 | +11.9% |
| 2023 | 19 | 68% | +$1,967 | +19.7% |
| 2024 | 22 | 73% | +$2,566 | +25.7% |
| 2025 | 26 | 62% | +$2,207 | +22.1% |
| 2026 (Jan–Mar) | 6 | 67% | +$558 | +5.6% |

> Every single year profitable. Worst year was 2018 at +4.8%.

---

### Baseline vs Optimised Comparison

| Variant | Trades | Win Rate | PF | Net Profit | Max DD |
|---|---|---|---|---|---|
| Baseline (v5a) | 1,025 | 45.5% | 1.64 | +$35,988 | 7.9% |
| + Ext≤1.5 only | 736 | 51.1% | 2.05 | +$38,242 | 5.1% |
| + RSI65 only | 671 | 53.9% | 2.30 | +$40,680 | 5.6% |
| **Ext1.5 + RSI65** ✅ | **419** | **63.5%** | **3.42** | **+$37,369** | **4.3%** |
| Ext1.2 + RSI60 | 392 | 63.0% | 3.36 | +$34,528 | 3.2% |

---

## Optimised Settings

| Setting | Baseline | Optimised |
|---|---|---|
| ADX Minimum | 22 | 22 |
| ATR Length | 14 | 14 |
| Daily EMA | 20 | 20 |
| H4 EMA Stack | 9>21>50 | 9>21>50 |
| RSI Gate | ≥50 / ≤50 | **≥65 / ≤35** |
| Extension Filter | ≤2.0×ATR | **≤1.5×ATR** |
| Session | London 06:00–09:00 UTC | London 06:00–09:00 UTC |
| R:R | 1:2 | 1:2 |

---

## Strategy Logic

**Step 1 — Daily Bias**
- Close > Daily EMA20 → LONGS only
- Close < Daily EMA20 → SHORTS only

**Step 2 — H4 Confirmation (all must align)**
- EMA9 > EMA21 > EMA50 (bull) or inverse (bear)
- ADX ≥ 22
- DI+ > DI− (bull) or DI− > DI+ (bear)
- RSI ≥ 65 (bull) or RSI ≤ 35 (bear) ← **optimised**
- Strong H4 candle rejected EMA21 in last 10 bars
- Price within **1.5×ATR** of H4 EMA21 ← **optimised**
- H4 close on right side of EMA9

**Step 3 — M15 Entry (London only: 06:00–09:00 UTC)**
- Price above M15 EMA21 (bull) or below (bear)
- M15 EMA9 cross in bias direction → signal fires

**Step 4 — Trade**
- Entry: market at candle close
- SL: 1×ATR(H4)
- TP: 2×ATR(H4)
- Max 1 trade per London session

---

## Setup

1. Open **XAUUSD** chart → **M15**
2. Pine Editor → paste `ALCHEMIST_SNR.pine` → Add to chart
3. Update settings: **RSI Minimum → 65**, **Extension Filter → 1.5**
4. For backtest → use `ALCHEMIST_SNR_STRATEGY.pine`

---

## Session Times

| Location | Window |
|---|---|
| UTC | 06:00 AM – 09:00 AM |
| Nigeria / Ghana (WAT) | 07:00 AM – 10:00 AM |
| Johannesburg (SAST) | 08:00 AM – 11:00 AM |
| Nairobi (EAT) | 09:00 AM – 12:00 PM |

---

## Files

| File | Description |
|---|---|
| `ALCHEMIST_SNR.pine` | Indicator — signals, trade tool lines, dashboard |
| `ALCHEMIST_SNR_STRATEGY.pine` | Strategy — use for TradingView backtest |
| `backtest/results/WINNER_Ext1.5+RSI65*.csv` | Full trade log (419 trades) |

---

*Built by Jesh · Backtested on 401,431 M1 bars · Mar 2009 – Mar 2026*
*Trading involves significant risk · Past performance does not guarantee future results*
