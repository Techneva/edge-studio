"""Merge fixture odds into app_odds.json.  Usage:
   python3 set_odds.py '{"Netherlands|Sweden":[1.71,3.9,4.7]}'
Keys are "Home|Away" exactly as in the fixture; values are [home,draw,away] decimal."""
import json, sys, os
path = os.path.join(os.path.dirname(__file__) or ".", "app_odds.json")
store = {}
if os.path.exists(path):
    try: store = json.load(open(path))
    except Exception: store = {}
if len(sys.argv) > 1:
    store.update(json.loads(sys.argv[1]))
    json.dump(store, open(path, "w"), indent=1)
print(f"app_odds.json now has {len(store)} fixtures with odds")
