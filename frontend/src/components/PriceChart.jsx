import { useEffect, useState } from 'react';
import {
  Chart as ChartJS, LineElement, CategoryScale, LinearScale, PointElement, TimeScale, Tooltip, Legend
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { Line } from 'react-chartjs-2';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, TimeScale, Tooltip, Legend);

const API_BASE = import.meta.env?.VITE_API_BASE || (typeof window !== 'undefined' && window.__API_BASE__) || '';

function PriceChart({ ticker, range = 'All' }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    if (!ticker || !API_BASE) return;
    fetch(`${API_BASE}/prices/${encodeURIComponent(ticker)}?range=${range}`)
      .then(r => r.json())
      .then(setData)
      .catch(err => console.error('Error fetching prices:', err));
  }, [ticker, range]);

  if (!Array.isArray(data) || data.length === 0) return <p>No price data available.</p>;

  const labels = data.map(p => new Date(p.timestamp));
  const series = data.map(p => p.price);

  const chartData = {
    labels,
    datasets: [{ label: `${ticker} Price`, data: series, fill: false, tension: 0.1 }]
  };

  const options = {
    responsive: true,
    plugins: { legend: { display: true, position: 'top' }, tooltip: { mode: 'index', intersect: false } },
    scales: {
      x: { type: 'time', time: { unit: range === '24h' ? 'hour' : range === '7d' ? 'day' : 'week' }, title: { display: true, text: 'Time' } },
      y: { beginAtZero: false, title: { display: true, text: 'Price' } }
    }
  };

  return <div className="w-full h-[500px] sm:h-[600px]"><Line data={chartData} options={options} /></div>;
}
export default PriceChart;
