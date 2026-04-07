"""
THE ALCHEMIST SNR — Backtest v5
XAUUSD 2009–2026

Timeframe cascade: Daily → H4 → M15 (weekly dropped entirely)

Logic:
- BIAS    : Daily EMA20 direction (bull = close > EMA20, bear = close < EMA20)
- H4 CONF : EMA9>21>50 stack + ADX>22 + DI direction + RSI>50/< 50 + EMA21 rejection
- M15 ENTRY: Price crosses M15 EMA9 in bias direction while above/below M15 EMA21
- SL: 1×ATR(H4) | TP: 2×ATR(H4) | 1:2 R:R | 1% risk
- Sessions: London (06-09 UTC) + NY (11-16 UTC) | max 1 trade per session
"""

import os
import warnings
import pandas as pd
import numpy as np
import pytz

warnings.filterwarnings("ignore")

M15_PARQUET = "/Users/mac/Desktop/JESH XAUUSD/data/XAUUSD_M15.parquet"
H1_PARQUET  = "/Users/mac/Desktop/JESH XAUUSD/data/XAUUSD_H1.parquet"
OUT_DIR     = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT_DIR, exist_ok=True)

UTC        = pytz.utc
ACCOUNT    = 10_000
RISK_PCT   = 0.01
COMMISSION = 1.0
ATR_LEN    = 14
SL_MULT    = 1.0
TP_MULT    = 2.0   # 1:2 R:R (v3 sweet spot, drop weekly removes the bottleneck)


def get_session(hour_utc):
    if 6 <= hour_utc < 9:
        return "London"
    if 11 <= hour_utc < 16:
        return "NY"
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  LOAD + RESAMPLE
# ─────────────────────────────────────────────────────────────────────────────

def load_parquet(path):
    df = pd.read_parquet(path)
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
    up   = h - h.shift(1)
    down = l.shift(1) - l
    dmp  = up.where((up > down) & (up > 0), 0)
    dmn  = down.where((down > up) & (down > 0), 0)
    atr14  = tr.ewm(span=length, min_periods=length).mean()
    di_pos = 100 * dmp.ewm(span=length, min_periods=length).mean() / atr14
    di_neg = 100 * dmn.ewm(span=length, min_periods=length).mean() / atr14
    dx     = (100 * (di_pos - di_neg).abs() / (di_pos + di_neg).replace(0, np.nan))
    adx    = dx.ewm(span=length, min_periods=length).mean()
    return adx, di_pos, di_neg


def calc_rsi(series, length=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).ewm(span=length, min_periods=length).mean()
    loss  = (-delta.clip(upper=0)).ewm(span=length, min_periods=length).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def prepare_h4(h4):
    h4 = h4.copy()
    h4["ema9"]  = calc_ema(h4["close"], 9)
    h4["ema21"] = calc_ema(h4["close"], 21)
    h4["ema50"] = calc_ema(h4["close"], 50)
    h4["atr"]   = calc_atr(h4, ATR_LEN)
    h4["adx"], h4["di_pos"], h4["di_neg"] = calc_adx(h4, ATR_LEN)
    h4["rsi"]   = calc_rsi(h4["close"], 14)
    return h4


def prepare_m15(m15):
    m15 = m15.copy()
    m15["ema9"]  = calc_ema(m15["close"], 9)
    m15["ema21"] = calc_ema(m15["close"], 21)
    return m15


def compute_daily_bias(daily):
    """
    Bull: daily close > EMA20 (shifted 1 bar — no lookahead)
    Bear: daily close < EMA20
    Weekly dropped entirely.
    """
    d_ema = calc_ema(daily["close"], 20).shift(1)
    d_c   = daily["close"].shift(1)
    bias  = pd.Series(0, index=daily.index)
    bias[d_c > d_ema] =  1
    bias[d_c < d_ema] = -1
    return bias


