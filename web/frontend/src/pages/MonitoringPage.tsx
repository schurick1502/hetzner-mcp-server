import { useState } from 'react'
import DockerMonitoring from '../components/DockerMonitoring'
import HetznerMonitoring from '../components/HetznerMonitoring'
import MetricsHistory from '../components/MetricsHistory'
import { Activity, Container, BarChart3 } from 'lucide-react'

type Tab = 'hetzner' | 'docker' | 'history'

export default function MonitoringPage() {
  const [activeTab, setActiveTab] = useState<Tab>('docker')

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Monitoring</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        <button
          onClick={() => setActiveTab('docker')}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
            activeTab === 'docker'
              ? 'border-hetzner-blue text-hetzner-blue'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Container size={20} />
          Docker Container
        </button>
        <button
          onClick={() => setActiveTab('hetzner')}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
            activeTab === 'hetzner'
              ? 'border-hetzner-blue text-hetzner-blue'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Activity size={20} />
          Hetzner Server
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
            activeTab === 'history'
              ? 'border-hetzner-blue text-hetzner-blue'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BarChart3 size={20} />
          Metriken-Historie
        </button>
      </div>

      {/* Docker Monitoring Tab */}
      {activeTab === 'docker' && <DockerMonitoring />}

      {/* Hetzner Server Monitoring Tab */}
      {activeTab === 'hetzner' && <HetznerMonitoring />}

      {/* Metrics History Tab */}
      {activeTab === 'history' && <MetricsHistory />}
    </div>
  )
}
