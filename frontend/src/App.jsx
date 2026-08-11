import { useEffect, useState } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import MapView from './pages/MapView'
import Analytics from './pages/Analytics'
import Alerts from './pages/Alerts'
import Upload from './pages/Upload'
import DataTable from './pages/DataTable'
import Settings from './pages/Settings'
import { getAlerts } from './services/api'

function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [alertCount, setAlertCount] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    getAlerts('Orange').then((a) => setAlertCount(a.length)).catch(() => {})
  }, [])

  return (
    <div className="min-h-screen">
      <Sidebar open={sidebarOpen} />
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/40 z-20 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}
      <div className="lg:pl-64 flex flex-col min-h-screen">
        <Navbar
          onMenuClick={() => setSidebarOpen((o) => !o)}
          alertCount={alertCount}
          onSearch={(q) => navigate(`/data?search=${encodeURIComponent(q)}`)}
        />
        <main className="flex-1 p-4 lg:p-8">{children}</main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/map" element={<MapView />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/data" element={<DataTable />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
