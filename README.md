# Edge Studio — auto-deployed World Cup 2026 betting model

A self-contained, market-anchored Dixon-Coles betting model and explorer. The site is a single
static HTML file regenerated and deployed automatically by GitHub Actions.

**Live site:** `https://<your-username>.github.io/<repo-name>/` (after the one-time setup below)

---

## One-time setup (≈3 minutes)

1. **Create a GitHub repo** and push the files listed under "What to commit" below.
2. In the repo: **Settings → Pages → Build and deployment → Source → "GitHub Actions".**
   (Do *not* pick "Deploy from a branch" — this project deploys via the workflow.)
3. Go to the **Actions** tab → run **"Build & deploy Edge Studio"** once (or just push).
   When it finishes, your live URL appears in the workflow summary and under Settings → Pages.

That's it. Every push and a daily schedule will rebuild and redeploy automatically.

## What to commit

Required (the build needs these):

```
wc_model.py            build_data.py      build_app.py     rebuild.py
app_odds.json          market_odds.json   cs_odds.json     results.csv
requirements.txt       .gitignore         .github/workflows/deploy.yml
```

Generated files (`wc-betting-studio.html`, `index.html`, `app_data.json`) are produced by the
workflow and are git-ignored — you don't commit them.

---

## How updates flow

- **Model refit:** the workflow runs `python rebuild.py`, which re-fits team strengths and
  regenerates the site. The daily cron (12:00 UTC) keeps the model current as time-decay shifts.
- **New odds:** the model embeds whatever is in `app_odds.json` (1X2) and `market_odds.json`
  (handicaps, totals, BTTS). To push fresh prices online, update those two files and `git push` —
  the workflow rebuilds and Pages redeploys within ~1 minute.
  - Locally you already have helpers: `python set_odds.py '{"Home|Away":[h,d,a]}'` and
    `python set_market_odds.py '{"Home|Away":{"O2.5":1.9,"AHH-1":1.8}}'`, then commit + push.
  - The Cowork daily task (`wc-clv-ledger-daily`) refreshes those JSON files each matchday;
    add a `git -C <repo> commit -am odds && git push` step to it to auto-publish.

> GitHub Actions itself can't browse the web for odds, so the *fetching* of new prices stays with
> the local task (or you); the Action handles refit + deploy. If you ever want fully hands-off
> odds, plug a paid odds API into `build_data.py` and read it in CI from a repo secret.

### Updating the historical dataset (optional)
`results.csv` (international results, used to fit strengths) is committed as a snapshot that
includes the 2026 World Cup fixtures. To refresh strengths with newer results, replace it and
push. (The workflow intentionally does **not** auto-download it, so a changed upstream file can't
silently break the fixtures list.)

---

## Local development

```
pip install -r requirements.txt
python rebuild.py          # -> app_data.json + wc-betting-studio.html
# open wc-betting-studio.html in a browser
```

This is a probability/strategy explorer, **not betting advice**. The bookmaker margin is in every
price; the tool manages process and variance, it does not manufacture an edge.
