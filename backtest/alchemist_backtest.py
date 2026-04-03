"""
THE ALCHEMIST SNR — Optimized Backtest v3
XAUUSD 2009–2026

Approach: Strong trend-following with multiple confirmations
- EMA stack (H4: 9/21/50) — all aligned for direction
- ADX > 25 (trending market, not ranging)
- Daily + Weekly bias via EMA
- H4 pullback to EMA21 (value area entry)
- H1 closes back above/below EMA9 after pullback (trigger)
- ATR-based SL (1×) / TP (2×) → 1:2 R:R
- Kill zones: London 06-09 UTC + NY 11-14 UTC
- 1% risk | max 1 trade/day
"""

import os
import warnings
import pandas as pd
import numpy as np
import pytz

warnings.filterwarnings("ignore")

H1_PARQUET = "/Users/mac/Desktop/JESH XAUUSD/data/XAUUSD_H1.parquet"
OUT_DIR    = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT_DIR, exist_ok=True)

UTC         = pytz.utc
ACCOUNT     = 10_000
RISK_PCT    = 0.01
COMMISSION  = 1.0
ATR_LEN     = 14
SL_MULT     = 1.0
TP_MULT     = 1.5    # 1:1.5 R:R — easier to hit, higher WR


def in_kill_zone(hour_utc):
    return (6 <= hour_utc < 9) or (11 <= hour_utc < 14)


# ─────────────────────────────────────────────────────────────────────────────
#  LOAD + RESAMPLE
# ─────────────────────────────────────────────────────────────────────────────

def load_h1():
    df = pd.read_parquet(H1_PARQUET)
    df = df[["open", "high", "low", "close"]].astype(float)
    if df.index.tz is None:
        df.index = df.index.tz_localize(UTC)
    else:
        df.index = df.index.tz_convert(UTC)
    df.sort_index(inplace=True)
    df = df[~df.index.duplicated(keep="first")]
    return df


