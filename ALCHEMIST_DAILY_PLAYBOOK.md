# Alchemist v5a — Daily Playbook
> Step-by-step routine. Same process every day.

---

## Before the Session — 05:45 UTC (06:45 WAT)

**15 minutes before London opens. Takes 5 minutes.**

### Step 1 — Check Daily Bias
Open XAUUSD Daily chart. Is price above or below the Daily EMA20 (yellow line)?

```
Price ABOVE Daily EMA20 → LONG bias today
Price BELOW Daily EMA20 → SHORT bias today
Price AT Daily EMA20    → No trade today (neutral)
```

### Step 2 — Check H4 Gate
Switch to H4 chart (or read the dashboard label on your M15 chart).

All 7 must be green for a valid setup:

| # | Check | Long | Short |
|---|---|---|---|
| 1 | EMA stack | EMA9 > EMA21 > EMA50 | EMA9 < EMA21 < EMA50 |
| 2 | ADX | ≥ 22 | ≥ 22 |
| 3 | DI direction | DI+ > DI− | DI− > DI+ |
| 4 | RSI | ≥ 50 | ≤ 50 |
| 5 | EMA21 rejection | Strong bull candle off EMA21 in last 10 bars | Strong bear candle off EMA21 in last 10 bars |
| 6 | Not overextended | Price within 2×ATR of H4 EMA21 | Price within 2×ATR of H4 EMA21 |
| 7 | H4 close side | H4 close above EMA9 | H4 close below EMA9 |

**If less than 7/7 → no trade today. Close the platform.**

### Step 3 — Switch to M15
Set chart to M15 XAUUSD. Confirm:
- Dashboard label shows ✅ CONFIRMED for H4 Gate
- Bias direction matches what you saw on the Daily
- Session shows "London ✅" once 06:00 UTC hits

---

## During the Session — 06:00–09:00 UTC (07:00–10:00 WAT)

**Be at your screen. Takes 30 seconds when a signal fires.**

### Watching for the Signal
- You are watching for an M15 EMA9 cross in the bias direction
- Price must be on the correct side of M15 EMA21 (above for longs, below for shorts)
- When the M15 bar **closes** with a valid cross → triangle appears + label shows entry levels

### When Signal Fires
```
1. Note the Entry, SL, TP from the label
2. Place market order at current price
3. Set Stop Loss at level shown — EXACTLY, no adjustments
4. Set Take Profit at level shown
5. Close the platform or walk away
```

**Do not:**
- Enter before the candle closes
- Move your SL after entry
- Add to the position
- Take a second trade if the first one hits SL

### If No Signal by 09:00 UTC
- Session over. No trade today. That's fine.
- The edge requires patience — not forcing trades

---

## After the Session

### Trade Taken
Log it:
```
Date | Direction | Entry | SL | TP | ATR | Result (pending/TP/SL) | P&L
```

### No Trade Taken
Note why — H4 gate not confirmed, no M15 cross, or missed the window.

---

## End of Week — Friday

- All open trades **must be closed by 19:00 UTC Friday**
- The Pine Script will show a warning — close manually if needed
- No new trades after 19:00 UTC Friday

---

## Weekly Review (Sunday)

Takes 10–15 minutes. Do this every week.

1. **Check Daily bias for Monday** — is XAUUSD above or below EMA20?
2. **Review last week's trades** — did you follow the rules?
3. **Note anything unusual** — big news week, high volatility, ranging market
4. **No changes to the strategy** — trust the 17-year backtest

---

## Key Levels to Note Each Day

Before the session, write down:
- **Daily EMA20 level** — where is bias line today?
- **Prev Day High (PDH)** — visible on chart as red step line
- **Prev Day Low (PDL)** — visible on chart as green step line
- **Asian session H/L** — grey step lines — potential liquidity targets
- **H4 EMA21 level** — purple step line — the zone price must have recently rejected

---

## Red Flags — Skip the Day

- Major news event within the session window (NFP, Fed, CPI)
- Gold spread is unusually wide at broker
- H4 ADX below 22 (ranging/choppy market)
- Price is sitting exactly at Daily EMA20 (no clear bias)
- You missed more than 30 minutes of the session

---

## Session Time Quick Reference

| Location | Trade Window |
|---|---|
| UTC | 06:00 AM – 09:00 AM |
| Lagos / Accra (WAT) | 07:00 AM – 10:00 AM |
| London (GMT) | 06:00 AM – 09:00 AM |
| London (BST, Apr–Oct) | 07:00 AM – 10:00 AM |
| Johannesburg (SAST) | 08:00 AM – 11:00 AM |
| Nairobi (EAT) | 09:00 AM – 12:00 PM |
| Dubai (GST) | 10:00 AM – 01:00 PM |

---

*Consistency beats perfection. Same process, every day, every trade.*
