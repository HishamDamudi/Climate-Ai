import { useState } from 'react'
import { MdMenu, MdSearch, MdNotifications, MdLightMode, MdDarkMode, MdLogout } from 'react-icons/md'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

export default function Navbar({ onMenuClick, alertCount = 0, onSearch }) {
  const { theme, toggleTheme } = useTheme()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')

  const submitSearch = (e) => {
    e.preventDefault()
    onSearch?.(query)
  }

  return (
    <header className="sticky top-0 z-20 h-16 flex items-center gap-4 px-4 lg:px-8 glass-card !rounded-none border-x-0 border-t-0">
      <button className="lg:hidden text-2xl" onClick={onMenuClick} aria-label="Open menu">
        <MdMenu />
      </button>

      <form onSubmit={submitSearch} className="hidden sm:flex items-center gap-2 flex-1 max-w-md
        bg-slate-100/70 dark:bg-slate-800/60 rounded-xl px-3 py-2">
        <MdSearch className="text-slate-400" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search district, state or coordinates…"
          className="bg-transparent outline-none text-sm w-full placeholder:text-slate-400"
        />
      </form>

      <div className="ml-auto flex items-center gap-2 sm:gap-4">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-slate-200/60 dark:hover:bg-slate-700/60"
          aria-label="Toggle theme"
        >
          {theme === 'light' ? <MdDarkMode /> : <MdLightMode />}
        </button>

        <button
          className="relative p-2 rounded-lg hover:bg-slate-200/60 dark:hover:bg-slate-700/60"
          aria-label="Notifications"
          onClick={() => navigate('/alerts')}
        >
          <MdNotifications />
          {alertCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 bg-severity-red text-white text-[10px]
              leading-none rounded-full w-4 h-4 flex items-center justify-center">
              {alertCount > 9 ? '9+' : alertCount}
            </span>
          )}
        </button>

        <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-slate-200 dark:border-slate-700">
          <div className="w-8 h-8 rounded-full bg-brand-500 text-white flex items-center justify-center text-sm font-semibold">
            {user?.username?.[0]?.toUpperCase() || '?'}
          </div>
          <div className="text-xs leading-tight">
            <div className="font-medium">{user?.username}</div>
            <div className="text-slate-400 capitalize">{user?.role}</div>
          </div>
          <button onClick={logout} className="ml-1 p-1.5 rounded-lg hover:bg-slate-200/60 dark:hover:bg-slate-700/60" aria-label="Logout">
            <MdLogout />
          </button>
        </div>
      </div>
    </header>
  )
}
