import { useEffect, useState } from 'react'
import { Line, Bar, Pie } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Tooltip, Legend, Filler,
} from 'chart.js'
import { getNationalTrend, getPredictions, getRegionSummary } from '../services/api'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Tooltip, Legend, Filler)

const RANGE_OPTIONS = [
  { label: '2 Weeks', days: 14 },
  { label: '1 Month', days: 30 },
  { label: '3 Months', days: 90 },
  { label: '1 Year', days: 365 },
]

export default function Analytics() {
  const [trend, setTrend] = useState([])
  const [regions, setRegions] = useState([])
  const [predictions, setPredictions] = useState([])
  const [days, setDays] = useState(90)

  useEffect(() => {
    getNationalTrend(days).then(setTrend)
  }, [days])

  useEffect(() => {
    getRegionSummary().then(setRegions)
    getPredictions().then(setPredictions)
  }, [])

  const labels = trend.map((t) => t.date)

  const trendData = {
    labels,
    datasets: [
      { label: 'Max Temp (°C)', data: trend.map((t) => t.avg_max_temp), borderColor: '#ef4444', backgroundColor: '#ef444422', tension: 0.35, fill: true },
      { label: 'Humidity (%)', data: trend.map((t) => t.avg_humidity), borderColor: '#0ea5e9', backgroundColor: '#0ea5e922', tension: 0.35, fill: true },
    ],
  }

  const rainAqiData = {
    labels,
    datasets: [
      { label: 'Rainfall (mm)', data: trend.map((t) => t.avg_rainfall), borderColor: '#2563eb', backgroundColor: '#2563eb22', tension: 0.35, fill: true },
      { label: 'AQI', data: trend.map((t) => t.avg_aqi), borderColor: '#a855f7', backgroundColor: '#a855f722', tension: 0.35, fill: true, yAxisID: 'y1' },
    ],
  }

  const regionBarData = {
    labels: regions.map((r) => r.region),
    datasets: [
      { label: 'Avg Max Temp (°C)', data: regions.map((r) => r.avg_max_temp), backgroundColor: '#ef4444aa' },
      { label: 'Avg AQI', data: regions.map((r) => r.avg_aqi), backgroundColor: '#a855f7aa' },
    ],
  }

  const riskCounts = predictions.reduce((acc, p) => {
    acc[p.risk_level] = (acc[p.risk_level] || 0) + 1
    return acc
  }, {})

  const riskPieData = {
    labels: Object.keys(riskCounts),
    datasets: [{
      data: Object.values(riskCounts),
      backgroundColor: ['#22c55e', '#f97316', '#ef4444', '#991b1b'],
    }],
  }

  const commonOpts = {
    responsive: true,
    plugins: { legend: { position: 'bottom' } },
    scales: { x: { ticks: { maxTicksLimit: 8 } } },
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Analytics</h1>
          <p className="text-sm text-slate-500">Temperature, humidity, rainfall, AQI and risk trends</p>
        </div>
        <div className="flex gap-2">
          {RANGE_OPTIONS.map((r) => (
            <button
              key={r.days}
              onClick={() => setDays(r.days)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border
                ${days === r.days ? 'bg-brand-600 text-white border-brand-600' : 'border-slate-200 dark:border-slate-700 text-slate-500'}`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-card p-5">
          <h2 className="text-sm font-semibold mb-3">Temperature &amp; Humidity Trend</h2>
          <Line data={trendData} options={commonOpts} />
        </div>
        <div className="glass-card p-5">
          <h2 className="text-sm font-semibold mb-3">Rainfall &amp; AQI Trend</h2>
          <Line data={rainAqiData} options={commonOpts} />
        </div>
        <div className="glass-card p-5">
          <h2 className="text-sm font-semibold mb-3">Region Comparison</h2>
          <Bar data={regionBarData} options={commonOpts} />
        </div>
        <div className="glass-card p-5 flex flex-col items-center">
          <h2 className="text-sm font-semibold mb-3 self-start">Current Risk Distribution</h2>
          <div className="max-w-xs w-full">
            <Pie data={riskPieData} options={{ plugins: { legend: { position: 'bottom' } } }} />
          </div>
        </div>
      </div>
    </div>
  )
}
