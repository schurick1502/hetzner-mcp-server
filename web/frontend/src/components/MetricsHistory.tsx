import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, Cpu, HardDrive, Network, Clock } from 'lucide-react'
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, LineChart, Line, Legend
} from 'recharts'
import { format } from 'date-fns'
import { metricsApi, serversApi } from '../services/api'

type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d'
type MetricTab = 'cpu' | 'disk' | 'network'

const TIME_RANGES: { key: TimeRange; label: string; hours: number }[] = [
  { key: '1h', label: '1 Stunde', hours: 1 },
  { key: '6h', label: '6 Stunden', hours: 6 },
  { key: '24h', label: '24 Stunden', hours: 24 },
  { key: '7d', label: '7 Tage', hours: 168 },
  { key: '30d', label: '30 Tage', hours: 720 },
]

function getTimeParams(range: TimeRange): { start: string; end: string } {
  const now = new Date()
  const hours = TIME_RANGES.find(r => r.key === range)!.hours
  const start = new Date(now.getTime() - hours * 60 * 60 * 1000)
  return {
    start: start.toISOString(),
    end: now.toISOString(),
  }
}

function tsToDate(ts: number | string): Date {
  // Timestamps from API are Unix epoch in seconds
  const num = typeof ts === 'string' ? parseFloat(ts) : ts
  if (!num || isNaN(num)) return new Date()
  // If the timestamp is in seconds (< 10 billion), convert to ms
  return new Date(num < 1e12 ? num * 1000 : num)
}

function formatTimestamp(ts: number | string, range: TimeRange): string {
  try {
    const date = tsToDate(ts)
    if (isNaN(date.getTime())) return ''
    if (range === '7d' || range === '30d') {
      return format(date, 'dd.MM HH:mm')
    }
    return format(date, 'HH:mm')
  } catch {
    return ''
  }
}

function safeFormatDate(ts: number | string): string {
  try {
    const date = tsToDate(ts)
    if (isNaN(date.getTime())) return String(ts)
    return format(date, 'dd.MM.yyyy HH:mm:ss')
  } catch {
    return String(ts)
  }
}

function formatValue(value: string | number): number {
  return typeof value === 'string' ? parseFloat(value) : value
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i]
}

interface TimeSeriesData {
  [key: string]: Array<{ timestamp: string; value: string }>
}

function processTimeSeries(timeSeries: TimeSeriesData, step: number = 1): any[] {
  const allTimestamps = new Set<number>()

  for (const key of Object.keys(timeSeries)) {
    for (const point of timeSeries[key]) {
      allTimestamps.add(parseFloat(point.timestamp))
    }
  }

  const sorted = Array.from(allTimestamps).sort((a, b) => a - b)

  // Downsample for large datasets
  const sampled = step > 1 ? sorted.filter((_, i) => i % step === 0) : sorted

  // Build lookup maps for O(1) access
  const lookups: Record<string, Map<number, number>> = {}
  for (const key of Object.keys(timeSeries)) {
    const map = new Map<number, number>()
    for (const point of timeSeries[key]) {
      map.set(parseFloat(point.timestamp), formatValue(point.value))
    }
    lookups[key] = map
  }

  return sampled.map(ts => {
    const row: any = { time: ts }
    for (const key of Object.keys(timeSeries)) {
      const val = lookups[key].get(ts)
      if (val !== undefined) {
        row[key] = val
      }
    }
    return row
  })
}

