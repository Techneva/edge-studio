"""
World Cup 2026 betting model — v2
=================================
Implements the upgraded pipeline derived from:
  - Sumpter, *Soccermatics*            -> Poisson goal model + correct-score matrix
  - Dixon & Coles (1997)               -> low-score / draw correction (rho)
  - Buchdahl, *Fixed Odds Sports Betting* -> de-vigging market odds to a fair line
  - Buchdahl, *Squares & Sharps*       -> favourite-longshot bias, CLV as the KPI
  - Kelly criterion                    -> stake sizing from computed edge

Everything is a probability/strategy illustration, NOT betting advice.
The bookmaker margin is in every price; this manages variance, not edge.
"""

import math, json, os
from dataclasses import dataclass, field

MAXG = 10            # truncate the scoreline grid at 10-10 (captures ~100% mass)
RHO = -0.10          # Dixon-Coles low-score correction (EPL fit ~ -0.08..-0.13)
KELLY_FRACTION = 0.25  # quarter-Kelly: standard hedge against model error
BANKROLL = 1000.0    # notional units for stake sizing
MIN_EDGE = 0.02      # only stake when model prob beats fair prob by >= 2 pts


# ----------------------------------------------------------------------------
# 1.  POISSON + DIXON-COLES SCORELINE ENGINE  (Soccermatics + Dixon-Coles)
# ----------------------------------------------------------------------------
def poisson_pmf(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)


def dc_tau(x, y, lam, mu, rho):
    """Dixon-Coles low-score correction factor for the 4 low scorelines."""
    if x == 0 and y == 0:
        return 1.0 - lam * mu * rho
    if x == 0 and y == 1:
        return 1.0 + lam * rho
    if x == 1 and y == 0:
        return 1.0 + mu * rho
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(home_xg, away_xg, rho=RHO):
    """Return dict {(h,a): prob} over the scoreline grid, normalised to 1."""
    m = {}
    total = 0.0
    for h in range(MAXG + 1):
        for a in range(MAXG + 1):
            p = (poisson_pmf(h, home_xg) * poisson_pmf(a, away_xg)
                 * dc_tau(h, a, home_xg, away_xg, rho))
            m[(h, a)] = p
            total += p
    return {k: v / total for k, v in m.items()}


# ----------------------------------------------------------------------------
# 2.  MARKET PROBABILITIES from the matrix
# ----------------------------------------------------------------------------
def market_probs(mat):
    home = draw = away = btts = 0.0
    over25 = 0.0
    for (h, a), p in mat.items():
        if h > a:
            home += p
        elif h == a:
            draw += p
        else:
            away += p
        if h >= 1 and a >= 1:
            btts += p
        if h + a >= 3:
            over25 += p
    return {"home": home, "draw": draw, "away": away,
            "btts_yes": btts, "btts_no": 1 - btts,
            "over25": over25, "under25": 1 - over25}


def top_scores(mat, n=6):
    return sorted(mat.items(), key=lambda kv: kv[1], reverse=True)[:n]


def double_chance(mp):
    return {"1X": mp["home"] + mp["draw"],
            "12": mp["home"] + mp["away"],
            "X2": mp["draw"] + mp["away"]}


# ----------------------------------------------------------------------------
# 3.  DE-VIGGING  (Buchdahl, Fixed Odds Sports Betting)
# ----------------------------------------------------------------------------
def devig_multiplicative(odds):
    """Simplest method: normalise raw implied probs by their sum (the overround)."""
    raw = [1 / o for o in odds]
    s = sum(raw)
    return [r / s for r in raw], s - 1  # fair probs, overround


def devig_odds_ratio(odds, tol=1e-10):
    """
    Buchdahl-favoured 'odds ratio' / differential method.  Solves for c such that
    fair_p = p / (c + (1-c)*... ) -- here we use the Shin-style OR formulation:
        fair_p_i = raw_p_i / (c - c*raw_p_i + raw_p_i)
    Applies MORE of the margin to longshots, consistent with favourite-longshot bias.
    """
    raw = [1 / o for o in odds]
    lo, hi = 0.0, 1.0  # bisection on c in (0,1]; c<1 puts extra margin on longshots
    # we parameterise margin via c>1 multiplier on log-odds; use simple bisection on a
    # scaling 'c' applied multiplicatively to true odds.  For robustness we bisect on
    # the normalisation constant of the odds-ratio transform.
    def fair_given_c(c):
        return [r / (c + r - c * r) for r in raw]
    lo, hi = 0.5, 5.0
    for _ in range(200):
        c = (lo + hi) / 2
        s = sum(fair_given_c(c))
        if s > 1:
            lo = c
        else:
            hi = c
        if abs(s - 1) < tol:
            break
    fair = fair_given_c((lo + hi) / 2)
    s = sum(fair)
    fair = [f / s for f in fair]
    return fair, sum(raw) - 1


