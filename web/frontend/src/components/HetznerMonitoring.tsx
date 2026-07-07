import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Server, Cpu, HardDrive, Activity, Wifi, Clock,
  MapPin, MemoryStick, Network,
  Gauge, Folder, Trash2, AlertTriangle,
  CheckCircle, FileText, Package, Container
} from 'lucide-react'
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { format } from 'date-fns'
import { getHetznerAccountHeaders } from '../services/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

interface ServerInfo {
  id: number
  name: string
  status: string
  public_ipv4: string
  public_ipv6: string
  server_type: {
    name: string
    cores: number
    memory: number
    disk: number
  }
  datacenter: string
  location: string
  image: string
  created: string
  backup_window: string
}

interface SystemMetrics {
  cpu_percent: number
  memory_used: number
  memory_total: number
  memory_percent: number
  disk_used: number
  disk_total: number
  disk_percent: number
  load_1: number
  load_5: number
  load_15: number
  uptime: string
  network_rx: number
  network_tx: number
  processes: number
}

interface HistoryPoint {
  time: number
  cpu: number
  memory: number
  network_rx: number
  network_tx: number
}

interface DiskAnalysis {
  top_directories: Array<{ path: string; size: string }>
  docker_usage: Array<{ type: string; total: string; active: string; size: string; reclaimable: string }>
  log_files: Array<{ path: string; size: string }>
  old_containers: Array<{ name: string; status: string; size: string }>
  dangling_images: Array<{ id: string; size: string }>
  journal_size: string
  apt_cache: string
}

interface CleanupSuggestion {
  category: string
  description: string
  potential_savings: string
  command: string
  risk: string
  safe_for_production: boolean
}

