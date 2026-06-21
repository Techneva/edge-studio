"""Fit strengths + export all remaining WC group fixtures as JSON for the app."""
import numpy as np, pandas as pd, json
from scipy.optimize import minimize

CUTOFF = pd.Timestamp(pd.Timestamp.now().date())   # dynamic: include every game played before today
HALF_LIFE_DAYS = 547; MIN_MATCHES = 10; RHO = -0.08

RAW = pd.read_csv("results.csv", parse_dates=["date"])
df = RAW.dropna(subset=["home_score","away_score"]).copy()
df = df[(df.date < CUTOFF) & (df.date >= pd.Timestamp("2016-01-01"))]
df["home_score"]=df.home_score.astype(int); df["away_score"]=df.away_score.astype(int)
xi=np.log(2)/HALF_LIFE_DAYS
df["w"]=np.exp(-xi*(CUTOFF-df.date).dt.days.values)
counts=pd.concat([df.home_team,df.away_team]).value_counts()
strong=set(counts[counts>=MIN_MATCHES].index)
lab=lambda t: t if t in strong else "Other"
df["H"]=df.home_team.map(lab); df["A"]=df.away_team.map(lab)
teams=sorted(set(df.H)|set(df.A)); idx={t:i for i,t in enumerate(teams)}; n=len(teams)
H=df.H.map(idx).values; A=df.A.map(idx).values
hg=df.home_score.values; ag=df.away_score.values; w=df.w.values
nn=(~df.neutral.astype(str).str.upper().eq("TRUE")).astype(float).values

def nll(p):
    atk,dfn,ha=p[:n],p[n:2*n],p[2*n]
    lam=np.exp(atk[H]-dfn[A]+ha*nn); mu=np.exp(atk[A]-dfn[H])
    obj=-(w*(hg*np.log(lam)-lam+ag*np.log(mu)-mu)).sum()
    rh=w*(hg-lam); ra=w*(ag-mu)
    ga=np.zeros(n); gd=np.zeros(n)
    np.add.at(ga,H,rh); np.add.at(ga,A,ra); np.add.at(gd,A,-rh); np.add.at(gd,H,-ra)
    g=-np.concatenate([ga,gd,[(rh*nn).sum()]])
    ma=atk.mean(); obj+=1e3*ma**2+1e-3*(atk@atk+dfn@dfn)
    g[:n]+=2e3*ma/n+2e-3*atk; g[n:2*n]+=2e-3*dfn
    return obj,g
res=minimize(nll,np.zeros(2*n+1),jac=True,method="L-BFGS-B",
             bounds=[(-3,3)]*(2*n)+[(0,1)],options={"maxiter":500})
atk,dfn,ha=res.x[:n],res.x[n:2*n],res.x[2*n]
print(f"fit ok={res.success} home_adv={ha:.3f} teams={n}")

def xg(home,away,neutral):
    he=0.0 if neutral else ha
    lam=float(np.exp(atk[idx[lab(home)]]-dfn[idx[lab(away)]]+he))
    mu =float(np.exp(atk[idx[lab(away)]]-dfn[idx[lab(home)]]))
    return round(lam,3),round(mu,3)

# remaining WC group fixtures (unplayed)
wc=RAW.copy(); wc["date"]=pd.to_datetime(wc["date"])
wc=wc[wc.tournament.str.contains("World Cup",case=False,na=False)]
rem=wc[(wc.home_score.isna()) & (wc.date>=pd.Timestamp("2026-06-11")) & (wc.date<=pd.Timestamp("2026-06-28"))].sort_values(["date","home_team"])  # all remaining group fixtures, independent of clock

# odds store: persistent app_odds.json ("Home|Away" -> [home,draw,away] decimal),
# refreshed by the daily scheduled task. Falls back to empty if absent.
import os as _os
ODDS_STORE = {}
if _os.path.exists("app_odds.json"):
    try: ODDS_STORE = json.load(open("app_odds.json"))
    except Exception: ODDS_STORE = {}
CS_STORE = {}
if _os.path.exists("cs_odds.json"):
    try: CS_STORE = json.load(open("cs_odds.json"))
    except Exception: CS_STORE = {}
MKT_STORE = {}
if _os.path.exists("market_odds.json"):
    try: MKT_STORE = json.load(open("market_odds.json"))
    except Exception: MKT_STORE = {}
fixtures=[]
for _,r in rem.iterrows():
    neu=str(r.neutral).upper()=="TRUE"
    lam,mu=xg(r.home_team,r.away_team,neu)
    key=f"{r.home_team}|{r.away_team}"
    fixtures.append({
        "date":r.date.strftime("%Y-%m-%d"),"home":r.home_team,"away":r.away_team,
        "neutral":neu,"venue":f"{r.get('city','')}, {r.get('country','')}".strip(", "),
        "home_xg":lam,"away_xg":mu,
        "odds":ODDS_STORE.get(key),  # [home,draw,away] decimal or None
        "cs_odds":CS_STORE.get(key, {}),  # {"h-a": decimal} correct-score prices
        "mkt":MKT_STORE.get(key, {})     # {marketKey: decimal} all other markets
    })

ratings={t:{"atk":round(float(atk[idx[t]]),4),"def":round(float(dfn[idx[t]]),4)}
         for t in teams if t!="Other"}
data={
 "competition":"FIFA World Cup 2026",
 "stage":"Group stage (remaining fixtures)",
 "generated":pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
 "model":{"type":"Dixon-Coles (Poisson + low-score correction)","rho":RHO,
          "home_adv":round(float(ha),4),"fit_through":(CUTOFF - pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
          "data":"real international results (martj42), time-weighted MLE, no leakage"},
 "fixtures":fixtures,"ratings":ratings,
}
json.dump(data,open("app_data.json","w"),indent=1)
print(f"fixtures: {len(fixtures)}  teams rated: {len(ratings)}")
print("with odds:", sum(1 for f in fixtures if f['odds']))
