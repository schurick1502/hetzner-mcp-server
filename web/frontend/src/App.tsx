import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Shield, Database, Network, Menu, LineChart, Terminal, Bot, Settings, ShieldCheck, DollarSign, Scale, Share2, MonitorSmartphone } from 'lucide-react'
import SecurityPage from './pages/SecurityPage'
import CostsPage from './pages/CostsPage'
import LoadBalancersPage from './pages/LoadBalancersPage'
import TopologyPage from './pages/TopologyPage'
import FirewallsPage from './pages/FirewallsPage'
import StoragePage from './pages/StoragePage'
import NetworksPage from './pages/NetworksPage'
import DashboardPage from './pages/DashboardPage'
import MonitoringPage from './pages/MonitoringPage'
import CliPage from './pages/CliPage'
import AiAssistantPage from './pages/AiAssistantPage'
import SettingsPage from './pages/SettingsPage'
import SshTerminalPage from './pages/SshTerminalPage'
import { miscApi, getActiveHetznerAccount, setActiveHetznerAccount } from './services/api'

interface HetznerAccount {
  id: string
  label: string
  is_default: boolean
}

function App() {
  const queryClient = useQueryClient()
  const [activeAccount, setActiveAccount] = useState<string>(getActiveHetznerAccount() || 'all')

  const { data: accountsData } = useQuery({
    queryKey: ['hetzner-accounts'],
    queryFn: miscApi.accounts,
  })

  const accounts: HetznerAccount[] = accountsData?.data?.accounts || []
  const defaultAccount: string | null = accountsData?.data?.default_account || null

  useEffect(() => {
    if (accounts.length === 0) return

    const isValid = accounts.some(acc => acc.id === activeAccount)
    if (isValid) return

    const next = 'all'
    setActiveAccount(next)
    setActiveHetznerAccount(next)
    queryClient.invalidateQueries()
  }, [accounts, defaultAccount, activeAccount, queryClient])

  const onAccountChange = (accountId: string) => {
    setActiveAccount(accountId)
    setActiveHetznerAccount(accountId)
    queryClient.invalidateQueries()
  }

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
            <NavLink to="/security" icon={<ShieldCheck size={20} />} label="Security" />
            <NavLink to="/firewalls" icon={<Shield size={20} />} label="Firewalls" />
            <NavLink to="/load-balancers" icon={<Scale size={20} />} label="Load Balancer" />
            <NavLink to="/storage" icon={<Database size={20} />} label="Storage" />
            <NavLink to="/networks" icon={<Network size={20} />} label="Networks" />
            <NavLink to="/topology" icon={<Share2 size={20} />} label="Topologie" />
            <NavLink to="/costs" icon={<DollarSign size={20} />} label="Kosten" />
            <NavLink to="/monitoring" icon={<LineChart size={20} />} label="Monitoring" />
            <NavLink to="/cli" icon={<Terminal size={20} />} label="CLI" />
            <NavLink to="/ssh" icon={<MonitorSmartphone size={20} />} label="SSH Terminal" />
            <NavLink to="/ai" icon={<Bot size={20} />} label="AI Assistant" />
            <div className="border-t border-white/20 my-4"></div>
            <NavLink to="/settings" icon={<Settings size={20} />} label="Einstellungen" />
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 p-8 overflow-auto">
          <div className="flex justify-end mb-4">
            <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2">
              <label className="text-sm text-gray-600">Account:</label>
              <select
                value={activeAccount}
                onChange={(e) => onAccountChange(e.target.value)}
                className="text-sm border rounded px-2 py-1 bg-white"
              >
                <option value="all">Alle Accounts</option>
                {accounts.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/security" element={<SecurityPage />} />
            <Route path="/firewalls" element={<FirewallsPage />} />
            <Route path="/load-balancers" element={<LoadBalancersPage />} />
            <Route path="/storage" element={<StoragePage />} />
            <Route path="/networks" element={<NetworksPage />} />
            <Route path="/topology" element={<TopologyPage />} />
            <Route path="/costs" element={<CostsPage />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
            <Route path="/cli" element={<CliPage />} />
            <Route path="/ssh" element={<SshTerminalPage />} />
            <Route path="/ai" element={<AiAssistantPage />} />
            <Route path="/settings" element={<SettingsPage />} />
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
