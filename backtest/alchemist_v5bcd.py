"""
THE ALCHEMIST SNR — v5b / v5c / v5d (fast multi-variant runner)

v5b: Volatility filter — ADX>=25, skip if 5-day H4 range < 3×ATR (chop)
v5c: 1:3 R:R on clean Daily→H4→M15
v5d: H4→M15 context + M5-proxy entry trigger (3-bar M15 EMA ≈ M5 EMA9)

Speed fix: H4 signals pre-aligned onto M15 index via ffill — no per-bar H4 scan.
All: Daily bias only | London + NY | 1% risk
"""
import os, warnings
import pandas as pd
import numpy as np
import pytz

warnings.filterwarnings("ignore")

M15_PARQUET = "/Users/mac/Desktop/JESH XAUUSD/data/XAUUSD_M15.parquet"
H1_PARQUET  = "/Users/mac/Desktop/JESH XAUUSD/data/XAUUSD_H1.parquet"
OUT_DIR     = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT_DIR, exist_ok=True)
UTC = pytz.utc
ACCOUNT    = 10_000
RISK_PCT   = 0.01
COMMISSION = 1.0
ATR_LEN    = 14


# ─────────────────────────────────────────────────────────────────────────────
#  UTILS
# ─────────────────────────────────────────────────────────────────────────────

def load_parquet(path):
    df = pd.read_parquet(path)[["open","high","low","close"]].astype(float)
    if df.index.tz is None: df.index = df.index.tz_localize(UTC)
    else: df.index = df.index.tz_convert(UTC)
    df.sort_index(inplace=True)
    return df[~df.index.duplicated(keep="first")]

def resample(df, rule):
    return df.resample(rule, closed="left", label="left").agg(
        {"open":"first","high":"max","low":"min","close":"last"}).dropna()

def calc_atr(df, n=14):
    h,l,pc = df["high"],df["low"],df["close"].shift(1)
    tr = pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(span=n,min_periods=n).mean()

def calc_ema(s, n): return s.ewm(span=n,min_periods=n).mean()

def calc_adx(df, n=14):
    h,l,pc = df["high"],df["low"],df["close"].shift(1)
    tr   = pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    up   = h-h.shift(1); dn = l.shift(1)-l
    dmp  = up.where((up>dn)&(up>0),0)
    dmn  = dn.where((dn>up)&(dn>0),0)
    atr  = tr.ewm(span=n,min_periods=n).mean()
    dip  = 100*dmp.ewm(span=n,min_periods=n).mean()/atr
    din  = 100*dmn.ewm(span=n,min_periods=n).mean()/atr
    dx   = 100*(dip-din).abs()/(dip+din).replace(0,np.nan)
    return dx.ewm(span=n,min_periods=n).mean(), dip, din

def calc_rsi(s, n=14):
    d=s.diff()
    g=d.clip(lower=0).ewm(span=n,min_periods=n).mean()
    lo=(-d.clip(upper=0)).ewm(span=n,min_periods=n).mean()
    return 100-(100/(1+g/lo.replace(0,np.nan)))


# ─────────────────────────────────────────────────────────────────────────────
#  BUILD H4 SIGNAL TABLE  (shift=1 bar to avoid lookahead)
# ─────────────────────────────────────────────────────────────────────────────

def build_h4_signals(h4_raw):
    h4 = h4_raw.copy()
    h4["ema9"]  = calc_ema(h4["close"], 9)
    h4["ema21"] = calc_ema(h4["close"], 21)
    h4["ema50"] = calc_ema(h4["close"], 50)
    h4["atr"]   = calc_atr(h4, ATR_LEN)
    h4["adx"], h4["di_pos"], h4["di_neg"] = calc_adx(h4, ATR_LEN)
    h4["rsi"]   = calc_rsi(h4["close"], 14)

    # 5-day rolling range (30 H4 bars ≈ 5 days) for chop filter
    h4["roll_hi"] = h4["high"].rolling(30).max()
    h4["roll_lo"] = h4["low"].rolling(30).min()

    # H4 EMA21 rejection flag (last 10 bars) — computed per bar, vectorised
    rej_l = pd.Series(False, index=h4.index)
    rej_s = pd.Series(False, index=h4.index)
    for lag in range(1, 11):
        hb_hi  = h4["high"].shift(lag)
        hb_lo  = h4["low"].shift(lag)
        hb_op  = h4["open"].shift(lag)
        hb_cl  = h4["close"].shift(lag)
        rng    = hb_hi - hb_lo
        bdy    = (hb_cl - hb_op).abs()
        strong = (rng > 0) & (bdy / rng.replace(0, np.nan) >= 0.4)
        rej_l |= strong & (hb_lo <= h4["ema21"] + h4["atr"]*0.5) & (hb_cl > hb_op) & (hb_cl > h4["ema9"])
        rej_s |= strong & (hb_hi >= h4["ema21"] - h4["atr"]*0.5) & (hb_cl < hb_op) & (hb_cl < h4["ema9"])

    h4["rej_long"]  = rej_l
    h4["rej_short"] = rej_s

    # Shift everything by 1 bar so M15 sees the *completed* H4 bar
    sig_cols = ["ema9","ema21","ema50","atr","adx","di_pos","di_neg",
                "rsi","roll_hi","roll_lo","rej_long","rej_short","close"]
    sig = h4[sig_cols].shift(1)
    sig.columns = ["h4_"+c for c in sig_cols]
    return sig


