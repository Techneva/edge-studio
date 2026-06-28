"""
Closing Line Value (CLV) ledger
===============================
Logs each bet's taken price vs the market's CLOSING no-vig price - the sharpest
available estimate of true probability. Per Buchdahl/Squares & Sharps, sustained
positive CLV is the real proof of edge, long before P&L is meaningful.

CLV% = taken_odds * closing_fair_prob(side) - 1
   > 0  you beat the closing line (good)
   < 0  you took a worse price than the no-vig close (paying the margin)

De-vig uses the odds-ratio (Buchdahl) method from wc_model.
"""
import csv, importlib.util, os
spec = importlib.util.spec_from_file_location("wc_model",
        os.path.join(os.path.dirname(__file__), "wc_model.py"))
wc = importlib.util.module_from_spec(spec); spec.loader.exec_module(wc)

IDX = {"home": 0, "draw": 1, "away": 2}

# ledger: each bet = taken 3-way line, the side backed, the CLOSING 3-way line
# (None if not captured), stake, and settled result (W/L/None=pending).
LEDGER = [
 # --- Friday Jun 19 (settled; closing lines were not separately captured) ---
 dict(date="2026-06-19", game="USA vs Australia",      side="away", taken=(1.60,4.33,5.00), close=None, stake=10, result="L"),
 dict(date="2026-06-19", game="Scotland vs Morocco",   side="away", taken=(5.25,3.60,1.70), close=None, stake=10, result="W"),
 dict(date="2026-06-19", game="Turkey vs Paraguay",    side="home", taken=(2.00,3.25,4.00), close=None, stake=10, result="L"),
 dict(date="2026-06-19", game="Brazil vs Haiti",       side="home", taken=(1.09,13.0,26.0), close=None, stake=10, result="W"),
 # --- Saturday Jun 20 (SETTLED: GER 2-1, ECU 0-0, NED 5-1, JPN 4-0) ---
 dict(date="2026-06-20", game="Netherlands vs Sweden", side="home", taken=(1.73,4.00,4.33), close=(1.714,3.90,4.70), stake=10, result="W"),  # NED 5-1
 dict(date="2026-06-20", game="Germany vs Ivory Coast",side="home", taken=(1.50,4.50,5.75), close=(1.50,4.60,6.00),  stake=10, result="W"),  # GER 2-1
 dict(date="2026-06-20", game="Ecuador vs Curacao",    side="home", taken=(1.13,9.00,19.0), close=(1.10,11.0,21.0),  stake=10, result="L"),  # ECU 0-0 draw
 dict(date="2026-06-20", game="Japan vs Tunisia",      side="home", taken=(1.526,4.10,7.00),close=(1.5405,4.10,7.00),stake=10, result="W"),  # JPN 4-0
 # --- Sunday Jun 21 (SETTLED: BEL 0-0 IRN, EGY 3-1 NZ, ESP 4-0 KSA, URU 2-2 CPV) ---
 dict(date="2026-06-21", game="Belgium vs Iran",       side="home", taken=(1.40,4.70,7.50),  close=(1.435,4.60,7.50),  stake=10, result="L"),  # 0-0 draw
 dict(date="2026-06-21", game="New Zealand vs Egypt",  side="away", taken=(5.90,4.00,1.588),  close=(5.75,4.00,1.629), stake=10, result="W"),  # EGY 3-1
 dict(date="2026-06-21", game="Spain vs Saudi Arabia", side="home", taken=(1.10,10.5,21.0),   close=(1.10,10.5,21.0),  stake=10, result="W"),  # ESP 4-0
 dict(date="2026-06-21", game="Uruguay vs Cape Verde", side="home", taken=(1.435,4.20,9.00),  close=(1.444,4.00,8.50), stake=10, result="L"),  # 2-2 draw
 # --- Monday Jun 22 (SETTLED: ARG 2-0 AUT, FRA 3-0 IRQ, NOR 3-2 SEN, JOR 1-2 ALG) ---
 dict(date="2026-06-22", game="Argentina vs Austria",  side="home", taken=(1.69,3.80,5.75),   close=(1.417,4.50,7.50), stake=10, result="W"),  # ARG 2-0
 dict(date="2026-06-22", game="France vs Iraq",        side="home", taken=(1.11,10.0,29.0),   close=(1.067,13.0,34.0), stake=10, result="W"),  # FRA 3-0
 dict(date="2026-06-22", game="Norway vs Senegal",     side="home", taken=(2.00,3.40,3.00),   close=(2.15,3.40,3.30),  stake=10, result="W"),  # NOR 3-2
 dict(date="2026-06-22", game="Jordan vs Algeria",     side="away", taken=(6.00,4.00,1.57),   close=(6.00,4.40,1.513), stake=10, result="W"),  # ALG 2-1
 # --- Tuesday Jun 23 (SETTLED: COL 1-0 DRC, ENG 0-0 GHA, CRO 1-0 PAN, POR 5-0 UZB) ---
 dict(date="2026-06-23", game="Colombia vs DR Congo",      side="home", taken=(1.526,4.00,7.00),  close=(1.526,4.00,7.00),  stake=10, result="W"),  # COL 1-0
 dict(date="2026-06-23", game="England vs Ghana",          side="home", taken=(1.222,6.50,13.0),  close=(1.222,6.50,13.0),  stake=10, result="L"),  # 0-0 draw
 dict(date="2026-06-23", game="Panama vs Croatia",         side="away", taken=(7.00,4.10,1.50),   close=(7.00,4.10,1.50),   stake=10, result="W"),  # CRO 1-0
 dict(date="2026-06-23", game="Portugal vs Uzbekistan",    side="home", taken=(1.20,7.00,12.0),   close=(1.20,7.00,12.0),   stake=10, result="W"),  # POR 5-0
 # --- Wednesday Jun 24 (SETTLED: BIH 3-1 QAT, SUI 2-1 CAN, MEX 3-0 CZE, MAR 4-2 HAI, BRA 3-0 SCO, RSA 1-0 KOR) ---
 dict(date="2026-06-24", game="Bosnia and Herzegovina vs Qatar", side="home", taken=(1.37,5.00,7.00),  close=(1.37,5.00,7.00),  stake=10, result="W"),  # BIH 3-1
 dict(date="2026-06-24", game="Canada vs Switzerland",           side="away", taken=(3.30,3.00,2.35),  close=(3.30,3.00,2.35),  stake=10, result="W"),  # SUI 2-1
 dict(date="2026-06-24", game="Mexico vs Czech Republic",        side="home", taken=(1.91,3.90,3.75),  close=(1.91,3.90,3.75),  stake=10, result="W"),  # MEX 3-0
 dict(date="2026-06-24", game="Morocco vs Haiti",                side="home", taken=(1.182,7.00,15.0), close=(1.182,7.00,15.0), stake=10, result="W"),  # MAR 4-2
 dict(date="2026-06-24", game="Scotland vs Brazil",              side="away", taken=(8.00,5.00,1.364), close=(8.00,5.00,1.364), stake=10, result="W"),  # BRA 3-0
 dict(date="2026-06-24", game="South Africa vs South Korea",     side="away", taken=(5.25,3.80,1.649), close=(5.25,3.80,1.649), stake=10, result="L"),  # RSA 1-0 (KOR lost)
 # --- Saturday Jun 27 (taken at near-kickoff close; ENG & CRO settled, others pending) ---
 dict(date="2026-06-27", game="Jordan vs Argentina",     side="away", taken=(17.0,7.50,1.143), close=(17.0,7.50,1.143), stake=10, result="W"),  # ARG 3-1
 dict(date="2026-06-27", game="Panama vs England",       side="away", taken=(17.0,8.00,1.143), close=(17.0,8.00,1.143), stake=10, result="W"),  # ENG 2-0
 dict(date="2026-06-27", game="Colombia vs Portugal",    side="away", taken=(3.50,3.80,1.952), close=(3.50,3.80,1.952), stake=10, result="L"),  # 0-0 draw
 dict(date="2026-06-27", game="Algeria vs Austria",      side="away", taken=(4.20,2.15,2.90),  close=(4.20,2.15,2.90),  stake=10, result="L"),  # 3-3 draw
 dict(date="2026-06-27", game="DR Congo vs Uzbekistan",  side="home", taken=(1.714,4.20,5.25), close=(1.714,4.20,5.25), stake=10, result="W"),  # DRC 3-1
 dict(date="2026-06-27", game="Croatia vs Ghana",        side="home", taken=(1.769,3.10,5.90), close=(1.769,3.10,5.90), stake=10, result="W"),  # CRO 2-1
 # --- Sunday Jun 28 (Round of 32; taken at near-kickoff close; pending) ---
 dict(date="2026-06-28", game="South Africa vs Canada",  side="away", taken=(5.50,3.50,1.714), close=(5.50,3.50,1.714), stake=10, result=None),
]

