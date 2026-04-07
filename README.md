# The Alchemist Strategy — XAUUSD v5a

> Gold (XAUUSD) Multi-Timeframe SNR Strategy | 17-Year Backtest | Daily → H4 → M15
> **Timeframe: M15 (15-minute) entry · London Session only (06:00–09:00 UTC)**
> **Session: 06:00 AM – 09:00 AM UTC · Lagos: 7:00–10:00 AM WAT**

---

## Backtest Results (2009–2026)

> All results on M15 entry timeframe. Do not trade outside London session.

| Metric | Result |
|---|---|
| Period | Mar 2009 – Mar 2026 |
| Timeframe | M15 entry · H4 confirmation · Daily bias |
| Initial Capital | $10,000 |
| **Final Balance** | **$37,579** |
| **Net Profit** | **+$27,579 (+276%)** |
| Total Trades | 813 |
| Trades/Month avg | 4.1 |
| Win Rate | **45.0%** |
| Profit Factor | **1.61** |
| R:R | 1:2 |
| Max Drawdown | −10.9% |
| Profitable Months | 130/200 **(65%)** |
| Profitable Years | **17/18** |

> 1% risk per trade · $1 commission · SL = 1×ATR(H4) · TP = 2×ATR(H4)

---

## How It Works

**Step 1 — Daily Bias**
Check if price is above or below the Daily EMA20.
- Above EMA20 → look for LONGS only
- Below EMA20 → look for SHORTS only

**Step 2 — H4 Confirmation (all must align)**
- EMA9 > EMA21 > EMA50 (long) or EMA9 < EMA21 < EMA50 (short)
- ADX ≥ 22 (trending market)
- DI+ > DI− (long) or DI− > DI+ (short)
- RSI ≥ 50 (long) or RSI ≤ 50 (short)
- Strong H4 candle rejected off EMA21 in the last 10 bars
- Price not overextended (within 2×ATR of EMA21)
- H4 close on right side of EMA9

**Step 3 — M15 Entry Trigger (London session only)**
- Price is above M15 EMA21 (long) or below M15 EMA21 (short)
- M15 EMA9 cross in bias direction → signal fires

**Step 4 — Place trade**
- Entry: market order on EMA9 cross close
- SL: 1×ATR(H4) below entry (long) or above entry (short)
- TP: 2×ATR(H4) — 1:2 R:R
- Walk away

**Step 5 — Force close**
All positions force-closed **Friday 19:00 UTC**. No weekend risk.

---

## Setup — TradingView

1. Open **XAUUSD** chart → set to **M15 (15-minute)** timeframe
2. Pine Editor → paste contents of `ALCHEMIST_SNR.pine` → Save → Add to chart
3. Confirm your chart timezone is **UTC**
4. Be at your screen: **06:00–09:00 AM UTC (Lagos: 7:00–10:00 AM WAT)**

> Free TradingView plan works. Use XAUUSD or GOLD ticker.

---

## Settings

| Setting | Value | Notes |
|---|---|---|
| ADX Minimum | 22 | Trending market gate |
| ATR Length | 14 | SL/TP calculation |
| Daily EMA Length | 20 | Bias filter |
| Session | London 06:00–09:00 UTC | Lagos: 7:00–10:00 AM WAT |
| Entry | Market order on M15 EMA9 cross | Wait for candle close |
| Stop Loss | 1×ATR(H4) | Auto-calculated on chart |
| Take Profit | 2×ATR(H4) = 1:2 R:R | Auto-calculated on chart |
| Risk | 1% per trade | $100 on $10k account |

---

## Execution — Every Trade, Every Time

```
Daily EMA20 direction confirmed →
H4 gate: all 7 conditions green →
London session open (06:00 UTC) →
M15 EMA9 crosses in bias direction →
Place trade at candle close price
SL → as shown on chart label
TP → as shown on chart label (2×ATR)
Done → close the platform, go live your life
```

**One trade per London session. If H4 gate is not fully confirmed — skip.**

---

## Session Times

| Location | All Year |
|---|---|
| **UTC** | **06:00 AM – 09:00 AM** |
| **Nigeria / Ghana (WAT)** | **07:00 AM – 10:00 AM** |
| London (GMT) | 06:00 AM – 09:00 AM |
| London (BST, summer) | 07:00 AM – 10:00 AM |
| Johannesburg (SAST) | 08:00 AM – 11:00 AM |
| Nairobi (EAT) | 09:00 AM – 12:00 PM |

> London is the cleanest session for Gold. NY adds noise — excluded by design.

---

## Year-by-Year Results (1% Risk, $10k Account)