function CpuChart({ data, range }: { data: any[]; range: TimeRange }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="font-semibold mb-4 flex items-center gap-2">
        <Cpu size={18} className="text-red-500" /> CPU-Auslastung
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="time"
            tickFormatter={(ts) => formatTimestamp(ts, range)}
            tick={{ fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis domain={[0, 'auto']} tick={{ fontSize: 10 }} tickFormatter={(v) => `${v.toFixed(0)}%`} />
          <Tooltip
            labelFormatter={(ts) => safeFormatDate(ts)}
            formatter={(value: number) => [`${value.toFixed(1)}%`, 'CPU']}
          />
          <Area type="monotone" dataKey="cpu" stroke="#D50C2D" fill="#D50C2D" fillOpacity={0.2} name="CPU" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

function DiskChart({ data, range }: { data: any[]; range: TimeRange }) {
  const hasIops = data.some(d => d['disk.0.iops.read'] !== undefined)
  const hasBandwidth = data.some(d => d['disk.0.bandwidth.read'] !== undefined)

  return (
    <div className="space-y-6">
      {hasIops && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <HardDrive size={18} className="text-green-500" /> Disk IOPS
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tickFormatter={(ts) => formatTimestamp(ts, range)}
                tick={{ fontSize: 10 }}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}`} />
              <Tooltip
                labelFormatter={(ts) => safeFormatDate(ts)}
                formatter={(value: number, name: string) => [
                  value.toFixed(1),
                  name.includes('read') ? 'Read IOPS' : 'Write IOPS'
                ]}
              />
              <Legend />
              <Line type="monotone" dataKey="disk.0.iops.read" stroke="#22c55e" name="Read IOPS" dot={false} />
              <Line type="monotone" dataKey="disk.0.iops.write" stroke="#f97316" name="Write IOPS" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {hasBandwidth && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <HardDrive size={18} className="text-blue-500" /> Disk Bandwidth
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tickFormatter={(ts) => formatTimestamp(ts, range)}
                tick={{ fontSize: 10 }}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => formatBytes(v)} />
              <Tooltip
                labelFormatter={(ts) => safeFormatDate(ts)}
                formatter={(value: number, name: string) => [
                  formatBytes(value) + '/s',
                  name.includes('read') ? 'Read' : 'Write'
                ]}
              />
              <Legend />
              <Area type="monotone" dataKey="disk.0.bandwidth.read" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} name="Read" dot={false} />
              <Area type="monotone" dataKey="disk.0.bandwidth.write" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.2} name="Write" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {!hasIops && !hasBandwidth && (
        <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
          Keine Disk-Metriken verfügbar
        </div>
      )}
    </div>
  )
}

function NetworkChart({ data, range }: { data: any[]; range: TimeRange }) {
  const hasData = data.some(d =>
    d['network.0.bandwidth.in'] !== undefined || d['network.0.bandwidth.out'] !== undefined
  )

  if (!hasData) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
        Keine Netzwerk-Metriken verfügbar
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="font-semibold mb-4 flex items-center gap-2">
        <Network size={18} className="text-blue-500" /> Netzwerk-Bandbreite
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="time"
            tickFormatter={(ts) => formatTimestamp(ts, range)}
            tick={{ fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => formatBytes(v)} />
          <Tooltip
            labelFormatter={(ts) => safeFormatDate(ts)}
            formatter={(value: number, name: string) => [
              formatBytes(value) + '/s',
              name.includes('in') ? 'Eingehend' : 'Ausgehend'
            ]}
          />
          <Legend />
          <Area type="monotone" dataKey="network.0.bandwidth.in" stroke="#22c55e" fill="#22c55e" fillOpacity={0.2} name="Eingehend" dot={false} />
          <Area type="monotone" dataKey="network.0.bandwidth.out" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} name="Ausgehend" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function MetricsHistory() {
  const [selectedServer, setSelectedServer] = useState<string>('')
  const [timeRange, setTimeRange] = useState<TimeRange>('1h')
  const [metricTab, setMetricTab] = useState<MetricTab>('cpu')

  const { data: serversData, isLoading: serversLoading } = useQuery({
    queryKey: ['servers'],
    queryFn: serversApi.list,
  })

  const servers = serversData?.data?.servers || []

  const serverOptions = servers.map((s: any) => ({
    value: `${s.__account || ''}|${s.name}`,
    name: s.name,
    account: s.__account || null,
  }))

  const activeServerValue = selectedServer || (serverOptions.length > 0 ? serverOptions[0].value : '')
  const activeServerOption = serverOptions.find((o: any) => o.value === activeServerValue)
  const activeServer = activeServerOption?.name || ''
  const activeAccount = activeServerOption?.account || undefined

  const metricType = metricTab === 'cpu' ? 'cpu' : metricTab === 'disk' ? 'disk' : 'network'
  const { start, end } = getTimeParams(timeRange)

  const { data: metricsData, isLoading: metricsLoading, isError } = useQuery({
    queryKey: ['hetzner-metrics-history', activeServer, activeAccount, metricType, timeRange],
    queryFn: () => metricsApi.getServerMetrics(activeServer, metricType, start, end, activeAccount),
    enabled: !!activeServer,
    refetchInterval: timeRange === '1h' ? 60000 : false,
  })

  const timeSeries: TimeSeriesData = metricsData?.data?.metrics?.time_series || {}

  // Downsample for larger ranges
  const step = timeRange === '30d' ? 10 : timeRange === '7d' ? 5 : 1
  const chartData = processTimeSeries(timeSeries, step)

  // CPU values from Hetzner API are already in percent (0-100+)
  const processedData = chartData

  if (serversLoading) {
    return <div className="text-center py-8 text-gray-500">Lade Server...</div>
  }

  if (servers.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <p className="text-yellow-800">Keine Server gefunden</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          {/* Server Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Server:</label>
            <select
              value={activeServerValue}
              onChange={(e) => setSelectedServer(e.target.value)}
              className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-hetzner-blue"
            >
              {serverOptions.map((s: any) => (
                <option key={s.value} value={s.value}>
                  {s.name}{s.account ? ` (${String(s.account).toUpperCase()})` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Time Range */}
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-500" />
            <div className="flex gap-1">
              {TIME_RANGES.map(r => (
                <button
                  key={r.key}
                  onClick={() => setTimeRange(r.key)}
                  className={`px-3 py-1.5 rounded text-sm transition-colors ${
                    timeRange === r.key
                      ? 'bg-hetzner-blue text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Metric Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setMetricTab('cpu')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            metricTab === 'cpu' ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <Cpu size={16} /> CPU
        </button>
        <button
          onClick={() => setMetricTab('disk')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            metricTab === 'disk' ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <HardDrive size={16} /> Disk I/O
        </button>
        <button
          onClick={() => setMetricTab('network')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            metricTab === 'network' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <Network size={16} /> Netzwerk
        </button>
      </div>

      {/* Charts */}
      {metricsLoading ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <BarChart3 className="mx-auto text-gray-400 animate-pulse mb-4" size={48} />
          <p className="text-gray-500">Lade Metriken...</p>
        </div>
      ) : isError ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Fehler beim Laden der Metriken. Server ist möglicherweise nicht erreichbar.</p>
        </div>
      ) : chartData.length === 0 ? (
        <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
          Keine Metriken für den gewählten Zeitraum verfügbar
        </div>
      ) : (
        <>
          {metricTab === 'cpu' && <CpuChart data={processedData} range={timeRange} />}
          {metricTab === 'disk' && <DiskChart data={processedData} range={timeRange} />}
          {metricTab === 'network' && <NetworkChart data={processedData} range={timeRange} />}

          <div className="text-xs text-gray-400 text-right">
            {chartData.length} Datenpunkte | Zeitraum: {TIME_RANGES.find(r => r.key === timeRange)?.label}
          </div>
        </>
      )}
    </div>
  )
}
