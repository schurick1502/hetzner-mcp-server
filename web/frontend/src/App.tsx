import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { Shield, Database, Network, Menu, LineChart, Terminal, Bot } from 'lucide-react'
import FirewallsPage from './pages/FirewallsPage'
import StoragePage from './pages/StoragePage'
import NetworksPage from './pages/NetworksPage'
import DashboardPage from './pages/DashboardPage'
import MonitoringPage from './pages/MonitoringPage'
import CliPage from './pages/CliPage'
import AiAssistantPage from './pages/AiAssistantPage'

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
            <NavLink to="/firewalls" icon={<Shield size={20} />} label="Firewalls" />
            <NavLink to="/storage" icon={<Database size={20} />} label="Storage" />
            <NavLink to="/networks" icon={<Network size={20} />} label="Networks" />
            <NavLink to="/monitoring" icon={<LineChart size={20} />} label="Monitoring" />
            <NavLink to="/cli" icon={<Terminal size={20} />} label="CLI" />
            <NavLink to="/ai" icon={<Bot size={20} />} label="AI Assistant" />
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 p-8 overflow-auto">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/firewalls" element={<FirewallsPage />} />
            <Route path="/storage" element={<StoragePage />} />
            <Route path="/networks" element={<NetworksPage />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
            <Route path="/cli" element={<CliPage />} />
            <Route path="/ai" element={<AiAssistantPage />} />
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
