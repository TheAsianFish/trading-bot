import { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  BarElement,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

import PriceChart from './components/PriceChart';
import SignalSummary from './components/SignalSummary';
import GeneratedSignals from './components/GeneratedSignals';
import TriggerSignals from './components/TriggerSignals';

ChartJS.register(
  BarElement,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend
);

function App() {
  const stockTickers = ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'NVDA', '^SPX'];
  const cryptoTickers = ['BTC-USD', 'ETH-USD', 'SOL-USD'];

  const [ticker, setTicker] = useState('AAPL');
  const [tickerFilter, setTickerFilter] = useState('ALL');
  const [priceData, setPriceData] = useState(null);
  const [signals, setSignals] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true');

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  const [signalFilter, setSignalFilter] = useState({ BUY: true, SELL: true });
  const [dateRange, setDateRange] = useState('24h');
  const REFRESH_INTERVAL_MS = 180000;

  const API_BASE = "http://Trading-bot-backend-env.eba-mztx8vdc.us-east-2.elasticbeanstalk.com";

  const fetchPriceData = () => {
    fetch(`${API_BASE}/prices/${ticker}?range=${dateRange}`)
      .then(res => res.json())
      .then(setPriceData)
      .catch(err => console.error(err));
  };

  useEffect(() => { fetchPriceData(); }, [ticker, dateRange]);

  const fetchSignalData = () => {
    fetch(`${API_BASE}/signals/recent`)
      .then(res => res.json())
      .then(setSignals)
      .catch(err => console.error(err));
  };
  const fetchSummaryData = () => {
    fetch(`${API_BASE}/signals/summary`)
      .then(res => res.json())
      .then(setSummaryData)
      .catch(err => console.error(err));
  };

  const [lastUpdated, setLastUpdated] = useState(null);
  const refreshAll = () => {
    fetchPriceData();
    fetchSignalData();
    fetchSummaryData();
    setLastUpdated(new Date().toLocaleString());
  };

  useEffect(() => { fetchSignalData(); }, []);
  useEffect(() => { fetchSummaryData(); }, []);
  useEffect(() => {
    const id = setInterval(fetchSignalData, REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, []);

  const now = Date.now();
  const daysToMs = { '24h': 86400000, '7d': 604800000, '30d': 2592000000, '90d': 7776000000 };
  const intentMap = { DROP_ALERT: 'SELL', OPEN_DOWN: 'SELL', OPEN_UP: 'BUY', MA_CROSS: 'SELL' };
  const safeSignals = Array.isArray(signals) ? signals : [];

  const filteredSignals = safeSignals
    .filter(s => intentMap[s.type] ? signalFilter[intentMap[s.type]] : true)
    .filter(s => {
      if (dateRange !== 'All' && now - new Date(s.timestamp).getTime() > daysToMs[dateRange]) return false;
      if (tickerFilter !== 'ALL' && s.ticker !== tickerFilter) return false;
      return true;
    });


  return (
    <div className="min-h-screen font-sans p-6 transition-colors bg-white dark:bg-gray-900 text-black dark:text-gray-100">
      <div className="max-w-7xl mx-auto">
        <header className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-blue-600 dark:text-blue-400">Trading Dashboard</h1>
          <div className="flex items-center gap-8">
            <span className="text-sm font-medium">{darkMode ? 'Dark Mode    .' : 'Light Mode    .'}</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" checked={darkMode} onChange={() => {
                const next = !darkMode;
                setDarkMode(next);
                localStorage.setItem('darkMode', next);
              }} />
              <div className="w-14 h-8 bg-gray-300 dark:bg-gray-600 rounded-full peer-checked:bg-blue-600 transition-colors duration-300" />
              <div className="absolute left-1 top-1 w-6 h-6 bg-white rounded-full shadow transform peer-checked:translate-x-6 transition-transform duration-300 flex items-center justify-center ring-2 ring-gray-400 dark:ring-gray-500">
                {darkMode ? '🌙' : '☀️'}
              </div>
            </label>
          </div>
        </header>

        {/* Chart Controls */}
        <section className="mb-6">
          <div className="space-y-3 w-full md:w-2/3">
            <h3 className="text-lg font-semibold mb-2">📈 Chart Controls</h3>
            <div className="flex justify-start items-center">
              <label className="mr-2 font-semibold">Select Ticker:</label>
              <select
                value={ticker}
                onChange={e => setTicker(e.target.value)}
                className="border p-2 rounded shadow-sm focus:outline-none focus:ring focus:border-blue-400"
              >
                <optgroup label="Stocks">
                  {stockTickers.map(s => <option key={s} value={s}>{s}</option>)}
                </optgroup>
                <optgroup label="Crypto">
                  {cryptoTickers.map(s => <option key={s} value={s}>{s}</option>)}
                </optgroup>
              </select>
            </div>
            <div className="flex gap-4 items-center">
              <span className="font-semibold">Range:</span>
              {['24h','7d','30d','90d','All'].map(r => (
                <button
                  key={r}
                  onClick={() => setDateRange(r)}
                  className={`px-3 py-1 rounded border transition duration-200 hover:bg-blue-600 hover:text-white ${dateRange===r? 'bg-blue-700 text-white border-blue-800' : 'bg-white text-blue-600 border-blue-600'}`}
                >{r}</button>
              ))}
            </div>
            <div className="flex flex-col items-start">
              <button onClick={refreshAll} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                🔄 Refresh All Data
              </button>
              <span className="text-sm text-gray-500 mt-1">Last updated: {lastUpdated || 'Just now'}</span>
            </div>
          </div>
        </section>

        <div className="p-4 border rounded shadow bg-white dark:bg-gray-800 mb-6">
          <h2 className="text-xl font-bold mb-2">📈 Price Chart</h2>
          <PriceChart ticker={ticker} range={dateRange} />
        </div>

        <section className="mb-6">
          <div className="space-y-3 w-full">
            <h3 className="text-lg font-semibold mb-2">📊 Filter Signals</h3>
            <div>
              <span className="font-semibold mr-2">Type:</span>
              {['BUY','SELL'].map(t => (
                <label key={t} className="mr-4">
                  <input type="checkbox" checked={signalFilter[t]} onChange={() => setSignalFilter(prev => ({...prev, [t]: !prev[t]}))} className="mr-1" />
                  {t}
                </label>
              ))}
            </div>
            <div>
              <span className="font-semibold mr-2">Ticker:</span>
              <select value={tickerFilter} onChange={e => setTickerFilter(e.target.value)} className="border p-2 rounded shadow-sm">
                <option value="ALL">ALL</option>
                {[...stockTickers,...cryptoTickers].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
        </section>

        <main className="grid grid-cols-2 gap-6">
          <div className="p-4 border rounded shadow bg-white dark:bg-gray-800">
            <h2 className="text-xl font-bold mb-2">📝 Recent Signals</h2>
            {filteredSignals?.length ? (
              <ul className="list-disc ml-5 mt-2">
                {filteredSignals.map((s,i) => <li key={i}>[{s.timestamp}] {s.ticker} — <strong>{s.type}</strong> @ ${s.price}</li>)}
              </ul>
            ) : <p className="text-center text-gray-500">No signals.</p>}
          </div>
          <div className="p-4 border rounded shadow bg-white dark:bg-gray-800">
            <h2 className="text-xl font-bold mb-2">📊 Signal Summary</h2>
            <SignalSummary data={summaryData} />
          </div>
          <div className="p-4 border rounded shadow bg-white dark:bg-gray-800">
            <GeneratedSignals ticker={ticker} />
          </div>
          <div className="p-4 border rounded shadow bg-white dark:bg-gray-800">
            <TriggerSignals ticker={ticker} onRefresh={fetchSummaryData} />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