const hetznerApi = {
  listServers: async () => {
    const res = await fetch(`${API_URL}/api/servers/`, { headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to fetch servers')
    return res.json()
  },
  getServer: async (name: string) => {
    const res = await fetch(`${API_URL}/api/servers/${name}`, { headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to fetch server')
    return res.json()
  },
  getSystemMetrics: async (host: string) => {
    const res = await fetch(`${API_URL}/api/docker/system-metrics?server=${encodeURIComponent(host)}`, { headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to fetch system metrics')
    return res.json()
  },
  getDiskAnalysis: async (host: string) => {
    const res = await fetch(`${API_URL}/api/docker/disk-analysis?server=${encodeURIComponent(host)}`, { headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to fetch disk analysis')
    return res.json()
  },
  executeCleanup: async (command: string, host: string) => {
    const res = await fetch(`${API_URL}/api/docker/cleanup?server=${encodeURIComponent(host)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getHetznerAccountHeaders() },
      body: JSON.stringify({ command })
    })
    if (!res.ok) throw new Error('Cleanup failed')
    return res.json()
  }
}

function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i]
}

function formatUptime(uptime: string): string {
  return uptime || 'N/A'
}

function ProgressBar({ value, color, label }: { value: number, color: string, label: string }) {
  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium">{value.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  )
}

type ViewTab = 'metrics' | 'disk-analysis'

export default function HetznerMonitoring() {
  const [selectedServer, setSelectedServer] = useState<string | null>(null)
  const [metricsHistory, setMetricsHistory] = useState<HistoryPoint[]>([])
  const [activeView, setActiveView] = useState<ViewTab>('metrics')
  const [cleanupOutput, setCleanupOutput] = useState<string | null>(null)
  const queryClient = useQueryClient()

  // Fetch Hetzner servers
  const { data: serversData, isLoading: serversLoading } = useQuery({
    queryKey: ['hetzner-servers'],
    queryFn: hetznerApi.listServers,
    refetchInterval: 60000,
  })

  const servers = serversData?.servers || []
  const activeServerName = selectedServer || (servers.length > 0 ? servers[0].name : null)
  const activeServer = servers.find((s: ServerInfo) => s.name === activeServerName)

  // Fetch server details
  const { data: serverDetails } = useQuery({
    queryKey: ['hetzner-server-details', activeServerName],
    queryFn: () => activeServerName ? hetznerApi.getServer(activeServerName) : null,
    enabled: !!activeServerName,
    refetchInterval: 30000,
  })

  // Fetch live system metrics via SSH
  const { data: metricsData, isLoading: metricsLoading } = useQuery({
    queryKey: ['hetzner-system-metrics', activeServer?.public_ipv4],
    queryFn: () => activeServer?.public_ipv4 ? hetznerApi.getSystemMetrics(activeServer.public_ipv4) : null,
    enabled: !!activeServer?.public_ipv4,
    refetchInterval: 5000,
  })

  const metrics: SystemMetrics | null = metricsData?.metrics || null

  // Fetch disk analysis
  const { data: diskData, isLoading: diskLoading, refetch: refetchDisk } = useQuery({
    queryKey: ['hetzner-disk-analysis', activeServer?.public_ipv4],
    queryFn: () => activeServer?.public_ipv4 ? hetznerApi.getDiskAnalysis(activeServer.public_ipv4) : null,
    enabled: !!activeServer?.public_ipv4 && activeView === 'disk-analysis',
    refetchInterval: false, // Manual refresh only
  })

  const diskAnalysis: DiskAnalysis | null = diskData?.analysis || null
  const cleanupSuggestions: CleanupSuggestion[] = diskData?.cleanup_suggestions || []

  // Cleanup mutation
  const cleanupMutation = useMutation({
    mutationFn: ({ command, host }: { command: string; host: string }) =>
      hetznerApi.executeCleanup(command, host),
    onSuccess: (data) => {
      setCleanupOutput(data.output || 'Bereinigung erfolgreich')
      refetchDisk()
      queryClient.invalidateQueries({ queryKey: ['hetzner-system-metrics'] })
    },
    onError: (error: Error) => {
      setCleanupOutput(`Fehler: ${error.message}`)
    }
  })

  // Update history when new metrics arrive
  useEffect(() => {
    if (metrics) {
      setMetricsHistory(prev => {
        const newPoint: HistoryPoint = {
          time: Date.now(),
          cpu: metrics.cpu_percent,
          memory: metrics.memory_percent,
          network_rx: metrics.network_rx,
          network_tx: metrics.network_tx,
        }
        const updated = [...prev, newPoint].slice(-60) // Keep last 60 points (5 min at 5s interval)
        return updated
      })
    }
  }, [metrics])

  // Reset history when server changes
  useEffect(() => {
    setMetricsHistory([])
  }, [activeServerName])

  const server = serverDetails?.server || activeServer

  if (serversLoading) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <Server className="text-gray-500 animate-pulse" size={24} />
          <div>
            <h3 className="font-semibold text-gray-800">Lade Server...</h3>
          </div>
        </div>
      </div>
    )
  }

  if (servers.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <p className="text-yellow-800">Keine Hetzner Server gefunden</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Server Selector & View Tabs */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700">Server:</label>
            <select
              value={activeServerName || ''}
              onChange={(e) => setSelectedServer(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hetzner-blue focus:border-transparent"
            >
              {servers.map((s: ServerInfo) => (
                <option key={s.id} value={s.name}>
                  {s.name} ({s.public_ipv4}) - {s.status}
                </option>
              ))}
            </select>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setActiveView('metrics')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeView === 'metrics'
                  ? 'bg-hetzner-blue text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Gauge size={18} />
              Live Metriken
            </button>
            <button
              onClick={() => setActiveView('disk-analysis')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeView === 'disk-analysis'
                  ? 'bg-hetzner-blue text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <HardDrive size={18} />
              Festplatten-Analyse
            </button>
          </div>
        </div>
      </div>

      {server && activeView === 'metrics' && (
        <>
          {/* Server Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center gap-3">
                <Server className="text-hetzner-blue" size={24} />
                <div>
                  <p className="text-sm text-gray-500">Server</p>
                  <p className="font-semibold">{server.name}</p>
                  <p className="text-xs text-gray-400">{server.server_type?.name}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center gap-3">
                <Cpu className="text-purple-500" size={24} />
                <div>
                  <p className="text-sm text-gray-500">CPU / RAM / Disk</p>
                  <p className="font-semibold">
                    {server.server_type?.cores} Cores / {server.server_type?.memory} GB / {server.server_type?.disk} GB
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center gap-3">
                <MapPin className="text-green-500" size={24} />
                <div>
                  <p className="text-sm text-gray-500">Standort</p>
                  <p className="font-semibold">{server.datacenter || server.location}</p>
                  <p className="text-xs text-gray-400">{server.image}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center gap-3">
                <Wifi className="text-blue-500" size={24} />
                <div>
                  <p className="text-sm text-gray-500">IPv4</p>
                  <p className="font-semibold font-mono">{server.public_ipv4}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Live Metrics */}
          {metrics ? (
            <>
              {/* Resource Usage */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* CPU */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Cpu className="text-hetzner-red" size={20} />
                    <h3 className="font-semibold">CPU-Auslastung</h3>
                  </div>
                  <div className="text-4xl font-bold text-hetzner-red mb-4">
                    {metrics.cpu_percent.toFixed(1)}%
                  </div>
                  <ProgressBar value={metrics.cpu_percent} color="bg-hetzner-red" label="CPU" />
                  <div className="mt-4 text-sm text-gray-600">
                    <p>Load: {metrics.load_1?.toFixed(2)} / {metrics.load_5?.toFixed(2)} / {metrics.load_15?.toFixed(2)}</p>
                  </div>
                </div>

                {/* Memory */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <MemoryStick className="text-purple-500" size={20} />
                    <h3 className="font-semibold">Speicher</h3>
                  </div>
                  <div className="text-4xl font-bold text-purple-600 mb-4">
                    {metrics.memory_percent.toFixed(1)}%
                  </div>
                  <ProgressBar value={metrics.memory_percent} color="bg-purple-500" label="RAM" />
                  <div className="mt-4 text-sm text-gray-600">
                    <p>{formatBytes(metrics.memory_used * 1024 * 1024)} / {formatBytes(metrics.memory_total * 1024 * 1024)}</p>
                  </div>
                </div>

                {/* Disk */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <HardDrive className="text-green-500" size={20} />
                    <h3 className="font-semibold">Festplatte</h3>
                  </div>
                  <div className="text-4xl font-bold text-green-600 mb-4">
                    {metrics.disk_percent.toFixed(1)}%
                  </div>
                  <ProgressBar value={metrics.disk_percent} color="bg-green-500" label="Disk" />
                  <div className="mt-4 text-sm text-gray-600">
                    <p>{formatBytes(metrics.disk_used * 1024 * 1024 * 1024)} / {formatBytes(metrics.disk_total * 1024 * 1024 * 1024)}</p>
                  </div>
                </div>
              </div>

              {/* Additional Info */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg shadow p-4">
                  <div className="flex items-center gap-3">
                    <Clock className="text-orange-500" size={20} />
                    <div>
                      <p className="text-sm text-gray-500">Uptime</p>
                      <p className="font-semibold">{formatUptime(metrics.uptime)}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-4">
                  <div className="flex items-center gap-3">
                    <Activity className="text-blue-500" size={20} />
                    <div>
                      <p className="text-sm text-gray-500">Prozesse</p>
                      <p className="font-semibold">{metrics.processes}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-4">
                  <div className="flex items-center gap-3">
                    <Network className="text-green-500" size={20} />
                    <div>
                      <p className="text-sm text-gray-500">Netzwerk RX</p>
                      <p className="font-semibold">{formatBytes(metrics.network_rx)}/s</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-4">
                  <div className="flex items-center gap-3">
                    <Network className="text-red-500" size={20} />
                    <div>
                      <p className="text-sm text-gray-500">Netzwerk TX</p>
                      <p className="font-semibold">{formatBytes(metrics.network_tx)}/s</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Charts */}
              {metricsHistory.length > 1 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* CPU History */}
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="font-semibold mb-4">CPU-Verlauf (5 Min)</h3>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={metricsHistory}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="time"
                          tickFormatter={(ts) => format(new Date(ts), 'HH:mm:ss')}
                          tick={{ fontSize: 10 }}
                        />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                        <Tooltip
                          labelFormatter={(ts) => format(new Date(ts), 'HH:mm:ss')}
                          formatter={(value) => [`${Number(value).toFixed(1)}%`, 'CPU']}
                        />
                        <Area type="monotone" dataKey="cpu" stroke="#D50C2D" fill="#D50C2D" fillOpacity={0.3} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Memory History */}
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="font-semibold mb-4">Speicher-Verlauf (5 Min)</h3>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={metricsHistory}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="time"
                          tickFormatter={(ts) => format(new Date(ts), 'HH:mm:ss')}
                          tick={{ fontSize: 10 }}
                        />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                        <Tooltip
                          labelFormatter={(ts) => format(new Date(ts), 'HH:mm:ss')}
                          formatter={(value) => [`${Number(value).toFixed(1)}%`, 'RAM']}
                        />
                        <Area type="monotone" dataKey="memory" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.3} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </>
          ) : metricsLoading ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <Gauge className="mx-auto text-gray-400 animate-pulse mb-4" size={48} />
              <p className="text-gray-500">Lade System-Metriken...</p>
            </div>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <p className="text-yellow-800">Keine Live-Metriken verfügbar. SSH-Verbindung prüfen.</p>
            </div>
          )}
        </>
      )}

      {/* Disk Analysis View */}
      {server && activeView === 'disk-analysis' && (
        <>
          {diskLoading ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <HardDrive className="mx-auto text-gray-400 animate-pulse mb-4" size={48} />
              <p className="text-gray-500">Analysiere Festplattennutzung...</p>
              <p className="text-xs text-gray-400 mt-2">Dies kann einige Sekunden dauern</p>
            </div>
          ) : diskAnalysis ? (
            <div className="space-y-6">
              {/* Cleanup Suggestions */}
              {cleanupSuggestions.length > 0 && (
                <div className="bg-white rounded-lg shadow">
                  <div className="p-4 border-b flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Trash2 className="text-hetzner-red" size={20} />
                      <h3 className="font-semibold">Bereinigungsvorschläge</h3>
                    </div>
                    <button
                      onClick={() => refetchDisk()}
                      className="text-sm text-hetzner-blue hover:underline"
                    >
                      Neu analysieren
                    </button>
                  </div>
                  <div className="p-4 space-y-3">
                    {cleanupSuggestions.map((suggestion, idx) => (
                      <div
                        key={idx}
                        className={`border rounded-lg p-4 ${
                          suggestion.risk === 'low' ? 'border-green-200 bg-green-50' :
                          suggestion.risk === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                          'border-red-200 bg-red-50'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                suggestion.category === 'Docker' ? 'bg-blue-100 text-blue-800' :
                                suggestion.category === 'System' ? 'bg-purple-100 text-purple-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {suggestion.category}
                              </span>
                              {suggestion.safe_for_production && (
                                <span className="flex items-center gap-1 text-xs text-green-600">
                                  <CheckCircle size={12} />
                                  Produktionssicher
                                </span>
                              )}
                              {suggestion.risk !== 'low' && (
                                <span className="flex items-center gap-1 text-xs text-yellow-600">
                                  <AlertTriangle size={12} />
                                  {suggestion.risk === 'medium' ? 'Mittleres Risiko' : 'Hohes Risiko'}
                                </span>
                              )}
                            </div>
                            <p className="font-medium mt-1">{suggestion.description}</p>
                            <p className="text-sm text-gray-600 mt-1">
                              Potentielle Einsparung: <span className="font-semibold text-green-600">{suggestion.potential_savings}</span>
                            </p>
                            <code className="text-xs bg-gray-800 text-green-400 px-2 py-1 rounded mt-2 inline-block">
                              {suggestion.command}
                            </code>
                          </div>
                          <button
                            onClick={() => {
                              if (confirm(`Möchtest du "${suggestion.command}" ausführen?\n\nDies kann nicht rückgängig gemacht werden!`)) {
                                // Add -f flag if not present for docker commands
                                let cmd = suggestion.command
                                if (cmd.startsWith('docker') && !cmd.includes('-f')) {
                                  cmd = cmd + ' -f'
                                }
                                cleanupMutation.mutate({
                                  command: cmd,
                                  host: activeServer?.public_ipv4 || ''
                                })
                              }
                            }}
                            disabled={cleanupMutation.isPending}
                            className={`ml-4 px-4 py-2 rounded-lg text-white transition-colors ${
                              suggestion.safe_for_production
                                ? 'bg-green-500 hover:bg-green-600'
                                : 'bg-yellow-500 hover:bg-yellow-600'
                            } disabled:opacity-50`}
                          >
                            {cleanupMutation.isPending ? '...' : 'Ausführen'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Cleanup Output */}
              {cleanupOutput && (
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-white font-medium">Ausgabe</h4>
                    <button
                      onClick={() => setCleanupOutput(null)}
                      className="text-gray-400 hover:text-white"
                    >
                      &times;
                    </button>
                  </div>
                  <pre className="text-green-400 text-sm font-mono whitespace-pre-wrap">
                    {cleanupOutput}
                  </pre>
                </div>
              )}

              {/* Top Directories */}
              <div className="bg-white rounded-lg shadow">
                <div className="p-4 border-b">
                  <div className="flex items-center gap-2">
                    <Folder className="text-yellow-500" size={20} />
                    <h3 className="font-semibold">Top 15 Verzeichnisse nach Größe</h3>
                  </div>
                </div>
                <div className="p-4">
                  <div className="space-y-2">
                    {diskAnalysis.top_directories.map((dir, idx) => (
                      <div key={idx} className="flex items-center justify-between py-2 border-b last:border-0">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-gray-100 text-gray-600 text-xs flex items-center justify-center">
                            {idx + 1}
                          </span>
                          <code className="text-sm">{dir.path}</code>
                        </div>
                        <span className={`font-mono font-semibold ${
                          dir.size.includes('G') ? 'text-red-600' :
                          dir.size.includes('M') ? 'text-yellow-600' : 'text-gray-600'
                        }`}>
                          {dir.size}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Docker Usage */}
              {diskAnalysis.docker_usage.length > 0 && (
                <div className="bg-white rounded-lg shadow">
                  <div className="p-4 border-b">
                    <div className="flex items-center gap-2">
                      <Container className="text-blue-500" size={20} />
                      <h3 className="font-semibold">Docker Speichernutzung</h3>
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      {diskAnalysis.docker_usage.map((item, idx) => (
                        <div key={idx} className="border rounded-lg p-4">
                          <p className="text-sm text-gray-500">{item.type}</p>
                          <p className="text-2xl font-bold">{item.size}</p>
                          <div className="flex justify-between text-xs mt-2">
                            <span>Aktiv: {item.active}</span>
                            <span className="text-green-600">Freigeben: {item.reclaimable}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Log Files & Other */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Log Files */}
                {diskAnalysis.log_files.length > 0 && (
                  <div className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b">
                      <div className="flex items-center gap-2">
                        <FileText className="text-orange-500" size={20} />
                        <h3 className="font-semibold">Größte Log-Dateien</h3>
                      </div>
                    </div>
                    <div className="p-4 max-h-64 overflow-y-auto">
                      {diskAnalysis.log_files.map((file, idx) => (
                        <div key={idx} className="flex justify-between py-1 text-sm border-b last:border-0">
                          <code className="text-gray-600 truncate flex-1">{file.path}</code>
                          <span className="font-mono ml-2">{file.size}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Old Containers */}
                {diskAnalysis.old_containers.length > 0 && (
                  <div className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b">
                      <div className="flex items-center gap-2">
                        <Package className="text-gray-500" size={20} />
                        <h3 className="font-semibold">Gestoppte Container</h3>
                      </div>
                    </div>
                    <div className="p-4 max-h-64 overflow-y-auto">
                      {diskAnalysis.old_containers.map((container, idx) => (
                        <div key={idx} className="flex justify-between py-1 text-sm border-b last:border-0">
                          <span className="truncate flex-1">{container.name}</span>
                          <span className="text-gray-500 text-xs ml-2">{container.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* System Info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg shadow p-4">
                  <p className="text-sm text-gray-500">Journal Logs</p>
                  <p className="text-xl font-semibold">{diskAnalysis.journal_size}</p>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                  <p className="text-sm text-gray-500">APT Cache</p>
                  <p className="text-xl font-semibold">{diskAnalysis.apt_cache}</p>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                  <p className="text-sm text-gray-500">Ungenutzte Images</p>
                  <p className="text-xl font-semibold">{diskAnalysis.dangling_images.length} Stück</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <p className="text-yellow-800">Festplattenanalyse konnte nicht geladen werden.</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
