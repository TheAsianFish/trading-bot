import { Bar } from 'react-chartjs-2';

function SignalSummary({ data }) {
  if (!data) return <p>Loading signal summary...</p>;

  const chartData = {
    labels: data.map(item => item.type),
    datasets: [
      {
        label: 'Signal Counts',
        data: data.map(item => item.count),
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        borderColor: 'rgb(54, 162, 235)',
        borderWidth: 1
      }
    ]
  };

  return (
    <div className="bg-white rounded shadow p-4 mb-6">
      <Bar data={chartData} />
    </div>
  );
}

export default SignalSummary;
