# Putting Edge Studio online

The whole app is one self-contained file: **`index.html`** (a copy of `wc-betting-studio.html`).
No server, no build step, no external dependencies — everything (the Dixon-Coles model, the
fixtures, the odds) is embedded. So you just need to host one static file.

---

## Option A — Fastest (drag-and-drop, ~1 minute, free)

**Netlify Drop** — go to https://app.netlify.com/drop and drag `index.html` onto the page.
You instantly get a public URL like `https://random-name.netlify.app`. Done.
(Equivalent: **Cloudflare Pages** direct upload, or **Vercel**.)

- To update later, drag the new `index.html` again, or connect the folder for auto-deploys.
- You can add a custom domain in the dashboard for free.

## Option B — Free + permanent + versioned (GitHub Pages)

1. Create a GitHub repo (e.g. `edge-studio`) and add `index.html` to it.
2. Repo **Settings → Pages → Build and deployment → Source: Deploy from a branch**, pick
   `main` / root, Save.
3. Your site goes live at `https://<your-username>.github.io/edge-studio/` in a minute or two.

## Option C — Quick throwaway link

- **tiiny.host** (upload the file, get a link) or **surge.sh** (`npx surge index.html`).
  Good for sharing temporarily.

---

## Keeping the odds current online (the one wrinkle)

The deployed page shows the odds **as of the last time you deployed** — it's a snapshot,
because there is no live backend. Visitors' own inputs (odds they type, games they select)
persist in *their* browser via localStorage, but the embedded prefilled odds are fixed at
deploy time. Two ways to keep it fresh:

1. **Manual (simplest):** whenever you run `rebuild.py` locally (or the daily task does), copy
   the new `wc-betting-studio.html` to `index.html` and re-deploy (re-drag to Netlify, or
   `git commit && push` for Pages). One command + one upload.

2. **Automatic (GitHub Actions):** host the whole repo (the Python pipeline + `results.csv` +
   `app_odds.json` + `market_odds.json`) on GitHub and add a scheduled workflow that runs
   `python rebuild.py`, commits the regenerated `index.html`, and lets Pages serve it. This
   makes the public site self-updating. It's a moderate setup (a `.github/workflows/*.yml`
   running Python on a cron) — ask and I can write that workflow for you.

---

## Before you share it publicly

- **Keep the disclaimer.** The footer already says "manages process and variance, not a
  guaranteed edge … not betting advice." Leave it in.
- **It's a tool, not a tipster.** The honest framing (model anchored to the market, CLV near
  zero) is a feature — present it as a probability/See-the-math explorer.
- **Host policies:** plain static hosting of betting-strategy content is generally fine on
  Netlify/Cloudflare/GitHub Pages. Ad networks and app stores are stricter about gambling, so
  avoid bolting on ads without checking their rules.
- **No personal data** is collected or sent anywhere — everything runs in the visitor's
  browser — which keeps privacy/compliance simple.
