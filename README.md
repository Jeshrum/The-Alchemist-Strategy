# The Alchemist Strategy — XAUUSD v5a

> Gold (XAUUSD) Multi-Timeframe SNR Strategy | Daily → H4 → M15 | London Session Only

---

## Strategy Logic

**Step 1 — Daily Bias**
- Close above Daily EMA20 → look for LONGS only
- Close below Daily EMA20 → look for SHORTS only

**Step 2 — H4 Confirmation (all must align)**
- EMA9 > EMA21 > EMA50 (long) or inverse (short)
- ADX ≥ 22 (trending market)
- DI+ > DI− (long) or DI− > DI+ (short)
- RSI ≥ 50 (long) or RSI ≤ 50 (short)
- Strong H4 candle rejected off EMA21 in last 10 bars
- Price within 2×ATR of EMA21 (not overextended)
- H4 close on right side of EMA9

**Step 3 — M15 Entry (London session only: 06:00–09:00 UTC)**
- Price above M15 EMA21 (long) or below (short)
- M15 EMA9 cross in bias direction → signal fires

**Step 4 — Trade Execution**
- Entry: market order at candle close
- SL: 1×ATR(H4)
- TP: 2×ATR(H4) → 1:2 R:R

---

## Setup

1. Open **XAUUSD** chart → set to **M15**
2. Pine Editor → paste `ALCHEMIST_SNR.pine` → Add to chart
3. For backtest → paste `ALCHEMIST_SNR_STRATEGY.pine` → check Strategy Report tab
4. Set chart timezone to **UTC**

---

## Session Times

| Location | Window |
|---|---|
| UTC | 06:00 AM – 09:00 AM |
| Nigeria / Ghana (WAT) | 07:00 AM – 10:00 AM |
| Johannesburg (SAST) | 08:00 AM – 11:00 AM |
| Nairobi (EAT) | 09:00 AM – 12:00 PM |

---

## Backtest Results

> Run `ALCHEMIST_SNR_STRATEGY.pine` on M15 XAUUSD in TradingView Strategy Tester.
> Results will be updated here once verified.

---

## Files

| File | Description |
|---|---|
| `ALCHEMIST_SNR.pine` | Indicator — signals, trade tool lines, dashboard |
| `ALCHEMIST_SNR_STRATEGY.pine` | Strategy — use this for backtest report |

---

*Built by Jesh · Trading involves significant risk · Past performance does not guarantee future results*