def fair_prob(three_way, side):
    fo, _ = wc.devig_odds_ratio(list(three_way))
    return fo[IDX[side]]

rows = []
for b in LEDGER:
    taken_odds = b["taken"][IDX[b["side"]]]
    if b["close"]:
        cf = fair_prob(b["close"], b["side"])
        clv = taken_odds * cf - 1.0          # CLV on odds basis
        beat = clv > 0
    else:
        cf, clv, beat = None, None, None
    pnl = (taken_odds*b["stake"] - b["stake"]) if b["result"] == "W" else \
          (-b["stake"] if b["result"] == "L" else None)
    rows.append({**b, "taken_odds": taken_odds, "close_fair": cf, "clv": clv,
                 "beat": beat, "pnl": pnl})

# write CSV
with open("clv_ledger.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date","game","side","taken_odds","close_fair_prob","CLV_pct","beat_close","result","pnl_units"])
    for r in rows:
        w.writerow([r["date"], r["game"], r["side"], f"{r['taken_odds']:.3f}",
                    "" if r["close_fair"] is None else f"{r['close_fair']:.4f}",
                    "" if r["clv"] is None else f"{r['clv']*100:.2f}",
                    "" if r["beat"] is None else ("yes" if r["beat"] else "no"),
                    r["result"] or "pending",
                    "" if r["pnl"] is None else f"{r['pnl']:.1f}"])

