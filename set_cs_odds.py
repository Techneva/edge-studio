"""Merge correct-score odds into cs_odds.json.  Usage:
   python3 set_cs_odds.py '{"Germany|Ivory Coast":{"1-0":9.5,"2-0":9.0}}'
Keys are "Home|Away"; inner keys are "homeGoals-awayGoals"; values decimal."""
import json, sys, os
path = os.path.join(os.path.dirname(__file__) or ".", "cs_odds.json")
store = {}
if os.path.exists(path):
    try: store = json.load(open(path))
    except Exception: store = {}
if len(sys.argv) > 1:
    for game, scores in json.loads(sys.argv[1]).items():
        store.setdefault(game, {}).update(scores)
    json.dump(store, open(path, "w"), indent=1, ensure_ascii=False)
print(f"cs_odds.json now has {len(store)} games with correct-score odds")
