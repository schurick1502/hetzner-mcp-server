import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { serversApi, metricsApi } from '../services/api'
import MetricsChart from '../components/MetricsChart'
import TimeRangeSelector from '../components/TimeRangeSelector'

export default function MonitoringPage() {
  const [selectedServer, setSelectedServer] = useState<string>('')
  const [timeRange, setTimeRange] = useState('1h')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const { data: serversData } = useQuery({
    queryKey: ['servers'],
    queryFn: serversApi.list,
  })

  const { data: metricsData } = useQuery({
    queryKey: ['metrics', selectedServer, timeRange],
    queryFn: () => {
      const now = new Date()
      const hours = timeRange === '1h' ? 1 : timeRange === '24h' ? 24 : 168
      const start = new Date(now.getTime() - hours * 60 * 60 * 1000).toISOString()
      return metricsApi.getServerMetrics(selectedServer, 'cpu,disk,network', start, now.toISOString())
    },
    enabled: !!selectedServer,
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const servers = serversData?.data?.servers || []

  useEffect(() => {
    if (servers.length > 0 && !selectedServer) {
      setSelectedServer(servers[0].name)
    }
  }, [servers, selectedServer])

  const metrics = metricsData?.data?.metrics?.time_series || {}

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Server-Monitoring</h1>
        <div className="flex items-center gap-4">
          <select
            value={selectedServer}
            onChange={(e) => setSelectedServer(e.target.value)}
            className="input"
          >
            {servers.map((s: any) => (
              <option key={s.id} value={s.name}>{s.name}</option>
            ))}
          </select>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            <span>Auto-Refresh (30s)</span>
          </label>
        </div>
      </div>

      <div className="mb-6">
        <TimeRangeSelector selected={timeRange} onChange={setTimeRange} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {metrics.cpu && (
          <MetricsChart
            data={metrics.cpu}
            title="CPU-Auslastung"
            color="#D50C2D"
            unit="%"
          />
        )}
        {metrics['network.0.bandwidth.in'] && (
          <MetricsChart
            data={metrics['network.0.bandwidth.in']}
            title="Netzwerk Eingehend"
            color="#0A1E42"
            unit="MB/s"
          />
        )}
        {metrics['disk.0.iops.read'] && (
          <MetricsChart
            data={metrics['disk.0.iops.read']}
            title="Disk IOPS (Read)"
            color="#10B981"
            unit="IOPS"
          />
        )}
        {metrics['disk.0.bandwidth.read'] && (
          <MetricsChart
            data={metrics['disk.0.bandwidth.read']}
            title="Disk Bandwidth (Read)"
            color="#8B5CF6"
            unit="MB/s"
          />
        )}
      </div>
    </div>
  )
}
