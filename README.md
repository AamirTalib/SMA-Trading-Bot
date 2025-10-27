# 🧠 SMA Trading Bot (Using Alpaca Paper Trading)

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

### 🔒 Environment Variables
This project uses a `.env` file to securely store private API credentials (e.g., `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`).  
Never commit this file to GitHub — it's automatically excluded via `.gitignore`.  
To run the bot locally, create your own `.env` file in the project root and add your personal Alpaca keys:
