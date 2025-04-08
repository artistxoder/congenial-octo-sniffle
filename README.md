# 🤖 Discord AI Auto Mod Bot

A lightweight AI-powered moderation bot for Discord built in **Python**. It includes auto-moderation, crypto and stock price commands, and uses the **Finnhub API** for financial data.

---

## 🔧 Features

- 🚫 **Auto Moderation** – Blocks toxic/banned words automatically
- 💬 **Command System**
  - `!stock [symbol]` – Get real-time stock prices
  - `!crypto [symbol]` – Get real-time cryptocurrency prices
- 🧠 **AI Ready** – Easily extendable to use AI for smarter moderation
- ⚙️ **Configurable via `.env`**

---

## 📦 Requirements

- Python 3.9+
- `discord.py`
- `requests`
- `.env` file with the following:

```env
TOKEN=your_discord_bot_token
FINNHUB_API_KEY=your_finnhub_api_key
