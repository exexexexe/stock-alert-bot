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

The same alert doesn't fire again right away. A day alert can repeat after 1 day, a week alert after 7 and a month alert after 30. A target alert re-arms once the price drops back below the target.

Prices come from Yahoo Finance, so it works with most stocks, ETFs and crypto worldwide. No API key needed.

## 1. Create your Telegram bot

1. In Telegram, message **@BotFather**, send `/newbot` and copy the token.
2. Open your new bot and press **Start**. The bot can't message you until you've messaged it first.

## 2. Run it locally

```bash
git clone https://github.com/<you>/stock-alert-bot.git
cd stock-alert-bot
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

cp .env.example .env                        # paste your bot token
.venv/bin/python stock_alert.py --chat-id   # prints your chat id → put it in .env

cp watchlist.example.json watchlist.json    # add your own tickers
.venv/bin/python stock_alert.py --status    # sends the current numbers to Telegram
.venv/bin/python stock_alert.py             # runs forever, checking every 30 min
```

## 3. Configure your watchlist

```json
{
  "thresholds": { "day_pct": 10, "week_pct": 20, "month_pct": 30 },
  "tickers": {
    "AAPL":      { "label": "Apple", "buy_price": 250, "target_price": 360 },
    "VOLV-B.ST": { "label": "Volvo B", "week_pct": 8 },
    "BTC-USD":   { "label": "Bitcoin" }
  }
}
```

| Field | Meaning |
|---|---|
| `thresholds` | Default % rise that triggers an alert, for all tickers |
| `day_pct` / `week_pct` / `month_pct` | Per-ticker override of the threshold |
| `buy_price` | Optional. Adds a "vs your buy price" line |
| `target_price` | Optional. Alerts once when the price reaches it |
| `label` | Optional. A readable name shown next to the ticker |

**Tickers use Yahoo Finance symbols.** Search [finance.yahoo.com](https://finance.yahoo.com) if you're unsure.
Examples: Stockholm `VOLV-B.ST`, Toronto `SHOP.TO`, Oslo `EQNR.OL`, London `VOD.L`, crypto `BTC-USD`.
Most mutual funds aren't on Yahoo.

"Week" means 5 trading days and "month" means 21 trading days.

## 4. Host it 24/7 on Railway

Running it on your laptop only works while the laptop is awake. To keep it always on:

1. Fork this repo.
2. On [railway.com](https://railway.com), create a new project and choose **Deploy from GitHub repo**, then pick your fork.
3. Under **Variables**, add:
   - `TELEGRAM_BOT_TOKEN`: your bot token
   - `TELEGRAM_CHAT_ID`: your chat id
   - `WATCHLIST_JSON`: your whole watchlist JSON pasted as the value. This keeps your holdings out of the public repo.
   - `CHECK_MINUTES`: optional, defaults to 30

`railway.json` already sets the start command. The bot uses very little CPU and memory, so it costs cents to a few dollars a month.

Optional: to stop repeat alerts from coming back after a redeploy, attach a volume mounted at `/data` and set `STATE_FILE=/data/state.json`.

## Privacy

`.env`, `watchlist.json` and `state.json` are gitignored. Never commit your bot token. Anyone who has it can control your bot.

## License

MIT
