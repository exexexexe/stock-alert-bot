"""Telegram alerts when watched stocks rise sharply or hit a target price.

Usage:
    python stock_alert.py            # loop forever, checking every CHECK_MINUTES
    python stock_alert.py --once     # single check (for cron / launchd)
    python stock_alert.py --status   # send current numbers for all tickers now
    python stock_alert.py --chat-id  # print your chat id (message the bot first)

Config comes from watchlist.json, or the WATCHLIST_JSON env var if set.
"""

import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests
import yfinance as yf

HERE = Path(__file__).parent
WATCHLIST = HERE / "watchlist.json"
STATE = Path(os.environ.get("STATE_FILE", HERE / "state.json"))

# How long before the same trigger may fire again for the same ticker.
COOLDOWN_DAYS = {"day": 1, "week": 7, "month": 30}


def load_env():
    env = HERE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def telegram(method, **params):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", json=params, timeout=20)
    r.raise_for_status()
    return r.json()


def send(text):
    telegram("sendMessage", chat_id=os.environ["TELEGRAM_CHAT_ID"], text=text, parse_mode="HTML")


def money(v):
    # Penny stocks need more decimals than large-caps.
    return f"{v:.4g}" if v < 1 else f"{v:,.2f}"


def pct(now, then):
    return (now / then - 1) * 100


def quote(ticker):
    t = yf.Ticker(ticker)
    closes = t.history(period="3mo", interval="1d")["Close"].dropna()
    if closes.empty:
        raise ValueError(f"no price history for {ticker}")
    price = float(closes.iloc[-1])
    # Newly listed securities may lack a full week/month; those periods become None.
    back = lambda n: pct(price, closes.iloc[-n - 1]) if len(closes) > n else None
    return {
        "ticker": ticker,
        "price": price,
        "currency": t.fast_info.get("currency") or "",
        "day": back(1),
        "week": back(5),    # 5 trading days back
        "month": back(21),  # ~21 trading days back
    }


def fmt(q, reasons=(), buy_price=None, label=None):
    arrow = lambda v: "n/a" if v is None else f"{'🟢' if v >= 0 else '🔴'} {v:+.1f}%"
    lines = []
    if reasons:
        lines.append("📈 <b>Price alert</b> — " + ", ".join(reasons))
    lines += [
        f"<b>{q['ticker']}</b>{f' ({label})' if label else ''}  {money(q['price'])} {q['currency']}",
        f"Day:   {arrow(q['day'])}",
        f"Week:  {arrow(q['week'])}",
        f"Month: {arrow(q['month'])}",
    ]
    if buy_price:
        lines.append(f"vs your buy price ({money(buy_price)}): {arrow(pct(q['price'], buy_price))}")
    return "\n".join(lines)


def check(config, state, force=False):
    today = date.today()
    thresholds = config.get("thresholds", {})
    for ticker, opts in config["tickers"].items():
        opts = opts or {}
        try:
            q = quote(ticker)
        except Exception as e:
            print(f"[{ticker}] fetch failed: {e}")
            continue

        seen = state.setdefault(ticker, {})
        reasons = []
        for period, cooldown in COOLDOWN_DAYS.items():
            limit = opts.get(f"{period}_pct", thresholds.get(f"{period}_pct"))
            last = seen.get(period)
            cooled = not last or today - date.fromisoformat(last) >= timedelta(days=cooldown)
            if limit is not None and q[period] is not None and q[period] >= limit and cooled:
                reasons.append(f"up {q[period]:.1f}% this {period}")
                seen[period] = today.isoformat()

        # Target price fires once, then re-arms after the price drops back below it.
        target = opts.get("target_price")
        if target:
            if q["price"] >= target and not seen.get("target_hit"):
                reasons.append(f"hit target {target:.2f}")
                seen["target_hit"] = True
            elif q["price"] < target:
                seen["target_hit"] = False

        print(f"[{ticker}] {money(q['price'])} " + " ".join(f"{p[0]}{q[p]:+.1f}%" if q[p] is not None else f"{p[0]}n/a" for p in COOLDOWN_DAYS)
              + (f"  -> ALERT {reasons}" if reasons else ""))
        if reasons or force:
            send(fmt(q, reasons, opts.get("buy_price"), opts.get("label")))


def main():
    sys.stdout.reconfigure(line_buffering=True)  # show logs immediately in containers
    load_env()
    args = sys.argv[1:]

    if "-h" in args or "--help" in args:
        print(__doc__)
        return

    if "--chat-id" in args:
        for u in telegram("getUpdates")["result"]:
            chat = (u.get("message") or {}).get("chat")
            if chat:
                print(chat["id"], chat.get("username") or chat.get("title"))
        return

    # WATCHLIST_JSON lets hosted deploys keep holdings out of the repo.
    config = json.loads(os.environ.get("WATCHLIST_JSON") or WATCHLIST.read_text())
    state = json.loads(STATE.read_text()) if STATE.exists() else {}

    def run(force=False):
        check(config, state, force)
        STATE.write_text(json.dumps(state, indent=2))

    if "--status" in args:
        run(force=True)
    elif "--once" in args:
        run()
    else:
        minutes = int(os.environ.get("CHECK_MINUTES", 30))
        while True:
            run()
            time.sleep(minutes * 60)


if __name__ == "__main__":
    main()
