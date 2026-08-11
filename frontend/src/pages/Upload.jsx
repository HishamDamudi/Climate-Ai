import { useRef, useState } from 'react'
import { MdUploadFile, MdCheckCircle, MdError } from 'react-icons/md'
import { uploadWeatherFile } from '../services/api'

const REQUIRED_COLUMNS = ['date', 'district', 'state', 'region', 'lat', 'lon', 'max_temp', 'humidity', 'wind_kmph', 'rainfall_mm']

export default function Upload() {
  const fileRef = useRef(null)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState([])
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const handleFile = (f) => {
    setFile(f)
    setResult(null)
    setError('')
    if (f && f.name.toLowerCase().endsWith('.csv')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const lines = e.target.result.split('\n').filter(Boolean).slice(0, 6)
        setPreview(lines.map((l) => l.split(',')))
      }
      reader.readAsText(f)
    } else {
      setPreview([])
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0])
  }

  const submit = async () => {
    if (!file) return
    setUploading(true)
    setProgress(0)
    setError('')
    try {
      const res = await uploadWeatherFile(file, setProgress)
      setResult(res)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold">Data Upload</h1>
        <p className="text-sm text-slate-500">
          Import CSV or Excel meteorological records. Required columns: {REQUIRED_COLUMNS.join(', ')}
        </p>
      </div>

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        className="glass-card p-10 border-2 border-dashed border-brand-300 dark:border-brand-700
          flex flex-col items-center justify-center gap-3 text-center cursor-pointer"
        onClick={() => fileRef.current?.click()}
      >
        <MdUploadFile className="text-4xl text-brand-500" />
        <p className="text-sm font-medium">Drag &amp; drop a .csv or .xlsx file here, or click to browse</p>
        {file && <p className="text-xs text-slate-500">Selected: {file.name}</p>}
        <input
          ref={fileRef}
          type="file"
          accept=".csv,.xlsx"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      {preview.length > 0 && (
        <div className="glass-card p-4 overflow-x-auto">
          <h2 className="text-sm font-semibold mb-2">Preview (first {preview.length - 1} rows)</h2>
          <table className="text-xs w-full">
            <thead>
              <tr>{preview[0].map((c, i) => <th key={i} className="text-left px-2 py-1 text-slate-400 font-medium">{c}</th>)}</tr>
            </thead>
            <tbody>
              {preview.slice(1).map((row, r) => (
                <tr key={r} className="border-t border-slate-100 dark:border-slate-800">
                  {row.map((c, i) => <td key={i} className="px-2 py-1">{c}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <button
        onClick={submit}
        disabled={!file || uploading}
        className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium
          rounded-xl px-5 py-2.5 text-sm"
      >
        {uploading ? `Uploading… ${progress}%` : 'Upload & Import'}
      </button>

      {uploading && (
        <div className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
          <div className="h-full bg-brand-500 transition-all" style={{ width: `${progress}%` }} />
        </div>
      )}

      {error && (
        <div className="glass-card p-4 flex items-start gap-2 text-severity-red text-sm">
          <MdError className="mt-0.5 shrink-0" /> {error}
        </div>
      )}

      {result && (
        <div className="glass-card p-4 flex items-start gap-2 text-sm">
          <MdCheckCircle className="mt-0.5 shrink-0 text-severity-green" />
          <div>
            <div className="font-medium">
              Imported {result.rows_imported} of {result.rows_received} rows from {result.filename}
            </div>
            {result.rows_rejected > 0 && (
              <div className="text-slate-500 mt-1">
                {result.rows_rejected} row(s) rejected.
                {result.errors?.length > 0 && (
                  <ul className="list-disc list-inside mt-1 text-xs text-severity-red">
                    {result.errors.slice(0, 8).map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
