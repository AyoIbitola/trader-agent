# Trader-Agent

Trader-Agent is an AI-powered Forex signal dashboard and Telegram bot. It fetches live market data, generates trading signals, and delivers them via a web dashboard and Telegram.

## Features

- **Live Candlestick Charts**: Visualize real-time Forex data from OANDA.
- **AI Signal Generation**: Get buy/sell signals for major currency pairs.
- **Telegram Bot**: Receive signals automatically or on demand, with options to stop/resume notifications.
- **Auto-Refresh Dashboard**: Stay updated with the latest market moves.
- **Signal History**: Review past predictions and performance.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit
- **Bot**: python-telegram-bot
- **Broker API**: OANDA (via oandapyV20)
- **Data**: Pandas, Plotly

## Setup

1. **Clone the repository**
   ```sh
   git clone https://github.com/yourusername/Trader-Agent.git
   cd Trader-Agent
   ```

2. **Create a virtual environment**
   ```sh
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate # Mac/Linux
   ```

3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   - Create a `.env` file in the root directory:
     ```
     OANDA_API_KEY=your_oanda_api_key
     TELEGRAM_BOT_TOKEN=your_telegram_bot_token
     FAST_API_URL=http://127.0.0.1:8000
     ```

5. **Run the backend**
   ```sh
   uvicorn backend.main:app --reload
   ```

6. **Run the Streamlit dashboard**
   ```sh
   streamlit run streamlit_app.py
   ```

7. **Start the Telegram bot**
   - The bot runs automatically with the backend, or you can run `backend/telegram_bot.py` directly.

## Usage

- Open the Streamlit dashboard in your browser.
- Interact with the Telegram bot using `/start` and `/predict`.
- Monitor live signals and charts.

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

## License

MIT License

---

**Note:** You need valid OANDA and Telegram credentials to use all features.