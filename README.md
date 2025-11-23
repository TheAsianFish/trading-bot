# 🧠 Trading Bot Dashboard (Fullstack)

An advanced trading signal dashboard and automation system built with **React**, **Flask**, and **PostgreSQL**. Designed to visualize prices, detect technical indicators and trading events, monitor them in a clean UI, and automated on **AWS Lambda**, **Elastic Beanstalk**, and other cloud services.

> ⚙️ Built for eventual real-time performance, quantitative strategy expansion, and backend signal pipelines for auto-trading.

---

## 🚀 Overview
The backend uses Flask as the main API layer and connects to a PostgreSQL database containing price history and generated signals. AWS Lambda handles automated data ingestion and signal generation, while Elastic Beanstalk hosts the API used by the frontend.
The frontend is built with React, Vite, and Tailwind, providing an interactive interface for viewing price charts and recent signals. It communicates directly with the Flask API and requires only an API base URL.

### 🔧 Backend (Flask + PostgreSQL)
- REST API for prices, indicators, and signal summaries
- Auto-generates signals like:
  - **RSI**, **MACD**, **Bollinger Bands**, **MA Crosses**, **Volume Spikes**
- Modular signal engine for future quant/AI logic
- Data collection via **Yahoo Finance** (yfinance)
- Organized in PostgreSQL tables (`prices`, `signals`, `generated_signals`)
- Webhook-ready for Discord or trading alerts

### 💻 Frontend (React + Vite + Tailwind)
- Interactive dashboard with:
  - 📈 Price Chart
  - 🧠 Generated Signals
  - 📊 Signal Summary
  - 📝 Recent Signals
- Filters by ticker, signal type, and date range
- Light/dark theme support
- Table and chart views for clarity
- Responsive layout with real-time updates planned

---

## 🗃️ Folder Structure

```
trading-bot/
├── backend/           # Flask API, signal engine, database access
│   ├── app.py
│   ├── config.py
│   ├── db_insert.py
│   ├── db_query.py
│   ├── price_fetcher.py
│   ├── signals_engine.py
│   └── README.md
│
├── frontend/          # React + Vite + Tailwind frontend
│   ├── index.html
│   ├── vite.config.js
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── components/
│   │   │   ├── PriceChart.jsx
│   │   │   ├── SignalSummary.jsx
│   │   │   ├── GeneratedSignals.jsx
│   │   │   └── TriggerSignals.jsx
│   └── README.md
└── README.md          # Project-wide summary
```

---

## ⚙️ Backend Setup Instructions

### 1. Create `config.py`

```python
DB_NAME = "your_db"
DB_USER = "your_user"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"
DB_PORT = "5432"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/..."

# Optional feature toggles
ENABLE_ALERTS = True
ALERT_COOLDOWN_MIN = 30
LOOKBACK_BARS = 400
ENABLE_REGIME_FILTER = True
THRESHOLD_PCT = 0.03
THRESHOLD_POSTURE = "momentum"
```

### 2. Install Requirements

```bash
pip install flask flask-cors psycopg2 pandas yfinance
```

### 3. Run the Server

```bash
python backend/app.py
```

### 3. Initialize the Database (first time only)
```bash
python backend/db_setup.py
```

---

## 🔌 API Endpoints

- `GET /health` — simple health check
- `GET /prices/<ticker>` — returns price history
- `GET /signals/recent` — returns 10 latest logic-based signals
- - `GET /signals/by/<ticker>` — returns signals for a specific ticker
- `GET /signals/summary` — returns signal counts by type
- `POST /signals/generate/<ticker>` — forces generation of all signals for ticker

---

## 📊 Database Schema Overview

### `prices`
| Column     | Type     | Description          |
|------------|----------|----------------------|
| ticker     | TEXT     | Stock/crypto symbol  |
| price      | REAL     | Latest price         |
| volume     | BIGINT   | Daily volume         |
| timestamp  | TIMESTAMP| Time of record       |

### `signals`
| Column         | Type       |
|----------------|------------|
| id             | SERIAL     |
| ticker         | TEXT       |
| signal_type    | TEXT       |
| signal_value   | REAL       |
| strategy       | TEXT       |
| confidence     | REAL       |
| action         | TEXT       |
| strength       | TEXT       |
| ...            | ...        |
| timestamp      | TIMESTAMPZ |

---

## 🧠 Signal Types (So Far)

- **RSI** — overbought/oversold momentum
- **MACD** — moving average crossovers
- **BOLLINGER** — price volatility bands
- **MA Cross** — 50/200-day golden/death crosses
- **THRESHOLD** — daily open percentage move model

---

## 🌐 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Set API base URL

VITE_API_BASE=https://your-elastic-beanstalk-url

---

## ✅ TODO / Future Roadmap

- [ ] Expand automated AWS workflows
- [ ] Add additional technical indicators such as breakouts, reversals, candlestick patterns, etc.
- [ ] Add multi-signal confirmation models and scoring
- [ ] Improve frontend charting and filtering tools
- [ ] Improve frontend UI/UX
- [ ] Build optional trading execution layer through external APIs
- [ ] Build web-scraping service for news and real-time updates for each ticker
- [ ] Prepare the project for open-source contribution

---

## 🔒 Security / Deployment Notes

- Never expose `config.py` in production
- Always use secure AWS IAM roles
- Keep PostgreSQL credentials private
- Separate public dashboard vs. private trading logic
- Consider FastAPI if switching to async/microservices

---

## 👤 Author

**Patrick Chung**  
Built as a scalable research and automation platform for modern trading strategies.

---
