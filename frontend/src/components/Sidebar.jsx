import { NavLink } from 'react-router-dom'
import {
  MdDashboard, MdMap, MdInsights, MdWarningAmber, MdUploadFile,
  MdTableChart, MdSettings, MdThermostat,
} from 'react-icons/md'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: MdDashboard, end: true },
  { to: '/map', label: 'Heatwave Map', icon: MdMap },
  { to: '/analytics', label: 'Analytics', icon: MdInsights },
  { to: '/alerts', label: 'Alerts', icon: MdWarningAmber },
  { to: '/upload', label: 'Data Upload', icon: MdUploadFile },
  { to: '/data', label: 'Data Table', icon: MdTableChart },
  { to: '/settings', label: 'Settings', icon: MdSettings },
]

export default function Sidebar({ open }) {
  return (
    <aside
      className={`fixed z-30 inset-y-0 left-0 w-64 transform transition-transform duration-300
      bg-gradient-to-b from-brand-700 to-brand-900 text-white
      ${open ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}
    >
      <div className="flex items-center gap-2 px-6 h-16 border-b border-white/10">
        <MdThermostat className="text-2xl text-severity-orange" />
        <span className="font-display font-semibold text-lg tracking-tight">Climate<span className="text-brand-300">AI</span></span>
      </div>
      <nav className="px-3 py-6 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors
               ${isActive ? 'bg-white/15 text-white' : 'text-brand-100/80 hover:bg-white/10 hover:text-white'}`
            }
          >
            <Icon className="text-lg shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="absolute bottom-0 inset-x-0 px-6 py-4 text-xs text-brand-200/70 border-t border-white/10">
        IMD Mumbai-Pune · KJS-CES-01
      </div>
    </aside>
  )
}
