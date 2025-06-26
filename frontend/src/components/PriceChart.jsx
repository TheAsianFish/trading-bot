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

function PriceChart({ ticker, data }) {
  if (!data || data.length === 0) return <p>No price data available.</p>;

  // 🕒 Limit to last 6 hours
  const now = new Date();
  const cutoff = new Date(now.getTime() - 6 * 60 * 60 * 1000); // 6 hours ago
  const filteredData = data.filter(point => new Date(point.timestamp) > cutoff);

  const chartData = {
    labels: filteredData.map(point => new Date(point.timestamp)),
    datasets: [
      {
        label: `${ticker} Price`,
        data: filteredData.map(point => point.price),
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
          unit: 'minute'
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
    <div className="w-full h-[400px]">
      <Line data={chartData} options={options} />
    </div>
  );
}

export default PriceChart;
