# The Alchemist SNR Strategy — XAUUSD

A multi-timeframe Supply & Demand / SNR strategy for GOLD, built from the Alchemist mentorship course. Backtested over 17 years (2009–2026).

---

## Backtest Results (v3 — 2009–2026)

| Metric | Result |
|---|---|
| Total Trades | 134 (~8/year) |
| Win Rate | **73.9%** |
| Net Profit | **+$11,249 (+112%)** |
| Profit Factor | **4.20** |
| Max Drawdown | **1.8%** |
| Profitable Months | 82% (75/91) |
| Avg Monthly P&L | $124 |
| Best Month | $610 |
| Worst Month | -$205 |

> Every single year profitable. Worst year: +1.4% (2026, only 1 trade).

---

## Year-by-Year

| Year | Net P&L | Return % | Trades | WR |
|------|---------|----------|--------|----|
| 2009 | $457 | +4.6% | 3 | 100% |
| 2010 | $687 | +6.9% | 13 | 62% |
| 2011 | $1,211 | +12.1% | 8 | 100% |
| 2012 | $750 | +7.5% | 10 | 70% |
| 2013 | $304 | +3.0% | 2 | 100% |
| 2014 | $503 | +5.0% | 10 | 60% |
| 2015 | $942 | +9.4% | 8 | 88% |
| 2016 | $485 | +4.9% | 10 | 60% |
| 2017 | $301 | +3.0% | 2 | 100% |
| 2018 | $894 | +8.9% | 11 | 73% |
| 2019 | $529 | +5.3% | 7 | 71% |
| 2020 | $796 | +8.0% | 7 | 86% |
| 2021 | $637 | +6.4% | 6 | 83% |
| 2022 | $297 | +3.0% | 7 | 57% |
| 2023 | $676 | +6.8% | 8 | 75% |
| 2024 | $530 | +5.3% | 7 | 71% |
| 2025 | $1,107 | +11.1% | 14 | 71% |
| 2026 | $141 | +1.4% | 1 | 100% |

---

## Strategy Rules

**Timeframes:** Weekly → Daily → H4 → H1 → Entry

**Bias (Daily + Weekly):**
- Daily EMA20 — price above = bullish bias, below = bearish
- Weekly EMA10 — confirms higher timeframe direction

**H4 Entry Setup:**
- EMA9 > EMA21 > EMA50 stack (longs) or reverse (shorts)
- ADX > 20 (trend strength confirmed)
- DI+/DI- direction confirms bias
- Price pulls back to EMA21 zone

**H1 Trigger:**
- Candle close crosses EMA9 in the trend direction

**Sessions:**
- London Kill Zone: 06:00–09:00 UTC
- New York Kill Zone: 11:00–14:00 UTC
- No Asia session trades

**Risk Management:**
- Risk: 1% per trade
- SL: 1× ATR(H4)
- TP: 2× ATR(H4) → 1:2 R:R
- Max 1 trade per day
- Friday force-close at 19:00 UTC

---

## Files

- `ALCHEMIST_STRATEGY.md` — Full strategy rules extracted from 5-part YouTube course
- `ALCHEMIST_SNR.pine` — Pine Script v5 indicator (TradingView)
- `backtest/alchemist_backtest.py` — Python backtest engine (v3)
- `backtest/results/trade_log_v3.csv` — Full trade log

---

## Data

- Source: XAUUSD H1 parquet (101,228 bars, 2009-03-15 → 2026-03-20)
- Resampled internally to H4, Daily, Weekly
