"""Today PDF: full core+savers bet slip on EVERY game, then model explanations."""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle)
import importlib.util, os

spec = importlib.util.spec_from_file_location("wc_model",
        os.path.join(os.path.dirname(__file__), "wc_model.py"))
wc = importlib.util.module_from_spec(spec); spec.loader.exec_module(wc)
wc.apply_fitted_xg(wc.SATURDAY)

NAVY = colors.HexColor("#1b2a4a"); ACCENT = colors.HexColor("#2e7d32")
LGREY = colors.HexColor("#f7f8fb"); MUTE = colors.HexColor("#777777")
styles = getSampleStyleSheet()
H = ParagraphStyle("H", parent=styles["Title"], textColor=NAVY, fontSize=18, spaceAfter=2)
SUB = ParagraphStyle("SUB", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#555"), leading=11)
SEC = ParagraphStyle("SEC", parent=styles["Heading2"], textColor=NAVY, fontSize=13, spaceBefore=10, spaceAfter=4)
GAME = ParagraphStyle("GAME", parent=styles["Heading3"], textColor=NAVY, fontSize=11.5, spaceBefore=8, spaceAfter=2)
NOTE = ParagraphStyle("NOTE", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#444"), spaceBefore=1, leading=11)
CELL = ParagraphStyle("CELL", parent=styles["Normal"], fontSize=8.4, leading=9.6)

def pct(x): return f"{x*100:.1f}%"

# indicative correct-score decimal odds (thread Bet365 where available; * = estimated)
CS_ODDS = {
 "Netherlands vs Sweden": {"2-1":9.00,"1-0":8.50,"2-0":9.50,"3-1":15.0,"3-0":13.0},
 "Germany vs Cote d'Ivoire": {"1-0":9.50,"2-0":9.00,"2-1":8.50,"3-0":13.0,"3-1":17.0},
 "Ecuador vs Curacao": {"1-0":7.50,"2-0":5.50,"3-0":6.00,"4-0":9.00,"2-1":13.0},
 "Japan vs Tunisia": {"1-0":7.00,"2-0":7.50,"3-0":11.0,"2-1":12.0,"0-0":8.00},
}
CORE_STAKE = 10.0           # banker/core stake per game
SAVER_STAKES = [4.0, 3.0, 2.0]  # anchor, 2nd, 3rd most-likely favourite scoreline

def analyse(match):
    mat = wc.score_matrix(match.home_xg, match.away_xg)
    mp = wc.market_probs(mat)
    odds3 = [match.market["home"], match.market["draw"], match.market["away"]]
    _, ovr = wc.devig_multiplicative(odds3)
    fo, _ = wc.devig_odds_ratio(odds3)
    fair = {"home": fo[0], "draw": fo[1], "away": fo[2]}
    dc = wc.double_chance(mp)
    rows = []
    for i, (k, lab) in enumerate([("home", match.home), ("draw", "Draw"), ("away", match.away)]):
        edge = mp[k] - fair[k]
        stk = wc.stake(mp[k], odds3[i]) if edge >= wc.MIN_EDGE else 0.0
        rows.append([lab, f"{odds3[i]:.2f}", pct(mp[k]), pct(fair[k]),
                     f"{edge*100:+.1f}", (f"{stk:.0f}" if stk > 0 else "-")])
    scores = "   ".join(f"{h}-{a} {p*100:.0f}%" for (h, a), p in wc.top_scores(mat, 4))
    return mat, mp, dc, ovr, rows, scores, fair, odds3

def build_plays(match):
    """Core favourite moneyline + top-3 favourite-winning correct-score savers."""
    mat = wc.score_matrix(match.home_xg, match.away_xg)
    mp = wc.market_probs(mat)
    odds3 = [match.market["home"], match.market["draw"], match.market["away"]]
    fo, _ = wc.devig_odds_ratio(odds3)
    fav = "home" if mp["home"] >= mp["away"] else "away"
    fav_lab, fav_odds = (match.home, odds3[0]) if fav == "home" else (match.away, odds3[2])
    fav_edge = mp[fav] - (fo[0] if fav == "home" else fo[2])
    kind = "Banker" if fav_odds < 1.30 else "Core"
    plays = [(f"{kind}: {fav_lab} win", fav_odds, CORE_STAKE, fav_edge >= wc.MIN_EDGE)]
    # savers: model's top scorelines that are favourite WINS, with a listed price
    cs = CS_ODDS.get(match.name, {})
    fav_scores = [((h, a), p) for (h, a), p in wc.top_scores(mat, 16)
                  if (h > a if fav == "home" else a > h)]
    used = 0
    for (h, a), p in fav_scores:
        key = f"{h}-{a}"
        if key in cs and used < len(SAVER_STAKES):
            plays.append((f"Saver: {fav_lab} {key}  ({p*100:.0f}%)", cs[key],
                          SAVER_STAKES[used], False))
            used += 1
    return plays

doc = SimpleDocTemplate("today-4games-model.pdf", pagesize=letter,
                        topMargin=0.55*inch, bottomMargin=0.5*inch,
                        leftMargin=0.6*inch, rightMargin=0.6*inch)
story = [
    Paragraph("World Cup 2026 - Today's Bets &amp; Model Read", H),
    Paragraph("Saturday June 20, 2026 (Japan v Tunisia is the late ~12am ET / Jun 21 kickoff). "
              "Core-and-savers slip on every game: a banker/core on the favourite plus the model's "
              "most-likely correct scores. Stakes in units; correct-score prices indicative. "
              "GREEN = the model rates the core a genuine edge vs the de-vigged fair line; other "
              "cores are taken for coverage despite no measured edge. Strategy illustration - not "
              "betting advice.", SUB),
    Spacer(1, 4),
    Paragraph("1 &nbsp;&middot;&nbsp; Today's Bets (core + savers, every game)", SEC),
]

slip = [["Game", "Bet", "Odds", "Stake (u)", "Returns"]]
style = [
    ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8.7),
    ("ALIGN", (2, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cdd3df")),
    ("TOPPADDING", (0, 0), (-1, -1), 3.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
]
r = 1; total = 0.0
for gi, m in enumerate(wc.SATURDAY):
    plays = build_plays(m); first = True
    for bet, odds, stake, is_edge in plays:
        total += stake
        slip.append([Paragraph(m.name if first else "", CELL), Paragraph(bet, CELL),
                     f"{odds:.2f}", f"{stake:.0f}", f"{stake*odds:.1f}"])
        if first:                      # core/banker row
            if is_edge:
                style += [("BACKGROUND", (0, r), (-1, r), colors.HexColor("#e3f1e4")),
                          ("FONTNAME", (0, r), (1, r), "Helvetica-Bold"),
                          ("TEXTCOLOR", (4, r), (4, r), ACCENT)]
            else:
                style += [("FONTNAME", (0, r), (1, r), "Helvetica-Bold")]
        else:
            style += [("BACKGROUND", (0, r), (-1, r), LGREY)]
        first = False; r += 1
    style += [("LINEBELOW", (0, r-1), (-1, r-1), 0.8, colors.HexColor("#9aa6bd"))]
t = Table(slip, colWidths=[1.45*inch, 3.05*inch, 0.7*inch, 0.85*inch, 0.85*inch], hAlign="LEFT")
t.setStyle(TableStyle(style)); story.append(t)
story.append(Paragraph(
    f"<b>Total staked: {total:.0f} units</b> across all four games. Note the discipline trade-off: "
    "only the Netherlands core carries a measured edge (green) - the other three favourites are "
    "model-rated as fairly-to-over-priced, so betting them is for coverage/entertainment and gives "
    "back more margin over time. The savers are sub-15% shots (each loses ~7 of 8).", NOTE))

story.append(Paragraph("2 &nbsp;&middot;&nbsp; Model detail &amp; reasoning, game by game", SEC))
col_w = [1.6*inch, 0.7*inch, 0.9*inch, 0.8*inch, 0.7*inch, 0.7*inch]
REC_TXT = {
 "Netherlands vs Sweden": "Real-data xG (2.32 vs 1.23) rates the Dutch a clear favourite - model 60.9% vs a 55.4% fair line. The core is a genuine +EV edge.",
 "Germany vs Cote d'Ivoire": "Model makes Germany only 53% (implied 64%): the win is poor value, so the core here is coverage, not edge. Savers cover the likeliest German wins.",
 "Ecuador vs Curacao": "Ecuador correctly dominant (83%) but fairly priced - the 1.13 banker returns little, so weight shifts to the low-scoring savers (1-0/2-0).",
 "Japan vs Tunisia": "Model 61.9% vs 63.7% fair - agrees with the market, so the core is coverage. Top score Japan 1-0 matches the consensus model; leans Under 2.5.",
}
for m in wc.SATURDAY:
    mat, mp, dc, ovr, rows, scores, fair, odds3 = analyse(m)
    story.append(Paragraph(
        f"{m.name} &nbsp;<font size=8 color='#777'>(fitted xG {m.home} {m.home_xg:.2f} - "
        f"{m.away_xg:.2f} {m.away} &middot; overround {ovr*100:.1f}% &middot; OOS cutoff Jun 19)</font>", GAME))
    data = [["Outcome", "Odds", "Model P", "Fair P", "Edge", "Stake"]] + rows
    gt = Table(data, colWidths=col_w, hAlign="LEFT")
    gs = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8.6),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cdd3df")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LGREY]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
    ]
    for ri, rr in enumerate(rows, start=1):
        if rr[-1] != "-":
            gs += [("BACKGROUND", (0, ri), (-1, ri), colors.HexColor("#eef6ef")),
                   ("TEXTCOLOR", (4, ri), (5, ri), ACCENT)]
    gt.setStyle(TableStyle(gs)); story.append(gt)
    story.append(Paragraph(
        f"<b>Scores:</b> {scores} &nbsp;|&nbsp; <b>BTTS-Y</b> {pct(mp['btts_yes'])} &nbsp;"
        f"<b>O2.5</b> {pct(mp['over25'])} &nbsp; <b>1X/12/X2</b> "
        f"{dc['1X']:.2f}/{dc['12']:.2f}/{dc['X2']:.2f}", NOTE))
    story.append(Paragraph(f"<b><font color='#2e7d32'>Read:</font></b> {REC_TXT[m.name]}", NOTE))

story.append(Spacer(1, 6))
story.append(Paragraph(
    "Edge = model probability minus fair (de-vigged) probability; the model flags a value bet only "
    "at edge of at least +2 pts. Four games decide nothing - the real test is closing-line value "
    "tracked over hundreds of bets.", SUB))
doc.build(story)
print("wrote today-4games-model.pdf")
