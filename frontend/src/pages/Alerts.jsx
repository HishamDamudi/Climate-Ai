import { useEffect, useState } from 'react'
import { MdSearch, MdFileDownload, MdClose } from 'react-icons/md'
import SeverityBadge from '../components/SeverityBadge'
import { getAlerts } from '../services/api'

const LEVELS = ['Green', 'Yellow', 'Orange', 'Red', 'Extreme']

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [minLevel, setMinLevel] = useState('Green')
  const [search, setSearch] = useState('')
  const [dismissed, setDismissed] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    getAlerts(minLevel, search).then((data) => {
      setAlerts(data)
      setLoading(false)
    })
  }

  useEffect(() => { load() }, [minLevel])

  const submitSearch = (e) => {
    e.preventDefault()
    load()
  }

  const visible = alerts.filter((a) => !dismissed.includes(a.id))

  const exportCsv = () => {
    const header = 'level,title,description,timestamp,affected_areas\n'
    const rows = visible.map((a) =>
      [a.level, a.title, a.description.replace(/,/g, ';'), a.timestamp, a.affected_areas.join('|')].join(',')
    )
    const blob = new Blob([header + rows.join('\n')], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'heatwave_alerts.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Heatwave Alerts</h1>
          <p className="text-sm text-slate-500">{visible.length} active alert(s) at or above {minLevel}</p>
        </div>
        <button onClick={exportCsv} className="flex items-center gap-2 text-sm font-medium bg-brand-600
          text-white px-4 py-2 rounded-xl hover:bg-brand-700">
          <MdFileDownload /> Export CSV
        </button>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <form onSubmit={submitSearch} className="flex items-center gap-2 bg-white/70 dark:bg-slate-800/70
          rounded-xl px-3 py-2 flex-1 border border-slate-200 dark:border-slate-700">
          <MdSearch className="text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search alerts by district or state…"
            className="bg-transparent outline-none text-sm w-full"
          />
        </form>
        <div className="flex gap-1 overflow-x-auto">
          {LEVELS.map((l) => (
            <button
              key={l}
              onClick={() => setMinLevel(l)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border whitespace-nowrap
                ${minLevel === l ? 'bg-brand-600 text-white border-brand-600' : 'border-slate-200 dark:border-slate-700 text-slate-500'}`}
            >
              {l}+
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="glass-card h-24 animate-pulse" />)}</div>
      ) : visible.length === 0 ? (
        <div className="glass-card p-8 text-center text-sm text-slate-400">
          No alerts at or above {minLevel} severity right now.
        </div>
      ) : (
        <div className="space-y-3">
          {visible.map((a) => (
            <div key={a.id} className="glass-card p-4 flex flex-col sm:flex-row sm:items-start gap-3">
              <SeverityBadge level={a.level} />
              <div className="flex-1">
                <div className="font-semibold text-sm">{a.title}</div>
                <p className="text-sm text-slate-500 mt-1">{a.description}</p>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {a.recommended_actions.map((act, i) => (
                    <span key={i} className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-lg text-slate-500">
                      {act}
                    </span>
                  ))}
                </div>
                <div className="text-xs text-slate-400 mt-2">{new Date(a.timestamp).toLocaleString()}</div>
              </div>
              <button
                onClick={() => setDismissed((d) => [...d, a.id])}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1"
                title="Dismiss"
              >
                <MdClose />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
