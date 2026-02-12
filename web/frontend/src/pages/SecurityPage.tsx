import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ShieldCheck, ShieldX, AlertTriangle, Info, RefreshCw, Server, Shield, Bell, Cpu, MemoryStick, HardDrive, Save } from 'lucide-react'
import { securityApi, alertingApi, serversApi } from '../services/api'

function ScoreCircle({ score }: { score: number }) {
  const color = score >= 80 ? 'text-green-500' : score >= 50 ? 'text-yellow-500' : 'text-red-500'
  const bgColor = score >= 80 ? 'bg-green-50 border-green-200' : score >= 50 ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div className={`flex flex-col items-center justify-center p-6 rounded-xl border ${bgColor}`}>
      <svg width="140" height="140" className="transform -rotate-90">
        <circle cx="70" cy="70" r={radius} stroke="#e5e7eb" strokeWidth="8" fill="none" />
        <circle
          cx="70" cy="70" r={radius}
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={`${color} transition-all duration-1000`}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className={`text-4xl font-bold ${color}`}>{score}</span>
        <span className="text-xs text-gray-500">/ 100</span>
      </div>
    </div>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const styles: Record<string, string> = {
    critical: 'bg-red-100 text-red-700 border-red-200',
    warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    info: 'bg-blue-100 text-blue-700 border-blue-200',
  }
  const icons: Record<string, React.ReactNode> = {
    critical: <ShieldX size={14} />,
    warning: <AlertTriangle size={14} />,
    info: <Info size={14} />,
  }
  const labels: Record<string, string> = {
    critical: 'Kritisch',
    warning: 'Warnung',
    info: 'Info',
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium ${styles[severity]}`}>
      {icons[severity]} {labels[severity]}
    </span>
  )
}

function ThresholdSlider({ label, icon, value, onChange, color }: {
  label: string; icon: React.ReactNode; value: number; onChange: (v: number) => void; color: string
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="flex items-center gap-1 text-sm">{icon} {label}</span>
        <span className={`text-sm font-bold ${color}`}>{value}%</span>
      </div>
      <input
        type="range" min="10" max="100" value={value}
        onChange={e => onChange(parseInt(e.target.value))}
        className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-blue-600"
      />
    </div>
  )
}

function AlertingTab() {
  const queryClient = useQueryClient()
  const [globalCpu, setGlobalCpu] = useState(80)
  const [globalRam, setGlobalRam] = useState(90)
  const [globalDisk, setGlobalDisk] = useState(85)
  const [initialized, setInitialized] = useState(false)

  const { data: configData } = useQuery({
    queryKey: ['alerting-config'],
    queryFn: alertingApi.getConfig,
  })

  const { data: statusData, isLoading: statusLoading, refetch: refetchStatus } = useQuery({
    queryKey: ['alerting-status'],
    queryFn: alertingApi.getStatus,
    refetchInterval: 30000,
  })

  const { data: serversList } = useQuery({
    queryKey: ['servers'],
    queryFn: serversApi.list,
  })

  // Config laden
  if (configData?.data?.data && !initialized) {
    const g = configData.data.data.global || {}
    if (g.cpu) setGlobalCpu(g.cpu)
    if (g.ram) setGlobalRam(g.ram)
    if (g.disk) setGlobalDisk(g.disk)
    setInitialized(true)
  }

  const saveConfig = useMutation({
    mutationFn: () => alertingApi.updateConfig({
      global_thresholds: { cpu: globalCpu, ram: globalRam, disk: globalDisk },
      server_thresholds: {},
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerting-config'] })
      refetchStatus()
    },
  })

  const alerts = statusData?.data?.data?.alerts || []
  const servers = statusData?.data?.data?.servers || []

  return (
    <div>
      {/* Aktive Alerts */}
      {alerts.length > 0 && (
        <div className="mb-6">
          <h3 className="font-bold text-red-600 flex items-center gap-2 mb-3">
            <Bell size={18} /> {alerts.length} aktive Alerts
          </h3>
          <div className="space-y-2">
            {alerts.map((alert: any, i: number) => (
              <div key={i} className="card !bg-red-50 border-l-4 border-l-red-500 !p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{alert.server}</span>
                  <span className="text-sm">
                    {alert.type.toUpperCase()}: <span className="font-bold text-red-600">{alert.value}%</span>
                    {' '}(Schwelle: {alert.threshold}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {alerts.length === 0 && !statusLoading && (
        <div className="card !bg-green-50 border-green-200 mb-6 flex items-center gap-3">
          <ShieldCheck className="text-green-600" size={24} />
          <div>
            <p className="font-medium text-green-800">Keine Alerts aktiv</p>
            <p className="text-sm text-green-600">Alle Werte liegen unter den konfigurierten Schwellenwerten.</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Schwellenwerte konfigurieren */}
        <div className="card">
          <h3 className="font-bold mb-4 flex items-center gap-2">
            <AlertTriangle size={18} /> Globale Schwellenwerte
          </h3>
          <div className="space-y-4">
            <ThresholdSlider label="CPU" icon={<Cpu size={14} />} value={globalCpu} onChange={setGlobalCpu}
              color={globalCpu > 90 ? 'text-red-600' : globalCpu > 70 ? 'text-yellow-600' : 'text-green-600'} />
            <ThresholdSlider label="RAM" icon={<MemoryStick size={14} />} value={globalRam} onChange={setGlobalRam}
              color={globalRam > 90 ? 'text-red-600' : globalRam > 70 ? 'text-yellow-600' : 'text-green-600'} />
            <ThresholdSlider label="Disk" icon={<HardDrive size={14} />} value={globalDisk} onChange={setGlobalDisk}
              color={globalDisk > 90 ? 'text-red-600' : globalDisk > 70 ? 'text-yellow-600' : 'text-green-600'} />
          </div>
          <button
            onClick={() => saveConfig.mutate()}
            disabled={saveConfig.isPending}
            className="btn btn-primary mt-4 flex items-center gap-2 text-sm"
          >
            <Save size={14} /> {saveConfig.isPending ? 'Speichere...' : 'Speichern'}
          </button>
          {saveConfig.isSuccess && <p className="text-green-600 text-sm mt-2">Gespeichert!</p>}
        </div>

        {/* Server-Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold flex items-center gap-2">
              <Server size={18} /> Server-Status
            </h3>
            <button onClick={() => refetchStatus()} className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
              <RefreshCw size={12} /> Aktualisieren
            </button>
          </div>
          {statusLoading ? (
            <p className="text-gray-500 text-sm">Lade Status...</p>
          ) : servers.length > 0 ? (
            <div className="space-y-3">
              {servers.map((srv: any) => (
                <div key={srv.server} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{srv.server}</span>
                    {srv.alerts.length > 0 ? (
                      <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">{srv.alerts.length} Alerts</span>
                    ) : (
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">OK</span>
                    )}
                  </div>
                  {srv.metrics ? (
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div>
                        <span className="text-gray-500">CPU</span>
                        <span className={`ml-1 font-bold ${srv.metrics.cpu > globalCpu ? 'text-red-600' : 'text-gray-800'}`}>
                          {srv.metrics.cpu}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">RAM</span>
                        <span className={`ml-1 font-bold ${srv.metrics.ram > globalRam ? 'text-red-600' : 'text-gray-800'}`}>
                          {srv.metrics.ram}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Disk</span>
                        <span className={`ml-1 font-bold ${srv.metrics.disk > globalDisk ? 'text-red-600' : 'text-gray-800'}`}>
                          {srv.metrics.disk}%
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400">Keine Metriken verfügbar</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Keine laufenden Server gefunden</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default function SecurityPage() {
  const [activeTab, setActiveTab] = useState<'audit' | 'alerting'>('audit')

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['security-audit'],
    queryFn: securityApi.audit,
  })

  const audit = data?.data?.data

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Security</h1>
          <p className="text-gray-500 mt-1">Sicherheitsanalyse und Alerting</p>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'audit' ? 'bg-hetzner-blue text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <span className="flex items-center gap-2"><ShieldCheck size={16} /> Security Audit</span>
        </button>
        <button
          onClick={() => setActiveTab('alerting')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'alerting' ? 'bg-hetzner-blue text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <span className="flex items-center gap-2"><AlertTriangle size={16} /> Alerting</span>
        </button>
      </div>

      {activeTab === 'audit' && (
        <>
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">Analyse läuft...</div>
          ) : audit ? (
            <div>
              {/* Score + Summary */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="relative flex items-center justify-center">
                  <ScoreCircle score={audit.score} />
                </div>
                <div className="card flex flex-col justify-center">
                  <div className="flex items-center gap-2 text-red-600 mb-1">
                    <ShieldX size={20} />
                    <span className="text-2xl font-bold">{audit.summary.critical}</span>
                  </div>
                  <p className="text-sm text-gray-600">Kritische Probleme</p>
                </div>
                <div className="card flex flex-col justify-center">
                  <div className="flex items-center gap-2 text-yellow-600 mb-1">
                    <AlertTriangle size={20} />
                    <span className="text-2xl font-bold">{audit.summary.warning}</span>
                  </div>
                  <p className="text-sm text-gray-600">Warnungen</p>
                </div>
                <div className="card flex flex-col justify-center">
                  <div className="flex items-center gap-2 text-blue-600 mb-1">
                    <Info size={20} />
                    <span className="text-2xl font-bold">{audit.summary.info}</span>
                  </div>
                  <p className="text-sm text-gray-600">Hinweise</p>
                </div>
              </div>

              {/* Stats */}
              <div className="flex gap-4 mb-6 text-sm text-gray-600">
                <span className="flex items-center gap-1"><Server size={14} /> {audit.protected_servers}/{audit.total_servers} Server geschützt</span>
                <span className="flex items-center gap-1"><Shield size={14} /> {audit.total_firewalls} Firewalls</span>
                <button
                  onClick={() => refetch()}
                  disabled={isFetching}
                  className="flex items-center gap-1 text-blue-600 hover:text-blue-800 ml-auto"
                >
                  <RefreshCw size={14} className={isFetching ? 'animate-spin' : ''} /> Erneut prüfen
                </button>
              </div>

              {/* Findings */}
              {audit.findings.length === 0 ? (
                <div className="card text-center py-8">
                  <ShieldCheck className="w-16 h-16 text-green-500 mx-auto mb-3" />
                  <h3 className="text-lg font-bold text-green-700">Keine Probleme gefunden</h3>
                  <p className="text-gray-500">Deine Infrastruktur sieht sicher aus!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {audit.findings.map((finding: any, i: number) => (
                    <div key={i} className={`card border-l-4 ${
                      finding.severity === 'critical' ? 'border-l-red-500' :
                      finding.severity === 'warning' ? 'border-l-yellow-500' : 'border-l-blue-500'
                    }`}>
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <SeverityBadge severity={finding.severity} />
                            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">{finding.category}</span>
                            <span className="text-xs text-gray-400 font-mono">{finding.resource}</span>
                          </div>
                          <h3 className="font-medium">{finding.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{finding.description}</p>
                          <p className="text-sm text-green-700 mt-2 bg-green-50 rounded px-3 py-1.5">
                            Empfehlung: {finding.recommendation}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-red-500">Fehler beim Laden der Audit-Daten</div>
          )}
        </>
      )}

      {activeTab === 'alerting' && <AlertingTab />}
    </div>
  )
}
