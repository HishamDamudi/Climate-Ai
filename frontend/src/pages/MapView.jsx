import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, LayersControl, useMap } from 'react-leaflet'
import { MdFullscreen, MdMyLocation } from 'react-icons/md'
import SeverityBadge from '../components/SeverityBadge'
import { getPredictions } from '../services/api'

const RISK_TO_COLOR = { Low: '#22c55e', Moderate: '#f97316', High: '#ef4444', Extreme: '#991b1b' }
const RISK_TO_SEVERITY = { Low: 'Green', Moderate: 'Orange', High: 'Red', Extreme: 'Extreme' }

function LocateControl() {
  const map = useMap()
  const locate = () => {
    map.locate().on('locationfound', (e) => {
      map.flyTo(e.latlng, 7)
    })
  }
  return (
    <button
      onClick={locate}
      className="absolute z-[1000] top-3 right-3 bg-white dark:bg-slate-800 shadow rounded-lg p-2"
      title="Use current location"
    >
      <MdMyLocation />
    </button>
  )
}

export default function MapView() {
  const [predictions, setPredictions] = useState([])
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    getPredictions().then(setPredictions).catch(() => {})
  }, [])

  const filtered = useMemo(() => {
    if (!search) return predictions
    const s = search.toLowerCase()
    return predictions.filter((p) => p.district.toLowerCase().includes(s) || p.state.toLowerCase().includes(s))
  }, [predictions, search])

  const requestFullscreen = () => {
    const el = document.getElementById('heatwave-map-container')
    el?.requestFullscreen?.()
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Heatwave Map</h1>
          <p className="text-sm text-slate-500">Region-wise severity, hotspots and forecast confidence</p>
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search district or state…"
          className="bg-white/70 dark:bg-slate-800/70 rounded-xl px-3 py-2 text-sm outline-none
            border border-slate-200 dark:border-slate-700 w-full sm:w-64"
        />
      </div>

      <div id="heatwave-map-container" className="glass-card p-2 relative">
        <button
          onClick={requestFullscreen}
          className="absolute z-[1000] top-5 left-5 bg-white dark:bg-slate-800 shadow rounded-lg p-2"
          title="Fullscreen"
        >
          <MdFullscreen />
        </button>
        <MapContainer center={[22.5, 79]} zoom={5} style={{ height: '540px', width: '100%' }} className="z-0">
          <LocateControl />
          <LayersControl position="topright">
            <LayersControl.BaseLayer checked name="Streets">
              <TileLayer
                attribution='&copy; OpenStreetMap contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
            </LayersControl.BaseLayer>
            <LayersControl.BaseLayer name="Terrain">
              <TileLayer
                attribution='&copy; OpenTopoMap'
                url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
              />
            </LayersControl.BaseLayer>
            <LayersControl.Overlay checked name="Heatwave Severity">
              <>
                {filtered.map((p) => (
                  <CircleMarker
                    key={p.district}
                    center={[p.lat, p.lon]}
                    radius={10 + p.heatwave_probability * 12}
                    pathOptions={{
                      color: RISK_TO_COLOR[p.risk_level],
                      fillColor: RISK_TO_COLOR[p.risk_level],
                      fillOpacity: 0.55,
                      weight: 2,
                    }}
                    eventHandlers={{ click: () => setSelected(p) }}
                  >
                    <Popup>
                      <div className="text-sm space-y-1">
                        <div className="font-semibold">{p.district}, {p.state}</div>
                        <div>Severity: {p.severity}</div>
                        <div>Expected max temp: {p.expected_temp}°C</div>
                        <div>Heatwave probability: {(p.heatwave_probability * 100).toFixed(0)}%</div>
                        <div>Population at risk: {p.population_at_risk?.toLocaleString()}</div>
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </>
            </LayersControl.Overlay>
          </LayersControl>
        </MapContainer>
      </div>

      <div className="glass-card p-4 flex flex-wrap items-center gap-4 text-xs">
        <span className="font-medium text-slate-500">Legend:</span>
        {Object.entries(RISK_TO_COLOR).map(([risk, color]) => (
          <span key={risk} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ background: color }} />
            {risk}
          </span>
        ))}
      </div>

      {selected && (
        <div className="glass-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">{selected.district}, {selected.state}</h2>
            <SeverityBadge level={RISK_TO_SEVERITY[selected.risk_level]} />
          </div>
          <p className="text-sm text-slate-500">{selected.explanation}</p>
        </div>
      )}
    </div>
  )
}
