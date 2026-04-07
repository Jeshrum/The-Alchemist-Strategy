# Alchemist v5a — Signal Guide
> Quick reference for reading and acting on every signal

---

## Signal Types

### ▲ LONG SIGNAL

**What it looks like on chart:**
- Green triangle below the bar
- Signal card appears: "▲ ALCHEMIST LONG"
- Shows: Entry · SL · TP · ATR · R:R 1:2

**What triggered it:**
1. Daily close is above Daily EMA20 → bullish bias
2. H4: EMA9 > EMA21 > EMA50 stack confirmed
3. H4: ADX ≥ 22 + DI+ > DI− + RSI ≥ 50
4. H4: Strong candle rejected off EMA21 in last 10 bars
5. London session active (06:00–09:00 UTC)
6. M15 price above M15 EMA21
7. M15 EMA9 crossed upward

**What you do:**
1. Wait for the M15 candle to **close** — signal fires on close
2. Enter at market (current close price)
3. Set SL at the level shown on chart label
4. Set TP at the level shown on chart label
5. Walk away — do not watch tick by tick

---

### ▼ SHORT SIGNAL

**What it looks like on chart:**
- Red triangle above the bar
- Signal card appears: "▼ ALCHEMIST SHORT"
- Shows: Entry · SL · TP · ATR · R:R 1:2

**What triggered it:**
1. Daily close is below Daily EMA20 → bearish bias
2. H4: EMA9 < EMA21 < EMA50 stack confirmed
3. H4: ADX ≥ 22 + DI− > DI+ + RSI ≤ 50
4. H4: Strong candle rejected off EMA21 in last 10 bars
5. London session active (06:00–09:00 UTC)
6. M15 price below M15 EMA21
7. M15 EMA9 crossed downward

**What you do:**
1. Wait for the M15 candle to **close** — signal fires on close
2. Enter at market (current close price)
3. Set SL at the level shown on chart label
4. Set TP at the level shown on chart label
5. Walk away

---

## Reading the Dashboard Label

The top-right label updates every bar and shows the full checklist:

```
ALCHEMIST v5a
━━━━━━━━━━━━━━━━━
Bias    : BULLISH ▲
Daily   : ▲ above EMA20
H4 Gate : ✅ CONFIRMED
  Stack : ✅
  ADX   : 28.4 ✅
  RSI   : 56.2
  Rej   : ✅
Session : London ✅
```

| Field | Meaning |
|---|---|
| Bias | Current daily direction — BULLISH or BEARISH |
| Daily | Is price above or below EMA20? |
| H4 Gate | All H4 conditions confirmed → ✅ CONFIRMED |
| Stack | H4 EMA9/21/50 properly stacked |
| ADX | Current H4 ADX value (need ≥ 22) |
| RSI | Current H4 RSI (need ≥50 long / ≤50 short) |
| Rej | EMA21 rejection candle found in last 10 H4 bars |
| Session | Current session status |

**If H4 Gate shows ⏳ waiting — do not trade regardless of M15.**

---

## Reading the Signal Card

```
▲ ALCHEMIST LONG
━━━━━━━━━━━━━━━━━
Entry  : 3,245.50
SL     : 3,228.30
TP     : 3,279.90
ATR    : 17.20
R:R    : 1:2
Session: London
```

| Field | Meaning |
|---|---|
| Entry | Your market entry price (current M15 close) |
| SL | Stop loss — place exactly here, never move it |
| TP | Take profit — 2× the risk distance |
| ATR | Current H4 ATR — SL and TP sized from this |
| R:R | Always 1:2 |

---

## Signal Outcome Scenarios

### ✅ TP Hit
- Price moved in your direction and hit 2×ATR target
- Account up. Log the trade. Done.

### ❌ SL Hit
- Price reversed and hit stop loss
- Account down 1%. Log the trade. No revenge trading. Wait for tomorrow.

### ⏰ Force Closed (Friday)
- Trade was open into Friday 19:00 UTC
- Position closed at market price — small win or small loss
- No weekend exposure

---

## Chart Levels Reference

| Element | Colour | Meaning |
|---|---|---|
| M15 EMA9 | Orange | Short-term momentum — entry trigger |
| M15 EMA21 | Purple | Medium-term trend — price must be on right side |
| Daily EMA20 | Yellow (step) | Macro bias — above = bull, below = bear |
| H4 EMA21 | Purple (step) | H4 structure reference |
| Green background | Blue (faint) | London session active (06:00–09:00 UTC) |
| Grey background | Grey (faint) | Asia session (no trade zone) |
| PDH/PDL | Red/Green step | Previous Day High/Low |
| PWH/PWL | Orange/Blue step | Previous Week High/Low |
| Asian H/L | Grey step | Previous Asian session range |
| Green triangle ▲ | Below bar | LONG signal |
| Red triangle ▼ | Above bar | SHORT signal |
| Green box | Above entry | TP zone (2×ATR) |
| Red box | Below entry (short) / Above (short SL) | SL zone (1×ATR) |

---

## Session Window

| Location | Session Time |
|---|---|
| **UTC** | **06:00 AM – 09:00 AM** |
| **Nigeria / Ghana (WAT)** | **07:00 AM – 10:00 AM** |
| London (GMT) | 06:00 AM – 09:00 AM |
| Johannesburg (SAST) | 08:00 AM – 11:00 AM |
| Nairobi (EAT) | 09:00 AM – 12:00 PM |

> Signals only fire inside this window. Anything outside — ignore it completely.

---

## Rules — Never Break These

1. **Wait for candle close** — never enter mid-candle on a forming cross
2. **H4 gate must be fully confirmed** — if dashboard shows ⏳, skip the day
3. **One trade per London session** — if you've already traded today, sit out
4. **Never move your SL** — set it and leave it
5. **No trades outside 06:00–09:00 UTC** — the edge is in this window only
6. **Friday 19:00 UTC** — all positions must be closed before the weekend

---

*One signal per session. One entry. Walk away.*
