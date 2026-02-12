import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Network, ChevronDown, ChevronRight, Plus, Trash2, Server, Globe } from 'lucide-react'
import { networksApi } from '../services/api'

function AddSubnetForm({ networkName, onClose }: { networkName: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [ipRange, setIpRange] = useState('')
  const [zone, setZone] = useState('eu-central')

  const addSubnet = useMutation({
    mutationFn: () => networksApi.addSubnet(networkName, { ip_range: ipRange, network_zone: zone, subnet_type: 'cloud' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['networks'] })
      onClose()
    },
  })

  return (
    <form onSubmit={(e) => { e.preventDefault(); addSubnet.mutate() }} className="border rounded-lg p-4 bg-blue-50 mt-3">
      <h4 className="font-medium mb-3">Neues Subnet</h4>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">IP-Range (CIDR)</label>
          <input value={ipRange} onChange={e => setIpRange(e.target.value)} placeholder="10.0.1.0/24" className="w-full border rounded px-2 py-1.5 text-sm" required />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Zone</label>
          <select value={zone} onChange={e => setZone(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm">
            <option value="eu-central">eu-central</option>
            <option value="us-east">us-east</option>
            <option value="us-west">us-west</option>
            <option value="ap-southeast">ap-southeast</option>
          </select>
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <button type="submit" disabled={addSubnet.isPending} className="btn btn-primary text-sm px-3 py-1.5">
          {addSubnet.isPending ? 'Speichere...' : 'Hinzufügen'}
        </button>
        <button type="button" onClick={onClose} className="text-sm px-3 py-1.5 text-gray-600">Abbrechen</button>
      </div>
      {addSubnet.isError && <p className="text-red-600 text-sm mt-2">Fehler beim Hinzufügen</p>}
    </form>
  )
}

function NetworkCard({ network }: { network: any }) {
  const [expanded, setExpanded] = useState(false)
  const [showAddSubnet, setShowAddSubnet] = useState(false)
  const queryClient = useQueryClient()

  const deleteNet = useMutation({
    mutationFn: () => networksApi.delete(network.name, true),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['networks'] }),
  })

  const deleteSubnet = useMutation({
    mutationFn: (ipRange: string) => networksApi.deleteSubnet(network.name, ipRange),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['networks'] }),
  })

  return (
    <div className="card">
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3">
          <Network className="w-6 h-6 text-orange-500" />
          <div>
            <h3 className="font-bold">{network.name}</h3>
            <p className="text-sm text-gray-600 font-mono">{network.ip_range}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-2 text-xs">
            <span className="px-2 py-1 bg-gray-100 rounded">{network.subnets?.length || 0} Subnets</span>
            <span className="px-2 py-1 bg-gray-100 rounded">{network.servers?.length || 0} Server</span>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation()
              if (confirm(`Netzwerk "${network.name}" wirklich löschen?`)) deleteNet.mutate()
            }}
            className="p-2 hover:bg-red-100 text-red-600 rounded"
            title="Löschen"
          >
            <Trash2 size={16} />
          </button>
          {expanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        </div>
      </div>

      {expanded && (
        <div className="mt-4 border-t pt-4">
          {/* Subnets */}
          <h4 className="text-sm font-medium mb-2 flex items-center gap-1"><Globe size={14} /> Subnets</h4>
          {network.subnets?.length > 0 ? (
            <table className="w-full text-sm mb-4">
              <thead>
                <tr className="border-b text-left">
                  <th className="py-2 px-2">IP-Range</th>
                  <th className="py-2 px-2">Typ</th>
                  <th className="py-2 px-2">Zone</th>
                  <th className="py-2 px-2">Gateway</th>
                  <th className="py-2 px-2 w-10"></th>
                </tr>
              </thead>
              <tbody>
                {network.subnets.map((subnet: any, i: number) => (
                  <tr key={i} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-2 font-mono">{subnet.ip_range}</td>
                    <td className="py-2 px-2">{subnet.type}</td>
                    <td className="py-2 px-2">{subnet.network_zone}</td>
                    <td className="py-2 px-2 font-mono">{subnet.gateway}</td>
                    <td className="py-2 px-2">
                      <button
                        onClick={() => deleteSubnet.mutate(subnet.ip_range)}
                        disabled={deleteSubnet.isPending}
                        className="p-1 hover:bg-red-100 text-red-500 rounded"
                        title="Subnet löschen"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-500 text-sm mb-4">Keine Subnets</p>
          )}

          {showAddSubnet ? (
            <AddSubnetForm networkName={network.name} onClose={() => setShowAddSubnet(false)} />
          ) : (
            <button onClick={() => setShowAddSubnet(true)} className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 mb-4">
              <Plus size={16} /> Subnet hinzufügen
            </button>
          )}

          {/* Server */}
          {network.servers?.length > 0 && (
            <div className="pt-3 border-t">
              <h4 className="text-sm font-medium mb-2 flex items-center gap-1"><Server size={14} /> Verbundene Server</h4>
              <div className="flex gap-2 flex-wrap">
                {network.servers.map((srv: string, i: number) => (
                  <span key={i} className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-xs">
                    <Server size={12} /> {srv}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function NetworksPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newIpRange, setNewIpRange] = useState('10.0.0.0/16')
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['networks'],
    queryFn: networksApi.list,
  })

  const createNet = useMutation({
    mutationFn: () => networksApi.create({ name: newName, ip_range: newIpRange }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['networks'] })
      setNewName('')
      setNewIpRange('10.0.0.0/16')
      setShowCreate(false)
    },
  })

  if (isLoading) return <div className="text-center py-8 text-gray-500">Laden...</div>

  const networks = data?.data?.networks || []

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Networks</h1>
        <button onClick={() => setShowCreate(!showCreate)} className="btn btn-primary flex items-center gap-2">
          <Plus size={20} /> Neues Netzwerk
        </button>
      </div>

      {showCreate && (
        <div className="card mb-6">
          <h3 className="font-bold mb-3">Neues Netzwerk erstellen</h3>
          <form onSubmit={(e) => { e.preventDefault(); createNet.mutate() }} className="flex gap-3">
            <input
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="Netzwerk-Name"
              className="flex-1 border rounded px-3 py-2"
              required
            />
            <input
              value={newIpRange}
              onChange={e => setNewIpRange(e.target.value)}
              placeholder="10.0.0.0/16"
              className="w-48 border rounded px-3 py-2 font-mono"
              required
            />
            <button type="submit" disabled={createNet.isPending} className="btn btn-primary">
              {createNet.isPending ? 'Erstelle...' : 'Erstellen'}
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-gray-600">Abbrechen</button>
          </form>
          {createNet.isError && <p className="text-red-600 text-sm mt-2">Fehler beim Erstellen</p>}
        </div>
      )}

      <div className="grid gap-4">
        {networks.map((net: any) => (
          <NetworkCard key={net.id} network={net} />
        ))}
        {networks.length === 0 && (
          <p className="text-center text-gray-500 py-8">Keine Netzwerke vorhanden</p>
        )}
      </div>
    </div>
  )
}