# summary over bets WITH a closing line
clv_rows = [r for r in rows if r["clv"] is not None]
avg = sum(r["clv"] for r in clv_rows)/len(clv_rows)
beat_rate = sum(1 for r in clv_rows if r["beat"])/len(clv_rows)
cum = sum(r["clv"] for r in clv_rows)
settled = [r for r in rows if r["pnl"] is not None]
pnl_tot = sum(r["pnl"] for r in settled); staked = sum(r["stake"] for r in settled)

hdr = f"{'date':11}{'game':26}{'side':5}{'takenO':>7}{'closeFair':>10}{'CLV%':>8}{'beat':>6}{'res':>5}"
print(hdr)
for r in rows:
    cf = "" if r["close_fair"] is None else f"{r['close_fair']*100:.1f}%"
    cv = "" if r["clv"] is None else f"{r['clv']*100:+.1f}"
    bt = "" if r["beat"] is None else ("Y" if r["beat"] else "n")
    rs = r["result"] or "-"
    print(f"{r['date']:11}{r['game'][:25]:26}{r['side']:5}{r['taken_odds']:>7.2f}{cf:>10}{cv:>8}{bt:>6}{rs:>5}")
print("-"*78)
print(f"CLV bets: {len(clv_rows)}  |  beat-close rate: {beat_rate*100:.0f}%  |  "
      f"avg CLV: {avg*100:+.2f}%  |  cumulative CLV: {cum*100:+.1f}%")
print(f"Settled P&L: staked {staked:.0f}u, net {pnl_tot:+.1f}u ({100*pnl_tot/staked:+.1f}% ROI)")

# ---- cumulative CLV chart ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
labels = [r["game"].split(" vs ")[0][:7] for r in clv_rows]
clvs = [r["clv"]*100 for r in clv_rows]
cumavg = []; s = 0
for i, c in enumerate(clvs):
    s += c; cumavg.append(s/(i+1))
fig, ax = plt.subplots(figsize=(7, 3.1))
bars = ax.bar(labels, clvs, color=["#2e7d32" if c > 0 else "#b23b3b" for c in clvs], alpha=0.75, width=0.55)
ax.plot(labels, cumavg, "o-", color="#1b2a4a", lw=2, label="running avg CLV")
ax.axhline(0, color="#888", lw=1)
ax.set_ylabel("CLV %"); ax.set_title("Closing Line Value per bet")
ax.legend(fontsize=8, loc="lower right")
for b, c in zip(bars, clvs):
    ax.text(b.get_x()+b.get_width()/2, c + (0.15 if c >= 0 else -0.35), f"{c:+.1f}", ha="center", fontsize=7.5)
plt.tight_layout(); plt.savefig("clv_chart.png", dpi=130); print("wrote clv_chart.png")
