import { useState } from 'react'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'

export default function Settings() {
  const { theme, toggleTheme } = useTheme()
  const { user } = useAuth()
  const [units, setUnits] = useState('celsius')
  const [notifyEmail, setNotifyEmail] = useState(true)
  const [notifySms, setNotifySms] = useState(false)
  const [minAlertLevel, setMinAlertLevel] = useState('Orange')
  const [saved, setSaved] = useState(false)

  const save = (e) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-slate-500">Preferences are stored locally in this demo build.</p>
      </div>

      <form onSubmit={save} className="space-y-6">
        <section className="glass-card p-5 space-y-3">
          <h2 className="text-sm font-semibold">Appearance</h2>
          <div className="flex items-center justify-between text-sm">
            <span>Theme</span>
            <button type="button" onClick={toggleTheme}
              className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 capitalize">
              {theme}
            </button>
          </div>
        </section>

        <section className="glass-card p-5 space-y-3">
          <h2 className="text-sm font-semibold">Units</h2>
          <div className="flex gap-2">
            {['celsius', 'fahrenheit'].map((u) => (
              <button
                type="button"
                key={u}
                onClick={() => setUnits(u)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border capitalize
                  ${units === u ? 'bg-brand-600 text-white border-brand-600' : 'border-slate-200 dark:border-slate-700 text-slate-500'}`}
              >
                {u}
              </button>
            ))}
          </div>
        </section>

        <section className="glass-card p-5 space-y-3">
          <h2 className="text-sm font-semibold">Notification Preferences</h2>
          <label className="flex items-center justify-between text-sm">
            <span>Email alerts</span>
            <input type="checkbox" checked={notifyEmail} onChange={(e) => setNotifyEmail(e.target.checked)} />
          </label>
          <label className="flex items-center justify-between text-sm">
            <span>SMS alerts</span>
            <input type="checkbox" checked={notifySms} onChange={(e) => setNotifySms(e.target.checked)} />
          </label>
          <label className="flex items-center justify-between text-sm">
            <span>Minimum alert level to notify</span>
            <select
              value={minAlertLevel}
              onChange={(e) => setMinAlertLevel(e.target.value)}
              className="bg-slate-100 dark:bg-slate-800 rounded-lg px-2 py-1 text-sm"
            >
              {['Green', 'Yellow', 'Orange', 'Red', 'Extreme'].map((l) => <option key={l}>{l}</option>)}
            </select>
          </label>
        </section>

        <section className="glass-card p-5 space-y-3">
          <h2 className="text-sm font-semibold">Profile</h2>
          <div className="text-sm text-slate-500">
            Signed in as <span className="font-medium text-slate-700 dark:text-slate-200">{user?.username}</span> ({user?.role})
          </div>
          <label className="block">
            <span className="text-xs text-slate-500">New password</span>
            <input type="password" placeholder="••••••••" className="mt-1 w-full bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm outline-none" />
          </label>
        </section>

        <button type="submit" className="bg-brand-600 hover:bg-brand-700 text-white font-medium rounded-xl px-5 py-2.5 text-sm">
          Save changes
        </button>
        {saved && <span className="ml-3 text-sm text-severity-green">Saved</span>}
      </form>
    </div>
  )
}
