# 🧠 Trading Bot Dashboard (Fullstack)

An advanced trading signal dashboard and automation system built with **React**, **Flask**, and **PostgreSQL**. Designed to detect technical indicators and trading events, visualize them in a clean UI, and prepare for future **AWS automation** and **algorithmic trading integration**.

> ⚙️ Built for eventual real-time performance, quantitative strategy expansion, and backend signal pipelines for auto-trading.

---

## 🚀 Features

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
```

### 2. Install Requirements

```bash
pip install flask flask-cors psycopg2 pandas yfinance
```

### 3. Run the Server

```bash
python app.py
```

---

## 🔌 API Endpoints

- `GET /prices/<ticker>` — returns price history
- `GET /signals/recent` — returns 10 latest logic-based signals
- `GET /signals/summary` — returns signal counts by type
- `GET /signals/generated/<ticker>` — technical indicators like RSI/MACD
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

### `generated_signals`
| Column          | Type      |
|-----------------|-----------|
| id              | SERIAL    |
| ticker          | TEXT      |
| signal_type     | TEXT      |
| signal_value    | REAL      |
| signal_strength | TEXT      |
| timestamp       | TIMESTAMP |

---

## 🧠 Signal Types (So Far)

- **RSI** — overbought/oversold momentum
- **MACD** — moving average crossovers
- **BOLLINGER** — price volatility bands
- **MA Cross** — 50/200-day golden/death crosses
- **VOLUME** — spike detection for trend changes

---

## 🌐 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## ✅ TODO / Future Roadmap

- [ ] Automate price and signal generation via AWS
- [ ] Add breakout, reversal, candlestick, and multi-signal detectors
- [ ] Full trading bot integration with execution via API
- [ ] Quant + ML model experimentation
- [ ] Auth and multi-user dashboards

---

## 🔒 Security / Deployment Notes

- Never expose `config.py` in production
- Separate public dashboard vs. private trading logic
- Consider FastAPI if switching to async/microservices

---

## 👤 Author

**Patrick Chung**  
Built as a research-backed production tool to compete and match against existing trading bots.

---
