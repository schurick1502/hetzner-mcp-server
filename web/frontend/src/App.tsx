import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { Server, Shield, HardDrive, Network, Menu } from 'lucide-react'
import ServersPage from './pages/ServersPage'
import FirewallsPage from './pages/FirewallsPage'
import VolumesPage from './pages/VolumesPage'
import NetworksPage from './pages/NetworksPage'
import DashboardPage from './pages/DashboardPage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex">
        {/* Sidebar */}
        <aside className="w-64 bg-hetzner-blue text-white p-6">
          <div className="mb-8">
            <h1 className="text-2xl font-bold">Hetzner Cloud</h1>
            <p className="text-sm text-gray-300">Management Console</p>
          </div>

          <nav className="space-y-2">
            <NavLink to="/" icon={<Menu size={20} />} label="Dashboard" />
            <NavLink to="/servers" icon={<Server size={20} />} label="Servers" />
            <NavLink to="/firewalls" icon={<Shield size={20} />} label="Firewalls" />
            <NavLink to="/volumes" icon={<HardDrive size={20} />} label="Volumes" />
            <NavLink to="/networks" icon={<Network size={20} />} label="Networks" />
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 p-8 overflow-auto">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/servers" element={<ServersPage />} />
            <Route path="/firewalls" element={<FirewallsPage />} />
            <Route path="/volumes" element={<VolumesPage />} />
            <Route path="/networks" element={<NetworksPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

function NavLink({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-white/10 transition-colors"
    >
      {icon}
      <span>{label}</span>
    </Link>
  )
}

export default App