# ─────────────────────────────────────────────────────────────────────────────
#  BACKTEST ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest(m15_raw, h4_raw, daily):
    print("  Preparing indicators...")
    h4   = prepare_h4(h4_raw)
    m15  = prepare_m15(m15_raw)
    bias = compute_daily_bias(daily)

    m15["date"]     = m15.index.date
    m15["hour_utc"] = m15.index.hour

    dates        = sorted(set(m15["date"]))
    active_trade = None
    session_done = {}   # {(date, session): True}
    trades       = []

    print(f"  Running {len(dates)} days...")

    for date in dates:
        dow = pd.Timestamp(date).dayofweek
        if dow >= 5:
            continue

        day_bars = m15[m15["date"] == date]
        if day_bars.empty:
            continue

        for i, (ts, bar) in enumerate(day_bars.iterrows()):
            utc_hour = bar["hour_utc"]
            o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]

            # ── Manage open trade ──────────────────────────────────────────
            if active_trade is not None:
                # Friday force close
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
            if dow == 4 and utc_hour >= 19:
                continue

            session = get_session(utc_hour)
            if session is None:
                continue

            if session_done.get((date, session)):
                continue

            # ── Daily bias only (no weekly) ────────────────────────────────
            day_ts   = pd.Timestamp(date, tz=UTC)
            bias_idx = bias.index[bias.index <= day_ts]
            if len(bias_idx) == 0:
                continue
            cur_bias = bias[bias_idx[-1]]
            if cur_bias == 0:
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
            h4_rsi   = h4_last["rsi"]
            h4_c     = h4_last["close"]

            if np.isnan(h4_atr) or h4_atr <= 0 or np.isnan(h4_adx):
                continue

            # ── H4 EMA stack (strict) ─────────────────────────────────────
            long_stack  = h4_ema9 > h4_ema21 > h4_ema50
            short_stack = h4_ema9 < h4_ema21 < h4_ema50

            if cur_bias == 1 and not long_stack:
                continue
            if cur_bias == -1 and not short_stack:
                continue

            # ── ADX > 22 ──────────────────────────────────────────────────
            if h4_adx < 22:
                continue

            # ── DI directional ────────────────────────────────────────────
            if cur_bias == 1 and h4_di_p <= h4_di_n:
                continue
            if cur_bias == -1 and h4_di_n <= h4_di_p:
                continue

            # ── RSI H4 ────────────────────────────────────────────────────
            if not np.isnan(h4_rsi):
                if cur_bias == 1 and h4_rsi < 50:
                    continue
                if cur_bias == -1 and h4_rsi > 50:
                    continue

            # ── H4 EMA21 rejection (last 10 bars, strong candle body) ─────
            h4_recent = h4_snap.tail(10)
            ema21_rejection_long  = False
            ema21_rejection_short = False

            for _, hb in h4_recent.iterrows():
                bar_range = hb["high"] - hb["low"]
                bar_body  = abs(hb["close"] - hb["open"])
                strong    = bar_range > 0 and bar_body / bar_range >= 0.4
                if not strong:
                    continue
                if (hb["low"] <= h4_ema21 + h4_atr * 0.5 and
                        hb["close"] > hb["open"] and hb["close"] > h4_ema9):
                    ema21_rejection_long = True
                if (hb["high"] >= h4_ema21 - h4_atr * 0.5 and
                        hb["close"] < hb["open"] and hb["close"] < h4_ema9):
                    ema21_rejection_short = True

            if cur_bias == 1 and not ema21_rejection_long:
                continue
            if cur_bias == -1 and not ema21_rejection_short:
                continue

            # ── Price not overextended from H4 EMA21 ─────────────────────
            dist_from_ema21 = abs(c - h4_ema21)
            if dist_from_ema21 > h4_atr * 2.0:
                continue

            # ── H4 close on right side of EMA9 ───────────────────────────
            if cur_bias == 1 and h4_c < h4_ema9:
                continue
            if cur_bias == -1 and h4_c > h4_ema9:
                continue

            # ── M15 trigger: EMA9 cross while on right side of EMA21 ──────
            m15_ema9  = bar["ema9"]
            m15_ema21 = bar["ema21"]
            if np.isnan(m15_ema9) or np.isnan(m15_ema21):
                continue
            if i == 0:
                continue

            prev_bar  = day_bars.iloc[i - 1]
            prev_c    = prev_bar["close"]
            prev_e9   = prev_bar["ema9"]
            if np.isnan(prev_e9):
                continue

            # M15: price must be on right side of EMA21 (trend confirmation)
            if cur_bias == 1 and c < m15_ema21:
                continue
            if cur_bias == -1 and c > m15_ema21:
                continue

            # M15 EMA9 cross trigger
            m15_long_trig  = (prev_c < prev_e9) and (c > m15_ema9) and (cur_bias == 1)
            m15_short_trig = (prev_c > prev_e9) and (c < m15_ema9) and (cur_bias == -1)

            # ── Entry ──────────────────────────────────────────────────────
            if m15_long_trig or m15_short_trig:
                sl_dist = h4_atr * SL_MULT
                tp_dist = h4_atr * TP_MULT
                lot     = max(0.01, round(ACCOUNT * RISK_PCT / (sl_dist * 100), 2))

                if m15_long_trig:
                    entry     = c
                    sl        = round(entry - sl_dist, 2)
                    tp        = round(entry + tp_dist, 2)
                    direction = "LONG"
                else:
                    entry     = c
                    sl        = round(entry + sl_dist, 2)
                    tp        = round(entry - tp_dist, 2)
                    direction = "SHORT"

                active_trade = {
                    "dir":     direction,
                    "entry":   entry,
                    "sl":      sl,
                    "tp":      tp,
                    "lot":     lot,
                    "open_ts": str(ts),
                    "session": session,
                }
                session_done[(date, session)] = True

    # Close any open trade at end of data
    if active_trade is not None:
        ep  = m15["close"].iloc[-1]
        pnl = (ep - active_trade["entry"]) * (1 if active_trade["dir"] == "LONG" else -1) * active_trade["lot"] * 100 - COMMISSION
        trades.append({**active_trade, "exit": ep, "reason": "fc", "pnl": pnl,
                       "year": m15.index[-1].year, "month": m15.index[-1].month,
                       "date": m15.index[-1].date()})

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
    avg_tpm = len(tdf) / tot_m

    lon = tdf[tdf["session"] == "London"] if "session" in tdf.columns else pd.DataFrame()
    ny  = tdf[tdf["session"] == "NY"]     if "session" in tdf.columns else pd.DataFrame()
    lon_wr = len(lon[lon["pnl"] > 0]) / len(lon) * 100 if len(lon) > 0 else 0
    ny_wr  = len(ny[ny["pnl"] > 0])  / len(ny)  * 100 if len(ny)  > 0 else 0

    print("\n" + "="*60)
    print("THE ALCHEMIST SNR v5 — BACKTEST RESULTS (2009–2026)")
    print("Cascade: Daily → H4 → M15  |  Weekly REMOVED")
    print("="*60)
    print(f"  Total Trades       : {len(tdf):,}")
    print(f"  Trades/Month avg   : {avg_tpm:.1f}")
    print(f"  Win Rate           : {len(wins)/len(tdf)*100:.1f}%")
    print(f"  Net Profit         : ${tdf['pnl'].sum():,.0f}")
    print(f"  Total Return       : {tdf['pnl'].sum()/ACCOUNT*100:+.0f}%")
    print(f"  Profit Factor      : {pf:.2f}")
    print(f"  Max Drawdown       : {max_dd:.1f}%")
    print(f"  Profitable Months  : {prof_m}/{tot_m} ({prof_m/tot_m*100:.0f}%)")
    print(f"  Avg Monthly P&L    : ${monthly.mean():,.0f}")
    print(f"  Worst Month        : ${monthly.min():,.0f}")
    print(f"  Best Month         : ${monthly.max():,.0f}")

    if len(lon) > 0 or len(ny) > 0:
        print(f"\n  London  : {len(lon):3d} trades | WR {lon_wr:.1f}% | P&L ${lon['pnl'].sum():,.0f}")
        print(f"  NY      : {len(ny):3d} trades | WR {ny_wr:.1f}% | P&L ${ny['pnl'].sum():,.0f}")

    print("\n" + "─"*60)
    print("YEAR-BY-YEAR")
    print("─"*60)
    print(f"{'Year':<8} {'Net P&L':>12} {'Return %':>10} {'Trades':>8} {'WR':>6}")
    print("-"*60)
    yearly_sorted = tdf.groupby("year")["pnl"].sum()
    for yr in sorted(yearly_sorted.index):
        pnl_yr = yearly_sorted[yr]
        pct    = pnl_yr / ACCOUNT * 100
        yr_t   = tdf[tdf["year"] == yr]
        yr_wr  = len(yr_t[yr_t["pnl"] > 0]) / len(yr_t) * 100 if len(yr_t) > 0 else 0
        print(f"{yr:<8} ${pnl_yr:>10,.0f} {pct:>+9.1f}% {len(yr_t):>8} {yr_wr:>5.0f}%")

    print("="*60)
    print(f"\nRisk: 1% | SL: 1×ATR(H4) | TP: 2×ATR(H4) | 1:2 R:R")
    print(f"Bias: Daily EMA20 only (weekly removed)")
    print(f"H4:  EMA9>21>50 stack + ADX>22 + DI + RSI + EMA21 rejection (10 bars)")
    print(f"M15: EMA21 side + EMA9 cross trigger")
    print(f"Sessions: London (06-09 UTC) + NY (11-16 UTC) | max 1 trade/session")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Loading M15 data from parquet...")
    m15 = load_parquet(M15_PARQUET)
    print(f"  {len(m15):,} M15 bars | {m15.index[0].date()} → {m15.index[-1].date()}")

    print("Loading H1 for H4 resample...")
    h1 = load_parquet(H1_PARQUET)

    print("Resampling to H4 and Daily...")
    h4    = resample(h1, "4h")
    daily = resample(h1, "1D")
    print(f"  H4: {len(h4):,} | Daily: {len(daily):,}")

    print("Running v5 backtest (Daily→H4→M15)...")
    trades = run_backtest(m15, h4, daily)
    print(f"  {len(trades):,} trades generated")

    if not trades.empty:
        trades.to_csv(os.path.join(OUT_DIR, "trade_log_v5.csv"), index=False)
        print(f"  Saved → backtest/results/trade_log_v5.csv")

    print_results(trades)
