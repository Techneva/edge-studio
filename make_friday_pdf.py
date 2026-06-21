"""Settled Friday report: core+savers slip vs actual results (out-of-sample)."""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import importlib.util, os

spec = importlib.util.spec_from_file_location("wc_model",
        os.path.join(os.path.dirname(__file__), "wc_model.py"))
wc = importlib.util.module_from_spec(spec); spec.loader.exec_module(wc)
wc.apply_fitted_xg(wc.FRIDAY)

NAVY = colors.HexColor("#1b2a4a"); WIN = colors.HexColor("#2e7d32"); LOSE = colors.HexColor("#b23b3b")
LGREY = colors.HexColor("#f7f8fb"); GREENBG = colors.HexColor("#e3f1e4"); REDBG = colors.HexColor("#fbeaea")
styles = getSampleStyleSheet()
H = ParagraphStyle("H", parent=styles["Title"], textColor=NAVY, fontSize=18, spaceAfter=2)
SUB = ParagraphStyle("SUB", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#555"), leading=11)
SEC = ParagraphStyle("SEC", parent=styles["Heading2"], textColor=NAVY, fontSize=13, spaceBefore=10, spaceAfter=4)
GAME = ParagraphStyle("GAME", parent=styles["Heading3"], textColor=NAVY, fontSize=11, spaceBefore=7, spaceAfter=2)
NOTE = ParagraphStyle("NOTE", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#444"), spaceBefore=1, leading=11)
CELL = ParagraphStyle("CELL", parent=styles["Normal"], fontSize=8.4, leading=9.6)
def pct(x): return f"{x*100:.1f}%"

CS_ODDS = {
 "USA vs Australia":     {"0-1":8.00,"0-2":13.0,"1-2":15.0},
 "Scotland vs Morocco":  {"0-1":6.00,"0-2":7.50,"1-2":9.50},
 "Turkey vs Paraguay":   {"1-0":7.00,"2-1":9.50,"2-0":11.0,"3-0":15.0},
 "Brazil vs Haiti":      {"2-0":7.50,"3-0":7.00,"4-0":8.50,"1-0":11.0},
}
CORE_STAKE = 10.0; SAVER_STAKES = [4.0, 3.0, 2.0]

def build_plays(m):
    mat = wc.score_matrix(m.home_xg, m.away_xg); mp = wc.market_probs(mat)
    odds3 = [m.market["home"], m.market["draw"], m.market["away"]]
    fo, _ = wc.devig_odds_ratio(odds3)
    fav = "home" if mp["home"] >= mp["away"] else "away"
    fav_lab, fav_odds = (m.home, odds3[0]) if fav == "home" else (m.away, odds3[2])
    fav_edge = mp[fav] - (fo[0] if fav == "home" else fo[2])
    kind = "Banker" if fav_odds < 1.30 else "Core"
    plays = [(f"{kind}: {fav_lab} win", fav, None, fav_odds, CORE_STAKE, fav_edge >= wc.MIN_EDGE)]
    cs = CS_ODDS.get(m.name, {}); used = 0
    for (h, a), p in [((h, a), p) for (h, a), p in wc.top_scores(mat, 16)
                      if (h > a if fav == "home" else a > h)]:
        key = f"{h}-{a}"
        if key in cs and used < len(SAVER_STAKES):
            plays.append((f"Saver: {fav_lab} {key} ({p*100:.0f}%)", fav, (h, a), cs[key], SAVER_STAKES[used], False))
            used += 1
    return plays, fav

doc = SimpleDocTemplate("yesterday-model-report-2026-06-19.pdf", pagesize=letter,
                        topMargin=0.55*inch, bottomMargin=0.5*inch, leftMargin=0.6*inch, rightMargin=0.6*inch)
story = [
    Paragraph("World Cup 2026 - Friday Settled: Model Core+Savers vs Results", H),
    Paragraph("Friday June 19, 2026, settled against actual scores. Bets from the Dixon-Coles model "
              "fitted ONLY on matches before Jun 19 - a genuine out-of-sample test (the model never "
              "saw these results). Same core+savers structure as the Saturday slip; thread Bet365 "
              "odds. GREEN row = won, RED = lost; shaded core = model-flagged value edge. Strategy "
              "illustration - not betting advice.", SUB),
    Spacer(1, 4),
    Paragraph("1 &nbsp;&middot;&nbsp; Settled bet slip", SEC),
]

slip = [["Game (result)", "Bet", "Odds", "Stake", "Result", "Return"]]
style = [
    ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8.6),
    ("ALIGN", (2, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cdd3df")),
    ("TOPPADDING", (0, 0), (-1, -1), 3.0), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
]
r = 1; tot_s = tot_r = edge_s = edge_r = 0.0
for m in wc.FRIDAY:
    h, a = m.actual; res = "home" if h > a else "draw" if h == a else "away"
    plays, fav = build_plays(m); first = True
    glabel = f"{m.name}  ({h}-{a})"
    for item in plays:
        if item[2] is None:   # core
            lab, side, _, odds, stake, is_edge = item; won = (side == res)
            if is_edge: edge_s += stake; edge_r += (stake*odds if won else 0)
        else:                 # saver
            lab, side, score, odds, stake, is_edge = item; won = (score == (h, a))
        ret = stake*odds if won else 0.0
        tot_s += stake; tot_r += ret
        slip.append([Paragraph(glabel if first else "", CELL), Paragraph(lab, CELL),
                     f"{odds:.2f}", f"{stake:.0f}", "WIN" if won else "lose", f"{ret:.1f}"])
        bg = GREENBG if won else REDBG
        style += [("BACKGROUND", (4, r), (5, r), bg),
                  ("TEXTCOLOR", (4, r), (4, r), WIN if won else LOSE)]
        if first:
            style += [("FONTNAME", (0, r), (1, r), "Helvetica-Bold")]
            if is_edge: style += [("BOX", (1, r), (1, r), 1.1, WIN)]
        first = False; r += 1
    style += [("LINEBELOW", (0, r-1), (-1, r-1), 0.8, colors.HexColor("#9aa6bd"))]
t = Table(slip, colWidths=[1.6*inch, 2.45*inch, 0.6*inch, 0.6*inch, 0.7*inch, 0.65*inch], hAlign="LEFT")
t.setStyle(TableStyle(style)); story.append(t)

net = tot_r - tot_s
story.append(Paragraph(
    f"<b>All core+savers: staked {tot_s:.0f}u &rarr; returned {tot_r:.1f}u &rarr; "
    f"net <font color='{'#2e7d32' if net>=0 else '#b23b3b'}'>{net:+.1f}u ({100*net/tot_s:+.1f}% ROI)</font>.</b> "
    f"Model-flagged EDGE-only (the single +EV bet, Australia): staked {edge_s:.0f}u &rarr; returned "
    f"{edge_r:.0f}u &rarr; net {edge_r-edge_s:+.0f}u (-100%). The slip stayed positive only because "
    "two anchor savers landed - Morocco 0-1 and Brazil 3-0, the model's own top scorelines.", NOTE))

story.append(Paragraph("2 &nbsp;&middot;&nbsp; What it means", SEC))
for txt in [
 "<b>The model's one value bet lost.</b> Its only positive-edge flag was Australia (+18.7 pts), because the fit rates the USA weak on recent form. The USA won 2-0. On n=1 this says nothing - but it is the same USA mis-rating behind ruleset Rule 16 (distrust the model when it disagrees violently with the market).",
 "<b>It underperformed the market on outcomes.</b> The model's favourite won 2 of 4 (Morocco, Brazil); simply backing the market favourite each game would have gone 3 of 4. The whole gap is the USA game, where the model took Australia and the market was right.",
 "<b>The +5% ROI is variance, not edge.</b> Four games, carried by two correct-score longshots that each hit ~1-in-8. Drop either anchor and the day is negative. Per the ruleset, the only real verdict is closing-line value tracked over hundreds of bets.",
]:
    story.append(Paragraph(txt, NOTE)); story.append(Spacer(1, 2))

doc.build(story)
print("wrote yesterday-model-report-2026-06-19.pdf")
