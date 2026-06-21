import json
data = json.load(open("app_data.json"))

TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Edge Studio — Football Betting Model</title>
<style>
:root{--navy:#1b2a4a;--ink:#1d2433;--muted:#6b7488;--line:#e2e6ee;--bg:#f4f6fa;--card:#fff;
 --green:#1f8f43;--greenbg:#e7f4ec;--red:#c0392b;--redbg:#fbecea;--accent:#2f6df0;--chip:#eef2f9;--amber:#b9821a}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg);font-size:14px;line-height:1.45}
header{background:var(--navy);color:#fff;padding:13px 20px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;position:sticky;top:0;z-index:20}
header h1{font-size:17px;margin:0;font-weight:700}
header .meta{font-size:11px;color:#b9c4dc}
.comp-select{background:#0f1d38;color:#fff;border:1px solid #34507f;border-radius:8px;padding:6px 10px}
.layout{display:flex;align-items:flex-start}
.sidebar{width:340px;min-width:340px;background:var(--card);border-right:1px solid var(--line);height:calc(100vh - 50px);overflow-y:auto;position:sticky;top:50px}
.controls{padding:12px 14px;border-bottom:1px solid var(--line);display:grid;grid-template-columns:1fr 1fr;gap:9px}
.controls label{font-size:10.5px;color:var(--muted);display:block;margin-bottom:3px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}
.controls input,.controls select{width:100%;padding:6px 8px;border:1px solid var(--line);border-radius:7px}
.controls .full{grid-column:1/3}
.controls .hint{font-size:9.5px;color:var(--muted);text-transform:none;font-weight:400;margin-top:2px}
.picker-head{padding:10px 14px;display:flex;justify-content:space-between;align-items:center;gap:8px;border-bottom:1px solid var(--line)}
.picker-head .t{font-weight:700;font-size:12.5px}
.btn{border:1px solid var(--line);background:#fff;border-radius:7px;padding:5px 9px;cursor:pointer;font-size:12px}
.btn:hover{background:var(--chip)}
.search{margin:10px 14px;width:calc(100% - 28px);padding:7px 10px;border:1px solid var(--line);border-radius:8px}
.dayhdr{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;padding:8px 14px 4px}
.fix{display:flex;align-items:center;gap:9px;padding:7px 14px;cursor:pointer;border-bottom:1px solid #f0f2f7}
.fix:hover{background:#f8fafd}
.fix input{margin:0;width:15px;height:15px;accent-color:var(--accent)}
.fix .tm{flex:1;min-width:0}.fix .tm b{font-weight:600}
.fix .xg{font-size:11px;color:var(--muted);font-variant-numeric:tabular-nums}
.fix .fav{font-size:10.5px;color:#fff;background:var(--navy);border-radius:10px;padding:1px 7px;white-space:nowrap}
.fix.host .tm:after{content:" · host";color:var(--accent);font-size:10px}
.main{flex:1;padding:16px 18px;min-width:0}
.summary{display:flex;flex-direction:column;gap:6px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-bottom:14px}
.summary .k{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.3px}
.summary .v{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums}
.summary .u{font-size:12px;color:var(--muted)}.summary .roi{font-size:12px;font-weight:600;color:var(--muted)}
.summary .srow{display:flex;gap:18px;flex-wrap:wrap;width:100%}
.summary .picks{width:100%;border-top:1px solid var(--line);margin-top:10px;padding-top:9px;display:flex;flex-wrap:wrap;gap:7px}
.pick{background:#eef3fc;border:1px solid #d7e0f0;border-radius:9px;padding:4px 9px;font-size:12px}
.pick .pscore{display:block;color:var(--muted);font-size:10.5px}
.empty{color:var(--muted);text-align:center;padding:60px 20px}
.game{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:13px}
.game h3{margin:0 0 2px;font-size:15.5px}
.game .sub{font-size:11.5px;color:var(--muted);margin-bottom:8px}
.rec{margin:6px 0;padding:12px 14px;border-radius:11px;font-size:15px;line-height:1.5;background:#eef3fc;border:2px solid #b9cdf0}
.rec.edge{background:var(--greenbg);border-color:#7cc492}
.rec.flat{background:#f6f8fc;border:1px solid var(--line)}
.rec b{font-weight:700}
.reclabel{display:block;font-size:10.5px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;color:var(--accent);margin-bottom:3px}
.rec.edge .reclabel{color:var(--green)}
.ins{margin:6px 0;padding:9px 12px;border-radius:10px;background:#fff7e9;border:1px solid #ecd6a8;font-size:13px}
.ins .reclabel{color:var(--amber)}
.datahdr{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);margin:12px 0 4px;border-top:1px solid var(--line);padding-top:8px}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
th,td{padding:4px 6px;text-align:center;border-bottom:1px solid var(--line);font-size:12px}
th{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.3px;font-weight:700}
td:first-child,th:first-child{text-align:left}
td input{width:56px;padding:3px 5px;border:1px solid var(--line);border-radius:6px;text-align:center}
.secrow td{background:#f2f5fa;font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.4px;color:var(--navy);text-align:left}
.row-bet{background:var(--greenbg)}
.pos{color:var(--green);font-weight:700}.neg{color:var(--red)}
.scorebar{margin-top:9px;font-size:11px;color:var(--muted)}
.scorebar b{color:#33405a}
.note{font-size:11px;color:#444;margin-top:7px;line-height:1.4}
footer{padding:16px 20px;color:var(--muted);font-size:11px;text-align:center}
.disclaim{max-width:780px;margin:0 auto}
@media(max-width:860px){.layout{flex-direction:column}.sidebar{width:100%;min-width:0;height:auto;position:static}}
</style>
</head>
<body>
<header>
  <h1>⚽ Edge Studio</h1>
  <select class="comp-select" id="comp">
    <option value="wc2026">FIFA World Cup 2026 — Group stage</option>
    <option value="" disabled>More competitions (coming soon)</option>
  </select>
  <span class="meta" id="modelmeta"></span>
</header>
<div class="layout">
  <aside class="sidebar">
    <div class="controls">
      <div><label>Bankroll (u)</label><input id="bankroll" type="number" value="1000" step="50"></div>
      <div><label>Kelly fraction</label><input id="kfrac" type="number" value="0.25" step="0.05" min="0" max="1"></div>
      <div><label>Edge threshold %</label><input id="thresh" type="number" value="2" step="0.5"></div>
      <div><label>Model trust</label><input id="trust" type="number" value="0.35" step="0.05" min="0" max="1">
        <div class="hint">0 = follow market · 1 = pure model</div></div>
      <div class="full"><label>Bet mode</label>
        <select id="mode"><option value="insured" selected>Favourite + insurance (low risk)</option>
        <option value="value">Value bets only (edge ≥ thr)</option></select></div>
    </div>
    <div class="picker-head"><span class="t" id="pickcount">Fixtures</span>
      <span><button class="btn" id="selall">All</button> <button class="btn" id="selnone">Clear</button></span></div>
    <input class="search" id="search" placeholder="Filter team or date…">
    <div id="fixtures"></div>
  </aside>
  <main class="main">
    <div class="summary" id="summary"></div>
    <div id="cards"><div class="empty">Pick fixtures on the left.<br>Probabilities are market-anchored; enter book odds on any market to get edge and a stake.</div></div>
  </main>
</div>
<footer><div class="disclaim">
  Dixon-Coles model on real international results, <b>calibrated toward the de-vigged market line</b> (model-trust slider).
  Low-margin markets (Asian handicap, totals, double chance) are priced straight from the model; correct score is a high-margin lottery, shown for reference only.
  All odds are <b>decimal</b>. The bookmaker margin is in every price — this manages process and variance, <b>not</b> a guaranteed edge. Not betting advice.
</div></footer>
<script>
const DATA = /*__DATA__*/;
const $ = s => document.querySelector(s);

/* ---------- engine (validated vs Python) ---------- */
function fact(n){let r=1;for(let i=2;i<=n;i++)r*=i;return r;}
function pois(k,l){return Math.exp(-l)*Math.pow(l,k)/fact(k);}
function tau(x,y,l,m,rho){if(x===0&&y===0)return 1-l*m*rho;if(x===0&&y===1)return 1+l*rho;if(x===1&&y===0)return 1+m*rho;if(x===1&&y===1)return 1-rho;return 1;}
function scoreMatrix(lh,la,rho,MAX=10){let m=[],t=0;for(let h=0;h<=MAX;h++){m[h]=[];for(let a=0;a<=MAX;a++){let p=pois(h,lh)*pois(a,la)*tau(h,a,lh,la,rho);m[h][a]=p;t+=p;}}for(let h=0;h<=MAX;h++)for(let a=0;a<=MAX;a++)m[h][a]/=t;return m;}
function probs(m){let home=0,draw=0,away=0,btts=0,MAX=m.length-1;for(let h=0;h<=MAX;h++)for(let a=0;a<=MAX;a++){let p=m[h][a];if(h>a)home+=p;else if(h===a)draw+=p;else away+=p;if(h>=1&&a>=1)btts+=p;}return{home,draw,away,btts};}
function topScores(m,n=5){let A=[],MAX=m.length-1;for(let h=0;h<=MAX;h++)for(let a=0;a<=MAX;a++)A.push([h,a,m[h][a]]);A.sort((x,y)=>y[2]-x[2]);return A.slice(0,n);}
function devig(o){let raw=o.map(x=>1/x);const fg=c=>raw.map(r=>r/(c+r-c*r));let lo=.5,hi=5;for(let i=0;i<200;i++){let c=(lo+hi)/2,s=fg(c).reduce((a,b)=>a+b,0);if(s>1)lo=c;else hi=c;if(Math.abs(s-1)<1e-10)break;}let f=fg((lo+hi)/2),s=f.reduce((a,b)=>a+b,0);return f.map(x=>x/s);}
function ah(m,side,line){let win=0,push=0,loss=0,MAX=m.length-1;for(let h=0;h<=MAX;h++)for(let a=0;a<=MAX;a++){let p=m[h][a];let d=(side==="home"?h-a:a-h)+line;if(d>1e-9)win+=p;else if(Math.abs(d)<1e-9)push+=p;else loss+=p;}return{win,push,loss};}
function ou(m,line){let over=0,MAX=m.length-1;for(let h=0;h<=MAX;h++)for(let a=0;a<=MAX;a++)if(h+a>line)over+=m[h][a];return over;}
function kelly(p,o){let b=o-1;return Math.max(0,(b*p-(1-p))/b);}
function calibrate(lam,mu,rho0,target,overT){let s=lam-mu,t=Math.max(lam+mu,.3),rho=rho0;
  for(let it=0;it<160;it++){let l=Math.max((t+s)/2,.04),mm=Math.max((t-s)/2,.04);let M=scoreMatrix(l,mm,rho),pr=probs(M);
    let eS=(pr.home-pr.away)-(target[0]-target[2]); s-=1.1*eS;
    let eD=pr.draw-target[1], eT;
    if(overT!=null){ eT=ou(M,2.5)-overT; t-=4.0*eT;   // O/U pins total
      rho+=0.8*eD; rho=Math.max(-0.30,Math.min(0.04,rho)); }  // rho pins draw
    else { eT=eD; t+=3.0*eD; }                          // no O/U: total pins draw
    t=Math.max(t,.3);
    if(Math.abs(eS)<2e-5&&Math.abs(eT)<2e-5&&(overT==null||Math.abs(eD)<3e-4))break;}
  return[Math.max((t+s)/2,.04),Math.max((t-s)/2,.04),rho];}

/* ---------- state ---------- */
let selected=new Set(), mOdds={}, trust=0.35;
const LS="edgestudio_v2";
try{let s=JSON.parse((typeof localStorage!=="undefined"&&localStorage.getItem(LS))||"{}");
 if(s.selected)selected=new Set(s.selected); if(s.mOdds)mOdds=s.mOdds; if(s.trust!=null)trust=s.trust;}catch(e){}
function fkey(f){return f.date+"|"+f.home+"|"+f.away;}
function save(){try{localStorage.setItem(LS,JSON.stringify({selected:[...selected],mOdds,trust}));}catch(e){}}
function num(v){let x=parseFloat(v);return isNaN(x)?null:x;}

/* ---------- per-game calibration + markets ---------- */
function get1x2(f){let k=fkey(f),o=mOdds[k]||{};
  let h=o.H??(f.odds?f.odds[0]:null),d=o.D??(f.odds?f.odds[1]:null),a=o.A??(f.odds?f.odds[2]:null);
  return (h&&d&&a)?[h,d,a]:null;}
function getMkt(f,key){let k=fkey(f),o=mOdds[k]||{},mk=f.mkt||{};return o[key]??mk[key]??null;}
function calc(f){
  const rho=DATA.model.rho;
  let baseM=scoreMatrix(f.home_xg,f.away_xg,rho), pm=probs(baseM), pmOver=ou(baseM,2.5);
  let o=get1x2(f), calM=baseM, anchored=false, totAnchored=false, lam=f.home_xg, mu=f.away_xg;
  if(o){let mk=devig(o),w=trust;
    let tg=[w*pm.home+(1-w)*mk[0], w*pm.draw+(1-w)*mk[1], w*pm.away+(1-w)*mk[2]];
    let s=tg[0]+tg[1]+tg[2]; tg=tg.map(x=>x/s);
    // goals-total anchor from O/U 2.5 (use 1X2 for supremacy, O/U for total)
    let oO=getMkt(f,"O2.5"),oU=getMkt(f,"U2.5"),overT=null;
    if(oO&&oU){let fv=devig([oO,oU]); overT=w*pmOver+(1-w)*fv[0]; totAnchored=true;}
    else if(oO){overT=w*pmOver+(1-w)*Math.min(0.98,(1/oO)/1.045); totAnchored=true;}
    else if(oU){overT=w*pmOver+(1-w)*Math.max(0.02,1-(1/oU)/1.045); totAnchored=true;}
    let cr; [lam,mu,cr]=calibrate(f.home_xg,f.away_xg,rho,tg,overT); calM=scoreMatrix(lam,mu,cr); anchored=true; var TG=tg;}
  return {pm, P:probs(calM), M:calM, o1x2:o, anchored, totAnchored, lam, mu, tgt:(typeof TG!=="undefined"?TG:null)};}

// build the market rows for a game; each: {sec,label,key,win,push,loss,book}
function marketRows(f,c){
  const M=c.M; let Q=c.tgt?{home:c.tgt[0],draw:c.tgt[1],away:c.tgt[2]}:c.P; const P={home:Q.home,draw:Q.draw,away:Q.away,btts:c.P.btts};
  let favHome=P.home>=P.away, favLab=favHome?f.home:f.away;
  let rows=[];
  rows.push({sec:"Match result (1X2)"});
  rows.push({label:f.home,key:"H",win:P.home,push:0,loss:1-P.home,book:f.odds?f.odds[0]:null});
  rows.push({label:"Draw",key:"D",win:P.draw,push:0,loss:1-P.draw,book:f.odds?f.odds[1]:null});
  rows.push({label:f.away,key:"A",win:P.away,push:0,loss:1-P.away,book:f.odds?f.odds[2]:null});
  rows.push({sec:"Double chance (insurance)"});
  rows.push({label:f.home+" or Draw (1X)",key:"DC1X",win:P.home+P.draw,push:0,loss:P.away});
  rows.push({label:"Draw or "+f.away+" (X2)",key:"DCX2",win:P.draw+P.away,push:0,loss:P.home});
  rows.push({sec:"Draw no bet"});
  rows.push({label:f.home+" (DNB)",key:"DNBH",win:P.home,push:P.draw,loss:P.away});
  rows.push({label:f.away+" (DNB)",key:"DNBA",win:P.away,push:P.draw,loss:P.home});
  rows.push({sec:"Asian handicap — "+favLab});
  let side=favHome?"home":"away";
  [[-0.5,"-0.5"],[-1,"-1"],[-1.5,"-1.5"],[-2,"-2"],[-2.5,"-2.5"],[0.5,"+0.5"]].forEach(([ln,t])=>{
    let r=ah(M,side,ln); rows.push({label:favLab+" "+t,key:"AH"+(favHome?"H":"A")+t,win:r.win,push:r.push,loss:r.loss});});
  rows.push({sec:"Total goals"});
  [1.5,2.5,3.5].forEach(L=>{let ov=ou(M,L);
    rows.push({label:"Over "+L,key:"O"+L,win:ov,push:0,loss:1-ov});
    rows.push({label:"Under "+L,key:"U"+L,win:1-ov,push:0,loss:ov});});
  rows.push({sec:"Both teams to score"});
  rows.push({label:"BTTS Yes",key:"BTTSY",win:P.btts,push:0,loss:1-P.btts});
  rows.push({label:"BTTS No",key:"BTTSN",win:1-P.btts,push:0,loss:P.btts});
  return rows;
}
function rowFair(r){return r.win>0?1+r.loss/r.win:99;}              // push-refund fair odds
function rowP(r){return r.win/(r.win+r.loss);}                       // effective win prob
function rowOdds(f,r){let k=fkey(f),o=mOdds[k]||{},mk=f.mkt||{};return o[r.key]??mk[r.key]??r.book??null;}
function rowEV(r,odds){return odds!=null? r.win*odds-(r.win+r.loss) : null;}  // per unit staked
const COMP={"O1.5":"U1.5","U1.5":"O1.5","O2.5":"U2.5","U2.5":"O2.5","O3.5":"U3.5","U3.5":"O3.5","BTTSY":"BTTSN","BTTSN":"BTTSY","DNBH":"DNBA","DNBA":"DNBH"};
function rowOddsKey(f,key){let k=fkey(f),o=mOdds[k]||{},mk=f.mkt||{};return o[key]??mk[key]??null;}
// returns {p, fair, od, ev} with the displayed prob shrunk toward the market when a book price exists.
// 1X2 rows are already anchored via the blended target, so they pass through unchanged.
function rowEval(f,r){
  let modelP=rowP(r), od=rowOdds(f,r), is1x2=(r.key==="H"||r.key==="D"||r.key==="A");
  let dispP=modelP, fair=rowFair(r), ev=(od!=null)?(r.win*od-(r.win+r.loss)):null;
  if(od!=null && !is1x2){
    let comp=COMP[r.key], oc=comp?rowOddsKey(f,comp):null, mf;
    if(oc){let a=1/od,b=1/oc; mf=a/(a+b);}            // de-vig the pair when both sides known
    else mf=(1/od)/1.045;                              // single price: light margin haircut
    mf=Math.max(0.004,Math.min(0.996,mf));
    dispP=trust*modelP+(1-trust)*mf; fair=1/dispP; ev=dispP*od-1;
  }
  return {p:dispP, fair, od, ev};
}

/* ---------- fixtures list ---------- */
function favBadge(f){let P=probs(scoreMatrix(f.home_xg,f.away_xg,DATA.model.rho));
  let s=[["",f.home,P.home],["","Draw",P.draw],["",f.away,P.away]].sort((a,b)=>b[2]-a[2])[0];
  return s[1]==="Draw"?`Draw ${(P.draw*100|0)}%`:`${s[1].slice(0,3)} ${(s[2]*100|0)}%`;}
function renderFixtures(){
  let q=$("#search").value.toLowerCase(),box=$("#fixtures");box.innerHTML="";let by={},n=0;
  DATA.fixtures.forEach(f=>{if(q&&!(f.home+" "+f.away+" "+f.date).toLowerCase().includes(q))return;(by[f.date]=by[f.date]||[]).push(f);});
  Object.keys(by).sort().forEach(d=>{let g=document.createElement("div");
    g.innerHTML=`<div class="dayhdr">${new Date(d+"T12:00:00").toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'})}</div>`;
    by[d].forEach(f=>{n++;let k=fkey(f),row=document.createElement("label");row.className="fix"+(f.neutral?"":" host");
      row.innerHTML=`<input type="checkbox" ${selected.has(k)?"checked":""}><span class="tm"><b>${f.home}</b> v <b>${f.away}</b><br>
        <span class="xg">xG ${f.home_xg.toFixed(2)} – ${f.away_xg.toFixed(2)}</span></span><span class="fav">${favBadge(f)}</span>`;
      row.querySelector("input").addEventListener("change",e=>{e.target.checked?selected.add(k):selected.delete(k);save();render();});
      g.appendChild(row);});box.appendChild(g);});
  $("#pickcount").textContent=`Fixtures (${n})`;
}

/* ---------- card ---------- */
function gameCard(f){
  const c=calc(f),P=c.P,rows=marketRows(f,c);
  const bank=parseFloat($("#bankroll").value)||1000,kf=parseFloat($("#kfrac").value),thr=parseFloat($("#thresh").value)/100,mode=$("#mode").value,unit=bank/1000;
  let favHome=P.home>=P.away, favLab=favHome?f.home:f.away, favP=favHome?P.home:P.away;
  // value bets = ALL rows with book odds clearing the edge threshold, ranked by EV
  let cands=[];
  rows.forEach(r=>{if(r.sec)return;let e=rowEval(f,r);if(e.od==null)return;if(e.ev>=thr)cands.push({r,od:e.od,ev:e.ev,p:e.p});});
  cands.sort((a,b)=>b.ev-a.ev);
  // insurance = favourite double chance
  let dcRow=rows.find(r=>r.key===(favHome?"DC1X":"DCX2")), dcE=rowEval(f,dcRow), dcOdds=dcE.od, dcFair=dcE.fair;
  // recommended bet block
  let rec,recClass;
  if(cands.length){ recClass="edge";
    rec=cands.map((c,i)=>{let stk=bank*kf*kelly(c.p,c.od);
      return `${i===0?'<b>BET</b> &nbsp;':'<span style="color:var(--muted)">also</span> &nbsp;'}<b>${c.r.label}</b> @ ${c.od} · stake ${stk.toFixed(0)}u &rarr; ${(stk*c.od).toFixed(1)}u <span style="color:var(--green);font-weight:700">+${(c.ev*100).toFixed(1)}%</span>`;}).join("<br>");
    if(cands.length>1) rec+=`<div style="font-size:11px;color:var(--muted);margin-top:5px">${cands.length} value bets — several overlap (e.g. a win and its handicap), so don't stake them all independently; pick one expression of the same view.</div>`;
  } else rec=`<b>No value bet</b> — priced markets are at/under the ${$("#thresh").value}% edge after anchoring. Enter book odds on more markets (handicap, totals, double chance) to surface others.`,recClass="flat";
  // insurance line
  let insStake=(mode==="insured"?8*unit:0);
  let insOdds=dcOdds??dcFair;
  let ins=`<span class="reclabel">Lower-variance pick (insurance)</span><b>${dcRow.label}</b> · model ${(dcE.p*100).toFixed(0)}% · ${dcOdds?("@ "+dcOdds):("fair "+dcFair.toFixed(2))}${insStake>0?` · stake ${insStake.toFixed(0)}u`:""}`;
  // markets table
  let tb="";
  rows.forEach(r=>{ if(r.sec){tb+=`<tr class="secrow"><td colspan="5">${r.sec}</td></tr>`;return;}
    let e=rowEval(f,r),od=e.od,ev=e.ev,k=fkey(f);
    tb+=`<tr><td>${r.label}</td><td>${(e.p*100).toFixed(1)}%</td><td>${e.fair.toFixed(2)}</td>
      <td><input class="mo" data-k="${k}" data-m="${r.key}" value="${od!=null?od:''}" placeholder="dec"></td>
      <td class="${ev==null?'':ev>=0?'pos':'neg'}">${ev==null?'–':(ev*100>=0?'+':'')+(ev*100).toFixed(0)+'%'}</td></tr>`;});
  let ts=topScores(c.M,4).map(s=>`${f.home} ${s[0]}-${s[1]} ${f.away} ${(s[2]*100).toFixed(0)}%`).join(" · ");
  let dd=new Date(f.date+"T12:00:00").toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'});
  let anchorNote = c.anchored
    ? `model ${(c.pm.home*100).toFixed(0)}/${(c.pm.draw*100).toFixed(0)}/${(c.pm.away*100).toFixed(0)} &rarr; anchored ${(P.home*100).toFixed(0)}/${(P.draw*100).toFixed(0)}/${(P.away*100).toFixed(0)} (trust ${trust})`
    : `pure model (no market odds) ${(P.home*100).toFixed(0)}/${(P.draw*100).toFixed(0)}/${(P.away*100).toFixed(0)}`;
  return `<div class="game"><h3>${f.home} <span style="color:var(--muted)">vs</span> ${f.away}</h3>
    <div class="sub">${dd} · ${f.venue||''} ${f.neutral?'':'· <span style="color:var(--accent)">host</span>'} · xG ${c.lam.toFixed(2)}–${c.mu.toFixed(2)} · ${anchorNote}</div>
    <div class="rec ${recClass}"><span class="reclabel">Recommended bet</span>${rec}</div>
    <div class="ins">${ins}</div>
    <div class="datahdr">Markets — model-priced (enter book odds for edge)</div>
    <table><thead><tr><th>Market</th><th>Model</th><th>Fair</th><th>Your odds (dec)</th><th>EV</th></tr></thead><tbody>${tb}</tbody></table>
    <div class="scorebar"><b>Correct score (high-margin lottery, reference only):</b> ${ts}</div>
  </div>`;
}

/* ---------- render ---------- */
function render(){
  trust=parseFloat($("#trust").value); if(isNaN(trust))trust=0.35;
  $("#kfrac").disabled=($("#mode").value!=="value"); $("#kfrac").style.opacity=$("#mode").value!=="value"?0.45:1;
  let sel=DATA.fixtures.filter(f=>selected.has(fkey(f)));
  $("#cards").innerHTML = sel.length? sel.map(gameCard).join("")
    : `<div class="empty">Pick fixtures on the left.<br>Probabilities are market-anchored; enter book odds on any market to get edge and a stake.</div>`;
  // summary
  const bank=parseFloat($("#bankroll").value)||1000,kf=parseFloat($("#kfrac").value),thr=parseFloat($("#thresh").value)/100,mode=$("#mode").value,unit=bank/1000;
  let nEdge=0,totStake=0,totEV=0,totPot=0;
  let picks=sel.map(f=>{let c=calc(f),P=c.P,favHome=P.home>=P.away,favLab=favHome?f.home:f.away,favP=favHome?P.home:P.away;
    let rows=marketRows(f,c);
    rows.forEach(r=>{if(r.sec)return;let e=rowEval(f,r);if(e.od==null)return;if(e.ev>=thr)nEdge++;});
    if(mode==="value"){
      rows.forEach(r=>{if(r.sec)return;let e=rowEval(f,r);if(e.od==null)return;
        if(e.ev>=thr){let stk=bank*kf*kelly(e.p,e.od);totStake+=stk;totEV+=stk*e.ev;totPot+=stk*e.od;}});
    } else {
      let o=c.o1x2, favOdds=o?(favHome?o[0]:o[2]):null, core=10*unit;
      totStake+=core; if(favOdds){totEV+=core*(favP*favOdds-1);totPot+=core*favOdds;}
      let dcRow=rows.find(r=>r.key===(favHome?"DC1X":"DCX2")),dcE=rowEval(f,dcRow),dcOdds=dcE.od??dcE.fair,ins=8*unit;
      totStake+=ins; totEV+=ins*(dcE.p*dcOdds-1); totPot+=ins*dcOdds;
    }
    let ts=topScores(c.M,1)[0];
    return `<span class="pick"><b>${favLab} win</b> ${(favP*100).toFixed(0)}%<span class="pscore">most likely ${f.home} ${ts[0]}-${ts[1]} ${f.away} ${(ts[2]*100).toFixed(0)}%</span></span>`;
  }).join("");
  let roi=totStake>0?totEV/totStake*100:0;
  $("#summary").innerHTML=`<div class="srow">
    <div><div class="k">Selected</div><div class="v">${sel.length}</div></div>
    <div><div class="k">Total stake</div><div class="v">${totStake.toFixed(0)}<span class="u"> u</span></div></div>
    <div title="Market-anchored probability-weighted profit. Negative = paying the margin."><div class="k">Exp. profit</div><div class="v" style="color:${totEV>=0?'var(--green)':'var(--red)'}">${totEV>=0?'+':''}${totEV.toFixed(0)}<span class="u"> u</span> <span class="roi">${roi>=0?'+':''}${roi.toFixed(1)}%</span></div></div>
    <div title="Payout if every favourite wins (core + insurance both cash)."><div class="k">Return if favs win</div><div class="v">${totPot.toFixed(0)}<span class="u"> u</span></div></div>
    <div><div class="k">Value edges</div><div class="v" style="color:var(--green)">${nEdge}</div></div>
    <div><div class="k">Calibration</div><div class="v" style="font-size:12px;font-weight:600">trust ${trust} · ρ ${DATA.model.rho}</div></div>
  </div>${sel.length?`<div class="picks"><div class="k" style="margin-bottom:4px">Most-probable picks</div>${picks}</div>`:''}`;
  document.querySelectorAll(".mo").forEach(inp=>inp.addEventListener("change",e=>{
    let k=e.target.dataset.k,m=e.target.dataset.m,v=num(e.target.value);
    mOdds[k]=mOdds[k]||{}; if(v==null)delete mOdds[k][m]; else mOdds[k][m]=v; save(); render();}));
}

/* ---------- init ---------- */
$("#trust").value=trust;
$("#modelmeta").textContent=`${DATA.fixtures.length} fixtures · fit ${DATA.model.fit_through} · market-anchored · decimal odds`;
["#bankroll","#kfrac","#thresh","#trust","#mode"].forEach(s=>$(s).addEventListener("input",render));
$("#search").addEventListener("input",renderFixtures);
$("#selall").addEventListener("click",()=>{DATA.fixtures.forEach(f=>selected.add(fkey(f)));save();renderFixtures();render();});
$("#selnone").addEventListener("click",()=>{selected.clear();save();renderFixtures();render();});
renderFixtures();render();
</script>
</body>
</html>'''
html = TEMPLATE.replace("/*__DATA__*/", json.dumps(data))
open("wc-betting-studio.html","w").write(html)
print("wrote wc-betting-studio.html", len(html), "bytes")