| Year | Trades | Win Rate | P&L | % Return |
|---|---|---|---|---|
| 2009 | 38 | 37% | +$368 | +3.7% |
| 2010 | 50 | 44% | +$1,594 | +15.9% |
| 2011 | 51 | 51% | +$2,629 | +26.3% |
| 2012 | 46 | 41% | +$1,017 | +10.2% |
| 2013 | 33 | 55% | +$2,047 | +20.5% |
| 2014 | 58 | 45% | +$1,950 | +19.5% |
| 2015 | 53 | 53% | +$2,999 | +30.0% |
| 2016 | 56 | 39% | +$924 | +9.2% |
| 2017 | 52 | 40% | +$1,053 | +10.5% |
| **2018** | 55 | 29% | **−$779** | **−7.8%** |
| 2019 | 30 | 43% | +$854 | +8.5% |
| 2020 | 53 | 42% | +$1,254 | +12.5% |
| 2021 | 47 | 57% | +$3,321 | +33.2% |
| 2022 | 49 | 43% | +$1,336 | +13.4% |
| 2023 | 38 | 39% | +$646 | +6.5% |
| 2024 | 44 | 52% | +$2,453 | +24.5% |
| 2025 | 46 | 54% | +$2,887 | +28.9% |
| 2026 (Jan–Mar) | 14 | 57% | +$1,025 | +10.3% |

> Only 2018 was a losing year (−7.8%) — prolonged Gold downtrend with heavy chop. All 17 other years profitable.

---

## Timeframe Cascade — Why It Works

| Timeframe | Role | Key Indicator |
|---|---|---|
| Daily | Macro bias | EMA20 — is price bullish or bearish? |
| H4 | Trend confirmation | EMA stack + ADX + DI + RSI + EMA21 rejection |
| M15 | Entry precision | EMA9 cross while on right side of EMA21 |

Weekly bias was deliberately removed. Testing showed weekly alignment blocked 40–50% of valid setups without improving win rate.

---

## Python Backtest Engine

Bar-by-bar Python backtest on 401,431 M15 bars. No lookahead bias. Pre-computes all H4 signals then merges onto M15 index via forward-fill — runs in under 15 seconds.

```bash
cd backtest
pip install pandas numpy pytz pyarrow
# Place XAUUSD_H1.parquet and XAUUSD_M15.parquet in ~/Desktop/JESH XAUUSD/data/
python3 alchemist_v5a_london.py    # final version — London only
python3 alchemist_v5bcd.py         # compare variants (vol filter, 1:3 RR, M5 entry)
```

Results saved to `backtest/results/trade_log_v5a.csv`

---

## Backtest Variants Tested

| Variant | WR | PF | Net Profit | Max DD | Notes |
|---|---|---|---|---|---|
| **v5a — London only** ✅ | **45.0%** | **1.61** | **+$27,579** | **10.9%** | **Final version** |
| v5 — London + NY | 43.1% | 1.49 | +$32,376 | 11.3% | NY adds noise, lower quality |
| v5b — Vol filter | 36.6% | 1.14 | +$7,802 | 23.2% | Filter blocked good trades |
| v5c — 1:3 R:R | 29.1% | 1.21 | +$12,912 | 21.8% | Gold doesn't run 3×ATR consistently |
| v5d — M5 entry | 36.7% | 1.14 | +$11,007 | 19.8% | Finer entry catches noise |

---

## FAQ

**Do I need TradingView Pro?** No. Free plan works.

**What chart symbol?** XAUUSD or GOLD. Any broker feed works.

**What timezone should my chart be?** UTC. The indicator uses UTC internally regardless.

**What if I miss the signal?** Skip it. Never chase a move. Another setup comes tomorrow.

**What timeframe?** M15 only for entry. The indicator handles H4 and Daily internally.

**Is it prop firm safe?** Max drawdown never exceeded 10.9% in 17 years. Use 1% risk during evaluation.

**Why London only?** London session produced 46.5% WR vs NY's 38% WR. Quality over quantity.

**Why no weekly bias?** Tested with weekly — blocked 40–50% of valid setups with no improvement. Daily EMA20 alone is cleaner and more responsive.

---

## Files

| File | Description |
|---|---|
| `ALCHEMIST_SNR.pine` | TradingView Pine Script v5a — paste into Pine Editor |
| `ALCHEMIST_STRATEGY.md` | Full original strategy rules from YouTube course |
| `ALCHEMIST_SIGNAL_GUIDE.md` | Quick reference — reading signals and execution |
| `ALCHEMIST_DAILY_PLAYBOOK.md` | Step-by-step daily routine |
| `backtest/alchemist_v5a_london.py` | Final backtest script (London only) |
| `backtest/alchemist_v5bcd.py` | Multi-variant comparison runner |
| `backtest/results/trade_log_v5a.csv` | All 813 trades, 2009–2026 |

---

*The Alchemist Strategy v5a — Built by Jesh | 17 years of XAUUSD edge | 401,431 M15 bars backtested*

> Trading involves significant risk. Past performance does not guarantee future results.
