"""
THE ALCHEMIST SNR — v5a: London Only
Daily → H4 → M15 | London session only (06-09 UTC) | 1:2 R:R
Goal: Higher WR by removing NY noise (London WR was 46.5% vs NY 38%)
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

UTC        = pytz.utc
ACCOUNT    = 10_000
RISK_PCT   = 0.01
COMMISSION = 1.0
ATR_LEN    = 14
SL_MULT    = 1.0
TP_MULT    = 2.0
VERSION    = "v5a-London"


def get_session(hour_utc):
    if 6 <= hour_utc < 9:
        return "London"
    return None   # NY excluded entirely


def load_parquet(path):
    df = pd.read_parquet(path)[["open","high","low","close"]].astype(float)
    if df.index.tz is None:
        df.index = df.index.tz_localize(UTC)
    else:
        df.index = df.index.tz_convert(UTC)
    df.sort_index(inplace=True)
    return df[~df.index.duplicated(keep="first")]


def resample(df, rule):
    return df.resample(rule, closed="left", label="left").agg(
        {"open":"first","high":"max","low":"min","close":"last"}).dropna()


def calc_atr(df, n=14):
    h,l,pc = df["high"],df["low"],df["close"].shift(1)
    tr = pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(span=n,min_periods=n).mean()

def calc_ema(s,n): return s.ewm(span=n,min_periods=n).mean()

def calc_adx(df, n=14):
    h,l,pc = df["high"],df["low"],df["close"].shift(1)
    tr   = pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    up   = h-h.shift(1); down = l.shift(1)-l
    dmp  = up.where((up>down)&(up>0),0)
    dmn  = down.where((down>up)&(down>0),0)
    atr  = tr.ewm(span=n,min_periods=n).mean()
    dip  = 100*dmp.ewm(span=n,min_periods=n).mean()/atr
    din  = 100*dmn.ewm(span=n,min_periods=n).mean()/atr
    dx   = 100*(dip-din).abs()/(dip+din).replace(0,np.nan)
    return dx.ewm(span=n,min_periods=n).mean(), dip, din

def calc_rsi(s, n=14):
    d = s.diff()
    g = d.clip(lower=0).ewm(span=n,min_periods=n).mean()
    l = (-d.clip(upper=0)).ewm(span=n,min_periods=n).mean()
    return 100-(100/(1+g/l.replace(0,np.nan)))

def prepare_h4(h4):
    h4=h4.copy()
    h4["ema9"]=calc_ema(h4["close"],9); h4["ema21"]=calc_ema(h4["close"],21)
    h4["ema50"]=calc_ema(h4["close"],50); h4["atr"]=calc_atr(h4,ATR_LEN)
    h4["adx"],h4["di_pos"],h4["di_neg"]=calc_adx(h4,ATR_LEN)
    h4["rsi"]=calc_rsi(h4["close"],14)
    return h4

def prepare_m15(m15):
    m15=m15.copy()
    m15["ema9"]=calc_ema(m15["close"],9)
    m15["ema21"]=calc_ema(m15["close"],21)
    return m15

def compute_daily_bias(daily):
    d_ema=calc_ema(daily["close"],20).shift(1)
    d_c=daily["close"].shift(1)
    bias=pd.Series(0,index=daily.index)
    bias[d_c>d_ema]=1; bias[d_c<d_ema]=-1
    return bias


def run_backtest(m15_raw, h4_raw, daily):
    h4=prepare_h4(h4_raw); m15=prepare_m15(m15_raw)
    bias=compute_daily_bias(daily)
    m15["date"]=m15.index.date; m15["hour_utc"]=m15.index.hour

    dates=sorted(set(m15["date"]))
    active_trade=None; session_done={}; trades=[]

    for date in dates:
        dow=pd.Timestamp(date).dayofweek
        if dow>=5: continue
        day_bars=m15[m15["date"]==date]
        if day_bars.empty: continue

        for i,(ts,bar) in enumerate(day_bars.iterrows()):
            utc_hour=bar["hour_utc"]
            o,h,l,c=bar["open"],bar["high"],bar["low"],bar["close"]

            if active_trade is not None:
                if dow==4 and utc_hour>=19:
                    pnl=(c-active_trade["entry"])*(1 if active_trade["dir"]=="LONG" else -1)*active_trade["lot"]*100-COMMISSION
                    trades.append({**active_trade,"exit":c,"reason":"fc","pnl":pnl,"year":ts.year,"month":ts.month,"date":date})
                    active_trade=None; continue
                if active_trade["dir"]=="LONG":
                    if h>=active_trade["tp"]:
                        pnl=(active_trade["tp"]-active_trade["entry"])*active_trade["lot"]*100-COMMISSION
                        trades.append({**active_trade,"exit":active_trade["tp"],"reason":"tp","pnl":pnl,"year":ts.year,"month":ts.month,"date":date}); active_trade=None
                    elif l<=active_trade["sl"]:
                        pnl=(active_trade["sl"]-active_trade["entry"])*active_trade["lot"]*100-COMMISSION
                        trades.append({**active_trade,"exit":active_trade["sl"],"reason":"sl","pnl":pnl,"year":ts.year,"month":ts.month,"date":date}); active_trade=None
                else:
                    if l<=active_trade["tp"]:
                        pnl=(active_trade["entry"]-active_trade["tp"])*active_trade["lot"]*100-COMMISSION
                        trades.append({**active_trade,"exit":active_trade["tp"],"reason":"tp","pnl":pnl,"year":ts.year,"month":ts.month,"date":date}); active_trade=None
                    elif h>=active_trade["sl"]:
                        pnl=(active_trade["entry"]-active_trade["sl"])*active_trade["lot"]*100-COMMISSION
                        trades.append({**active_trade,"exit":active_trade["sl"],"reason":"sl","pnl":pnl,"year":ts.year,"month":ts.month,"date":date}); active_trade=None
                continue

            if utc_hour<6: continue
            if dow==4 and utc_hour>=19: continue
            session=get_session(utc_hour)
            if session is None: continue
            if session_done.get((date,session)): continue

            day_ts=pd.Timestamp(date,tz=UTC)
            bias_idx=bias.index[bias.index<=day_ts]
            if len(bias_idx)==0: continue
            cur_bias=bias[bias_idx[-1]]
            if cur_bias==0: continue

            h4_snap=h4[h4.index<=ts]
            if len(h4_snap)<55: continue
            hL=h4_snap.iloc[-1]
            if np.isnan(hL["atr"]) or hL["atr"]<=0 or np.isnan(hL["adx"]): continue

            if cur_bias==1 and not (hL["ema9"]>hL["ema21"]>hL["ema50"]): continue
            if cur_bias==-1 and not (hL["ema9"]<hL["ema21"]<hL["ema50"]): continue
            if hL["adx"]<22: continue
            if cur_bias==1 and hL["di_pos"]<=hL["di_neg"]: continue
            if cur_bias==-1 and hL["di_neg"]<=hL["di_pos"]: continue
            if not np.isnan(hL["rsi"]):
                if cur_bias==1 and hL["rsi"]<50: continue
                if cur_bias==-1 and hL["rsi"]>50: continue

            h4r=h4_snap.tail(10)
            rej_l=rej_s=False
            for _,hb in h4r.iterrows():
                rng=hb["high"]-hb["low"]; bdy=abs(hb["close"]-hb["open"])
                if rng<=0 or bdy/rng<0.4: continue
                if hb["low"]<=hL["ema21"]+hL["atr"]*0.5 and hb["close"]>hb["open"] and hb["close"]>hL["ema9"]: rej_l=True
                if hb["high"]>=hL["ema21"]-hL["atr"]*0.5 and hb["close"]<hb["open"] and hb["close"]<hL["ema9"]: rej_s=True
            if cur_bias==1 and not rej_l: continue
            if cur_bias==-1 and not rej_s: continue
            if abs(c-hL["ema21"])>hL["atr"]*2.0: continue
            if cur_bias==1 and hL["close"]<hL["ema9"]: continue
            if cur_bias==-1 and hL["close"]>hL["ema9"]: continue

            e9=bar["ema9"]; e21=bar["ema21"]
            if np.isnan(e9) or np.isnan(e21): continue
            if i==0: continue
            pb=day_bars.iloc[i-1]; pc2=pb["close"]; pe9=pb["ema9"]
            if np.isnan(pe9): continue
            if cur_bias==1 and c<e21: continue
            if cur_bias==-1 and c>e21: continue

            trig_l=(pc2<pe9)and(c>e9)and(cur_bias==1)
            trig_s=(pc2>pe9)and(c<e9)and(cur_bias==-1)

            if trig_l or trig_s:
                sl_d=hL["atr"]*SL_MULT; tp_d=hL["atr"]*TP_MULT
                lot=max(0.01,round(ACCOUNT*RISK_PCT/(sl_d*100),2))
                if trig_l:
                    entry=c; sl=round(entry-sl_d,2); tp=round(entry+tp_d,2); direction="LONG"
                else:
                    entry=c; sl=round(entry+sl_d,2); tp=round(entry-tp_d,2); direction="SHORT"
                active_trade={"dir":direction,"entry":entry,"sl":sl,"tp":tp,"lot":lot,"open_ts":str(ts),"session":session}
                session_done[(date,session)]=True

    if active_trade is not None:
        ep=m15["close"].iloc[-1]
        pnl=(ep-active_trade["entry"])*(1 if active_trade["dir"]=="LONG" else -1)*active_trade["lot"]*100-COMMISSION
        trades.append({**active_trade,"exit":ep,"reason":"fc","pnl":pnl,"year":m15.index[-1].year,"month":m15.index[-1].month,"date":m15.index[-1].date()})
    return pd.DataFrame(trades)


def print_results(tdf, version):
    if tdf.empty: print("No trades."); return
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
    print(f"\n{'─'*60}\nYEAR-BY-YEAR\n{'─'*60}")
    print(f"{'Year':<8} {'Net P&L':>12} {'Return %':>10} {'Trades':>8} {'WR':>6}")
    print("-"*60)
    for yr in sorted(yearly.index):
        p=yearly[yr]; yr_t=tdf[tdf["year"]==yr]
        wr=len(yr_t[yr_t["pnl"]>0])/len(yr_t)*100 if len(yr_t)>0 else 0
        print(f"{yr:<8} ${p:>10,.0f} {p/ACCOUNT*100:>+9.1f}% {len(yr_t):>8} {wr:>5.0f}%")
    print(f"{'='*60}")
    print(f"\nRisk:1% | SL:1×ATR(H4) | TP:{TP_MULT}×ATR(H4) | Bias:Daily EMA20")


if __name__=="__main__":
    print(f"Running {VERSION}...")
    m15=load_parquet(M15_PARQUET)
    h1=load_parquet(H1_PARQUET)
    h4=resample(h1,"4h"); daily=resample(h1,"1D")
    trades=run_backtest(m15,h4,daily)
    print(f"  {len(trades):,} trades")
    if not trades.empty:
        trades.to_csv(os.path.join(OUT_DIR,"trade_log_v5a.csv"),index=False)
    print_results(trades, VERSION)
