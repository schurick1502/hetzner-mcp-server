import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Scale, ChevronDown, ChevronRight, Plus, Trash2, Server, Globe, Activity, Settings2 } from 'lucide-react'
import { loadBalancersApi } from '../services/api'

function AddServiceForm({ lbId, onClose }: { lbId: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [protocol, setProtocol] = useState('tcp')
  const [listenPort, setListenPort] = useState('80')
  const [destPort, setDestPort] = useState('80')
  const [proxyprotocol, setProxyprotocol] = useState(false)
  const [hcProtocol, setHcProtocol] = useState('tcp')
  const [hcInterval, setHcInterval] = useState('15')
  const [hcTimeout, setHcTimeout] = useState('10')
  const [hcRetries, setHcRetries] = useState('3')

  const addService = useMutation({
    mutationFn: (data: any) => loadBalancersApi.addService(lbId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loadBalancers'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    addService.mutate({
      protocol,
      listen_port: parseInt(listenPort),
      destination_port: parseInt(destPort),
      proxyprotocol,
      health_check_protocol: hcProtocol,
      health_check_interval: parseInt(hcInterval),
      health_check_timeout: parseInt(hcTimeout),
      health_check_retries: parseInt(hcRetries),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="border rounded-lg p-4 bg-blue-50 mt-3">
      <h4 className="font-medium mb-3">Neuer Service</h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Protokoll</label>
          <select value={protocol} onChange={e => setProtocol(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm">
            <option value="tcp">TCP</option>
            <option value="http">HTTP</option>
            <option value="https">HTTPS</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Listen-Port</label>
          <input type="number" value={listenPort} onChange={e => setListenPort(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm" required />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Ziel-Port</label>
          <input type="number" value={destPort} onChange={e => setDestPort(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm" required />
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={proxyprotocol} onChange={e => setProxyprotocol(e.target.checked)} />
            Proxy Protocol
          </label>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Health-Check Protokoll</label>
          <select value={hcProtocol} onChange={e => setHcProtocol(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm">
            <option value="tcp">TCP</option>
            <option value="http">HTTP</option>
            <option value="https">HTTPS</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Intervall (s)</label>
          <input type="number" value={hcInterval} onChange={e => setHcInterval(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Timeout (s)</label>
          <input type="number" value={hcTimeout} onChange={e => setHcTimeout(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Retries</label>
          <input type="number" value={hcRetries} onChange={e => setHcRetries(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm" />
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <button type="submit" disabled={addService.isPending} className="btn btn-primary text-sm px-3 py-1.5">
          {addService.isPending ? 'Speichere...' : 'Hinzufügen'}
        </button>
        <button type="button" onClick={onClose} className="text-sm px-3 py-1.5 text-gray-600 hover:text-gray-800">Abbrechen</button>
      </div>
      {addService.isError && <p className="text-red-600 text-sm mt-2">Fehler beim Hinzufügen des Service</p>}
    </form>
  )
}

function AddTargetForm({ lbId, onClose }: { lbId: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [targetType, setTargetType] = useState('server')
  const [server, setServer] = useState('')
  const [labelSelector, setLabelSelector] = useState('')
  const [ip, setIp] = useState('')
  const [usePrivateIp, setUsePrivateIp] = useState(false)

  const addTarget = useMutation({
    mutationFn: (data: any) => loadBalancersApi.addTarget(lbId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loadBalancers'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    addTarget.mutate({
      target_type: targetType,
      server: targetType === 'server' ? server : undefined,
      label_selector: targetType === 'label_selector' ? labelSelector : undefined,
      ip: targetType === 'ip' ? ip : undefined,
      use_private_ip: usePrivateIp,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="border rounded-lg p-4 bg-green-50 mt-3">
      <h4 className="font-medium mb-3">Neues Target</h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Target-Typ</label>
          <select value={targetType} onChange={e => setTargetType(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm">
            <option value="server">Server</option>
            <option value="label_selector">Label Selector</option>
            <option value="ip">IP-Adresse</option>
          </select>
        </div>
        {targetType === 'server' && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Server (Name/ID)</label>
            <input value={server} onChange={e => setServer(e.target.value)} placeholder="server-name" className="w-full border rounded px-2 py-1.5 text-sm" required />
          </div>
        )}
        {targetType === 'label_selector' && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Label Selector</label>
            <input value={labelSelector} onChange={e => setLabelSelector(e.target.value)} placeholder="env=prod" className="w-full border rounded px-2 py-1.5 text-sm" required />
          </div>
        )}
        {targetType === 'ip' && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">IP-Adresse</label>
            <input value={ip} onChange={e => setIp(e.target.value)} placeholder="10.0.0.1" className="w-full border rounded px-2 py-1.5 text-sm" required />
          </div>
        )}
        <div className="flex items-end">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={usePrivateIp} onChange={e => setUsePrivateIp(e.target.checked)} />
            Private IP nutzen
          </label>
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <button type="submit" disabled={addTarget.isPending} className="btn btn-primary text-sm px-3 py-1.5">
          {addTarget.isPending ? 'Speichere...' : 'Hinzufügen'}
        </button>
        <button type="button" onClick={onClose} className="text-sm px-3 py-1.5 text-gray-600 hover:text-gray-800">Abbrechen</button>
      </div>
      {addTarget.isError && <p className="text-red-600 text-sm mt-2">Fehler beim Hinzufügen des Targets</p>}
    </form>
  )
}

function LoadBalancerCard({ lb }: { lb: any }) {
  const [expanded, setExpanded] = useState(false)
  const [showAddService, setShowAddService] = useState(false)
  const [showAddTarget, setShowAddTarget] = useState(false)
  const queryClient = useQueryClient()

  const deleteLb = useMutation({
    mutationFn: () => loadBalancersApi.delete(lb.name, true),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['loadBalancers'] }),
  })

  const deleteService = useMutation({
    mutationFn: (listenPort: number) => loadBalancersApi.deleteService(lb.name, listenPort),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['loadBalancers'] }),
  })

  const removeTarget = useMutation({
    mutationFn: (data: any) => loadBalancersApi.removeTarget(lb.name, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['loadBalancers'] }),
  })

  const changeAlgorithm = useMutation({
    mutationFn: (algorithmType: string) => loadBalancersApi.changeAlgorithm(lb.name, { algorithm_type: algorithmType }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['loadBalancers'] }),
  })

  const services = lb.services || []
  const targets = lb.targets || []

  return (
    <div className="card">
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3">
          <Scale className="w-6 h-6 text-pink-600" />
          <div>
            <h3 className="font-bold">{lb.name}</h3>
            <p className="text-sm text-gray-600">
              {lb.load_balancer_type || 'lb11'} - {lb.location}
              <span className="ml-2 text-xs bg-gray-100 px-1.5 py-0.5 rounded">{lb.algorithm || 'round_robin'}</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {lb.public_ip && (
            <span className="text-xs font-mono text-gray-500 mr-2">{lb.public_ip}</span>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation()
              if (confirm(`Load Balancer "${lb.name}" wirklich löschen?`)) deleteLb.mutate()
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
        <div className="mt-4 border-t pt-4 space-y-6">
          {/* Algorithm */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Settings2 size={16} className="text-gray-500" />
              <h4 className="font-medium text-sm">Algorithmus</h4>
            </div>
            <div className="flex gap-2">
              {['round_robin', 'least_connections'].map(algo => (
                <button
                  key={algo}
                  onClick={() => changeAlgorithm.mutate(algo)}
                  disabled={changeAlgorithm.isPending}
                  className={`px-3 py-1.5 rounded text-sm transition-colors ${
                    lb.algorithm === algo
                      ? 'bg-pink-100 text-pink-700 border border-pink-300'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {algo === 'round_robin' ? 'Round Robin' : 'Least Connections'}
                </button>
              ))}
            </div>
          </div>

          {/* Services */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Activity size={16} className="text-gray-500" />
              <h4 className="font-medium text-sm">Services ({services.length})</h4>
            </div>
            {services.length > 0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="py-2 px-2">Protokoll</th>
                    <th className="py-2 px-2">Listen-Port</th>
                    <th className="py-2 px-2">Ziel-Port</th>
                    <th className="py-2 px-2">Health-Check</th>
                    <th className="py-2 px-2">Proxy Protocol</th>
                    <th className="py-2 px-2 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {services.map((svc: any, i: number) => (
                    <tr key={i} className="border-b hover:bg-gray-50">
                      <td className="py-2 px-2">
                        <span className="px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-700 uppercase">
                          {svc.protocol}
                        </span>
                      </td>
                      <td className="py-2 px-2 font-mono">{svc.listen_port}</td>
                      <td className="py-2 px-2 font-mono">{svc.destination_port}</td>
                      <td className="py-2 px-2 text-xs text-gray-500">
                        {svc.health_check?.protocol || 'tcp'}:{svc.health_check?.port || svc.destination_port}
                      </td>
                      <td className="py-2 px-2">
                        {svc.proxyprotocol ? (
                          <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">Ja</span>
                        ) : (
                          <span className="text-xs text-gray-400">Nein</span>
                        )}
                      </td>
                      <td className="py-2 px-2">
                        <button
                          onClick={() => deleteService.mutate(svc.listen_port)}
                          disabled={deleteService.isPending}
                          className="p-1 hover:bg-red-100 text-red-500 rounded"
                          title="Service entfernen"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-gray-500 text-sm">Keine Services konfiguriert</p>
            )}

            {showAddService ? (
              <AddServiceForm lbId={lb.name} onClose={() => setShowAddService(false)} />
            ) : (
              <button onClick={() => setShowAddService(true)} className="mt-2 flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800">
                <Plus size={16} /> Service hinzufügen
              </button>
            )}
          </div>

          {/* Targets */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Server size={16} className="text-gray-500" />
              <h4 className="font-medium text-sm">Targets ({targets.length})</h4>
            </div>
            {targets.length > 0 ? (
              <div className="space-y-2">
                {targets.map((target: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center gap-2">
                      {target.type === 'server' ? (
                        <Server size={14} className="text-blue-500" />
                      ) : target.type === 'ip' ? (
                        <Globe size={14} className="text-green-500" />
                      ) : (
                        <span className="text-xs">🏷</span>
                      )}
                      <span className="text-sm font-medium">
                        {target.type === 'server' && (target.server?.name || target.server)}
                        {target.type === 'ip' && target.ip}
                        {target.type === 'label_selector' && target.label_selector}
                      </span>
                      <span className="text-xs bg-gray-200 px-1.5 py-0.5 rounded">{target.type}</span>
                      {target.use_private_ip && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">Private IP</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {target.health_status && (
                        <span className={`w-2 h-2 rounded-full ${
                          target.health_status === 'healthy' ? 'bg-green-500' :
                          target.health_status === 'unhealthy' ? 'bg-red-500' : 'bg-gray-400'
                        }`} title={target.health_status} />
                      )}
                      <button
                        onClick={() => removeTarget.mutate({
                          target_type: target.type,
                          server: target.type === 'server' ? (target.server?.name || target.server) : undefined,
                          ip: target.type === 'ip' ? target.ip : undefined,
                          label_selector: target.type === 'label_selector' ? target.label_selector : undefined,
                        })}
                        disabled={removeTarget.isPending}
                        className="p-1 hover:bg-red-100 text-red-500 rounded"
                        title="Target entfernen"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">Keine Targets konfiguriert</p>
            )}

            {showAddTarget ? (
              <AddTargetForm lbId={lb.name} onClose={() => setShowAddTarget(false)} />
            ) : (
              <button onClick={() => setShowAddTarget(true)} className="mt-2 flex items-center gap-1 text-sm text-green-600 hover:text-green-800">
                <Plus size={16} /> Target hinzufügen
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function LoadBalancersPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState('lb11')
  const [newLocation, setNewLocation] = useState('fsn1')
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['loadBalancers'],
    queryFn: loadBalancersApi.list,
  })

  const createLb = useMutation({
    mutationFn: () => loadBalancersApi.create({ name: newName, load_balancer_type: newType, location: newLocation }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loadBalancers'] })
      setNewName('')
      setShowCreate(false)
    },
  })

  if (isLoading) return <div className="text-center py-8 text-gray-500">Laden...</div>

  const loadBalancers = data?.data?.load_balancers || []

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Load Balancer</h1>
          <p className="text-gray-500 mt-1">Traffic-Verteilung und Health-Checks</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="btn btn-primary flex items-center gap-2">
          <Plus size={20} /> Neuer Load Balancer
        </button>
      </div>

      {showCreate && (
        <div className="card mb-6">
          <h3 className="font-bold mb-3">Neuen Load Balancer erstellen</h3>
          <form onSubmit={(e) => { e.preventDefault(); createLb.mutate() }} className="flex gap-3 flex-wrap">
            <input
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="Name"
              className="flex-1 min-w-[200px] border rounded px-3 py-2"
              required
            />
            <select value={newType} onChange={e => setNewType(e.target.value)} className="border rounded px-3 py-2">
              <option value="lb11">LB11</option>
              <option value="lb21">LB21</option>
              <option value="lb31">LB31</option>
            </select>
            <select value={newLocation} onChange={e => setNewLocation(e.target.value)} className="border rounded px-3 py-2">
              <option value="fsn1">Falkenstein (fsn1)</option>
              <option value="nbg1">Nürnberg (nbg1)</option>
              <option value="hel1">Helsinki (hel1)</option>
              <option value="ash">Ashburn (ash)</option>
              <option value="hil">Hillsboro (hil)</option>
            </select>
            <button type="submit" disabled={createLb.isPending} className="btn btn-primary">
              {createLb.isPending ? 'Erstelle...' : 'Erstellen'}
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-gray-600">Abbrechen</button>
          </form>
          {createLb.isError && <p className="text-red-600 text-sm mt-2">Fehler beim Erstellen</p>}
        </div>
      )}

      <div className="grid gap-4">
        {loadBalancers.map((lb: any) => (
          <LoadBalancerCard key={lb.id} lb={lb} />
        ))}
        {loadBalancers.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <Scale className="w-16 h-16 mx-auto mb-3 text-gray-300" />
            <p className="text-lg">Keine Load Balancer vorhanden</p>
            <p className="text-sm mt-1">Erstelle einen Load Balancer, um Traffic auf deine Server zu verteilen.</p>
          </div>
        )}
      </div>
    </div>
  )
}
