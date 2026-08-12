import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { MdThermostat, MdLockOutline, MdPersonOutline } from 'react-icons/md'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('climate123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate(location.state?.from?.pathname || '/', { replace: true })
    } catch (err) {
      setError(err?.response?.data?.detail || 'Invalid username or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br
      from-brand-900 via-brand-700 to-brand-500 p-4">
      <div className="w-full max-w-md glass-card !bg-white/90 dark:!bg-slate-900/90 p-8">
        <div className="flex flex-col items-center gap-2 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-brand-600 flex items-center justify-center text-white text-2xl">
            <MdThermostat />
          </div>
          <h1 className="font-display text-xl font-semibold">Climate Intelligence System</h1>
          <p className="text-sm text-slate-500 text-center">Heatwave Monitoring, Prediction &amp; Early Warning</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="text-xs font-medium text-slate-500">Username</span>
            <div className="mt-1 flex items-center gap-2 bg-slate-100 dark:bg-slate-800 rounded-xl px-3 py-2.5">
              <MdPersonOutline className="text-slate-400" />
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="bg-transparent outline-none w-full text-sm"
                required
              />
            </div>
          </label>

          <label className="block">
            <span className="text-xs font-medium text-slate-500">Password</span>
            <div className="mt-1 flex items-center gap-2 bg-slate-100 dark:bg-slate-800 rounded-xl px-3 py-2.5">
              <MdLockOutline className="text-slate-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-transparent outline-none w-full text-sm"
                required
              />
            </div>
          </label>

          {error && <p className="text-sm text-severity-red">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white
              font-medium rounded-xl py-2.5 text-sm transition-colors"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="text-xs text-slate-400 mt-6 text-center">
          Demo credentials — admin / climate123 (full access) or viewer / viewer123 (read-only)
        </p>
      </div>
    </div>
  )
}