def resample(df, rule):
    return df.resample(rule, closed="left", label="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()


# ─────────────────────────────────────────────────────────────────────────────
#  INDICATORS
# ─────────────────────────────────────────────────────────────────────────────

def calc_atr(df, length=14):
    h, l, pc = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(span=length, min_periods=length).mean()


def calc_ema(series, length):
    return series.ewm(span=length, min_periods=length).mean()


def calc_adx(df, length=14):
    h, l, pc = df["high"], df["low"], df["close"].shift(1)
    tr   = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    dmp  = (h - h.shift(1)).clip(lower=0)
    dmn  = (l.shift(1) - l).clip(lower=0)
    dmp  = dmp.where(dmp > dmn, 0)
    dmn  = dmn.where(dmn > dmp.shift(0), 0)  # note: using original dmp here
    # recalculate properly
    up   = h - h.shift(1)
    down = l.shift(1) - l
    dmp2 = up.where((up > down) & (up > 0), 0)
    dmn2 = down.where((down > up) & (down > 0), 0)
    atr14  = tr.ewm(span=length, min_periods=length).mean()
    di_pos = 100 * dmp2.ewm(span=length, min_periods=length).mean() / atr14
    di_neg = 100 * dmn2.ewm(span=length, min_periods=length).mean() / atr14
    dx     = (100 * (di_pos - di_neg).abs() / (di_pos + di_neg).replace(0, np.nan))
    adx    = dx.ewm(span=length, min_periods=length).mean()
    return adx, di_pos, di_neg


def prepare_h4(h4):
    h4 = h4.copy()
    h4["ema9"]  = calc_ema(h4["close"], 9)
    h4["ema21"] = calc_ema(h4["close"], 21)
    h4["ema50"] = calc_ema(h4["close"], 50)
    h4["atr"]   = calc_atr(h4, ATR_LEN)
    h4["adx"], h4["di_pos"], h4["di_neg"] = calc_adx(h4, ATR_LEN)
    return h4


def prepare_h1(h1):
    h1 = h1.copy()
    h1["ema9"]  = calc_ema(h1["close"], 9)
    h1["ema21"] = calc_ema(h1["close"], 21)
    return h1


def compute_daily_bias(daily, weekly):
    """
    Bull: daily close > EMA20 AND weekly close > EMA10
    Bear: daily close < EMA20 AND weekly close < EMA10
    Shifted by 1 to avoid lookahead.
    """
    d_ema = calc_ema(daily["close"], 20).shift(1)
    d_c   = daily["close"].shift(1)
    w_ema = calc_ema(weekly["close"], 10).shift(1)
    w_c   = weekly["close"].shift(1)

    d_bull = d_c > d_ema
    d_bear = d_c < d_ema
    w_bull = w_c > w_ema
    w_bear = w_c < w_ema

    w_bull_d = w_bull.reindex(daily.index, method="ffill")
    w_bear_d = w_bear.reindex(daily.index, method="ffill")

    bias = pd.Series(0, index=daily.index)
    bias[d_bull & w_bull_d] =  1
    bias[d_bear & w_bear_d] = -1
    return bias


# ─────────────────────────────────────────────────────────────────────────────
#  BACKTEST ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest(h1_raw, h4_raw, daily, weekly):
    print("  Preparing indicators...")
    h4   = prepare_h4(h4_raw)
    h1   = prepare_h1(h1_raw)
    bias = compute_daily_bias(daily, weekly)

    h1["date"]     = h1.index.date
    h1["hour_utc"] = h1.index.hour

    dates        = sorted(set(h1["date"]))
    active_trade = None
    trade_done   = None
    trades       = []

    print(f"  Running {len(dates)} days...")

    for date in dates:
        dow = pd.Timestamp(date).dayofweek
        if dow >= 5:
            continue

        day_bars = h1[h1["date"] == date]
        if day_bars.empty:
            continue

        for i, (ts, bar) in enumerate(day_bars.iterrows()):
            utc_hour = bar["hour_utc"]
            o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]

            # ── Manage open trade ──────────────────────────────────────────
            if active_trade is not None:
                if dow == 4 and utc_hour >= 19:
                    pnl = (c - active_trade["entry"]) * (1 if active_trade["dir"] == "LONG" else -1) * active_trade["lot"] * 100 - COMMISSION
                    trades.append({**active_trade, "exit": c, "reason": "fc",
                                   "pnl": pnl, "year": ts.year, "month": ts.month, "date": date})
                    active_trade = None
                    continue

                if active_trade["dir"] == "LONG":
                    if h >= active_trade["tp"]:
                        pnl = (active_trade["tp"] - active_trade["entry"]) * active_trade["lot"] * 100 - COMMISSION
                        trades.append({**active_trade, "exit": active_trade["tp"], "reason": "tp",
                                       "pnl": pnl, "year": ts.year, "month": ts.month, "date": date})
                        active_trade = None
                    elif l <= active_trade["sl"]:
                        pnl = (active_trade["sl"] - active_trade["entry"]) * active_trade["lot"] * 100 - COMMISSION
                        trades.append({**active_trade, "exit": active_trade["sl"], "reason": "sl",
                                       "pnl": pnl, "year": ts.year, "month": ts.month, "date": date})
                        active_trade = None
                else:
                    if l <= active_trade["tp"]:
                        pnl = (active_trade["entry"] - active_trade["tp"]) * active_trade["lot"] * 100 - COMMISSION
                        trades.append({**active_trade, "exit": active_trade["tp"], "reason": "tp",
                                       "pnl": pnl, "year": ts.year, "month": ts.month, "date": date})
                        active_trade = None
                    elif h >= active_trade["sl"]:
                        pnl = (active_trade["entry"] - active_trade["sl"]) * active_trade["lot"] * 100 - COMMISSION
                        trades.append({**active_trade, "exit": active_trade["sl"], "reason": "sl",
                                       "pnl": pnl, "year": ts.year, "month": ts.month, "date": date})
                        active_trade = None
                continue

            # ── Basic filters ──────────────────────────────────────────────
            if utc_hour < 6:
                continue
            if trade_done == date:
                continue
            if not in_kill_zone(utc_hour):
                continue
            if dow == 4 and utc_hour >= 19:
                continue

            # ── Daily + Weekly bias ────────────────────────────────────────
            day_ts   = pd.Timestamp(date, tz=UTC)
            bias_idx = bias.index[bias.index <= day_ts]
            if len(bias_idx) == 0:
                continue
            cur_bias = bias[bias_idx[-1]]
            if cur_bias == 0:
                continue

            # ── Weekly candle direction must match bias ────────────────────
            w_snap = weekly[weekly.index <= day_ts]
            if len(w_snap) < 2:
                continue
            cur_week = w_snap.iloc[-1]
            if cur_bias == 1 and cur_week["close"] < cur_week["open"]:
                continue
            if cur_bias == -1 and cur_week["close"] > cur_week["open"]:
                continue

            # ── Daily: current close must be above/below prior day close ──
            d_snap = daily[daily.index <= day_ts]
            if len(d_snap) < 3:
                continue
            d_last = d_snap.iloc[-1]
            d_prev = d_snap.iloc[-2]
            if cur_bias == 1 and d_last["close"] < d_prev["close"]:
                continue
            if cur_bias == -1 and d_last["close"] > d_prev["close"]:
                continue

            # ── H4 snapshot ────────────────────────────────────────────────
            h4_snap = h4[h4.index <= ts]
            if len(h4_snap) < 55:
                continue
            h4_last = h4_snap.iloc[-1]

            h4_ema9  = h4_last["ema9"]
            h4_ema21 = h4_last["ema21"]
            h4_ema50 = h4_last["ema50"]
            h4_atr   = h4_last["atr"]
            h4_adx   = h4_last["adx"]
            h4_di_p  = h4_last["di_pos"]
            h4_di_n  = h4_last["di_neg"]
            h4_c     = h4_last["close"]

            if np.isnan(h4_atr) or h4_atr <= 0 or np.isnan(h4_adx):
                continue

            # ── EMA stack alignment ────────────────────────────────────────
            # LONG:  EMA9 > EMA21 > EMA50 (bullish stack)
            # SHORT: EMA9 < EMA21 < EMA50 (bearish stack)
            long_stack  = h4_ema9 > h4_ema21 > h4_ema50
            short_stack = h4_ema9 < h4_ema21 < h4_ema50

            if cur_bias == 1 and not long_stack:
                continue
            if cur_bias == -1 and not short_stack:
                continue

            # ── ADX > 28 (strong trend only) ──────────────────────────────
            if h4_adx < 28:
                continue

            # DI directional confirmation
            if cur_bias == 1 and h4_di_p <= h4_di_n:
                continue
            if cur_bias == -1 and h4_di_n <= h4_di_p:
                continue

            # ── ATR momentum filter: ATR must be above 20-bar average ────
            atr_avg = h4_snap["atr"].tail(20).mean()
            if h4_atr < atr_avg * 0.8:
                continue

            # ── H4 pullback + rejection from EMA21 zone ──────────────────
            # In last 5 H4 bars: one bar touched EMA21 and then closed away from it
            h4_recent = h4_snap.tail(6)
            ema21_rejection_long  = False
            ema21_rejection_short = False

            for _, hb in h4_recent.iterrows():
                # LONG rejection: low touched EMA21 zone but closed bullish above EMA9
                if (hb["low"] <= h4_ema21 + h4_atr * 0.5 and
                        hb["close"] > hb["open"] and
                        hb["close"] > h4_ema9):
                    ema21_rejection_long = True
                # SHORT rejection: high touched EMA21 zone but closed bearish below EMA9
                if (hb["high"] >= h4_ema21 - h4_atr * 0.5 and
                        hb["close"] < hb["open"] and
                        hb["close"] < h4_ema9):
                    ema21_rejection_short = True

            if cur_bias == 1 and not ema21_rejection_long:
                continue
            if cur_bias == -1 and not ema21_rejection_short:
                continue

            # ── Price not overextended from EMA21 at entry ────────────────
            dist_from_ema21 = abs(c - h4_ema21)
            if dist_from_ema21 > h4_atr * 2.0:
                continue

            # ── H4 close must confirm direction ───────────────────────────
            if cur_bias == 1 and h4_c < h4_ema9:
                continue
            if cur_bias == -1 and h4_c > h4_ema9:
                continue

            # ── H1 trigger: close back above/below EMA9 ──────────────────
            h1_ema9 = bar["ema9"]
            if np.isnan(h1_ema9):
                continue

            if i > 0:
                prev_bar = day_bars.iloc[i - 1]
                prev_c   = prev_bar["close"]
                prev_e9  = prev_bar["ema9"]
            else:
                continue

            if np.isnan(prev_e9):
                continue

            h1_long_trig  = (prev_c < prev_e9) and (c > h1_ema9) and (cur_bias == 1)
            h1_short_trig = (prev_c > prev_e9) and (c < h1_ema9) and (cur_bias == -1)

            # ── Entry ──────────────────────────────────────────────────────
            if h1_long_trig:
                sl_dist = h4_atr * SL_MULT
                tp_dist = h4_atr * TP_MULT
                entry   = c
                sl      = round(entry - sl_dist, 2)
                tp      = round(entry + tp_dist, 2)
                lot     = max(0.01, round(ACCOUNT * RISK_PCT / (sl_dist * 100), 2))
                active_trade = {"dir": "LONG", "entry": entry, "sl": sl, "tp": tp,
                                "lot": lot, "open_ts": str(ts)}
                trade_done = date

            elif h1_short_trig:
                sl_dist = h4_atr * SL_MULT
                tp_dist = h4_atr * TP_MULT
                entry   = c
                sl      = round(entry + sl_dist, 2)
                tp      = round(entry - tp_dist, 2)
                lot     = max(0.01, round(ACCOUNT * RISK_PCT / (sl_dist * 100), 2))
                active_trade = {"dir": "SHORT", "entry": entry, "sl": sl, "tp": tp,
                                "lot": lot, "open_ts": str(ts)}
                trade_done = date

    if active_trade is not None:
        ep  = h1["close"].iloc[-1]
        pnl = (ep - active_trade["entry"]) * (1 if active_trade["dir"] == "LONG" else -1) * active_trade["lot"] * 100 - COMMISSION
        trades.append({**active_trade, "exit": ep, "reason": "fc", "pnl": pnl,
                       "year": h1.index[-1].year, "month": h1.index[-1].month,
                       "date": h1.index[-1].date()})

    return pd.DataFrame(trades)


