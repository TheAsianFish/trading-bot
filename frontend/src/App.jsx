import React, { useState } from "react";
import PriceChart from "./components/PriceChart";
import UnifiedSignalsTable from "./components/UnifiedSignalsTable";

export default function App() {
  const [selectedTicker, setSelectedTicker] = useState("AAPL");
  const [selectedRange, setSelectedRange] = useState("24h");

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Trading Dashboard</h1>

      {/* Chart Controls */}
      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-2">📊 Chart Controls</h2>
        <div className="flex items-center gap-2 mb-2">
          <label>Select Ticker:</label>
          <select
            value={selectedTicker}
            onChange={(e) => setSelectedTicker(e.target.value)}
            className="border p-1"
          >
            <option value="AAPL">AAPL</option>
            <option value="MSFT">MSFT</option>
            <option value="GOOGL">GOOGL</option>
            <option value="TSLA">TSLA</option>
            <option value="AMZN">AMZN</option>
            <option value="META">META</option>
            <option value="NVDA">NVDA</option>
            <option value="BTC-USD">BTC-USD</option>
            <option value="ETH-USD">ETH-USD</option>
            <option value="SOL-USD">SOL-USD</option>
            <option value="^GSPC">S&P 500</option>
          </select>

          <label>Range:</label>
          <div className="flex gap-2">
            {["24h", "7d", "30d", "90d", "All"].map((r) => (
              <button
                key={r}
                onClick={() => setSelectedRange(r)}
                className={`px-2 py-1 border ${
                  selectedRange === r ? "bg-blue-200" : "bg-white"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="px-3 py-1 bg-blue-500 text-white rounded"
        >
          Refresh All Data
        </button>
      </section>

      {/* Price Chart */}
      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-2">📈 Price Chart</h2>
        <PriceChart ticker={selectedTicker} range={selectedRange} />
      </section>

      {/* Unified Signals Table */}
      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-2">🧾 Unified Signals</h2>
        <UnifiedSignalsTable />
      </section>
    </div>
  );
}
