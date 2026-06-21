"""
CLV ledger — the real edge test (market-aware)
==============================================
Per Buchdahl/Squares & Sharps, sustained positive Closing Line Value is the proof
of edge, long before P&L means anything. This tracks every bet the app recommended,
the price we TOOK, and (once captured) the CLOSING price, on ANY market.

CLV% = taken_odds / closing_odds - 1
   > 0  you took a bigger price than the close  -> you beat the market (good)
   < 0  the price shortened against you

Source of truth: clv_ledger.csv  (date, game, market, label, taken_odds, close_odds,
result[W/L/P/pending], stake). CLV and P&L are derived.

Usage:
  python clv.py seed         # (re)build ledger rows from _recs.json + SCORES below
  python clv.py close FILE   # fill closing odds from a JSON {"date|game|market": close_odds}
  python clv.py              # report: per-bet CLV + P&L, summary, chart
"""
import sys, csv, json, os

LEDGER = "clv_ledger.csv"
FIELDS = ["date", "game", "market", "label", "taken_odds", "close_odds", "result", "stake"]

# settled final scores (home_goals, away_goals)
SCORES = {
    "Ecuador|Curaçao": (0, 0),
    "Germany|Ivory Coast": (2, 1),
    "Netherlands|Sweden": (5, 1),
    "Tunisia|Japan": (0, 4),
    "Spain|Saudi Arabia": (5, 0),
}
DATES = {
    "Ecuador|Curaçao": "2026-06-20", "Germany|Ivory Coast": "2026-06-20",
    "Netherlands|Sweden": "2026-06-20", "Tunisia|Japan": "2026-06-20",
    "Spain|Saudi Arabia": "2026-06-21",
}


def settle(mkey, h, a):
    tot, diff = h + a, h - a
    if mkey in ("H",): return "W" if h > a else "L"
    if mkey in ("A",): return "W" if a > h else "L"
    if mkey in ("D",): return "W" if h == a else "L"
    if mkey == "DC1X": return "W" if h >= a else "L"
    if mkey == "DCX2": return "W" if a >= h else "L"
    if mkey == "DNBH": return "P" if h == a else ("W" if h > a else "L")
    if mkey == "DNBA": return "P" if h == a else ("W" if a > h else "L")
    if mkey == "BTTSY": return "W" if (h >= 1 and a >= 1) else "L"
    if mkey == "BTTSN": return "W" if not (h >= 1 and a >= 1) else "L"
    if mkey and mkey[0] == "O":
        try: return "W" if tot > float(mkey[1:]) else "L"
        except ValueError: pass
    if mkey and mkey[0] == "U":
        try: return "W" if tot < float(mkey[1:]) else "L"
        except ValueError: pass
    if mkey.startswith("AHH"):
        m = diff + float(mkey[3:]); return "P" if abs(m) < 1e-9 else ("W" if m > 0 else "L")
    if mkey.startswith("AHA"):
        m = -diff + float(mkey[3:]); return "P" if abs(m) < 1e-9 else ("W" if m > 0 else "L")
    if "-" in mkey and mkey.split("-")[0].lstrip("+-").isdigit():
        x, y = mkey.split("-"); return "W" if (h == int(x) and a == int(y)) else "L"
    return "pending"


def load():
    if not os.path.exists(LEDGER): return []
    rd = csv.DictReader(open(LEDGER, newline=""))
    if not rd.fieldnames or "market" not in rd.fieldnames:
        return []   # old/incompatible format -> start fresh
    return [r for r in rd if r.get("market")]


def write(rows):
    with open(LEDGER, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in FIELDS})


def seed():
    """Add the app's gated VALUE recommendations for the settled games (from _recs.json)."""
    if not os.path.exists("_recs.json"):
        print("need _recs.json (run the node extractor first)"); return
    recs = json.load(open("_recs.json"))
    rows = load()
    have = {(r["date"], r["game"], r["market"]) for r in rows}
    added = 0
    for key, (h, a) in SCORES.items():
        for b in recs.get(key, {}).get("bets", []):
            if b["kind"] != "v":  # log the model's value edges (the actual recommendations)
                continue
            date = DATES[key]; mkey = b["mkey"]
            if (date, key, mkey) in have: continue
            rows.append({"date": date, "game": key, "market": mkey, "label": b["label"],
                         "taken_odds": f"{b['odds']:.3f}", "close_odds": "",
                         "result": settle(mkey, h, a), "stake": f"{b.get('stake',1) or 1:.2f}"})
            added += 1
    write(rows); print(f"seeded {added} value-bet rows into {LEDGER} (total {len(rows)})")