def build_daily_bias(daily):
    d_ema = calc_ema(daily["close"], 20).shift(1)
    d_c   = daily["close"].shift(1)
    bias  = pd.Series(0, index=daily.index)
    bias[d_c > d_ema] =  1
    bias[d_c < d_ema] = -1
    return bias


# ─────────────────────────────────────────────────────────────────────────────
#  MERGE: align H4 signals + daily bias onto M15 index (ffill)
# ─────────────────────────────────────────────────────────────────────────────

def build_m15_frame(m15_raw, h4_sig, daily_bias):
    m15 = m15_raw.copy()
    m15["ema9"]  = calc_ema(m15["close"], 9)
    m15["ema21"] = calc_ema(m15["close"], 21)
    # M5-proxy EMAs: 3-bar and 7-bar of M15 ≈ EMA9 and EMA21 on M5
    m15["m5e9"]  = calc_ema(m15["close"], 3)
    m15["m5e21"] = calc_ema(m15["close"], 7)

    # Forward-fill H4 signals onto M15 timestamps
    h4_on_m15 = h4_sig.reindex(m15.index, method="ffill")
    bias_on_m15 = daily_bias.reindex(m15.index, method="ffill").fillna(0)

    m15 = pd.concat([m15, h4_on_m15], axis=1)
    m15["bias"] = bias_on_m15
    m15["hour_utc"] = m15.index.hour
    m15["date"] = m15.index.date
    m15["dow"]  = m15.index.dayofweek
    return m15


