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

