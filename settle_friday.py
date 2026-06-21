"""Settle the same core+savers strategy on Friday's games (true out-of-sample)."""
import importlib.util, os
spec = importlib.util.spec_from_file_location("wc_model",
        os.path.join(os.path.dirname(__file__), "wc_model.py"))
wc = importlib.util.module_from_spec(spec); spec.loader.exec_module(wc)
wc.apply_fitted_xg(wc.FRIDAY)   # Friday fixtures fit on data BEFORE Jun 19

# Friday correct-score odds (thread Bet365 values)
# keyed by actual final score (home-away). away-favourite games use away-win scores.
CS_ODDS = {
 "USA vs Australia":     {"0-1":8.00,"0-2":13.0,"1-2":15.0},   # model fav = Australia (away)
 "Scotland vs Morocco":  {"0-1":6.00,"0-2":7.50,"1-2":9.50},   # model fav = Morocco (away)
 "Turkey vs Paraguay":   {"1-0":7.00,"2-1":9.50,"2-0":11.0,"3-0":15.0},
 "Brazil vs Haiti":      {"2-0":7.50,"3-0":7.00,"4-0":8.50,"1-0":11.0},
}
CORE_STAKE = 10.0
SAVER_STAKES = [4.0, 3.0, 2.0]

def build_plays(m):
    mat = wc.score_matrix(m.home_xg, m.away_xg)
    mp = wc.market_probs(mat)
    odds3 = [m.market["home"], m.market["draw"], m.market["away"]]
    fo, _ = wc.devig_odds_ratio(odds3)
    fav = "home" if mp["home"] >= mp["away"] else "away"
    fav_lab, fav_odds = (m.home, odds3[0]) if fav == "home" else (m.away, odds3[2])
    fav_edge = mp[fav] - (fo[0] if fav == "home" else fo[2])
    plays = [("CORE", f"{fav_lab} win", fav, None, fav_odds, CORE_STAKE, fav_edge)]
    cs = CS_ODDS.get(m.name, {})
    fav_scores = [((h, a), p) for (h, a), p in wc.top_scores(mat, 16)
                  if (h > a if fav == "home" else a > h)]
    used = 0
    for (h, a), p in fav_scores:
        key = f"{h}-{a}"
        if key in cs and used < len(SAVER_STAKES):
            plays.append(("SAVER", f"{fav_lab} {key}", fav, (h, a), cs[key], SAVER_STAKES[used], None))
            used += 1
    return plays, fav

print(f"{'GAME / bet':30}{'odds':>6}{'stk':>5}{'result':>8}{'return':>8}   edge")
tot_stake = tot_ret = 0.0
edge_stake = edge_ret = 0.0   # only the model-flagged (positive-edge) bets
for m in wc.FRIDAY:
    h, a = m.actual
    res = "home" if h > a else "draw" if h == a else "away"
    plays, fav = build_plays(m)
    print(f"\n{m.name}  ACTUAL {h}-{a}  (fav={fav}, fav {'WON' if fav==res else 'did NOT win'})")
    for kind, lab, side, score, odds, stake, edge in plays:
        tot_stake += stake
        if kind == "CORE":
            won = (side == res)
            ret = stake*odds if won else 0.0
            etag = f"{edge*100:+.1f}" + ("*" if edge >= wc.MIN_EDGE else "")
            if edge >= wc.MIN_EDGE:
                edge_stake += stake; edge_ret += ret
        else:
            won = (score == (h, a))
            ret = stake*odds if won else 0.0
            etag = ""
        tot_ret += ret
        print(f"  {kind:5} {lab:21}{odds:>6.2f}{stake:>5.0f}{('WIN' if won else 'lose'):>8}{ret:>8.1f}   {etag}")

print("\n" + "="*60)
print(f"ALL core+savers : staked {tot_stake:.0f}  returned {tot_ret:.1f}  "
      f"net {tot_ret-tot_stake:+.1f}  ROI {100*(tot_ret-tot_stake)/tot_stake:+.1f}%")
print(f"EDGE-ONLY cores : staked {edge_stake:.0f}  returned {edge_ret:.1f}  "
      f"net {edge_ret-edge_stake:+.1f}" + ("" if edge_stake==0 else f"  ROI {100*(edge_ret-edge_stake)/edge_stake:+.1f}%"))
