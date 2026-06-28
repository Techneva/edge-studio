"""Fit strengths + export all fixtures (group + knockout rounds) as JSON for the app.

Group fixtures come from results.csv (unplayed WC games in the group window). Knockout
fixtures come from knockout.json (added round-by-round as the bracket is confirmed). Every
fixture carries a "stage" field; data["stages"] lists the stages present (drives the app's
stage selector). Strengths use the shared dc_fit (joint Dixon-Coles, partial pooling),
xG is totals-recalibrated, and per-fixture xG uncertainty (xgse) is shipped for the
edge-confidence filter.
"""
import numpy as np, pandas as pd, json, os as _os
import dc_fit

CUTOFF = pd.Timestamp(pd.Timestamp.now().date())
HALF_LIFE_DAYS = 547; MIN_MATCHES = 10

RAW = pd.read_csv("results.csv", parse_dates=["date"])
RAW_played = RAW.dropna(subset=["home_score", "away_score"]).copy()
pred, ok, ntrain = dc_fit.fit(RAW_played, CUTOFF, half_life=HALF_LIFE_DAYS,
                              min_matches=MIN_MATCHES, mode="dc", pool="shrink")
RHO = round(float(pred.rho), 4); ha = pred.ha
print(f"fit ok={ok} home_adv={ha:.3f} rho={RHO} teams={len(pred.idx)} train={ntrain}")

CAL_ST = 0.65; CAL_TBAR = 2.68; K_SE = 0.7   # totals recalibration + xG-uncertainty scale


def xg(home, away, neutral):
    lam, mu = pred.xg(home, away, neutral)
    S, T = lam - mu, lam + mu
    Tp = CAL_TBAR + CAL_ST * (T - CAL_TBAR)
    return round(max((Tp + S) / 2, 0.05), 3), round(max((Tp - S) / 2, 0.05), 3)


def _load(p):
    if _os.path.exists(p):
        try: return json.load(open(p))
        except Exception: return {}
    return {}


ODDS_STORE = _load("app_odds.json"); CS_STORE = _load("cs_odds.json"); MKT_STORE = _load("market_odds.json")


def make_fixture(home, away, neutral, date, venue, stage):
    lam, mu = xg(home, away, neutral); key = f"{home}|{away}"
    return {"date": date, "home": home, "away": away, "neutral": bool(neutral), "venue": venue,
            "home_xg": lam, "away_xg": mu, "stage": stage,
            "xgse": round(pred.xg_logse(home, away, K_SE), 4),
            "odds": ODDS_STORE.get(key), "cs_odds": CS_STORE.get(key, {}), "mkt": MKT_STORE.get(key, {})}


# --- group-stage fixtures (unplayed WC games in the group window) ---
wc = RAW.copy(); wc["date"] = pd.to_datetime(wc["date"])
wc = wc[wc.tournament.str.contains("World Cup", case=False, na=False)]
rem = wc[(wc.home_score.isna()) & (wc.date >= pd.Timestamp("2026-06-11")) & (wc.date <= pd.Timestamp("2026-06-28"))].sort_values(["date", "home_team"])
fixtures = []
for _, r in rem.iterrows():
    neu = str(r.neutral).upper() == "TRUE"
    venue = f"{r.get('city','')}, {r.get('country','')}".strip(", ")
    fixtures.append(make_fixture(r.home_team, r.away_team, neu, r.date.strftime("%Y-%m-%d"), venue, "Group stage"))

# --- knockout-stage fixtures (from knockout.json, added round-by-round) ---
KO = _load("knockout.json"); order = KO.get("order", ["Group stage"])
for stage in order:
    if stage == "Group stage":
        continue
    for m in KO.get("rounds", {}).get(stage, []):
        fixtures.append(make_fixture(m["home"], m["away"], m.get("neutral", True), m["date"], m.get("venue", ""), stage))

stages = [s for s in order if any(f["stage"] == s for f in fixtures)]

ratings = {t: {"atk": round(float(pred.atk[pred.idx[t]]), 4), "def": round(float(pred.dfn[pred.idx[t]]), 4)}
           for t in pred.idx if t != "Other"}
data = {
 "competition": "FIFA World Cup 2026", "stage": "All stages",
 "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
 "model": {"type": "Dixon-Coles (joint MLE, partial pooling, totals-recalibrated)", "rho": RHO,
           "home_adv": round(float(ha), 4), "fit_through": (CUTOFF - pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
           "total_cal": {"shrink": CAL_ST, "center": CAL_TBAR},
           "data": "real international results (martj42), time-weighted joint Dixon-Coles MLE, partial pooling, no leakage"},
 "stages": stages, "fixtures": fixtures, "ratings": ratings,
}
json.dump(data, open("app_data.json", "w"), indent=1)
print(f"fixtures: {len(fixtures)} | stages: {stages} | with odds: {sum(1 for f in fixtures if f['odds'])}")
