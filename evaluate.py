"""
Walk-forward out-of-sample evaluation harness
==============================================
The referee for every model change. For each match in the evaluation window we
predict using a fit trained ONLY on data strictly before that match's snapshot
(no leakage), then score the probabilities against what actually happened.

Metrics:
  - 1X2 multiclass Brier score  (lower = better; perfect 0, random ~0.66)
  - 1X2 log-loss                (lower = better)
  - Brier Skill Score vs climatology (share-of-outcomes baseline; >0 = beats it)
  - Reliability curve + Expected Calibration Error (ECE) for pooled 1X2 probs
  - Over/Under 2.5 and BTTS: Brier + log-loss

Usage:
  python evaluate.py                 # shipped model (poisson / hard pooling)
  python evaluate.py dc shrink       # improved model (joint DC / partial pooling)
  python evaluate.py dc shrink mytag # custom output tag
Run two tags then `python evaluate.py compare A B` to diff them.
"""
import sys, json
import numpy as np, pandas as pd
import dc_fit, wc_model

EVAL_START = "2023-01-01"
EVAL_END   = "2025-12-31"
STEP_DAYS  = 60
RHO        = -0.08
CAL_ST     = 0.65      # totals recalibration (match production build_data); set 1.0 to disable
CAL_TBAR   = 2.68


def _cal(lam, mu):
    S, T = lam - mu, lam + mu
    Tp = CAL_TBAR + CAL_ST * (T - CAL_TBAR)
    return max((Tp + S) / 2, 0.05), max((Tp - S) / 2, 0.05)


def predict_block(RAW, mode, pool):
    RAW = RAW[RAW.date <= pd.Timestamp(EVAL_END)]
    snaps = pd.date_range(EVAL_START, EVAL_END, freq=f"{STEP_DAYS}D")
    rows = []
    for s in snaps:
        pred, ok, ntrain = dc_fit.fit(RAW, s, rho=RHO, mode=mode, pool=pool)
        rho = pred.rho
        block = RAW[(RAW.date >= s) & (RAW.date < s + pd.Timedelta(days=STEP_DAYS))]
        for _, r in block.iterrows():
            if not (pred.known(r.home_team) and pred.known(r.away_team)):
                continue                       # only score teams the model actually rates
            neu = str(r.neutral).upper() == "TRUE"
            lam, mu = pred.xg(r.home_team, r.away_team, neu)
            lam, mu = _cal(lam, mu)
            mat = wc_model.score_matrix(lam, mu, rho)
            mp = wc_model.market_probs(mat)
            hg, ag = int(r.home_score), int(r.away_score)
            outcome = 0 if hg > ag else 1 if hg == ag else 2
            rows.append(dict(date=r.date, home=r.home_team, away=r.away_team,
                             p_home=mp["home"], p_draw=mp["draw"], p_away=mp["away"],
                             outcome=outcome,
                             p_over=mp["over25"], over=int(hg + ag >= 3),
                             p_btts=mp["btts_yes"], btts=int(hg >= 1 and ag >= 1)))
        print(f"  snapshot {s.date()} fit_ok={ok} rho={rho:+.3f} train={ntrain} cum_matches={len(rows)}")
    return pd.DataFrame(rows)


def metrics(df):
    P = df[["p_home", "p_draw", "p_away"]].values
    y = df["outcome"].values
    Y = np.zeros_like(P); Y[np.arange(len(y)), y] = 1
    brier = ((P - Y) ** 2).sum(axis=1).mean()
    pa = np.clip(P[np.arange(len(y)), y], 1e-9, 1)
    logloss = -np.log(pa).mean()
    # climatology baseline = empirical outcome shares
    base = Y.mean(axis=0)
    brier_base = ((base[None, :] - Y) ** 2).sum(axis=1).mean()
    bss = 1 - brier / brier_base
    # reliability over pooled per-class probabilities
    flatP = P.reshape(-1); flatY = Y.reshape(-1)
    bins = np.linspace(0, 1, 11)
    bi = np.clip(np.digitize(flatP, bins) - 1, 0, 9)
    rel = []
    ece = 0.0
    for b in range(10):
        m = bi == b
        if m.sum() == 0:
            rel.append((np.nan, np.nan, 0)); continue
        mp_, ef = flatP[m].mean(), flatY[m].mean()
        rel.append((mp_, ef, int(m.sum())))
        ece += m.sum() / len(flatP) * abs(mp_ - ef)

    def binm(p, yv):
        p = np.clip(p, 1e-9, 1 - 1e-9)
        return ((p - yv) ** 2).mean(), -(yv * np.log(p) + (1 - yv) * np.log(1 - p)).mean()
    ou_b, ou_l = binm(df.p_over.values, df.over.values)
    bt_b, bt_l = binm(df.p_btts.values, df.btts.values)
    return dict(n=len(df), brier=brier, logloss=logloss, brier_base=brier_base,
                bss=bss, ece=ece, rel=rel,
                ou_brier=ou_b, ou_logloss=ou_l, ou_rate=df.over.mean(), ou_pred=df.p_over.mean(),
                bt_brier=bt_b, bt_logloss=bt_l, bt_rate=df.btts.mean(), bt_pred=df.p_btts.mean(),
                shares=base.tolist())


def reliability_png(rel, path, title):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print("  (matplotlib unavailable, skipping plot:", e, ")"); return
    xs = [r[0] for r in rel]; ys = [r[1] for r in rel]; ns = [r[2] for r in rel]
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.plot([0, 1], [0, 1], "--", color="#999", lw=1, label="perfect")
    ax.plot(xs, ys, "o-", color="#2f6df0", lw=2, label="model")
    for x, yv, nb in zip(xs, ys, ns):
        if nb and not np.isnan(x):
            ax.annotate(str(nb), (x, yv), fontsize=7, color="#555",
                        xytext=(0, 5), textcoords="offset points", ha="center")
    ax.set_xlabel("predicted probability"); ax.set_ylabel("observed frequency")
    ax.set_title(title); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.legend(); ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(path, dpi=130); print("  wrote", path)


def report(tag, m):
    L = []
    L.append(f"# Model evaluation — `{tag}`\n")
    L.append(f"Walk-forward out-of-sample, {EVAL_START} → {EVAL_END}, "
             f"refit every {STEP_DAYS} days. **{m['n']} matches** scored "
             f"(both teams rated).\n")
    L.append("## 1X2 (match result)\n")
    L.append(f"| metric | value | reference |\n|---|---|---|")
    L.append(f"| Multiclass Brier | **{m['brier']:.4f}** | climatology {m['brier_base']:.4f} · perfect 0 |")
    L.append(f"| Brier skill score | **{m['bss']*100:+.1f}%** | >0 beats outcome-share baseline |")
    L.append(f"| Log-loss | **{m['logloss']:.4f}** | lower better |")
    L.append(f"| Calibration error (ECE) | **{m['ece']*100:.2f}%** | 0 = perfectly calibrated |")
    L.append(f"\nOutcome base rates (H/D/A): {m['shares'][0]:.3f} / {m['shares'][1]:.3f} / {m['shares'][2]:.3f}\n")
    L.append("### Reliability (pooled 1X2 probabilities)\n")
    L.append("| predicted bin | mean pred | observed | n |\n|---|---|---|---|")
    for lo, (mp_, ef, nb) in zip(np.arange(0, 1, .1), m["rel"]):
        if nb:
            L.append(f"| {lo:.1f}–{lo+.1:.1f} | {mp_:.3f} | {ef:.3f} | {nb} |")
    L.append("\n## Other markets\n")
    L.append("| market | Brier | log-loss | pred rate | actual rate |\n|---|---|---|---|---|")
    L.append(f"| Over 2.5 | {m['ou_brier']:.4f} | {m['ou_logloss']:.4f} | {m['ou_pred']:.3f} | {m['ou_rate']:.3f} |")
    L.append(f"| BTTS yes | {m['bt_brier']:.4f} | {m['bt_logloss']:.4f} | {m['bt_pred']:.3f} | {m['bt_rate']:.3f} |")
    L.append("\n*CLV (closing-line value) is the real edge test but needs historical "
             "closing odds, which this dataset lacks — it is tracked going forward in "
             "`clv_ledger.csv`. These metrics measure probabilistic accuracy & calibration.*\n")
    return "\n".join(L)


def run(mode, pool, tag):
    print(f"Evaluating mode={mode} pool={pool} -> tag={tag}")
    RAW = dc_fit.load_results()
    df = predict_block(RAW, mode, pool)
    df.to_csv(f"eval_pred_{tag}.csv", index=False)
    m = metrics(df)
    print(f"\n  Brier {m['brier']:.4f} | BSS {m['bss']*100:+.1f}% | logloss {m['logloss']:.4f} | ECE {m['ece']*100:.2f}%")
    open(f"model-eval-{tag}.md", "w").write(report(tag, m))
    reliability_png(m["rel"], f"eval_reliability_{tag}.png", f"Reliability — {tag}")
    json.dump({k: v for k, v in m.items() if k != "rel"}, open(f"eval_metrics_{tag}.json", "w"), indent=1)
    print(f"  wrote model-eval-{tag}.md, eval_metrics_{tag}.json")
    return m


def compare(a, b):
    ma = json.load(open(f"eval_metrics_{a}.json")); mb = json.load(open(f"eval_metrics_{b}.json"))
    print(f"\n{'metric':16}{a:>14}{b:>14}{'Δ':>12}")
    for k, lab in [("brier", "Brier"), ("logloss", "Log-loss"), ("bss", "Brier-skill"),
                   ("ece", "ECE"), ("ou_logloss", "O/U logloss"), ("bt_logloss", "BTTS logloss")]:
        d = mb[k] - ma[k]
        print(f"{lab:16}{ma[k]:>14.4f}{mb[k]:>14.4f}{d:>+12.4f}")
    print("\n(Brier/log-loss/ECE: lower is better. Brier-skill: higher is better.)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "compare":
        compare(args[1], args[2])
    else:
        mode = args[0] if len(args) > 0 else "poisson"
        pool = args[1] if len(args) > 1 else "hard"
        tag = args[2] if len(args) > 2 else f"{mode}_{pool}"
        run(mode, pool, tag)
