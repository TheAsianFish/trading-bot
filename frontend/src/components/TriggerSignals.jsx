// components/TriggerSignals.jsx
import { useState } from 'react';
const API_BASE = import.meta.env?.VITE_API_BASE || (typeof window !== 'undefined' && window.__API_BASE__) || '';

function TriggerSignals({ ticker, onRefresh }) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const handleGenerate = async () => {
    setLoading(true); setStatus(null);
    try {
      const res = await fetch(`${API_BASE}/signals/generate/${encodeURIComponent(ticker)}`, { method: 'POST' });
      const result = await res.json();
      setStatus(result.status || result.error || 'Unknown response');
      if (onRefresh) onRefresh();
    } catch {
      setStatus('❌ Failed to generate signals.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded shadow p-4">
      <h2 className="text-xl font-bold mb-2">⚙️ Generate Signals</h2>
      <button onClick={handleGenerate} disabled={loading}
        className={`px-4 py-2 rounded text-white transition ${loading? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'}`}>
        {loading ? 'Generating...' : `Run Analysis for ${ticker}`}
      </button>
      {status && <p className="mt-3 text-sm text-gray-700">{status}</p>}
    </div>
  );
}
export default TriggerSignals;