# ─────────────────────────────────────────────────────────────────────────────
#  FAST BACKTEST ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest(m15_df, sl_mult=1.0, tp_mult=2.0,
                 london_only=False, volatility_filter=False, use_m5_entry=False):

    def get_session(h):
        if 6 <= h < 9:  return "London"
        if not london_only and 11 <= h < 16: return "NY"
        return None

    active = None
    session_done = {}
    trades = []
    bars = m15_df.values
    cols = list(m15_df.columns)

    def col(name): return cols.index(name)

    iO=col("open"); iH=col("high"); iL=col("low"); iC=col("close")
    iE9=col("ema9"); iE21=col("ema21")
    iM5E9=col("m5e9"); iM5E21=col("m5e21")
    iBIAS=col("bias"); iHOUR=col("hour_utc"); iDATE=col("date"); iDOW=col("dow")
    iH4E9=col("h4_ema9"); iH4E21=col("h4_ema21"); iH4E50=col("h4_ema50")
    iH4ATR=col("h4_atr"); iH4ADX=col("h4_adx")
    iH4DIP=col("h4_di_pos"); iH4DIN=col("h4_di_neg")
    iH4RSI=col("h4_rsi"); iH4RHI=col("h4_roll_hi"); iH4RLO=col("h4_roll_lo")
    iH4RJL=col("h4_rej_long"); iH4RJS=col("h4_rej_short")
    iH4C=col("h4_close")

    ts_index = m15_df.index
    n = len(bars)

    for idx in range(n):
        row  = bars[idx]
        ts   = ts_index[idx]
        hour = int(row[iHOUR])
        date = row[iDATE]
        dow  = int(row[iDOW])
        o,h,l,c = row[iO],row[iH],row[iL],row[iC]

        # ── Manage open trade ─────────────────────────────────────────────
        if active is not None:
            if dow == 4 and hour >= 19:
                pnl = (c - active["entry"]) * (1 if active["dir"]=="LONG" else -1) * active["lot"] * 100 - COMMISSION
                trades.append({**active,"exit":c,"reason":"fc","pnl":pnl,"year":ts.year,"month":ts.month,"date":date})
                active = None; continue
            if active["dir"] == "LONG":
                if h >= active["tp"]:
                    pnl=(active["tp"]-active["entry"])*active["lot"]*100-COMMISSION
                    trades.append({**active,"exit":active["tp"],"reason":"tp","pnl":pnl,"year":ts.year,"month":ts.month,"date":date}); active=None
                elif l <= active["sl"]:
                    pnl=(active["sl"]-active["entry"])*active["lot"]*100-COMMISSION
                    trades.append({**active,"exit":active["sl"],"reason":"sl","pnl":pnl,"year":ts.year,"month":ts.month,"date":date}); active=None
            else:
                if l <= active["tp"]:
                    pnl=(active["entry"]-active["tp"])*active["lot"]*100-COMMISSION
                    trades.append({**active,"exit":active["tp"],"reason":"tp","pnl":pnl,"year":ts.year,"month":ts.month,"date":date}); active=None
                elif h >= active["sl"]:
                    pnl=(active["entry"]-active["sl"])*active["lot"]*100-COMMISSION
                    trades.append({**active,"exit":active["sl"],"reason":"sl","pnl":pnl,"year":ts.year,"month":ts.month,"date":date}); active=None
            continue

        # ── Session / basic ───────────────────────────────────────────────
        if dow >= 5 or hour < 6: continue
        if dow == 4 and hour >= 19: continue
        session = get_session(hour)
        if session is None: continue
        if session_done.get((date, session)): continue

        # ── Bias ─────────────────────────────────────────────────────────
        bias = int(row[iBIAS])
        if bias == 0: continue

        # ── H4 values ────────────────────────────────────────────────────
        h4e9=row[iH4E9]; h4e21=row[iH4E21]; h4e50=row[iH4E50]
        h4atr=row[iH4ATR]; h4adx=row[iH4ADX]
        h4dip=row[iH4DIP]; h4din=row[iH4DIN]
        h4rsi=row[iH4RSI]; h4c=row[iH4C]

        if np.isnan(h4atr) or h4atr<=0 or np.isnan(h4adx): continue

        # EMA stack
        if bias== 1 and not (h4e9>h4e21>h4e50): continue
        if bias==-1 and not (h4e9<h4e21<h4e50): continue

        # ADX
        adx_thresh = 25 if volatility_filter else 22
        if h4adx < adx_thresh: continue

        # DI
        if bias== 1 and h4dip<=h4din: continue
        if bias==-1 and h4din<=h4dip: continue

        # RSI
        if not np.isnan(h4rsi):
            if bias== 1 and h4rsi<50: continue
            if bias==-1 and h4rsi>50: continue

        # Volatility / chop filter
        if volatility_filter:
            rhi=row[iH4RHI]; rlo=row[iH4RLO]
            if not np.isnan(rhi) and (rhi-rlo) < h4atr*3.0: continue

        # H4 EMA21 rejection
        if bias== 1 and not row[iH4RJL]: continue
        if bias==-1 and not row[iH4RJS]: continue

        # Not overextended
        if abs(c - h4e21) > h4atr * 2.0: continue

        # H4 close side of EMA9
        if bias== 1 and h4c < h4e9: continue
        if bias==-1 and h4c > h4e9: continue

        # ── M15 / M5-proxy trigger ────────────────────────────────────────
        if idx == 0: continue
        prev = bars[idx-1]

        if use_m5_entry:
            e9=row[iM5E9]; e21=row[iM5E21]; pe9=prev[iM5E9]; prev_c=prev[iC]
        else:
            e9=row[iE9]; e21=row[iE21]; pe9=prev[iE9]; prev_c=prev[iC]

        if np.isnan(e9) or np.isnan(e21) or np.isnan(pe9): continue
        if bias== 1 and c < e21: continue
        if bias==-1 and c > e21: continue

        trig_l = (prev_c < pe9) and (c > e9) and (bias == 1)
        trig_s = (prev_c > pe9) and (c < e9) and (bias == -1)

        if trig_l or trig_s:
            sl_d = h4atr * sl_mult
            tp_d = h4atr * tp_mult
            lot  = max(0.01, round(ACCOUNT * RISK_PCT / (sl_d * 100), 2))
            if trig_l:
                entry=c; sl=round(c-sl_d,2); tp=round(c+tp_d,2); direction="LONG"
            else:
                entry=c; sl=round(c+sl_d,2); tp=round(c-tp_d,2); direction="SHORT"
            active = {"dir":direction,"entry":entry,"sl":sl,"tp":tp,"lot":lot,
                      "open_ts":str(ts),"session":session}
            session_done[(date, session)] = True

    if active is not None:
        ep = m15_df["close"].iloc[-1]
        last = m15_df.index[-1]
        pnl = (ep-active["entry"])*(1 if active["dir"]=="LONG" else -1)*active["lot"]*100-COMMISSION
        trades.append({**active,"exit":ep,"reason":"fc","pnl":pnl,
                       "year":last.year,"month":last.month,"date":last.date()})
    return pd.DataFrame(trades)


