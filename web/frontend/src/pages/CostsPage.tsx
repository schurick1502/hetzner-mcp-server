import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { DollarSign, Server, HardDrive, Camera, Globe, Scale, ArrowUpDown, Cpu, MemoryStick } from 'lucide-react'
import { costsApi } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const CATEGORY_COLORS: Record<string, string> = {
  servers: '#3b82f6',
  volumes: '#8b5cf6',
  snapshots: '#f59e0b',
  floating_ips: '#10b981',
  primary_ips: '#06b6d4',
  load_balancers: '#ec4899',
}

const CATEGORY_LABELS: Record<string, string> = {
  servers: 'Server',
  volumes: 'Volumes',
  snapshots: 'Snapshots',
  floating_ips: 'Floating IPs',
  primary_ips: 'Primary IPs',
  load_balancers: 'Load Balancer',
}

type SortKey = 'price_monthly' | 'cores' | 'memory' | 'disk'

export default function CostsPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'compare'>('overview')
  const [sortKey, setSortKey] = useState<SortKey>('price_monthly')
  const [sortAsc, setSortAsc] = useState(true)
  const [cpuFilter, setCpuFilter] = useState<string>('all')
  const [archFilter, setArchFilter] = useState<string>('all')

  const { data, isLoading } = useQuery({
    queryKey: ['costs'],
    queryFn: costsApi.getCosts,
  })

  if (isLoading) return <div className="text-center py-8 text-gray-500">Berechne Kosten...</div>

  const costs = data?.data?.data
  if (!costs) return <div className="text-center py-8 text-red-500">Fehler beim Laden</div>

  const breakdown = costs.breakdown
  const chartData = Object.entries(breakdown)
    .filter(([_, v]: [string, any]) => v.total > 0)
    .map(([key, v]: [string, any]) => ({
      name: CATEGORY_LABELS[key] || key,
      kosten: v.total,
      color: CATEGORY_COLORS[key] || '#6b7280',
    }))

  // Server-Typen für Vergleich
  let serverTypes = [...(costs.server_types || [])]
  if (cpuFilter !== 'all') serverTypes = serverTypes.filter(t => t.cpu_type === cpuFilter)
  if (archFilter !== 'all') serverTypes = serverTypes.filter(t => t.architecture === archFilter)
  serverTypes.sort((a: any, b: any) => sortAsc ? a[sortKey] - b[sortKey] : b[sortKey] - a[sortKey])

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc)
    else { setSortKey(key); setSortAsc(true) }
  }

  const SortHeader = ({ label, field }: { label: string; field: SortKey }) => (
    <th
      className="py-2 px-3 cursor-pointer hover:bg-gray-100 select-none"
      onClick={() => handleSort(field)}
    >
      <span className="flex items-center gap-1">
        {label}
        {sortKey === field && <ArrowUpDown size={12} className="text-blue-500" />}
      </span>
    </th>
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Kosten</h1>
          <p className="text-gray-500 mt-1">Geschätzte monatliche Kosten und Server-Vergleich</p>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'overview' ? 'bg-hetzner-blue text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <span className="flex items-center gap-2"><DollarSign size={16} /> Kostenübersicht</span>
        </button>
        <button
          onClick={() => setActiveTab('compare')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'compare' ? 'bg-hetzner-blue text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <span className="flex items-center gap-2"><Scale size={16} /> Server-Vergleich</span>
        </button>
      </div>

      {activeTab === 'overview' && (
        <div>
          {/* Gesamtkosten */}
          <div className="card mb-6 bg-gradient-to-r from-blue-50 to-purple-50">
            <div className="flex items-center gap-3">
              <DollarSign className="w-10 h-10 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Geschätzte monatliche Kosten</p>
                <p className="text-3xl font-bold text-gray-900">{costs.total_monthly.toFixed(2)} &euro;</p>
              </div>
            </div>
          </div>

          {/* Chart */}
          {chartData.length > 0 && (
            <div className="card mb-6">
              <h3 className="font-bold mb-4">Aufschlüsselung nach Kategorie</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={chartData} layout="vertical" margin={{ left: 80 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tickFormatter={(v) => `${v}€`} />
                  <YAxis type="category" dataKey="name" width={80} />
                  <Tooltip formatter={(value: any) => [`${Number(value).toFixed(2)} €`, 'Kosten']} />
                  <Bar dataKey="kosten" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Detail-Tabellen */}
          {Object.entries(breakdown).map(([category, data]: [string, any]) => {
            if (data.items.length === 0) return null
            const Icon = category === 'servers' ? Server : category === 'volumes' ? HardDrive :
              category === 'snapshots' ? Camera : Globe
            return (
              <div key={category} className="card mb-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-bold flex items-center gap-2">
                    <Icon size={18} style={{ color: CATEGORY_COLORS[category] }} />
                    {CATEGORY_LABELS[category]}
                  </h3>
                  <span className="font-bold text-gray-700">{data.total.toFixed(2)} &euro;/Monat</span>
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-gray-500">
                      <th className="py-1 px-2">Name</th>
                      <th className="py-1 px-2">Details</th>
                      <th className="py-1 px-2 text-right">Kosten/Monat</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((item: any, i: number) => (
                      <tr key={i} className="border-b last:border-0 hover:bg-gray-50">
                        <td className="py-1.5 px-2 font-medium">{item.name || item.ip}</td>
                        <td className="py-1.5 px-2 text-gray-500">
                          {item.type && <span>{item.type}</span>}
                          {item.size_gb && <span>{item.size_gb} GB</span>}
                          {item.server && <span className="ml-2 text-xs bg-gray-100 px-1.5 py-0.5 rounded">{item.server}</span>}
                          {item.location && <span className="ml-2 text-xs bg-gray-100 px-1.5 py-0.5 rounded">{item.location}</span>}
                        </td>
                        <td className="py-1.5 px-2 text-right font-mono">{item.monthly.toFixed(2)} &euro;</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          })}
        </div>
      )}

      {activeTab === 'compare' && (
        <div>
          {/* Filter */}
          <div className="flex gap-4 mb-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">CPU-Typ</label>
              <select value={cpuFilter} onChange={e => setCpuFilter(e.target.value)} className="border rounded px-3 py-1.5 text-sm">
                <option value="all">Alle</option>
                <option value="shared">Shared</option>
                <option value="dedicated">Dedicated</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Architektur</label>
              <select value={archFilter} onChange={e => setArchFilter(e.target.value)} className="border rounded px-3 py-1.5 text-sm">
                <option value="all">Alle</option>
                <option value="x86">x86</option>
                <option value="arm">ARM</option>
              </select>
            </div>
          </div>

          {/* Vergleichstabelle */}
          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="py-2 px-3">Typ</th>
                  <SortHeader label="Cores" field="cores" />
                  <SortHeader label="RAM (GB)" field="memory" />
                  <SortHeader label="Disk (GB)" field="disk" />
                  <th className="py-2 px-3">Storage</th>
                  <th className="py-2 px-3">CPU</th>
                  <th className="py-2 px-3">Arch</th>
                  <th className="py-2 px-3">Traffic</th>
                  <th className="py-2 px-3 text-right">Preis/h</th>
                  <SortHeader label="Preis/Monat" field="price_monthly" />
                </tr>
              </thead>
              <tbody>
                {serverTypes.map((st: any) => (
                  <tr key={st.name} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3 font-bold">{st.name}</td>
                    <td className="py-2 px-3">
                      <span className="flex items-center gap-1"><Cpu size={12} /> {st.cores}</span>
                    </td>
                    <td className="py-2 px-3">
                      <span className="flex items-center gap-1"><MemoryStick size={12} /> {st.memory}</span>
                    </td>
                    <td className="py-2 px-3">{st.disk}</td>
                    <td className="py-2 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-xs ${st.storage_type === 'local' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                        {st.storage_type}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-xs ${st.cpu_type === 'dedicated' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'}`}>
                        {st.cpu_type}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-xs">{st.architecture}</td>
                    <td className="py-2 px-3 text-xs text-gray-500">{st.included_traffic ? `${Math.round(st.included_traffic / 1024 / 1024 / 1024 / 1024)} TB` : '-'}</td>
                    <td className="py-2 px-3 text-right font-mono text-xs text-gray-500">{st.price_hourly.toFixed(4)} &euro;</td>
                    <td className="py-2 px-3 text-right font-mono font-bold">{st.price_monthly.toFixed(2)} &euro;</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