# ----------------------------------------------------------------------------
# 4.  EV, KELLY STAKING, CLV  (Mr-Tips EV + Kelly + Buchdahl CLV)
# ----------------------------------------------------------------------------
def ev_per_unit(p, odds):
    """Expected profit per 1 unit staked at decimal `odds` with true prob `p`."""
    return p * (odds - 1) - (1 - p)


def kelly_fraction(p, odds):
    """Full-Kelly fraction of bankroll. f* = (b*p - q)/b, b = odds-1."""
    b = odds - 1
    f = (b * p - (1 - p)) / b
    return max(0.0, f)


def stake(p, odds, bankroll=BANKROLL, frac=KELLY_FRACTION):
    return round(bankroll * frac * kelly_fraction(p, odds), 2)


def clv(taken_odds, closing_fair_prob):
    """
    Closing line value: did the price you took beat the closing no-vig price?
    Positive => you beat the closing fair line (the real skill signal).
    """
    your_implied = 1 / taken_odds
    return closing_fair_prob - your_implied  # >0 means you got a better-than-fair price


# ----------------------------------------------------------------------------
# 5.  MATCH DEFINITIONS  (xG inputs are illustrative, from the thread's reads)
# ----------------------------------------------------------------------------
@dataclass
class Match:
    name: str
    home: str
    away: str
    home_xg: float
    away_xg: float
    market: dict           # market decimal odds we are pricing against
    actual: tuple = None   # (h,a) final score if known, for backtest
    xg_source: str = "hand-typed"


# Real-data expected goals fitted by fit_strengths.py (Dixon-Coles MLE on actual
# international results, no leakage). If present, they OVERRIDE the hand-typed values.
def apply_fitted_xg(matches):
    path = os.path.join(os.path.dirname(__file__), "fitted_xg.json")
    if not os.path.exists(path):
        return
    fitted = json.load(open(path))
    for m in matches:
        if m.name in fitted:
            m.home_xg = fitted[m.name]["home_xg"]
            m.away_xg = fitted[m.name]["away_xg"]
            cut = fitted[m.name].get("cutoff", "?")
            m.xg_source = f"fitted real data, OOS cutoff {cut}"


# Friday Jun 19 (settled) -- for backtest
FRIDAY = [
    Match("USA vs Australia", "USA", "AUS", 1.55, 0.75,
          {"home": 1.60, "draw": 4.33, "away": 5.00}, actual=(2, 0)),
    Match("Scotland vs Morocco", "SCO", "MAR", 0.70, 1.20,
          {"home": 5.25, "draw": 3.60, "away": 1.70}, actual=(0, 1)),
    Match("Turkey vs Paraguay", "TUR", "PAR", 1.15, 1.10,
          {"home": 2.00, "draw": 3.25, "away": 4.00}, actual=(0, 1)),
    Match("Brazil vs Haiti", "BRA", "HAI", 2.40, 0.40,
          {"home": 1.09, "draw": 13.0, "away": 26.0}, actual=(3, 0)),
]

# Saturday Jun 20 (today)
SATURDAY = [
    Match("Netherlands vs Sweden", "NED", "SWE", 1.40, 1.30,
          {"home": 1.73, "draw": 4.00, "away": 4.33}),
    Match("Germany vs Cote d'Ivoire", "GER", "CIV", 1.70, 0.85,
          {"home": 1.50, "draw": 4.50, "away": 5.75}),
    Match("Ecuador vs Curacao", "ECU", "CUW", 1.55, 0.55,
          {"home": 1.13, "draw": 9.00, "away": 19.0}),
    # Japan -190 / Draw +310 / Tunisia +600  (FanDuel three-way, neutral, Monterrey)
    Match("Japan vs Tunisia", "JPN", "TUN", 1.60, 0.56,
          {"home": 1.526, "draw": 4.10, "away": 7.00}),
]