# ─────────────────────────────────────────────────────────────────────────────
#  PRINT
# ─────────────────────────────────────────────────────────────────────────────

def print_results(tdf, version, tp_mult):
    if tdf.empty: print(f"{version}: No trades."); return
    wins=tdf[tdf["pnl"]>0]
    monthly=tdf.groupby(["year","month"])["pnl"].sum()
    yearly=tdf.groupby("year")["pnl"].sum()
    gp=wins["pnl"].sum(); gl=abs(tdf[tdf["pnl"]<=0]["pnl"].sum())
    pf=gp/gl if gl>0 else 9999
    eq=ACCOUNT+tdf["pnl"].cumsum(); mdd=abs(((eq-eq.cummax())/eq.cummax()*100).min())
    pm=(monthly>0).sum(); tm=len(monthly)
    print(f"\n{'='*60}")
    print(f"ALCHEMIST {version} — RESULTS (2009–2026)")
    print(f"{'='*60}")
    print(f"  Total Trades       : {len(tdf):,}")
    print(f"  Trades/Month avg   : {len(tdf)/tm:.1f}")
    print(f"  Win Rate           : {len(wins)/len(tdf)*100:.1f}%")
    print(f"  Net Profit         : ${tdf['pnl'].sum():,.0f}")
    print(f"  Total Return       : {tdf['pnl'].sum()/ACCOUNT*100:+.0f}%")
    print(f"  Profit Factor      : {pf:.2f}")
    print(f"  Max Drawdown       : {mdd:.1f}%")
    print(f"  Profitable Months  : {pm}/{tm} ({pm/tm*100:.0f}%)")
    print(f"  Avg Monthly P&L    : ${monthly.mean():,.0f}")
    print(f"  Worst Month        : ${monthly.min():,.0f}")
    print(f"  Best Month         : ${monthly.max():,.0f}")
    for sess in ["London","NY"]:
        st=tdf[tdf["session"]==sess] if "session" in tdf.columns else pd.DataFrame()
        if len(st)>0:
            wr=len(st[st["pnl"]>0])/len(st)*100
            print(f"  {sess:<8}: {len(st):3d} trades | WR {wr:.1f}% | P&L ${st['pnl'].sum():,.0f}")
    print(f"\n{'─'*60}\nYEAR-BY-YEAR\n{'─'*60}")
    print(f"{'Year':<8} {'Net P&L':>12} {'Return %':>10} {'Trades':>8} {'WR':>6}")
    print("-"*60)
    for yr in sorted(yearly.index):
        p=yearly[yr]; yr_t=tdf[tdf["year"]==yr]
        wr=len(yr_t[yr_t["pnl"]>0])/len(yr_t)*100 if len(yr_t)>0 else 0
        print(f"{yr:<8} ${p:>10,.0f} {p/ACCOUNT*100:>+9.1f}% {len(yr_t):>8} {wr:>5.0f}%")
    print(f"{'='*60}")
    print(f"SL:1×ATR | TP:{tp_mult}×ATR | Bias:Daily EMA20 | {version}")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time
    print("Loading data...")
    m15   = load_parquet(M15_PARQUET)
    h1    = load_parquet(H1_PARQUET)
    h4    = resample(h1, "4h")
    daily = resample(h1, "1D")
    print(f"  M15:{len(m15):,} | H4:{len(h4):,} | Daily:{len(daily):,}")

    print("Pre-computing H4 signals & daily bias...")
    h4_sig    = build_h4_signals(h4)
    daily_bias = build_daily_bias(daily)

    print("Merging onto M15 index (ffill)...")
    m15_df = build_m15_frame(m15, h4_sig, daily_bias)
    print(f"  M15 frame ready: {m15_df.shape}")

    variants = [
        # (label,           sl,  tp,  london, vol_filter, m5_entry, csv)
        ("v5b-VolFilter",  1.0, 2.0, False, True,  False, "trade_log_v5b.csv"),
        ("v5c-1:3RR",      1.0, 3.0, False, False, False, "trade_log_v5c.csv"),
        ("v5d-M5Entry",    1.0, 2.0, False, False, True,  "trade_log_v5d.csv"),
    ]

    for label, sl, tp, lo, vf, m5e, csv in variants:
        t0 = time.time()
        print(f"\nRunning {label}...")
        tdf = run_backtest(m15_df, sl_mult=sl, tp_mult=tp,
                           london_only=lo, volatility_filter=vf, use_m5_entry=m5e)
        print(f"  {len(tdf):,} trades in {time.time()-t0:.1f}s")
        if not tdf.empty:
            tdf.to_csv(os.path.join(OUT_DIR, csv), index=False)
            print(f"  Saved → results/{csv}")
        print_results(tdf, label, tp)