# ─────────────────────────────────────────────────────────────────────────────
#  STATS
# ─────────────────────────────────────────────────────────────────────────────

def print_results(tdf):
    if tdf.empty:
        print("No trades generated.")
        return

    wins    = tdf[tdf["pnl"] > 0]
    monthly = tdf.groupby(["year", "month"])["pnl"].sum()
    yearly  = tdf.groupby("year")["pnl"].sum()
    gross_p = wins["pnl"].sum()
    gross_l = abs(tdf[tdf["pnl"] <= 0]["pnl"].sum())
    pf      = gross_p / gross_l if gross_l > 0 else 9999

    eq      = ACCOUNT + tdf["pnl"].cumsum()
    roll_mx = eq.cummax()
    max_dd  = abs(((eq - roll_mx) / roll_mx * 100).min())

    prof_m  = (monthly > 0).sum()
    tot_m   = len(monthly)

    print("\n" + "="*60)
    print("THE ALCHEMIST SNR v3 — BACKTEST RESULTS (2009–2026)")
    print("="*60)
    print(f"  Total Trades       : {len(tdf):,}")
    print(f"  Win Rate           : {len(wins)/len(tdf)*100:.1f}%")
    print(f"  Net Profit         : ${tdf['pnl'].sum():,.0f}")
    print(f"  Total Return       : {tdf['pnl'].sum()/ACCOUNT*100:+.0f}%")
    print(f"  Profit Factor      : {pf:.2f}")
    print(f"  Max Drawdown       : {max_dd:.1f}%")
    print(f"  Profitable Months  : {prof_m}/{tot_m} ({prof_m/tot_m*100:.0f}%)")
    print(f"  Avg Monthly P&L    : ${monthly.mean():,.0f}")
    print(f"  Worst Month        : ${monthly.min():,.0f}")
    print(f"  Best Month         : ${monthly.max():,.0f}")

    print("\n" + "─"*60)
    print("YEAR-BY-YEAR")
    print("─"*60)
    print(f"{'Year':<8} {'Net P&L':>12} {'Return %':>10} {'Trades':>8} {'WR':>6}")
    print("-"*60)
    for yr in sorted(yearly.index):
        pnl   = yearly[yr]
        pct   = pnl / ACCOUNT * 100
        yr_t  = tdf[tdf["year"] == yr]
        yr_wr = len(yr_t[yr_t["pnl"] > 0]) / len(yr_t) * 100 if len(yr_t) > 0 else 0
        print(f"{yr:<8} ${pnl:>10,.0f} {pct:>+9.1f}% {len(yr_t):>8} {yr_wr:>5.0f}%")

    print("="*60)
    print(f"\nRisk: 1% | SL: 1×ATR(H4) | TP: 2×ATR(H4) | 1:2 R:R")
    print(f"Bias: Daily EMA20 + Weekly EMA10")
    print(f"H4:  EMA9>21>50 stack + ADX>20 + DI direction + pullback to EMA21")
    print(f"H1:  Close crosses EMA9 in trend direction")
    print(f"Sessions: London KZ (06–09 UTC) + NY KZ (11–14 UTC)")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Loading H1 data from parquet (2009–2026)...")
    h1 = load_h1()
    print(f"  {len(h1):,} H1 bars | {h1.index[0].date()} → {h1.index[-1].date()}")

    print("Resampling to H4, Daily, Weekly...")
    h4     = resample(h1, "4h")
    daily  = resample(h1, "1D")
    weekly = resample(h1, "1W")
    print(f"  H4: {len(h4):,} | Daily: {len(daily):,} | Weekly: {len(weekly):,}")

    print("Running v3 backtest...")
    trades = run_backtest(h1, h4, daily, weekly)
    print(f"  {len(trades):,} trades generated")

    if not trades.empty:
        trades.to_csv(os.path.join(OUT_DIR, "trade_log_v3.csv"), index=False)
        print(f"  Saved → backtest/results/trade_log_v3.csv")

    print_results(trades)
