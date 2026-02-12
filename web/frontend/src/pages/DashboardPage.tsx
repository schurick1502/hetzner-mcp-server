import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Server, Shield, HardDrive, Network, Key, Camera, Archive, Image, Container, Cpu, MemoryStick, HardDrive as Disk, Activity, Play, Square, RotateCw, CheckSquare } from 'lucide-react'
import { serversApi, firewallsApi, volumesApi, networksApi, miscApi, storageApi, dockerApi, healthApi, bulkApi } from '../services/api'

function UsageBar({ percent, color }: { percent: number; color: string }) {
  return (
    <div className="w-full bg-gray-200 rounded-full h-3">
      <div
        className={`h-3 rounded-full transition-all ${color}`}
        style={{ width: `${Math.min(percent, 100)}%` }}
      />
    </div>
  )
}

export default function DashboardPage() {
  const [selectedServers, setSelectedServers] = useState<Set<string>>(new Set())
  const [bulkResult, setBulkResult] = useState<any>(null)
  const queryClient = useQueryClient()

  const bulkAction = useMutation({
    mutationFn: ({ action, names }: { action: string; names: string[] }) => bulkApi.execute(action, names),
    onSuccess: (res) => {
      setBulkResult(res.data?.data)
      queryClient.invalidateQueries({ queryKey: ['servers'] })
      setSelectedServers(new Set())
      setTimeout(() => setBulkResult(null), 5000)
    },
  })

  const toggleServer = (name: string) => {
    setSelectedServers(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  const { data: servers } = useQuery({ queryKey: ['servers'], queryFn: serversApi.list })
  const { data: firewalls } = useQuery({ queryKey: ['firewalls'], queryFn: firewallsApi.list })
  const { data: volumes } = useQuery({ queryKey: ['volumes'], queryFn: volumesApi.list })
  const { data: networks } = useQuery({ queryKey: ['networks'], queryFn: networksApi.list })
  const { data: sshKeys } = useQuery({ queryKey: ['sshKeys'], queryFn: miscApi.sshKeys })
  const { data: snapshots } = useQuery({ queryKey: ['snapshots'], queryFn: storageApi.snapshots })
  const { data: backups } = useQuery({ queryKey: ['backups'], queryFn: storageApi.backups })
  const { data: systemImages } = useQuery({ queryKey: ['systemImages'], queryFn: storageApi.systemImages })

  const { data: healthChecks } = useQuery({
    queryKey: ['healthChecks'],
    queryFn: healthApi.check,
    refetchInterval: 60000,
  })

  const { data: dockerServers } = useQuery({ queryKey: ['dockerServers'], queryFn: dockerApi.servers })

  // Ersten verbundenen Server für Metriken finden
  const connectedServer = dockerServers?.data?.servers?.find((s: any) => s.status === 'connected')

  const { data: dockerContainers } = useQuery({
    queryKey: ['dockerContainers', connectedServer?.host],
    queryFn: () => dockerApi.containers(connectedServer.host),
    enabled: !!connectedServer,
  })

  const { data: systemMetrics } = useQuery({
    queryKey: ['systemMetrics', connectedServer?.host],
    queryFn: () => dockerApi.systemMetrics(connectedServer.host),
    enabled: !!connectedServer,
    refetchInterval: 15000,
  })

  const stats = [
    { name: 'Servers', count: servers?.data?.count || 0, icon: <Server className="w-6 h-6" />, color: 'bg-blue-500' },
    { name: 'Firewalls', count: firewalls?.data?.count || 0, icon: <Shield className="w-6 h-6" />, color: 'bg-green-500' },
    { name: 'Volumes', count: volumes?.data?.count || 0, icon: <HardDrive className="w-6 h-6" />, color: 'bg-purple-500' },
    { name: 'Networks', count: networks?.data?.count || 0, icon: <Network className="w-6 h-6" />, color: 'bg-orange-500' },
    { name: 'Snapshots', count: snapshots?.data?.count || 0, icon: <Camera className="w-6 h-6" />, color: 'bg-cyan-500' },
    { name: 'Backups', count: backups?.data?.count || 0, icon: <Archive className="w-6 h-6" />, color: 'bg-amber-500' },
    { name: 'Images', count: systemImages?.data?.count || 0, icon: <Image className="w-6 h-6" />, color: 'bg-pink-500' },
    { name: 'SSH Keys', count: sshKeys?.data?.count || 0, icon: <Key className="w-6 h-6" />, color: 'bg-teal-500' },
  ]

  const metrics = systemMetrics?.data?.metrics
  const containers = dockerContainers?.data

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      {/* Ressourcen-Übersicht */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="card !p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className={`${stat.color} text-white p-1.5 rounded-md`}>
                {stat.icon}
              </div>
            </div>
            <p className="text-2xl font-bold">{stat.count}</p>
            <p className="text-xs text-gray-500">{stat.name}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Server-Auslastung */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-hetzner-blue" />
            <h2 className="text-xl font-bold">Server-Auslastung</h2>
          </div>
          {metrics ? (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="flex items-center gap-1"><Cpu size={14} /> CPU</span>
                  <span className="font-medium">{metrics.cpu_percent}%</span>
                </div>
                <UsageBar percent={metrics.cpu_percent} color={metrics.cpu_percent > 80 ? 'bg-red-500' : metrics.cpu_percent > 50 ? 'bg-yellow-500' : 'bg-blue-500'} />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="flex items-center gap-1"><MemoryStick size={14} /> RAM</span>
                  <span className="font-medium">{(metrics.memory_used / 1024).toFixed(1)} / {(metrics.memory_total / 1024).toFixed(1)} GB ({metrics.memory_percent}%)</span>
                </div>
                <UsageBar percent={metrics.memory_percent} color={metrics.memory_percent > 80 ? 'bg-red-500' : metrics.memory_percent > 50 ? 'bg-yellow-500' : 'bg-purple-500'} />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="flex items-center gap-1"><Disk size={14} /> Disk</span>
                  <span className="font-medium">{metrics.disk_used} / {metrics.disk_total} GB ({metrics.disk_percent}%)</span>
                </div>
                <UsageBar percent={metrics.disk_percent} color={metrics.disk_percent > 80 ? 'bg-red-500' : metrics.disk_percent > 50 ? 'bg-yellow-500' : 'bg-green-500'} />
              </div>
              <div className="grid grid-cols-3 gap-3 pt-2 border-t text-sm text-gray-600">
                <div>
                  <p className="text-xs text-gray-400">Load</p>
                  <p className="font-medium text-gray-800">{metrics.load_1} / {metrics.load_5} / {metrics.load_15}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Uptime</p>
                  <p className="font-medium text-gray-800">{metrics.uptime}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Prozesse</p>
                  <p className="font-medium text-gray-800">{metrics.processes}</p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Keine Metriken verfügbar</p>
          )}
        </div>

        {/* Docker-Status */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Container className="w-5 h-5 text-hetzner-blue" />
            <h2 className="text-xl font-bold">Docker-Status</h2>
          </div>
          {containers ? (
            <div>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold">{containers.container_count}</p>
                  <p className="text-xs text-gray-500">Gesamt</p>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{containers.running_count}</p>
                  <p className="text-xs text-gray-500">Running</p>
                </div>
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <p className="text-2xl font-bold text-red-600">{containers.container_count - containers.running_count}</p>
                  <p className="text-xs text-gray-500">Stopped</p>
                </div>
              </div>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {containers.containers?.filter((c: any) => !c.running).map((c: any) => (
                  <div key={c.id} className="flex items-center justify-between text-sm px-2 py-1.5 bg-red-50 rounded">
                    <span className="font-medium truncate">{c.name}</span>
                    <span className="text-red-600 text-xs ml-2 whitespace-nowrap">{c.status}</span>
                  </div>
                ))}
                {containers.containers?.filter((c: any) => !c.running).length === 0 && (
                  <p className="text-sm text-green-600 text-center py-2">Alle Container laufen</p>
                )}
              </div>
              {connectedServer && (
                <div className="mt-3 pt-3 border-t text-xs text-gray-400">
                  {connectedServer.name} ({connectedServer.host}) - {connectedServer.docker_version}
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Keine Docker-Verbindung</p>
          )}
        </div>
      </div>

      {/* Bulk-Aktions-Toolbar */}
      {selectedServers.size > 0 && (
        <div className="card mb-4 !bg-blue-50 border-blue-200 flex items-center justify-between">
          <span className="text-sm font-medium text-blue-800">
            <CheckSquare size={16} className="inline mr-1" />
            {selectedServers.size} Server ausgewählt
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => bulkAction.mutate({ action: 'start', names: [...selectedServers] })}
              disabled={bulkAction.isPending}
              className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700"
            >
              <Play size={14} /> Starten
            </button>
            <button
              onClick={() => bulkAction.mutate({ action: 'stop', names: [...selectedServers] })}
              disabled={bulkAction.isPending}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700"
            >
              <Square size={14} /> Stoppen
            </button>
            <button
              onClick={() => bulkAction.mutate({ action: 'reboot', names: [...selectedServers] })}
              disabled={bulkAction.isPending}
              className="flex items-center gap-1 px-3 py-1.5 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700"
            >
              <RotateCw size={14} /> Reboot
            </button>
            <button
              onClick={() => bulkAction.mutate({ action: 'snapshot', names: [...selectedServers] })}
              disabled={bulkAction.isPending}
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              <Camera size={14} /> Snapshot
            </button>
            <button
              onClick={() => setSelectedServers(new Set())}
              className="px-3 py-1.5 text-gray-600 text-sm hover:text-gray-800"
            >
              Abbrechen
            </button>
          </div>
        </div>
      )}

      {/* Bulk-Ergebnis */}
      {bulkResult && (
        <div className={`card mb-4 text-sm ${bulkResult.error_count > 0 ? '!bg-yellow-50' : '!bg-green-50'}`}>
          <p className="font-medium">
            Bulk {bulkResult.action}: {bulkResult.success_count}/{bulkResult.total} erfolgreich
          </p>
          {bulkResult.results?.filter((r: any) => !r.success).map((r: any, i: number) => (
            <p key={i} className="text-red-600 mt-1">{r.server}: {r.error}</p>
          ))}
        </div>
      )}

      {/* Server-Liste mit Health Checks */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Server</h2>
          {(servers?.data?.servers?.length || 0) > 0 && (
            <button
              onClick={() => {
                const allNames = servers?.data?.servers?.map((s: any) => s.name) || []
                if (selectedServers.size === allNames.length) setSelectedServers(new Set())
                else setSelectedServers(new Set(allNames))
              }}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              {selectedServers.size === (servers?.data?.servers?.length || 0) ? 'Keine auswählen' : 'Alle auswählen'}
            </button>
          )}
        </div>
        <div className="space-y-2">
          {servers?.data?.servers?.map((server: any) => {
            const health = healthChecks?.data?.data?.checks?.find((c: any) => c.server === server.name)
            const statusColor = health?.status === 'healthy' ? 'bg-green-400' :
              health?.status === 'degraded' ? 'bg-yellow-400' :
              health?.status === 'down' ? 'bg-red-400' : 'bg-gray-300'
            const statusTitle = health?.status === 'healthy' ? `Erreichbar (${health.response_ms}ms)` :
              health?.status === 'degraded' ? 'Nur SSH erreichbar' :
              health?.status === 'down' ? 'Nicht erreichbar' :
              health?.status === 'off' ? 'Server aus' : 'Prüfe...'
            const isSelected = selectedServers.has(server.name)

            return (
              <div
                key={server.id}
                className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                  isSelected ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50 hover:bg-gray-100'
                }`}
                onClick={() => toggleServer(server.name)}
              >
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleServer(server.name)}
                    onClick={(e) => e.stopPropagation()}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600"
                  />
                  <div className="relative">
                    <Server className="w-5 h-5 text-gray-400" />
                    <div className={`absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full ${statusColor} border border-white`} title={statusTitle} />
                  </div>
                  <div>
                    <p className="font-medium">{server.name}</p>
                    <p className="text-sm text-gray-600">{server.server_type} - {server.location}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {health?.response_ms > 0 && (
                    <span className="text-xs text-gray-400">{health.response_ms}ms</span>
                  )}
                  <div className="text-right text-sm">
                    <p className="font-mono text-gray-700">{server.public_ipv4}</p>
                    <p className="text-xs text-gray-400">{server.public_ipv6?.replace('/64', '')}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    server.status === 'running' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {server.status}
                  </span>
                </div>
              </div>
            )
          }) || <p className="text-gray-500">Keine Server vorhanden</p>}
        </div>
      </div>
    </div>
  )
}