# ----------------------------------------------------------------------------
# 6.  REPORTING
# ----------------------------------------------------------------------------
def analyse(match: Match):
    mat = score_matrix(match.home_xg, match.away_xg)
    mp = market_probs(mat)
    dc = double_chance(mp)

    # de-vig the 3-way market two ways
    odds3 = [match.market["home"], match.market["draw"], match.market["away"]]
    fair_mult, ovr = devig_multiplicative(odds3)
    fair_or, _ = devig_odds_ratio(odds3)
    fair = {"home": fair_or[0], "draw": fair_or[1], "away": fair_or[2]}

    print("=" * 74)
    print(f"{match.name}   (xG: {match.home} {match.home_xg}  {match.away} {match.away_xg}"
          f"  [{match.xg_source}])")
    print("-" * 74)
    print(f"  Market overround: {ovr*100:4.1f}%   "
          f"(de-vig: multiplicative vs odds-ratio/Buchdahl)")
    print(f"  {'Outcome':<8}{'ModelP':>8}{'MktImpl':>9}{'FairMult':>10}"
          f"{'FairOR':>9}{'Edge':>8}{'Stake':>8}")
    labels = [("home", match.home), ("draw", "Draw"), ("away", match.away)]
    for i, (key, lab) in enumerate(labels):
        modelp = mp[key]
        mkt_impl = 1 / odds3[i]
        edge = modelp - fair[key]            # model vs Buchdahl fair line
        stk = stake(modelp, odds3[i]) if edge >= MIN_EDGE else 0.0
        flag = " <= bet" if stk > 0 else ""
        print(f"  {lab:<8}{modelp:>8.3f}{mkt_impl:>9.3f}{fair_mult[i]:>10.3f}"
              f"{fair[key]:>9.3f}{edge:>+8.3f}{stk:>8.1f}{flag}")
    print(f"  Double chance (model):  1X {dc['1X']:.3f}   "
          f"12 {dc['12']:.3f}   X2 {dc['X2']:.3f}")
    print(f"  BTTS yes {mp['btts_yes']:.3f}   Over2.5 {mp['over25']:.3f}")
    print("  Most-likely scores:  " +
          "   ".join(f"{h}-{a} {p*100:4.1f}%" for (h, a), p in top_scores(mat, 6)))
    if match.actual:
        h, a = match.actual
        res = "home" if h > a else "draw" if h == a else "away"
        print(f"  ACTUAL: {h}-{a}  ({res} win)   "
              f"model gave that scoreline {mat[(h,a)]*100:.1f}%, "
              f"that outcome {mp[res]*100:.1f}%")
    return mat, mp


def raw_vs_dc_check():
    """Sanity: Dixon-Coles must lift draw / low-score probability vs raw Poisson."""
    print("\n" + "=" * 74)
    print("VERIFICATION: Dixon-Coles vs raw Poisson on a coin-flip game (1.4 vs 1.3)")
    print("-" * 74)
    raw = score_matrix(1.4, 1.3, rho=0.0)
    dc = score_matrix(1.4, 1.3, rho=RHO)
    draw_raw = sum(p for (h, a), p in raw.items() if h == a)
    draw_dc = sum(p for (h, a), p in dc.items() if h == a)
    print(f"  P(draw)  raw Poisson = {draw_raw:.4f}   Dixon-Coles = {draw_dc:.4f}"
          f"   (lift {(draw_dc-draw_raw)*100:+.2f} pts)")
    print(f"  P(1-1)   raw = {raw[(1,1)]:.4f}   DC = {dc[(1,1)]:.4f}")
    print(f"  matrix sums: raw {sum(raw.values()):.6f}  dc {sum(dc.values()):.6f}")


if __name__ == "__main__":
    apply_fitted_xg(SATURDAY)
    apply_fitted_xg(FRIDAY)
    print("\n############  SATURDAY JUN 20 — TODAY'S SLATE  ############\n")
    for m in SATURDAY:
        analyse(m)

    print("\n\n############  FRIDAY JUN 19 — BACKTEST vs ACTUALS  ############\n")
    hits = 0
    for m in FRIDAY:
        _, mp = analyse(m)
        h, a = m.actual
        res = "home" if h > a else "draw" if h == a else "away"
        fav = max(("home", "draw", "away"), key=lambda k: mp[k])
        if fav == res:
            hits += 1
    print(f"\n  Model top-pick outcome correct on {hits}/4 Friday games.")

    raw_vs_dc_check()
