"""CLV ledger PDF: table + cumulative-CLV chart + interpretation."""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
import importlib.util, os, csv

# run the tracker to refresh ledger + chart
import subprocess, sys
subprocess.run([sys.executable, "clv_tracker.py"], cwd=os.path.dirname(__file__) or ".",
               capture_output=True)

NAVY = colors.HexColor("#1b2a4a"); WIN = colors.HexColor("#2e7d32"); LOSE = colors.HexColor("#b23b3b")
LGREY = colors.HexColor("#f7f8fb"); MUTE = colors.HexColor("#888888")
styles = getSampleStyleSheet()
H = ParagraphStyle("H", parent=styles["Title"], textColor=NAVY, fontSize=17, spaceAfter=2)
SUB = ParagraphStyle("SUB", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#555"), leading=11)
SEC = ParagraphStyle("SEC", parent=styles["Heading2"], textColor=NAVY, fontSize=12.5, spaceBefore=9, spaceAfter=3)
NOTE = ParagraphStyle("NOTE", parent=styles["Normal"], fontSize=8.6, textColor=colors.HexColor("#333"), spaceBefore=2, leading=11.5)
CELL = ParagraphStyle("CELL", parent=styles["Normal"], fontSize=8.3, leading=9.6)

rows = list(csv.DictReader(open("clv_ledger.csv")))

doc = SimpleDocTemplate("clv-ledger.pdf", pagesize=letter, topMargin=0.5*inch,
                        bottomMargin=0.5*inch, leftMargin=0.6*inch, rightMargin=0.6*inch)
story = [
    Paragraph("World Cup 2026 - Closing Line Value (CLV) Ledger", H),
    Paragraph("CLV compares the price you TOOK to the market's CLOSING no-vig price - the sharpest "
              "estimate of the true probability. Sustained positive CLV is the real proof of an edge, "
              "long before win/loss results mean anything (Buchdahl, Squares &amp; Sharps). "
              "CLV% = taken odds x closing fair prob - 1; positive means you beat the close. "
              "Strategy illustration - not betting advice.", SUB),
    Spacer(1, 4),
    Paragraph("1 &nbsp;&middot;&nbsp; Bet ledger", SEC),
]

head = ["Date", "Game", "Bet", "Taken", "Close fair", "CLV%", "Beat?", "Result"]
data = [head]
for r in rows:
    data.append([r["date"][5:], r["game"], r["side"], r["taken_odds"],
                 (r["close_fair_prob"] and f"{float(r['close_fair_prob'])*100:.1f}%") or "-",
                 (r["CLV_pct"] and f"{float(r['CLV_pct']):+.1f}") or "-",
                 r["beat_close"] or "-", r["result"]])
tbl = Table([[Paragraph(str(c), CELL) if i == 1 else str(c) for i, c in enumerate(row)] for row in data],
            colWidths=[0.55*inch,1.85*inch,0.55*inch,0.6*inch,0.85*inch,0.6*inch,0.55*inch,0.7*inch],
            hAlign="LEFT")
ts = [
    ("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),colors.white),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.3),
    ("ALIGN",(2,0),(-1,-1),"CENTER"),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cdd3df")),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,LGREY]),
    ("TOPPADDING",(0,0),(-1,-1),2.8),("BOTTOMPADDING",(0,0),(-1,-1),2.8),
]
for i, r in enumerate(rows, start=1):
    if r["CLV_pct"]:
        col = WIN if float(r["CLV_pct"]) > 0 else LOSE
        ts.append(("TEXTCOLOR",(5,i),(6,i),col))
    else:
        ts.append(("TEXTCOLOR",(4,i),(6,i),MUTE))
    if r["result"] == "W": ts.append(("TEXTCOLOR",(7,i),(7,i),WIN))
    elif r["result"] == "L": ts.append(("TEXTCOLOR",(7,i),(7,i),LOSE))
tbl.setStyle(TableStyle(ts)); story.append(tbl)

# summary numbers (recompute from rows)
clv_vals = [float(r["CLV_pct"]) for r in rows if r["CLV_pct"]]
beat = sum(1 for r in rows if r["beat_close"] == "yes")
avg = sum(clv_vals)/len(clv_vals)
pnls = [float(r["pnl_units"]) for r in rows if r["pnl_units"]]
staked = sum(10 for r in rows if r["pnl_units"])
story.append(Paragraph(
    f"<b>Closing lines captured: {len(clv_vals)} bets (today's slate).</b> Beat-close rate "
    f"<b>{beat}/{len(clv_vals)}</b> &nbsp;|&nbsp; average CLV <b><font color='#b23b3b'>{avg:+.1f}%</font></b> "
    f"&nbsp;|&nbsp; cumulative CLV {sum(clv_vals):+.1f}%. &nbsp; Friday's four are settled for P&amp;L "
    f"(staked {staked:.0f}u core-only, net {sum(pnls):+.1f}u) but had no separately-captured closing "
    "line, so they carry no CLV.", NOTE))

story.append(Paragraph("2 &nbsp;&middot;&nbsp; CLV per bet (real open &rarr; close)", SEC))
story.append(Image("clv_chart.png", width=6.6*inch, height=2.93*inch))

story.append(Paragraph("3 &nbsp;&middot;&nbsp; What the ledger says", SEC))
for t in [
 "<b>The strategy is NOT beating the close.</b> Average CLV is negative (-2.3%) and only 1 of 4 bets beat the closing line. Sustained, that points to a long-run loss at roughly the margin - the sober verdict the model's own 'edge' numbers can't give you.",
 "<b>The model's flagged edge is not confirmed by the market.</b> The model rated Netherlands a +5.5-pt value bet, but the Dutch CLOSED around 56% (taken 1.73 = -2.8% CLV). The sharper closing market disagreed that they were that strong - exactly why CLV outranks an in-house model.",
 "<b>The one bet that beat the close was Ecuador (+0.4%).</b> Its line shortened from 1.13 to ~1.10, so the earlier 1.13 was genuinely a better-than-closing price - a real, if tiny, positive signal.",
 "<b>Four bets prove nothing.</b> CLV only becomes a verdict over hundreds of bets. This ledger is the instrument: log taken odds when you bet, the full 3-way closing line at kickoff, and the running average tells you whether there is an edge before the bankroll does.",
]:
    story.append(Paragraph(t, NOTE)); story.append(Spacer(1, 1))

story.append(Spacer(1, 3))
story.append(Paragraph("Data: clv_ledger.csv (re-runnable via clv_tracker.py). Taken = thread Bet365 "
              "lines; closing = FanDuel three-way pre-kickoff (Jun 20-21). De-vig: odds-ratio method.", SUB))
doc.build(story)
print("wrote clv-ledger.pdf")
