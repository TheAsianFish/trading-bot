import { useEffect, useMemo, useState } from 'react';

const API_BASE =
  import.meta.env?.VITE_API_BASE ||
  (typeof window !== 'undefined' && window.__API_BASE__) ||
  '';

const ACTION_COLORS = {
  BUY: 'bg-green-100 text-green-800 border-green-300',
  SELL: 'bg-red-100 text-red-800 border-red-300',
  NEUTRAL: 'bg-gray-100 text-gray-700 border-gray-300',
};

function Badge({ text }) {
  const cls = ACTION_COLORS[text] || ACTION_COLORS.NEUTRAL;
  return <span className={`px-2 py-0.5 border rounded text-xs font-semibold ${cls}`}>{text}</span>;
}

function Controls({
  tickers, filters, setFilters, onRefresh, refreshing,
}) {
  return (
    <div className="flex flex-wrap gap-3 items-end mb-4">
      <div className="flex flex-col">
        <label className="text-xs font-semibold text-gray-500">Ticker</label>
        <select
          className="border p-2 rounded"
          value={filters.ticker}
          onChange={e => setFilters(f => ({ ...f, ticker: e.target.value }))}
        >
          <option value="ALL">ALL</option>
          {tickers.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      <div className="flex flex-col">
        <label className="text-xs font-semibold text-gray-500">Action</label>
        <div className="flex gap-2">
          {['BUY','SELL','NEUTRAL'].map(a => (
            <label key={a} className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={filters.actions[a]}
                onChange={() => setFilters(f => ({ ...f, actions: { ...f.actions, [a]: !f.actions[a] }}))}
              />
              <span>{a}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="flex flex-col">
        <label className="text-xs font-semibold text-gray-500">Since</label>
        <select
          className="border p-2 rounded"
          value={filters.since}
          onChange={e => setFilters(f => ({ ...f, since: e.target.value }))}
        >
          {['6h','12h','24h','7d','30d','All'].map(w => <option key={w} value={w}>{w}</option>)}
        </select>
      </div>

      <div className="flex-1 min-w-[200px] flex flex-col">
        <label className="text-xs font-semibold text-gray-500">Search (ticker / signal / message)</label>
        <input
          className="border p-2 rounded"
          placeholder="e.g. BTC-USD macd buy"
          value={filters.q}
          onChange={e => setFilters(f => ({ ...f, q: e.target.value }))}
        />
      </div>

      <div className="flex items-center gap-3 ml-auto">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={filters.auto}
            onChange={() => setFilters(f => ({ ...f, auto: !f.auto }))}
          />
          Auto-refresh
        </label>
        <button
          onClick={onRefresh}
          disabled={refreshing}
          className={`px-3 py-2 rounded text-white ${refreshing ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
        >
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
    </div>
  );
}

export default function UnifiedSignalsTable() {
  const [rows, setRows] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const [filters, setFilters] = useState({
    ticker: 'ALL',
    actions: { BUY: true, SELL: true, NEUTRAL: true },
    since: '24h',
    q: '',
    auto: true,
  });

  const tickers = useMemo(() => {
    const set = new Set(rows.map(r => r.ticker).filter(Boolean));
    return Array.from(set).sort();
  }, [rows]);

  const fetchSignals = async () => {
    if (!API_BASE) return;
    setRefreshing(true);
    try {
      // Pull a healthy chunk and filter client-side
      const res = await fetch(`${API_BASE}/signals/recent?limit=500`);
      const data = await res.json();
      setRows(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('[signals] fetch error', e);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, []);

  useEffect(() => {
    if (!filters.auto) return;
    const id = setInterval(fetchSignals, 60_000); // 1 min
    return () => clearInterval(id);
  }, [filters.auto]);

  const now = Date.now();
  const SINCE_MS = { '6h': 6*3600e3, '12h': 12*3600e3, '24h': 24*3600e3, '7d': 7*86400e3, '30d': 30*86400e3 };

  const filtered = useMemo(() => {
    const q = filters.q.trim().toLowerCase();
    return rows.filter(r => {
      if (!filters.actions[r.action ?? 'NEUTRAL']) return false;
      if (filters.ticker !== 'ALL' && r.ticker !== filters.ticker) return false;
      if (filters.since !== 'All') {
        const ts = new Date(r.timestamp).getTime();
        if (now - ts > (SINCE_MS[filters.since] || 0)) return false;
      }
      if (q) {
        const hay = `${r.ticker} ${r.signal_type} ${r.action} ${r.message || ''}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    }).sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp));
  }, [rows, filters, now]);

  // simple client-side paging
  const [page, setPage] = useState(1);
  const pageSize = 25;
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  useEffect(() => { setPage(1); }, [filters]); // reset page on filters change
  const pageRows = filtered.slice((page-1)*pageSize, page*pageSize);

  return (
    <section className="p-4 border rounded shadow bg-white dark:bg-gray-800">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold">Unified Signals</h2>
        <span className="text-sm text-gray-500">{filtered.length} results</span>
      </div>

      <Controls
        tickers={tickers}
        filters={filters}
        setFilters={setFilters}
        onRefresh={fetchSignals}
        refreshing={refreshing}
      />

      <div className="overflow-x-auto">
        <table className="w-full text-sm border border-gray-300 dark:border-gray-600">
          <thead className="bg-gray-100 dark:bg-gray-700">
            <tr>
              <th className="px-3 py-2 border dark:border-gray-600 text-left">Time (UTC)</th>
              <th className="px-3 py-2 border dark:border-gray-600 text-left">Ticker</th>
              <th className="px-3 py-2 border dark:border-gray-600 text-left">Signal</th>
              <th className="px-3 py-2 border dark:border-gray-600 text-left">Action</th>
              <th className="px-3 py-2 border dark:border-gray-600 text-right">Value</th>
              <th className="px-3 py-2 border dark:border-gray-600 text-left">Triggered By</th>
              <th className="px-3 py-2 border dark:border-gray-600 text-left">Params</th>
              <th className="px-3 py-2 border dark:border-gray-600 text-left">Message</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.length === 0 ? (
              <tr><td colSpan="8" className="text-center text-gray-500 py-6">No signals.</td></tr>
            ) : pageRows.map((r, i) => (
              <tr key={`${r.id ?? i}-${r.timestamp}`} className="border-t dark:border-gray-600">
                <td className="px-3 py-2">{new Date(r.timestamp).toISOString().replace('T',' ').replace('Z','')}</td>
                <td className="px-3 py-2 font-mono">{r.ticker}</td>
                <td className="px-3 py-2">{r.signal_type}</td>
                <td className="px-3 py-2"><Badge text={r.action || 'NEUTRAL'} /></td>
                <td className="px-3 py-2 text-right">
                  {typeof r.signal_value === 'number' ? r.signal_value.toFixed(4) : ''}
                </td>
                <td className="px-3 py-2">{r.triggered_by || ''}</td>
                <td className="px-3 py-2">
                  <code className="text-xs">
                    {r.params ? JSON.stringify(r.params).slice(0, 80) : '{}'}{(r.params && JSON.stringify(r.params).length > 80) ? '…' : ''}
                  </code>
                </td>
                <td className="px-3 py-2">{r.message || ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* pagination */}
      <div className="flex items-center justify-between mt-3">
        <div className="text-sm text-gray-500">Page {page} / {pageCount}</div>
        <div className="flex gap-2">
          <button
            className="px-3 py-1 border rounded disabled:opacity-50"
            onClick={() => setPage(p => Math.max(1, p-1))}
            disabled={page === 1}
          >Prev</button>
          <button
            className="px-3 py-1 border rounded disabled:opacity-50"
            onClick={() => setPage(p => Math.min(pageCount, p+1))}
            disabled={page === pageCount}
          >Next</button>
        </div>
      </div>
    </section>
  );
}
