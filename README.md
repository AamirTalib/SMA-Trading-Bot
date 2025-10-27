# 🧠 SMA Trading Bot (Alpaca Paper)

A simple automated trading bot that:
- Pulls **1-minute bar data** from the Alpaca Paper Trading API  
- Runs a **5/20 Simple Moving Average (SMA)** crossover strategy  
- Places **bracket orders** (entry + stop-loss + take-profit)  
- Trades **only on signal change** to avoid overtrading  
- Automatically pauses **when the market is closed**  
- Logs all activity to `trades_log.csv` for later performance analysis  

> ⚡️ Inspired by [this tutorial](https://www.youtube.com/watch?v=b3VFMdjBfKA), then extended by **Aamir Talib** with:
> - Stop-loss / take-profit bracket logic  
> - Market-hours guard  
> - Signal-change detection  
> - Trade & PnL CSV logging  
> - Environment variable security via `.env`  

---

## 🧰 Setup

### 1️⃣ Install Dependencies
Make sure you have Python ≥ 3.9 installed.  
Open your terminal inside the project folder and run:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
This installs:
alpaca-trade-api → Connects to Alpaca’s API
python-dotenv → Loads API keys securely
pandas → Calculates SMAs and logs trades
2️⃣ Create a .env File (⚠️ Do NOT commit this)
In the root of the project (same folder as simpleTradingBot.py), create a file named .env containing:
APCA_API_KEY_ID=YOUR_KEY
APCA_API_SECRET_KEY=YOUR_SECRET
APCA_API_BASE_URL=https://paper-api.alpaca.markets
APCA_API_VERSION=v2
This file keeps your secrets private.
The bot automatically reads these values when it runs.
3️⃣ Edit Your Tickers (Optional)
Open simpleTradingBot.py and update the ticker list:
TICKERS = ["AAPL", "MSFT", "GOOGL", "XOM", "SPY"]
These are safe, large-cap / ETF tickers for testing.
You can change them to any Alpaca-supported symbols.
4️⃣ Run the Bot
python simpleTradingBot.py
✅ During market hours (9:30 AM – 4:00 PM ET) → executes one trading cycle per minute.
🌙 After hours → sleeps for ~5 minutes and checks again automatically.