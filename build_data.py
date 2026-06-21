"""Fit strengths + export all remaining WC group fixtures as JSON for the app.

Uses the shared dc_fit module in JOINT Dixon-Coles mode with partial pooling:
  - mode="dc"     : the low-score tau(rho) term is inside the likelihood and rho
                    is estimated jointly (no longer a hardcoded constant).
  - pool="shrink" : every team keeps its own rating, sample-size-shrunk toward the
                    global mean (replaces the old MIN_MATCHES "Other" collapse).
Validated out-of-sample by evaluate.py (lower Brier/log-loss vs the old fit).
"""
import numpy as np, pandas as pd, json, os as _os
import dc_fit

CUTOFF = pd.Timestamp(pd.Timestamp.now().date())   # dynamic: include every game played before today
HALF_LIFE_DAYS = 547; MIN_MATCHES = 10

RAW = pd.read_csv("results.csv", parse_dates=["date"])
RAW_played = RAW.dropna(subset=["home_score", "away_score"]).copy()

pred, ok, ntrain = dc_fit.fit(RAW_played, CUTOFF, half_life=HALF_LIFE_DAYS,
                              min_matches=MIN_MATCHES, mode="dc", pool="shrink")
RHO = round(float(pred.rho), 4)
ha = pred.ha
print(f"fit ok={ok} home_adv={ha:.3f} rho={RHO} teams={len(pred.idx)} train={ntrain}")


# Totals recalibration (validated out-of-sample in evaluate/calibrate_fit: the raw
# model is over-confident on per-game totals, so regress each game's expected total
# toward the global mean while leaving supremacy untouched). O/U log-loss 0.677->0.667.
CAL_ST = 0.65          # keep 65% of the total's deviation from the mean
CAL_TBAR = 2.68        # global mean international total goals
K_SE = 0.7             # xG-uncertainty scale (calibrated out-of-sample; neutral on log-loss, not over-inflated)

def xg(home, away, neutral):
    lam, mu = pred.xg(home, away, neutral)
    S, T = lam - mu, lam + mu
    Tp = CAL_TBAR + CAL_ST * (T - CAL_TBAR)        # shrink total toward the mean
    return round(max((Tp + S) / 2, 0.05), 3), round(max((Tp - S) / 2, 0.05), 3)


# remaining WC group fixtures (unplayed)
wc = RAW.copy(); wc["date"] = pd.to_datetime(wc["date"])
wc = wc[wc.tournament.str.contains("World Cup", case=False, na=False)]
rem = wc[(wc.home_score.isna()) & (wc.date >= pd.Timestamp("2026-06-11")) & (wc.date <= pd.Timestamp("2026-06-28"))].sort_values(["date", "home_team"])

# odds store: persistent app_odds.json ("Home|Away" -> [home,draw,away] decimal),
# refreshed by the daily scheduled task. Falls back to empty if absent.
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
fixtures = []
for _, r in rem.iterrows():
    neu = str(r.neutral).upper() == "TRUE"
    lam, mu = xg(r.home_team, r.away_team, neu)
    key = f"{r.home_team}|{r.away_team}"
    fixtures.append({
        "date": r.date.strftime("%Y-%m-%d"), "home": r.home_team, "away": r.away_team,
        "neutral": neu, "venue": f"{r.get('city','')}, {r.get('country','')}".strip(", "),
        "home_xg": lam, "away_xg": mu,
        "xgse": round(pred.xg_logse(r.home_team, r.away_team, K_SE), 4),  # 1-sigma log-xG uncertainty
        "odds": ODDS_STORE.get(key),
        "cs_odds": CS_STORE.get(key, {}),
        "mkt": MKT_STORE.get(key, {})
    })

ratings = {t: {"atk": round(float(pred.atk[pred.idx[t]]), 4), "def": round(float(pred.dfn[pred.idx[t]]), 4)}
           for t in pred.idx if t != "Other"}
data = {
 "competition": "FIFA World Cup 2026",
 "stage": "Group stage (remaining fixtures)",
 "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
 "model": {"type": "Dixon-Coles (joint MLE, partial pooling, totals-recalibrated)", "rho": RHO,
           "home_adv": round(float(ha), 4), "fit_through": (CUTOFF - pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
           "total_cal": {"shrink": CAL_ST, "center": CAL_TBAR},
           "data": "real international results (martj42), time-weighted joint Dixon-Coles MLE, partial pooling, no leakage"},
 "fixtures": fixtures, "ratings": ratings,
}
json.dump(data, open("app_data.json", "w"), indent=1)
print(f"fixtures: {len(fixtures)}  teams rated: {len(ratings)}")
print("with odds:", sum(1 for f in fixtures if f['odds']))
