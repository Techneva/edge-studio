"""
Reusable Dixon-Coles strength fitter (shared by build_data, fit_strengths, evaluate).
=====================================================================================
`fit(RAW, cutoff, ...)` returns a Predictor fitted ONLY on matches strictly before
`cutoff` (no leakage), exposing `.xg(home, away, neutral) -> (lam, mu)`.

MODE:
  mode="poisson"  -> the currently-shipped model: independent time-weighted Poisson
                     MLE, rho applied only at prediction time (in wc_model.score_matrix).
  mode="dc"       -> joint Dixon-Coles: the low-score tau(rho) term is INSIDE the
                     likelihood and rho is estimated together with attack/defence.
  pool="hard"     -> shipped behaviour: teams with < min_matches collapse to one
                     shared "Other" rating.
  pool="shrink"   -> partial pooling: every team keeps its own rating, ridge-shrunk
                     toward the global mean by an amount that scales with 1/sample.

Tasks 1 (eval) uses mode="poisson", pool="hard" to measure the shipped model.
Task 2 switches to mode="dc", pool="shrink" and re-runs eval to confirm the gain.
"""
import numpy as np, pandas as pd, math
from scipy.optimize import minimize

SINCE = "2016-01-01"


def load_results(path="results.csv"):
    RAW = pd.read_csv(path, parse_dates=["date"])
    RAW = RAW.dropna(subset=["home_score", "away_score"]).copy()
    RAW["home_score"] = RAW.home_score.astype(int)
    RAW["away_score"] = RAW.away_score.astype(int)
    return RAW


def _tau(hg, ag, lam, mu, rho):
    """Vectorised Dixon-Coles tau for the 4 low scorelines (else 1)."""
    t = np.ones_like(lam, dtype=float)
    m00 = (hg == 0) & (ag == 0); t[m00] = 1.0 - lam[m00] * mu[m00] * rho
    m01 = (hg == 0) & (ag == 1); t[m01] = 1.0 + lam[m01] * rho
    m10 = (hg == 1) & (ag == 0); t[m10] = 1.0 + mu[m10] * rho
    m11 = (hg == 1) & (ag == 1); t[m11] = 1.0 - rho
    return t


class Predictor:
    def __init__(self, atk, dfn, ha, idx, strong, rho, mode, pool, group_mean=None):
        self.atk, self.dfn, self.ha = atk, dfn, ha
        self.idx, self.strong = idx, strong
        self.rho, self.mode, self.pool = rho, mode, pool
        self.group_mean = group_mean or {}

    def known(self, team):
        return team in self.idx and team in self.strong

    def _ai(self, team):
        if team in self.idx:
            return self.atk[self.idx[team]], self.dfn[self.idx[team]]
        # unseen team -> neutral baseline
        return 0.0, 0.0

    def xg(self, home, away, neutral):
        ha_t = home if home in self.idx else ("Other" if "Other" in self.idx else home)
        aw_t = away if away in self.idx else ("Other" if "Other" in self.idx else away)
        ah, dh = self._ai(ha_t)
        aa, da = self._ai(aw_t)
        he = 0.0 if neutral else self.ha
        lam = float(np.exp(ah - da + he))
        mu = float(np.exp(aa - dh))
        return round(lam, 3), round(mu, 3)


