import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Play, Square, RotateCcw, Server,
  AlertCircle, CheckCircle, FileText, ChevronDown, ChevronRight,
  Box, Layers, Cpu, Network
} from 'lucide-react'
import { getHetznerAccountHeaders } from '../services/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

interface Container {
  id: string
  name: string
  image: string
  status: string
  state: string
  ports: string
  created: string
  running: boolean
  health: string
  project: string
  networks: string
}

interface ContainerStats {
  cpu: string
  memory: string
  mem_perc: string
  net_io: string
  block_io: string
}

interface MonitoredServer {
  name: string
  host: string
  user: string
  port: number
  status: string
  docker_version?: string
  error?: string
}

interface ProjectGroup {
  name: string
  displayName: string
  containers: Container[]
  runningCount: number
  totalCount: number
}

const dockerApi = {
  listServers: async () => {
    const res = await fetch(`${API_URL}/api/docker/servers`, { headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to fetch servers')
    return res.json()
  },
  listContainers: async (server?: string) => {
    const url = server ? `${API_URL}/api/docker/containers?server=${encodeURIComponent(server)}` : `${API_URL}/api/docker/containers`
    const res = await fetch(url, { headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to fetch containers')
    return res.json()
  },
  getStats: async (name: string, server?: string) => {
    const url = server ? `${API_URL}/api/docker/containers/${name}/stats?server=${encodeURIComponent(server)}` : `${API_URL}/api/docker/containers/${name}/stats`
    const res = await fetch(url, { headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to fetch stats')
    return res.json()
  },
  getLogs: async (name: string, lines: number = 50, server?: string) => {
    const params = new URLSearchParams({ lines: lines.toString() })
    if (server) params.append('server', server)
    const res = await fetch(`${API_URL}/api/docker/containers/${name}/logs?${params}`, { headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to fetch logs')
    return res.json()
  },
  startContainer: async (name: string, server?: string) => {
    const url = server ? `${API_URL}/api/docker/containers/${name}/start?server=${encodeURIComponent(server)}` : `${API_URL}/api/docker/containers/${name}/start`
    const res = await fetch(url, { method: 'POST', headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to start container')
    return res.json()
  },
  stopContainer: async (name: string, server?: string) => {
    const url = server ? `${API_URL}/api/docker/containers/${name}/stop?server=${encodeURIComponent(server)}` : `${API_URL}/api/docker/containers/${name}/stop`
    const res = await fetch(url, { method: 'POST', headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to stop container')
    return res.json()
  },
  restartContainer: async (name: string, server?: string) => {
    const url = server ? `${API_URL}/api/docker/containers/${name}/restart?server=${encodeURIComponent(server)}` : `${API_URL}/api/docker/containers/${name}/restart`
    const res = await fetch(url, { method: 'POST', headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to restart container')
    return res.json()
  },
  getSystemInfo: async (server?: string) => {
    const url = server ? `${API_URL}/api/docker/system?server=${encodeURIComponent(server)}` : `${API_URL}/api/docker/system`
    const res = await fetch(url, { headers: getHetznerAccountHeaders() })
    if (!res.ok) throw new Error('Failed to fetch system info')
    return res.json()
  },
  checkHealth: async (server?: string) => {
    const url = server ? `${API_URL}/api/docker/health?server=${encodeURIComponent(server)}` : `${API_URL}/api/docker/health`
    const res = await fetch(url, { headers: getHetznerAccountHeaders() })
    return res.json()
  }
}

// Map project names to friendly display names
const projectDisplayNames: Record<string, string> = {
  'dokumentenscanner': 'DocFlow KI-Suite',
  'zammad-docker-compose': 'Zammad Helpdesk',
  'n8n': 'n8n Automation',
  'onemillion-odoo': 'OneMillion Odoo',
  'onemillion-tunnel': 'OneMillion Tunnel',
  'grebsmart-odoo': 'GrebSmart Odoo',
  'grebsmart-tunnel': 'GrebSmart Tunnel',
}

// Project colors
const projectColors: Record<string, string> = {
  'dokumentenscanner': 'bg-purple-500',
  'zammad-docker-compose': 'bg-yellow-500',
  'n8n': 'bg-orange-500',
  'onemillion-odoo': 'bg-blue-500',
  'onemillion-tunnel': 'bg-blue-400',
  'grebsmart-odoo': 'bg-green-500',
  'grebsmart-tunnel': 'bg-green-400',
}

function groupContainersByProject(containers: Container[]): ProjectGroup[] {
  const groups: Record<string, Container[]> = {}

  containers.forEach(container => {
    const project = container.project || 'Andere'
    if (!groups[project]) {
      groups[project] = []
    }
    groups[project].push(container)
  })

  return Object.entries(groups)
    .map(([name, containers]) => ({
      name,
      displayName: projectDisplayNames[name] || name,
      containers: containers.sort((a, b) => a.name.localeCompare(b.name)),
      runningCount: containers.filter(c => c.running).length,
      totalCount: containers.length
    }))
    .sort((a, b) => a.displayName.localeCompare(b.displayName))
}

export default function DockerMonitoring() {
  const [selectedServer, setSelectedServer] = useState<string | null>(null)
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set())
  const [selectedContainer, setSelectedContainer] = useState<string | null>(null)
  const [showLogs, setShowLogs] = useState(false)
  const queryClient = useQueryClient()

  // Fetch available servers
  const { data: serversData, isLoading: serversLoading } = useQuery({
    queryKey: ['docker-servers'],
    queryFn: dockerApi.listServers,
    refetchInterval: 60000,
  })

  const servers: MonitoredServer[] = serversData?.servers || []
  const connectedServers = servers.filter(s => s.status === 'connected')
  const activeServer = selectedServer || (connectedServers.length > 0 ? connectedServers[0].host : null)

  const { data: healthData } = useQuery({
    queryKey: ['docker-health', activeServer],
    queryFn: () => dockerApi.checkHealth(activeServer || undefined),
    refetchInterval: 30000,
    enabled: !!activeServer,
  })

  const { data: containersData, isLoading, error } = useQuery({
    queryKey: ['docker-containers', activeServer],
    queryFn: () => dockerApi.listContainers(activeServer || undefined),
    refetchInterval: 10000,
    enabled: healthData?.success === true && !!activeServer,
  })

  const { data: _systemData } = useQuery({
    queryKey: ['docker-system', activeServer],
    queryFn: () => dockerApi.getSystemInfo(activeServer || undefined),
    enabled: healthData?.success === true && !!activeServer,
  })

  const { data: statsData } = useQuery({
    queryKey: ['docker-stats', selectedContainer, activeServer],
    queryFn: () => selectedContainer ? dockerApi.getStats(selectedContainer, activeServer || undefined) : null,
    enabled: !!selectedContainer && !!activeServer,
    refetchInterval: 5000,
  })

  const { data: logsData } = useQuery({
    queryKey: ['docker-logs', selectedContainer, activeServer],
    queryFn: () => selectedContainer ? dockerApi.getLogs(selectedContainer, 100, activeServer || undefined) : null,
    enabled: !!selectedContainer && showLogs && !!activeServer,
  })

  const startMutation = useMutation({
    mutationFn: (name: string) => dockerApi.startContainer(name, activeServer || undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['docker-containers', activeServer] }),
  })

  const stopMutation = useMutation({
    mutationFn: (name: string) => dockerApi.stopContainer(name, activeServer || undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['docker-containers', activeServer] }),
  })

  const restartMutation = useMutation({
    mutationFn: (name: string) => dockerApi.restartContainer(name, activeServer || undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['docker-containers', activeServer] }),
  })

  const containers: Container[] = containersData?.containers || []
  const projectGroups = groupContainersByProject(containers)
  const stats: ContainerStats | null = statsData?.stats || null

  const toggleProject = (projectName: string) => {
    setExpandedProjects(prev => {
      const newSet = new Set(prev)
      if (newSet.has(projectName)) {
        newSet.delete(projectName)
      } else {
        newSet.add(projectName)
      }
      return newSet
    })
  }

  const expandAll = () => {
    setExpandedProjects(new Set(projectGroups.map(g => g.name)))
  }

  const collapseAll = () => {
    setExpandedProjects(new Set())
  }

  // Loading servers
  if (serversLoading) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <Server className="text-gray-500 animate-pulse" size={24} />
          <div>
            <h3 className="font-semibold text-gray-800">Lade Server...</h3>
            <p className="text-gray-600 text-sm">Verbindung zu Docker-Hosts wird hergestellt</p>
          </div>
        </div>
      </div>
    )
  }

  // No servers configured
  if (servers.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <AlertCircle className="text-yellow-500" size={24} />
          <div>
            <h3 className="font-semibold text-yellow-800">Keine Server konfiguriert</h3>
            <p className="text-yellow-600 text-sm">
              Bitte konfigurieren Sie DOCKER_MONITOR_SERVERS in der .env-Datei
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Connection status
  if (!healthData?.success && activeServer) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <AlertCircle className="text-red-500" size={24} />
          <div>
            <h3 className="font-semibold text-red-800">Verbindung fehlgeschlagen</h3>
            <p className="text-red-600 text-sm">
              Kann keine Verbindung zum Docker-Host herstellen: {healthData?.error || 'Unbekannter Fehler'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-4">
            <select
              value={activeServer || ''}
              onChange={(e) => {
                setSelectedServer(e.target.value)
                setSelectedContainer(null)
                setShowLogs(false)
              }}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hetzner-blue focus:border-transparent"
            >
              {servers.map((server) => (
                <option key={server.host} value={server.host}>
                  {server.name} ({server.host})
                </option>
              ))}
            </select>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <CheckCircle className="text-green-500" size={16} />
              <span>{containersData?.running_count || 0} / {containersData?.container_count || 0} Container</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={expandAll} className="text-sm text-hetzner-blue hover:underline">
              Alle aufklappen
            </button>
            <span className="text-gray-300">|</span>
            <button onClick={collapseAll} className="text-sm text-hetzner-blue hover:underline">
              Alle zuklappen
            </button>
          </div>
        </div>
      </div>

      {/* Project Groups */}
      {isLoading ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          <Layers className="mx-auto mb-4 animate-pulse" size={48} />
          <p>Lade Container...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 rounded-lg p-8 text-center text-red-500">
          Fehler beim Laden der Container
        </div>
      ) : (
        <div className="space-y-2">
          {projectGroups.map((group) => (
            <div key={group.name} className="bg-white rounded-lg shadow overflow-hidden">
              {/* Project Header */}
              <div
                onClick={() => toggleProject(group.name)}
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {expandedProjects.has(group.name) ? (
                    <ChevronDown size={20} className="text-gray-500" />
                  ) : (
                    <ChevronRight size={20} className="text-gray-500" />
                  )}
                  <div className={`w-3 h-3 rounded-full ${projectColors[group.name] || 'bg-gray-400'}`} />
                  <div>
                    <h3 className="font-semibold">{group.displayName}</h3>
                    <p className="text-xs text-gray-500">{group.name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    group.runningCount === group.totalCount
                      ? 'bg-green-100 text-green-800'
                      : group.runningCount === 0
                        ? 'bg-gray-100 text-gray-800'
                        : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {group.runningCount} / {group.totalCount} running
                  </span>
                </div>
              </div>

              {/* Containers List */}
              {expandedProjects.has(group.name) && (
                <div className="border-t">
                  {group.containers.map((container) => (
                    <div
                      key={container.id}
                      className={`flex items-center justify-between px-4 py-3 border-b last:border-b-0 hover:bg-gray-50 transition-colors ${
                        selectedContainer === container.name ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className="pl-8">
                          {container.running ? (
                            <span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block animate-pulse" />
                          ) : (
                            <span className="w-2.5 h-2.5 rounded-full bg-gray-400 inline-block" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <Box size={14} className="text-gray-400 flex-shrink-0" />
                            <span className="font-medium truncate">{container.name}</span>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5 flex-wrap">
                            <span className="truncate max-w-[180px]">{container.image}</span>
                            {container.ports && (
                              <span className="font-mono text-blue-600">{container.ports.split(',')[0]}</span>
                            )}
                            {container.networks && (
                              <span className="flex items-center gap-1 text-purple-600">
                                <Network size={10} />
                                <span className="truncate max-w-[150px]">
                                  {container.networks.split(',')[0]}
                                  {container.networks.includes(',') && ` +${container.networks.split(',').length - 1}`}
                                </span>
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          container.running ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                        }`}>
                          {container.state}
                        </span>

                        <div className="flex items-center gap-1 ml-2" onClick={(e) => e.stopPropagation()}>
                          {container.running ? (
                            <>
                              <button
                                onClick={() => stopMutation.mutate(container.name)}
                                disabled={stopMutation.isPending}
                                className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                                title="Stop"
                              >
                                <Square size={14} />
                              </button>
                              <button
                                onClick={() => restartMutation.mutate(container.name)}
                                disabled={restartMutation.isPending}
                                className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                title="Restart"
                              >
                                <RotateCcw size={14} />
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => startMutation.mutate(container.name)}
                              disabled={startMutation.isPending}
                              className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                              title="Start"
                            >
                              <Play size={14} />
                            </button>
                          )}
                          <button
                            onClick={() => {
                              setSelectedContainer(container.name)
                              setShowLogs(true)
                            }}
                            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                            title="Logs"
                          >
                            <FileText size={14} />
                          </button>
                          <button
                            onClick={() => setSelectedContainer(
                              selectedContainer === container.name ? null : container.name
                            )}
                            className="p-1.5 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded transition-colors"
                            title="Stats"
                          >
                            <Cpu size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Stats & Logs Panel */}
      {selectedContainer && (
        <div className="bg-white rounded-lg shadow">
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="font-semibold flex items-center gap-2">
              <Box size={18} />
              {selectedContainer}
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowLogs(false)}
                className={`px-3 py-1 rounded text-sm ${!showLogs ? 'bg-hetzner-blue text-white' : 'bg-gray-100'}`}
              >
                Stats
              </button>
              <button
                onClick={() => setShowLogs(true)}
                className={`px-3 py-1 rounded text-sm ${showLogs ? 'bg-hetzner-blue text-white' : 'bg-gray-100'}`}
              >
                Logs
              </button>
              <button
                onClick={() => {
                  setSelectedContainer(null)
                  setShowLogs(false)
                }}
                className="text-gray-400 hover:text-gray-600 ml-2"
              >
                &times;
              </button>
            </div>
          </div>

          {!showLogs && stats && (
            <div className="p-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 uppercase">CPU</p>
                  <p className="text-2xl font-bold text-hetzner-blue">{stats.cpu}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 uppercase">Memory</p>
                  <p className="text-2xl font-bold text-purple-600">{stats.mem_perc}</p>
                  <p className="text-xs text-gray-400">{stats.memory}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 uppercase">Network I/O</p>
                  <p className="text-sm font-mono">{stats.net_io}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 uppercase">Block I/O</p>
                  <p className="text-sm font-mono">{stats.block_io}</p>
                </div>
              </div>
            </div>
          )}

          {showLogs && logsData && (
            <div className="p-4">
              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-auto max-h-80 font-mono">
                {logsData.logs || 'Keine Logs verfügbar'}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
