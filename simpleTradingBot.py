from alpaca_trade_api.rest import REST, TimeFrame
from datetime import datetime
from dotenv import load_dotenv
import csv
import os
import time

load_dotenv()

# --- ALPACA CONFIG ---
API_KEY  = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
TICKERS = ["AAPL", "MSFT", "GOOGL", "XOM", "SPY"]

# Risk Parameters
STOP_PCT = 0.02          # 2% stop below entry
TAKE_PROFIT_PCT = 0.04   # 4% take-profit above entry
MIN_TICK = 0.01          # U.S. equities minimum tick

# Behavior
TRADE_ON_SIGNAL_CHANGE = True  # only place an order when the signal flips
DRY_RUN = False                # if True, prints intended trades but does not send orders


# INIT
api = REST(API_KEY, API_SECRET, BASE_URL)

LOG_FILE = "trades_log.csv"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        csv.writer(f).writerow([
            "timestamp", "symbol", "event", "qty", "price",
            "stop_price", "take_profit_price",
            "equity", "daily_pnl", "note"
        ])

# remember last signal per symbol
last_signal = {}  


# UTILS
def market_is_open():
    clock = api.get_clock()
    return clock.is_open

def sleep_until_next_minute():
    # Align to 1-minute bars without busy-waiting
    now = datetime.now()
    secs = 60 - now.second
    # Small guard in case exactly on boundary
    time.sleep(1 if secs == 60 else secs)
    
def account_metrics():
    """Return (equity, daily_pnl) as floats."""
    acct = api.get_account()
    equity = float(acct.equity)
    last_equity = float(getattr(acct, "last_equity", equity))
    return equity, (equity - last_equity)


def log_row(symbol, event, qty=0, price=None, stop=None, tp=None, note=""):
    equity, daily_pnl = account_metrics()
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([
            datetime.now().isoformat(timespec="seconds"),
            symbol, event, qty, price, stop, tp, equity, daily_pnl, note
        ])


def simple_moving_average_strat(df):
    """5/20 SMA crossover -> 'buy' / 'sell' / 'hold'."""
    df["sma_fast"] = df["close"].rolling(window=5).mean()
    df["sma_slow"] = df["close"].rolling(window=20).mean()

    fast = df["sma_fast"].iloc[-1]
    slow = df["sma_slow"].iloc[-1]

    if fast > slow:
        return "buy"
    elif fast < slow:
        return "sell"
    else:
        return "hold"


def get_long_qty(symbol) -> int:
    """Return current long quantity (0 if flat or short)."""
    try:
        for p in api.list_positions():
            if p.symbol == symbol:
                q = int(p.qty)
                return q if q > 0 else 0
    except Exception:
        pass
    return 0


def cancel_open_orders(symbol):
    """Cancel any open orders for the symbol (prevents qty drift)."""
    try:
        for o in api.list_orders(status="open"):
            if o.symbol == symbol:
                api.cancel_order(o.id)
    except Exception as e:
        print(f"[WARN] cancel_open_orders {symbol}: {e}")


def place_order(signal, symbol, qty):
    """
    BUY  -> bracket order (market entry + stop + take-profit), enforces >= $0.01 spacing.
    SELL -> cancel open orders, then flatten any existing long qty at market.
    """
    # last price from most recent 1m bar
    bar = api.get_bars(symbol, TimeFrame.Minute, limit=1).df.iloc[-1]
    px = float(bar.close)

    if signal == "buy":
        # skip if already long
        if get_long_qty(symbol) > 0:
            print(f"[INFO] {symbol} already long; skipping buy.")
            log_row(symbol, "info", note="already long; skip buy")
            return

        # Compute Stop Loss / Take Profit and enforce tick spacing
        raw_stop = px * (1 - STOP_PCT)
        raw_tp   = px * (1 + TAKE_PROFIT_PCT)

        stop_price = round(min(raw_stop, px - MIN_TICK), 2)
        take_profit_price = round(max(raw_tp,   px + MIN_TICK), 2)

        # Final guard after rounding
        if take_profit_price < px + MIN_TICK:
            take_profit_price = round(px + MIN_TICK, 2)
        if stop_price > px - MIN_TICK:
            stop_price = round(px - MIN_TICK, 2)

        if DRY_RUN:
            print(f"[DRY] BUY {symbol} ~{px} SL={stop_price} TP={take_profit_price} qty={qty}")
            log_row(symbol, "dry_buy", qty, px, stop_price, take_profit_price)
            return

        try:
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                type="market",
                time_in_force="gtc",
                order_class="bracket",
                take_profit={"limit_price": take_profit_price},
                stop_loss={"stop_price": stop_price},
            )
            print(f"[TRADE] BUY {symbol} @ ~{px}  SL={stop_price}  TP={take_profit_price}")
            log_row(symbol, "buy", qty, px, stop_price, take_profit_price, note="bracket buy")
        except Exception as e:
            print(f"[ERROR] submit_order BUY {symbol}: {e}")
            log_row(symbol, "error_buy", qty, px, stop_price, take_profit_price, note=str(e))

    elif signal == "sell":
        long_qty = get_long_qty(symbol)
        if long_qty <= 0:
            print(f"[INFO] {symbol} not long; skipping sell.")
            log_row(symbol, "info", note="not long; skip sell")
            return

        cancel_open_orders(symbol)

        if DRY_RUN:
            print(f"[DRY] SELL {symbol} flatten qty={long_qty} @ ~{px}")
            log_row(symbol, "dry_sell", long_qty, px)
            return

        try:
            # Sell exactly the current long qty
            api.submit_order(
                symbol=symbol,
                qty=long_qty,
                side="sell",
                type="market",
                time_in_force="gtc",
            )
            print(f"[TRADE] SELL {symbol} qty={long_qty} (flatten long)")
            log_row(symbol, "sell", qty=long_qty, price=px, note="flatten long")
        except Exception as e:
            print(f"[ERROR] close/flatten {symbol}: {e}")
            log_row(symbol, "error_sell", note=str(e))


# MAIN LOOP
if __name__ == "__main__":
    while True:
        # --- Check if market is open ---
        if not market_is_open():
            print(f"[INFO] Market closed — sleeping (now {datetime.now().strftime('%H:%M:%S')})")
            time.sleep(300)  # sleep for 5 minutes when market is closed
            continue

        # === Trading pass across all tickers ===
        for ticker in TICKERS:
            bars = api.get_bars(ticker, TimeFrame.Minute, limit=100).df
            signal = simple_moving_average_strat(bars)
            last_px = float(bars["close"].iloc[-1])

            # Log the current signal and price
            log_row(ticker, f"signal={signal}", price=last_px)

            # Trade only if the signal changed
            if TRADE_ON_SIGNAL_CHANGE:
                prev = last_signal.get(ticker)
                if prev == signal:
                    print(f"[INFO] {ticker} signal unchanged ({signal}); no trade.")
                    continue
                last_signal[ticker] = signal

            # Print and execute new signal
            print(f"[SIGNAL] {ticker}: {signal}")
            if signal in ("buy", "sell"):
                place_order(signal, ticker, qty=1)

        # Align loop to next 1-minute bar
        sleep_until_next_minute()