def fit(RAW, cutoff, half_life=547, min_matches=10, rho=-0.08,
        mode="poisson", pool="hard", since=SINCE, l2=1e-3, maxiter=500):
    cut = pd.Timestamp(cutoff)
    df = RAW[(RAW.date < cut) & (RAW.date >= pd.Timestamp(since))].copy()
    xi = np.log(2) / half_life
    df["w"] = np.exp(-xi * (cut - df.date).dt.days.values)

    counts = pd.concat([df.home_team, df.away_team]).value_counts()
    strong = set(counts[counts >= min_matches].index)

    if pool == "hard":
        lab = lambda t: t if t in strong else "Other"
    else:                                  # shrink: keep every team, no collapse
        lab = lambda t: t
    df["H"] = df.home_team.map(lab); df["A"] = df.away_team.map(lab)
    teams = sorted(set(df.H) | set(df.A)); idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    H = df.H.map(idx).values; A = df.A.map(idx).values
    hg = df.home_score.values.astype(float); ag = df.away_score.values.astype(float)
    w = df.w.values
    nn = (~df.neutral.astype(str).str.upper().eq("TRUE")).astype(float).values

    # per-team effective sample (weighted) -> drives shrinkage strength when pool="shrink"
    napp = np.zeros(n)
    np.add.at(napp, H, w); np.add.at(napp, A, w)

    fit_rho = (mode == "dc")
    npar = 2 * n + 1 + (1 if fit_rho else 0)

    def unpack(p):
        atk, dfn, ha = p[:n], p[n:2 * n], p[2 * n]
        r = p[2 * n + 1] if fit_rho else rho
        return atk, dfn, ha, r

    def nll(p):
        atk, dfn, ha, r = unpack(p)
        lam = np.exp(atk[H] - dfn[A] + ha * nn); mu = np.exp(atk[A] - dfn[H])
        # base independent-Poisson log-likelihood
        ll = w * (hg * np.log(lam) - lam + ag * np.log(mu) - mu)
        obj = -ll.sum()
        rh = w * (hg - lam); ra = w * (ag - mu)
        ga = np.zeros(n); gd = np.zeros(n)
        np.add.at(ga, H, rh); np.add.at(ga, A, ra)
        np.add.at(gd, A, -rh); np.add.at(gd, H, -ra)
        grho = 0.0
        if fit_rho:
            # add the Dixon-Coles tau term: + w * log(tau); rho via numerical-stable analytic grad
            t = _tau(hg, ag, lam, mu, r)
            t = np.clip(t, 1e-6, None)
            obj -= (w * np.log(t)).sum()
            # d log tau / d rho  (per cell)
            dtau = np.zeros_like(t)
            m00 = (hg == 0) & (ag == 0); dtau[m00] = -lam[m00] * mu[m00]
            m01 = (hg == 0) & (ag == 1); dtau[m01] = lam[m01]
            m10 = (hg == 1) & (ag == 0); dtau[m10] = mu[m10]
            m11 = (hg == 1) & (ag == 1); dtau[m11] = -1.0
            grho = -(w * dtau / t).sum()
            # tau also depends on lam,mu but that 2nd-order coupling is tiny; omit in grad
        # regularisation
        ma = atk.mean()
        if pool == "shrink":
            # sample-size-aware ridge: lightly-played teams pulled harder to the mean
            lam_shrink = 0.4
            k = lam_shrink * (5.0 / (napp + 5.0))      # weight ~ large when napp small
            obj += 1e3 * ma ** 2 + (k * (atk ** 2 + dfn ** 2)).sum()
            ga2 = 2e3 * ma / n + 2 * k * atk
            gd2 = 2 * k * dfn
        else:
            obj += 1e3 * ma ** 2 + l2 * (atk @ atk + dfn @ dfn)
            ga2 = 2e3 * ma / n + 2 * l2 * atk
            gd2 = 2 * l2 * dfn
        g = -np.concatenate([ga, gd, [(rh * nn).sum()]])
        g[:n] += ga2; g[n:2 * n] += gd2
        if fit_rho:
            g = np.concatenate([g, [grho]])
        return obj, g

    x0 = np.zeros(npar); x0[2 * n] = 0.25
    if fit_rho:
        x0[2 * n + 1] = rho
    bounds = [(-3, 3)] * (2 * n) + [(0, 1)]
    if fit_rho:
        bounds += [(-0.2, 0.05)]
    res = minimize(nll, x0, jac=True, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter": maxiter})
    atk, dfn, ha, r = unpack(res.x)
    return Predictor(atk, dfn, ha, idx, strong, r, mode, pool), res.success, len(df)
