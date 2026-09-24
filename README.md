# stock-alert-bot

A small Telegram bot for long-term holders who don't want to open their broker app every day.
It checks your stocks every 30 minutes and messages you only when something worth knowing happens:

- a stock is **up X% in a day, week or month** (you pick the thresholds)
- a stock **reaches a target price** you set

```
📈 Price alert — up 21.4% this month
AAPL (Apple)  337.02 USD
Day:   🔴 -0.8%
Week:  🟢 +6.3%
Month: 🟢 +21.4%
vs your buy price (250.00): 🟢 +34.8%
```

Prices come from Yahoo Finance, so it works with most stocks, ETFs and crypto worldwide. No API key or paid data needed.

---

## Quick start (about 5 minutes, no coding)

You need a Telegram account, a GitHub account and a [Railway](https://railway.com) account. Railway runs the bot 24/7 and costs cents to a few dollars a month.

### Step 1: Make your Telegram bot (1 min)

1. In Telegram, search for **@BotFather** and send `/newbot`.
2. Pick a name and a username ending in `bot`. BotFather replies with a **token** like `123456:ABC-xyz...`. Copy it.
3. Open your new bot and press **Start**. It can't message you until you do this.

### Step 2: Get your chat ID (30 sec)

Open this in your browser, with your token pasted in:

```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

Look for `"chat":{"id":123456789`. That number is your **chat ID**.
If you see `"result":[]`, send your bot a message and refresh the page.

### Step 3: Write your watchlist (2 min)

List the stocks you want to watch, using their [Yahoo Finance](https://finance.yahoo.com) symbols:

```json
{
  "thresholds": { "day_pct": 10, "week_pct": 20, "month_pct": 30 },
  "tickers": {
    "AAPL":      { "label": "Apple", "buy_price": 250 },
    "VOLV-B.ST": { "label": "Volvo B", "target_price": 350 },
    "BTC-USD":   { "label": "Bitcoin" }
  }
}
```

See [watchlist options](#watchlist-options) below for everything you can set.

### Step 4: Deploy on Railway (1 min)

1. **Fork** this repo (top-right button on GitHub).
2. On Railway, click **New Project**, choose **Deploy from GitHub repo** and pick your fork.
3. Open the service, go to **Variables** and add:

| Variable | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | your token from step 1 |
| `TELEGRAM_CHAT_ID` | your chat ID from step 2 |
| `WATCHLIST_JSON` | your whole watchlist from step 3, pasted as-is |

That's it. Railway builds and starts the bot. Open the **Deployments** tab and check the logs: you should see one line per ticker, like `[AAPL] 337.02 d-0.8% w+1.4% m+8.6%`.

**Recommended:** attach a **Volume** mounted at `/data` and add the variable `STATE_FILE=/data/state.json`. Otherwise the bot forgets which alerts it already sent each time it redeploys, and may send one again.

Your holdings stay private. They live in Railway variables, not in your fork.

---

## Watchlist options

| Field | Where | Meaning |
|---|---|---|
| `day_pct` / `week_pct` / `month_pct` | `thresholds` | Default % rise that triggers an alert, for all tickers |
| `day_pct` / `week_pct` / `month_pct` | per ticker | Override the threshold for that ticker only |
| `buy_price` | per ticker | Adds a "vs your buy price" line |
| `target_price` | per ticker | Alerts once when the price reaches it |
| `label` | per ticker | A readable name shown next to the ticker |

Every field is optional except the ticker itself. `"TSLA": {}` works fine.

**Finding ticker symbols:** search the company on [finance.yahoo.com](https://finance.yahoo.com) and use the symbol shown there.

| Market | Example |
|---|---|
| US | `AAPL`, `GME` |
| Stockholm | `VOLV-B.ST` |
| Oslo | `EQNR.OL` |
| Toronto | `SHOP.TO` |
| London | `VOD.L` |
| Crypto | `BTC-USD`, `XRP-USD` |

Most mutual funds and some ETPs aren't on Yahoo. If one doesn't work, try following its underlying asset instead, for example `XRP-USD` for an XRP ETP.

**How alerts avoid spamming you:** each alert type has a waiting period before it can fire again for the same ticker. A day alert waits 1 day, a week alert 7 days and a month alert 30 days. A target alert fires once, then re-arms after the price drops back below the target. "Week" means 5 trading days and "month" means 21 trading days.

---

## Run it on your own computer instead

This works only while your computer is on and awake. It's handy for testing.

```bash
git clone https://github.com/exexexexe/stock-alert-bot.git
cd stock-alert-bot
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

cp .env.example .env                        # paste your token and chat ID
cp watchlist.example.json watchlist.json    # add your tickers

.venv/bin/python stock_alert.py --chat-id   # prints your chat ID (message the bot first)
.venv/bin/python stock_alert.py --status    # sends current numbers for every ticker now
.venv/bin/python stock_alert.py             # runs forever, checking every 30 min
.venv/bin/python stock_alert.py --once      # one check, for cron/launchd
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `400 Bad Request: chat not found` | You haven't pressed **Start** on your bot, or the chat ID is wrong. Message the bot, then repeat step 2. |
| `401 Unauthorized` | The bot token is wrong or has extra spaces. Copy it from BotFather again. |
| `[TICKER] fetch failed` | Yahoo doesn't know that symbol. Check it on finance.yahoo.com. |
| Railway logs are empty | Check the **Build Logs** tab for install errors. |
| No alerts at all | Probably nothing has risen past your thresholds yet. Temporarily set `"day_pct": 0` to test. |

Never commit your bot token or share it. Anyone who has it can control your bot. `.env`, `watchlist.json` and `state.json` are already gitignored.

## License

MIT