def close_from(path):
    m = json.load(open(path))   # {"date|game|market": closing_odds}
    rows = load(); n = 0
    for r in rows:
        k = f"{r['date']}|{r['game']}|{r['market']}"
        if k in m and not r["close_odds"]:
            r["close_odds"] = f"{float(m[k]):.3f}"; n += 1
    write(rows); print(f"filled {n} closing prices")


def report():
    rows = load()
    if not rows: print("empty ledger — run: python clv.py seed"); return
    clv_rows, settled = [], []
    print(f"\n{'date':11}{'game':24}{'market':10}{'taken':>7}{'close':>7}{'CLV%':>8}{'res':>5}{'P/L':>8}")
    print("-" * 80)
    pnl_tot = stake_tot = 0.0
    for r in rows:
        to = float(r["taken_odds"]); st = float(r["stake"] or 0)
        co = float(r["close_odds"]) if r["close_odds"] else None
        clv = (to / co - 1) if co else None
        res = r["result"]
        pnl = (st * (to - 1)) if res == "W" else (-st if res == "L" else (0.0 if res == "P" else None))
        if clv is not None: clv_rows.append(clv)
        if pnl is not None: settled.append(pnl); pnl_tot += pnl; stake_tot += st
        print(f"{r['date']:11}{r['game'][:23]:24}{r['market']:10}{to:>7.2f}"
              f"{(co if co else 0):>7.2f}{('' if clv is None else f'{clv*100:+.1f}'):>8}"
              f"{res:>5}{('' if pnl is None else f'{pnl:+.2f}'):>8}")
    print("-" * 80)
    if clv_rows:
        beat = sum(1 for c in clv_rows if c > 0) / len(clv_rows)
        print(f"CLV: {len(clv_rows)} bets w/ close · beat-rate {beat*100:.0f}% · avg {sum(clv_rows)/len(clv_rows)*100:+.2f}% · cumulative {sum(clv_rows)*100:+.1f}%")
    else:
        print("CLV: no closing prices captured yet — fill them with `python clv.py close <json>` "
              "near kickoff to start measuring edge.")
    if settled:
        w = sum(1 for p in settled if p > 0); l = sum(1 for p in settled if p < 0)
        print(f"Record: {len(settled)} settled ({w}W-{l}L) · staked {stake_tot:.2f}u · "
              f"net {pnl_tot:+.2f}u · ROI {(pnl_tot/stake_tot*100 if stake_tot else 0):+.1f}%")
    chart(rows)


def chart(rows):
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    except Exception: return
    cum, run = [], 0.0; labels = []
    for r in rows:
        to = float(r["taken_odds"]); st = float(r["stake"] or 0); res = r["result"]
        pnl = (st * (to - 1)) if res == "W" else (-st if res == "L" else 0.0)
        if res in ("W", "L", "P"):
            run += pnl; cum.append(run); labels.append(r["game"].split("|")[0][:7] + " " + r["market"])
    if not cum: return
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    ax.plot(range(len(cum)), cum, "o-", color="#1b2a4a", lw=2)
    ax.axhline(0, color="#888", lw=1)
    ax.fill_between(range(len(cum)), cum, 0, where=[c >= 0 for c in cum], color="#2e7d32", alpha=.15)
    ax.fill_between(range(len(cum)), cum, 0, where=[c < 0 for c in cum], color="#b23b3b", alpha=.15)
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=7)
    ax.set_ylabel("cumulative P&L (u)"); ax.set_title("App value-bet record (cumulative units)")
    plt.tight_layout(); plt.savefig("clv_chart.png", dpi=130); print("wrote clv_chart.png")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "seed": seed()
    elif cmd == "close": close_from(sys.argv[2])
    else: report()
