"""Merge market odds into market_odds.json.  Usage:
   python3 set_market_odds.py '{"Germany|Ivory Coast":{"O2.5":1.95,"U2.5":1.85,"BTTSY":2.1,"AHH-1":1.95}}'
Keys are "Home|Away"; inner keys are app market keys
(H,D,A,DC1X,DCX2,DNBH,DNBA,AHH-0.5,AHH-1,AHH-1.5,AHH+0.5,AHA-0.5,...,O1.5,U1.5,O2.5,U2.5,O3.5,U3.5,BTTSY,BTTSN)."""
import json, sys, os
p = os.path.join(os.path.dirname(__file__) or ".", "market_odds.json")
store = json.load(open(p)) if os.path.exists(p) else {}
if len(sys.argv) > 1:
    for g, mk in json.loads(sys.argv[1]).items():
        store.setdefault(g, {}).update(mk)
    json.dump(store, open(p, "w"), indent=1, ensure_ascii=False)
print(f"market_odds.json now has {len(store)} games")
