import { useEffect, useState } from 'react'
import {
  MdThermostat, MdWaterDrop, MdAir, MdUmbrella, MdCloud, MdWbSunny,
  MdWarningAmber, MdVerified, MdGroups, MdAccessTime,
} from 'react-icons/md'
import MetricCard from '../components/MetricCard'
import SeverityBadge from '../components/SeverityBadge'
import { getNationalSummary, getPredictions, getCurrentWeather } from '../services/api'

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [predictions, setPredictions] = useState([])
  const [weather, setWeather] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      const [s, p, w] = await Promise.all([getNationalSummary(), getPredictions(), getCurrentWeather()])
      setSummary(s)
      setPredictions(p)
      setWeather(w)
      setError('')
    } catch (e) {
      setError('Could not reach the Climate AI API. Is the backend running on port 8000?')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, 60000)
    return () => clearInterval(id)
  }, [])

  if (loading) {
    return <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="glass-card h-24 animate-pulse" />
      ))}
    </div>
  }

  if (error) {
    return <div className="glass-card p-6 text-severity-red text-sm">{error}</div>
  }

  const worst = [...predictions].sort((a, b) =>
    ['Low', 'Moderate', 'High', 'Extreme'].indexOf(b.risk_level) -
    ['Low', 'Moderate', 'High', 'Extreme'].indexOf(a.risk_level)
  )[0]
  const avgConfidence = predictions.length
    ? Math.round((predictions.reduce((a, p) => a + p.confidence_score, 0) / predictions.length) * 100)
    : 0
  const totalAtRisk = predictions.reduce((a, p) => a + (p.population_at_risk || 0), 0)
  const humid = weather.length ? (weather.reduce((a, w) => a + w.humidity, 0) / weather.length).toFixed(0) : '–'
  const wind = weather.length ? (weather.reduce((a, w) => a + w.wind_kmph, 0) / weather.length).toFixed(1) : '–'
  const rain = weather.length ? (weather.reduce((a, w) => a + w.rainfall_mm, 0) / weather.length).toFixed(1) : '–'
  const heatIdx = weather.length ? (weather.reduce((a, w) => a + w.heat_index, 0) / weather.length).toFixed(1) : '–'
  const uv = weather.length ? (weather.reduce((a, w) => a + w.uv_index, 0) / weather.length).toFixed(1) : '–'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">National Overview</h1>
        <p className="text-sm text-slate-500">
          Live snapshot across {summary.districts_monitored} monitored districts
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard icon={MdThermostat} label="Avg Max Temperature" value={summary.avg_max_temp} unit="°C" accent="red" />
        <MetricCard icon={MdWaterDrop} label="Avg Humidity" value={humid} unit="%" accent="sky" />
        <MetricCard icon={MdWbSunny} label="Avg Heat Index" value={heatIdx} unit="°C" accent="orange" />
        <MetricCard icon={MdAir} label="Avg Wind Speed" value={wind} unit="km/h" accent="brand" />
        <MetricCard icon={MdUmbrella} label="Avg Rainfall" value={rain} unit="mm" accent="sky" />
        <MetricCard icon={MdCloud} label="Avg AQI" value={summary.avg_aqi} accent="purple" />
        <MetricCard icon={MdWbSunny} label="Avg UV Index" value={uv} accent="yellow" />
        <MetricCard icon={MdGroups} label="Population at Risk" value={totalAtRisk.toLocaleString()} accent="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-card p-5 lg:col-span-1 flex flex-col gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
            <MdWarningAmber /> Highest Current Risk
          </div>
          {worst ? (
            <>
              <div className="text-lg font-semibold">{worst.district}, {worst.state}</div>
              <SeverityBadge level={{ Low: 'Green', Moderate: 'Orange', High: 'Red', Extreme: 'Extreme' }[worst.risk_level]} />
              <p className="text-sm text-slate-500">{worst.explanation}</p>
            </>
          ) : <p className="text-sm text-slate-400">No data</p>}
        </div>

        <div className="glass-card p-5 flex flex-col gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
            <MdVerified /> Prediction Confidence
          </div>
          <div className="font-mono text-3xl font-semibold">{avgConfidence}%</div>
          <p className="text-sm text-slate-500">Average model confidence across all {predictions.length} district forecasts.</p>
        </div>

        <div className="glass-card p-5 flex flex-col gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
            <MdAccessTime /> Last Updated
          </div>
          <div className="font-mono text-lg font-semibold">{new Date().toLocaleString()}</div>
          <p className="text-sm text-slate-500">Auto-refreshes every 60 seconds from the live API.</p>
        </div>
      </div>
    </div>
  )
}
