import { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  TimeScale,
  Tooltip,
  Legend
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  TimeScale,
  Tooltip,
  Legend
);

function PriceChart({ ticker, range = 'All' }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    if (!ticker) return;
    fetch(`http://localhost:5000/prices/${ticker}?range=${range}`)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error('Error fetching prices:', err));
  }, [ticker, range]);

  if (!data || data.length === 0) return <p>No price data available.</p>;

  const chartData = {
    labels: data.map(point => new Date(point.timestamp)),
    datasets: [
      {
        label: `${ticker} Price`,
        data: data.map(point => point.price),
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      }
    ]
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        display: true,
        position: 'top'
      },
      tooltip: {
        mode: 'index',
        intersect: false
      }
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: range === '24h' ? 'hour' : range === '7d' ? 'day' : 'week'
        },
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Price ($)'
        },
        beginAtZero: false
      }
    }
  };

  return (
    <div className="w-full h-[500px] sm:h-[600px]">
      <Line data={chartData} options={options} />
    </div>
  );
}

export default PriceChart;
