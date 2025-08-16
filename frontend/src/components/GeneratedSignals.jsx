// components/GeneratedSignals.jsx
import { useEffect, useState } from 'react';

const API_BASE = import.meta.env?.VITE_API_BASE || (typeof window !== 'undefined' && window.__API_BASE__) || '';

function GeneratedSignals({ ticker }) {
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState({ BUY: true, SELL: true, NEUTRAL: true });

  useEffect(() => {
    if (!ticker || !API_BASE) return;
    fetch(`${API_BASE}/signals/by/${encodeURIComponent(ticker)}?limit=100`)
      .then(res => res.json())
      .then(setRows)
      .catch(err => console.error('Error fetching generated signals:', err));
  }, [ticker]);

  const filtered = Array.isArray(rows) ? rows.filter(r => filter[r.action ?? 'NEUTRAL']) : [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded shadow p-4">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><span role="img">🧠</span> Generated Signals</h2>

      <div className="flex gap-4 mb-4 text-sm">
        {['BUY','SELL','NEUTRAL'].map(type => (
          <label key={type} className="flex items-center gap-1">
            <input type="checkbox" checked={filter[type]} onChange={() => setFilter(p => ({...p, [type]: !p[type]}))}/>
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
              <th className="px-4 py-2 border dark:border-gray-600">Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r, i) => {
              const color =
                r.action === 'BUY' ? 'text-green-700 font-semibold'
                : r.action === 'SELL' ? 'text-red-700 font-semibold'
                : 'text-gray-600';
              return (
                <tr key={i} className="border-t dark:border-gray-600">
                  <td className="px-4 py-2">{r.signal_type}</td>
                  <td className="px-4 py-2">{new Date(r.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-2">{typeof r.signal_value === 'number' ? r.signal_value.toFixed(4) : ''}</td>
                  <td className={`px-4 py-2 uppercase ${color}`}>{r.action}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : <p className="text-gray-500 dark:text-gray-400 text-sm">No signals generated yet for {ticker}.</p>}
    </div>
  );
}
export default GeneratedSignals;
