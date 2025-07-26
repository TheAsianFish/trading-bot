// components/GeneratedSignals.jsx

import { useEffect, useState } from 'react';

function GeneratedSignals({ ticker }) {
  const [data, setData] = useState([]);
  const [filter, setFilter] = useState({ BUY: true, SELL: true, NEUTRAL: true });

  const API_BASE = "http://Trading-bot-backend-env.eba-mztx8vdc.us-east-2.elasticbeanstalk.com";

  useEffect(() => {
    if (!ticker) return;
    fetch(`${API_BASE}/signals/generated/${ticker}`)
      .then((res) => res.json())
      .then((res) => setData(res))
      .catch((err) => console.error('Error fetching generated signals:', err));
  }, [ticker]);

  const filtered = Array.isArray(data) ? data.filter(item => filter[item.signal_strength]) : [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded shadow p-4">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <span role="img">🧠</span> Generated Signals
      </h2>

      {/* Toggle Filter */}
      <div className="flex gap-4 mb-4 text-sm">
        {['BUY', 'SELL', 'NEUTRAL'].map(type => (
          <label key={type} className="flex items-center gap-1">
            <input
              type="checkbox"
              checked={filter[type]}
              onChange={() => setFilter(prev => ({ ...prev, [type]: !prev[type] }))}
            />
            <span>{type}</span>
          </label>
        ))}
      </div>

      {filtered.length > 0 ? (
        <table className="w-full text-sm border border-gray-300 dark:border-gray-600">
          <thead>
            <tr className="bg-gray-100 dark:bg-gray-700 text-left">
              <th className="px-4 py-2 border dark:border-gray-600">📈 Indicator</th>
              <th className="px-4 py-2 border dark:border-gray-600">🕒 Timestamp</th>
              <th className="px-4 py-2 border dark:border-gray-600">Value</th>
              <th className="px-4 py-2 border dark:border-gray-600">Signal</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item, idx) => {
              const { signal_type, timestamp, signal_value, signal_strength } = item;
              const colorClass =
                signal_strength === 'BUY'
                  ? 'text-green-700 font-semibold'
                  : signal_strength === 'SELL'
                  ? 'text-red-700 font-semibold'
                  : 'text-gray-600';

              return (
                <tr key={idx} className="border-t dark:border-gray-600">
                  <td className="px-4 py-2">{signal_type}</td>
                  <td className="px-4 py-2">{new Date(timestamp).toLocaleString()}</td>
                  <td className="px-4 py-2">{signal_value}</td>
                  <td className={`px-4 py-2 uppercase ${colorClass}`}>{signal_strength}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : (
        <p className="text-gray-500 dark:text-gray-400 text-sm">No signals generated yet for {ticker}.</p>
      )}
    </div>
  );
}

export default GeneratedSignals;
