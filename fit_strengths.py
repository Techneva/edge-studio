"""
Fit team attack/defence strengths from REAL international results
=================================================================
Dixon-Coles time-weighted maximum-likelihood fit on actual goals data
(martj42/international_results). Produces expected-goal rates (lambda, mu)
for each fixture.

PER-FIXTURE CUTOFF (rigorous out-of-sample): every fixture is predicted using
ONLY matches that kicked off strictly before that fixture's own date. This is
the correct setup for tracking closing-line value (CLV) going forward — no game
ever sees its own result or any later result.
"""
import numpy as np, pandas as pd
from scipy.optimize import minimize
import json

HALF_LIFE_DAYS = 547      # ~1.5y time-decay half-life
MIN_MATCHES = 10          # teams with fewer recent games -> pooled "Other" prior
RHO = -0.08               # fixed (validated ~ -0.079 EPL); tau applied at predict time

RAW = pd.read_csv("results.csv", parse_dates=["date"])
RAW = RAW.dropna(subset=["home_score", "away_score"]).copy()
RAW["home_score"] = RAW["home_score"].astype(int)
RAW["away_score"] = RAW["away_score"].astype(int)

# fixtures: (name, home, away, neutral, kickoff_date)
FIX = [
 ("USA vs Australia",        "United States", "Australia",   False, "2026-06-19"),
 ("Scotland vs Morocco",     "Scotland",      "Morocco",     True,  "2026-06-19"),
 ("Turkey vs Paraguay",      "Turkey",        "Paraguay",    True,  "2026-06-19"),
 ("Brazil vs Haiti",         "Brazil",        "Haiti",       True,  "2026-06-19"),
 ("Netherlands vs Sweden",   "Netherlands",   "Sweden",      True,  "2026-06-20"),
 ("Germany vs Cote d'Ivoire","Germany",       "Ivory Coast", True,  "2026-06-20"),
 ("Ecuador vs Curacao",      "Ecuador",       "Curaçao",     True,  "2026-06-20"),
 ("Japan vs Tunisia",        "Japan",         "Tunisia",     True,  "2026-06-20"),
]


def fit(cutoff):
    """Fit Dixon-Coles attack/defence on all matches strictly before `cutoff`."""
    cut = pd.Timestamp(cutoff)
    df = RAW[(RAW.date < cut) & (RAW.date >= pd.Timestamp("2016-01-01"))].copy()
    xi = np.log(2) / HALF_LIFE_DAYS
    df["w"] = np.exp(-xi * (cut - df["date"]).dt.days.values)

    counts = pd.concat([df.home_team, df.away_team]).value_counts()
    strong = set(counts[counts >= MIN_MATCHES].index)
    lab = lambda t: t if t in strong else "Other"
    df["H"] = df.home_team.map(lab); df["A"] = df.away_team.map(lab)
    teams = sorted(set(df.H) | set(df.A)); idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    H = df.H.map(idx).values; A = df.A.map(idx).values
    hg = df.home_score.values; ag = df.away_score.values; w = df.w.values
    nn = (~df.neutral.astype(str).str.upper().eq("TRUE")).astype(float).values

    def negll_and_grad(p):
        atk, dfn, ha = p[:n], p[n:2*n], p[2*n]
        lam = np.exp(atk[H] - dfn[A] + ha*nn); mu = np.exp(atk[A] - dfn[H])
        obj = -(w*(hg*np.log(lam) - lam + ag*np.log(mu) - mu)).sum()
        rh = w*(hg - lam); ra = w*(ag - mu)
        g_atk = np.zeros(n); g_def = np.zeros(n)
        np.add.at(g_atk, H, rh); np.add.at(g_atk, A, ra)
        np.add.at(g_def, A, -rh); np.add.at(g_def, H, -ra)
        grad = -np.concatenate([g_atk, g_def, [(rh*nn).sum()]])
        ma = atk.mean()
        obj += 1e3*ma**2 + 1e-3*(atk@atk + dfn@dfn)
        grad[:n] += 2e3*ma/n + 2e-3*atk; grad[n:2*n] += 2e-3*dfn
        return obj, grad

    x0 = np.concatenate([np.zeros(n), np.zeros(n), [0.25]])
    res = minimize(negll_and_grad, x0, jac=True, method="L-BFGS-B",
                   bounds=[(-3, 3)]*(2*n) + [(0, 1)], options={"maxiter": 500})
    atk, dfn, ha = res.x[:n], res.x[n:2*n], res.x[2*n]
    return atk, dfn, ha, idx, lab, res.success, len(df)


def xg(atk, dfn, ha, idx, lab, home, away, neutral):
    he = 0.0 if neutral else ha
    lam = np.exp(atk[idx[lab(home)]] - dfn[idx[lab(away)]] + he)
    mu  = np.exp(atk[idx[lab(away)]] - dfn[idx[lab(home)]])
    return round(float(lam), 3), round(float(mu), 3)


# fit once per distinct cutoff, then predict that cutoff's fixtures
cutoffs = sorted(set(f[4] for f in FIX))
fits = {}
for c in cutoffs:
    atk, dfn, ha, idx, lab, ok, nrows = fit(c)
    fits[c] = (atk, dfn, ha, idx, lab)
    print(f"cutoff {c}: fit ok={ok}  home_adv={ha:.3f}  matches_used={nrows}")

out = {}
print(f"\n{'fixture':28}{'cutoff':>12}{'home_xG':>9}{'away_xG':>9}")
for name, h, a, neu, date in FIX:
    atk, dfn, ha, idx, lab = fits[date]
    lam, mu = xg(atk, dfn, ha, idx, lab, h, a, neu)
    out[name] = {"home_xg": lam, "away_xg": mu, "home": h, "away": a,
                 "neutral": neu, "cutoff": date, "out_of_sample": True}
    print(f"{name:28}{date:>12}{lam:>9.2f}{mu:>9.2f}")

json.dump(out, open("fitted_xg.json", "w"), indent=2)
print("\nwrote fitted_xg.json (per-fixture out-of-sample cutoffs)")
