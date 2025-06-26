
# 📈 Trading Bot Dashboard – Backend

This project is the backend component of a trading signal dashboard. It provides RESTful APIs to retrieve stock/crypto prices and generate/store technical indicators like RSI, MACD, Bollinger Bands, and Volume Spikes.

---

## 🧠 Features

- Built with **Flask** + **PostgreSQL**
- Retrieves and stores historical prices (Yahoo Finance)
- Detects basic price-based events (DROP_ALERT, MA_CROSS)
- Computes technical indicators: **RSI**, **MACD**, **Bollinger Bands**, and **Volume Spikes**
- REST API returns price data and generated signals
- Modular architecture — easy to add more indicators

---

## 🗃️ Database Schema

### `prices`
| Column     | Type     | Notes               |
|------------|----------|---------------------|
| ticker     | TEXT     | Stock or crypto ID  |
| price      | REAL     | Closing price       |
| volume     | BIGINT   | Daily trade volume  |
| timestamp  | TIMESTAMP| Default = now       |

### `signals`
Stores basic, logic-triggered events.

### `generated_signals`
Stores calculated indicators like RSI, MACD, etc.

| Column          | Type      |
|-----------------|-----------|
| id              | SERIAL    |
| ticker          | TEXT      |
| signal_type     | TEXT      |
| signal_value    | REAL      |
| signal_strength | TEXT      |
| timestamp       | TIMESTAMP |

---

## 🔌 API Endpoints

### `GET /prices/<ticker>`
Returns historical price data for a given ticker.

### `GET /signals/recent`
Returns the 10 most recent basic signals.

### `GET /signals/summary`
Returns signal type counts from `signals`.

### `GET /signals/generated/<ticker>`
Returns up to 20 recent technical indicators from `generated_signals`.

### `POST /signals/generate/<ticker>`
Triggers RSI, MACD, Bollinger, and Volume Spike signal generation for that ticker.

---

## ⚙️ Setup Instructions

### 1. Environment Variables (`config.py`)
Create a `config.py` file in the root:

```python
DB_NAME = "your_database"
DB_USER = "your_user"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"
DB_PORT = "5432"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/..."
```

### 2. Install Dependencies

```bash
pip install flask flask-cors psycopg2 pandas yfinance
```

### 3. Run the Server

```bash
python3 app.py
```

---

## 📂 File Structure

```
backend/
├── app.py                 # Flask API server
├── config.py              # DB and webhook config
├── db_insert.py           # Price + signal insertion logic
├── db_query.py            # Manual DB testing (optional)
├── price_fetcher.py       # Yahoo Finance fetch loop
├── signals_engine.py      # RSI, MACD, Bollinger, Volume
└── README.md              # This file
```

---

## 🔄 Next Steps

- [ ] Add ticker metadata (stock vs. crypto)
- [ ] Connect frontend dashboard
- [ ] Add breakout signals
- [ ] Deploy with automated scheduling
