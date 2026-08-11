import { useEffect, useMemo, useState } from 'react'
import { MdFileDownload, MdSearch } from 'react-icons/md'
import { getCurrentWeather } from '../services/api'

const ALL_COLUMNS = [
  { key: 'district', label: 'District' },
  { key: 'state', label: 'State' },
  { key: 'region', label: 'Region' },
  { key: 'max_temp', label: 'Max Temp (°C)' },
  { key: 'humidity', label: 'Humidity (%)' },
  { key: 'wind_kmph', label: 'Wind (km/h)' },
  { key: 'rainfall_mm', label: 'Rainfall (mm)' },
  { key: 'heat_index', label: 'Heat Index' },
  { key: 'aqi', label: 'AQI' },
  { key: 'uv_index', label: 'UV Index' },
  { key: 'date', label: 'Date' },
]

const PAGE_SIZE = 8

export default function DataTable() {
  const [rows, setRows] = useState([])
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('max_temp')
  const [sortDir, setSortDir] = useState('desc')
  const [page, setPage] = useState(1)
  const [visibleCols, setVisibleCols] = useState(ALL_COLUMNS.map((c) => c.key))

  useEffect(() => { getCurrentWeather().then(setRows) }, [])

  const filtered = useMemo(() => {
    let data = rows
    if (search) {
      const s = search.toLowerCase()
      data = data.filter((r) => r.district.toLowerCase().includes(s) || r.state.toLowerCase().includes(s))
    }
    return [...data].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1
      if (a[sortKey] < b[sortKey]) return -1 * dir
      if (a[sortKey] > b[sortKey]) return 1 * dir
      return 0
    })
  }, [rows, search, sortKey, sortDir])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const pageRows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir('asc') }
  }

  const toggleCol = (key) => {
    setVisibleCols((cols) => (cols.includes(key) ? cols.filter((c) => c !== key) : [...cols, key]))
  }

  const exportCsv = () => {
    const cols = ALL_COLUMNS.filter((c) => visibleCols.includes(c.key))
    const header = cols.map((c) => c.key).join(',') + '\n'
    const body = filtered.map((r) => cols.map((c) => r[c.key]).join(',')).join('\n')
    const blob = new Blob([header + body], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'weather_snapshot.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Data Table</h1>
          <p className="text-sm text-slate-500">Latest observation per district — sortable and exportable</p>
        </div>
        <button onClick={exportCsv} className="flex items-center gap-2 text-sm font-medium bg-brand-600
          text-white px-4 py-2 rounded-xl hover:bg-brand-700">
          <MdFileDownload /> Export CSV
        </button>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex items-center gap-2 bg-white/70 dark:bg-slate-800/70 rounded-xl px-3 py-2
          flex-1 border border-slate-200 dark:border-slate-700">
          <MdSearch className="text-slate-400" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search district or state…"
            className="bg-transparent outline-none text-sm w-full"
          />
        </div>
        <div className="flex flex-wrap gap-1">
          {ALL_COLUMNS.map((c) => (
            <button
              key={c.key}
              onClick={() => toggleCol(c.key)}
              className={`text-[11px] px-2 py-1 rounded-md border
                ${visibleCols.includes(c.key) ? 'border-brand-400 text-brand-600 bg-brand-50 dark:bg-brand-900/30' : 'border-slate-200 dark:border-slate-700 text-slate-400'}`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700">
              {ALL_COLUMNS.filter((c) => visibleCols.includes(c.key)).map((c) => (
                <th
                  key={c.key}
                  onClick={() => toggleSort(c.key)}
                  className="text-left px-4 py-3 font-medium text-slate-500 cursor-pointer select-none whitespace-nowrap"
                >
                  {c.label} {sortKey === c.key ? (sortDir === 'asc' ? '▲' : '▼') : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((r, i) => (
              <tr key={i} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                {ALL_COLUMNS.filter((c) => visibleCols.includes(c.key)).map((c) => (
                  <td key={c.key} className="px-4 py-2.5 whitespace-nowrap">{r[c.key]}</td>
                ))}
              </tr>
            ))}
            {pageRows.length === 0 && (
              <tr><td className="px-4 py-8 text-center text-slate-400" colSpan={visibleCols.length}>No matching records</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-400">Page {page} of {pageCount} · {filtered.length} records</span>
        <div className="flex gap-2">
          <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-40">Prev</button>
          <button disabled={page === pageCount} onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-40">Next</button>
        </div>
      </div>
    </div>
  )
}
