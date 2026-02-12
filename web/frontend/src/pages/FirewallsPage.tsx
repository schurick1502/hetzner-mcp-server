import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Shield, ChevronDown, ChevronRight, Plus, Trash2, ArrowDownLeft, ArrowUpRight, Server } from 'lucide-react'
import { firewallsApi } from '../services/api'

interface Rule {
  direction: string
  protocol: string
  source_ips: string[]
  destination_ips: string[]
  port: string | null
}

function AddRuleForm({ firewallName, onClose }: { firewallName: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [direction, setDirection] = useState('in')
  const [protocol, setProtocol] = useState('tcp')
  const [ips, setIps] = useState('0.0.0.0/0, ::/0')
  const [port, setPort] = useState('')

  const addRule = useMutation({
    mutationFn: (rule: any) => firewallsApi.addRule(firewallName, rule),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firewalls'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const ipList = ips.split(',').map(ip => ip.trim()).filter(Boolean)
    addRule.mutate({
      direction,
      protocol,
      source_ips: direction === 'in' ? ipList : [],
      destination_ips: direction === 'out' ? ipList : [],
      port: ['tcp', 'udp'].includes(protocol) ? port || null : null,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="border rounded-lg p-4 bg-blue-50 mt-3">
      <h4 className="font-medium mb-3">Neue Regel</h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Richtung</label>
          <select value={direction} onChange={e => setDirection(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm">
            <option value="in">Eingehend (In)</option>
            <option value="out">Ausgehend (Out)</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Protokoll</label>
          <select value={protocol} onChange={e => setProtocol(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm">
            <option value="tcp">TCP</option>
            <option value="udp">UDP</option>
            <option value="icmp">ICMP</option>
            <option value="esp">ESP</option>
            <option value="gre">GRE</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">{direction === 'in' ? 'Quell-IPs' : 'Ziel-IPs'}</label>
          <input value={ips} onChange={e => setIps(e.target.value)} placeholder="0.0.0.0/0, ::/0" className="w-full border rounded px-2 py-1.5 text-sm" />
        </div>
        {['tcp', 'udp'].includes(protocol) && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Port(s)</label>
            <input value={port} onChange={e => setPort(e.target.value)} placeholder="80 oder 8000-9000" className="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
        )}
      </div>
      <div className="flex gap-2 mt-3">
        <button type="submit" disabled={addRule.isPending} className="btn btn-primary text-sm px-3 py-1.5">
          {addRule.isPending ? 'Speichere...' : 'Hinzufügen'}
        </button>
        <button type="button" onClick={onClose} className="text-sm px-3 py-1.5 text-gray-600 hover:text-gray-800">Abbrechen</button>
      </div>
      {addRule.isError && <p className="text-red-600 text-sm mt-2">Fehler beim Hinzufügen der Regel</p>}
    </form>
  )
}

function FirewallCard({ firewall }: { firewall: any }) {
  const [expanded, setExpanded] = useState(false)
  const [showAddRule, setShowAddRule] = useState(false)
  const queryClient = useQueryClient()

  const deleteFw = useMutation({
    mutationFn: () => firewallsApi.delete(firewall.name, true),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['firewalls'] }),
  })

  const deleteRule = useMutation({
    mutationFn: (index: number) => {
      const newRules = firewall.rules.filter((_: any, i: number) => i !== index)
      return firewallsApi.setRules(firewall.name, newRules)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['firewalls'] }),
  })

  return (
    <div className="card">
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-green-600" />
          <div>
            <h3 className="font-bold">{firewall.name}</h3>
            <p className="text-sm text-gray-600">
              {firewall.rules_count} Regeln
              {firewall.applied_to?.length > 0 && (
                <span className="ml-2">
                  - Angewendet auf: {firewall.applied_to.map((a: any) => a.server).filter(Boolean).join(', ') || 'Keine Server'}
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              if (confirm(`Firewall "${firewall.name}" wirklich löschen?`)) deleteFw.mutate()
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
          {firewall.rules?.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="py-2 px-2">Richtung</th>
                  <th className="py-2 px-2">Protokoll</th>
                  <th className="py-2 px-2">IPs</th>
                  <th className="py-2 px-2">Port</th>
                  <th className="py-2 px-2 w-10"></th>
                </tr>
              </thead>
              <tbody>
                {firewall.rules.map((rule: Rule, index: number) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-2">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
                        rule.direction === 'in' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'
                      }`}>
                        {rule.direction === 'in' ? <ArrowDownLeft size={12} /> : <ArrowUpRight size={12} />}
                        {rule.direction === 'in' ? 'Eingehend' : 'Ausgehend'}
                      </span>
                    </td>
                    <td className="py-2 px-2 uppercase font-mono">{rule.protocol}</td>
                    <td className="py-2 px-2 font-mono text-xs">
                      {(rule.direction === 'in' ? rule.source_ips : rule.destination_ips)?.join(', ') || 'Alle'}
                    </td>
                    <td className="py-2 px-2 font-mono">{rule.port || 'Alle'}</td>
                    <td className="py-2 px-2">
                      <button
                        onClick={() => deleteRule.mutate(index)}
                        disabled={deleteRule.isPending}
                        className="p-1 hover:bg-red-100 text-red-500 rounded"
                        title="Regel löschen"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-500 text-sm">Keine Regeln definiert</p>
          )}

          {showAddRule ? (
            <AddRuleForm firewallName={firewall.name} onClose={() => setShowAddRule(false)} />
          ) : (
            <button onClick={() => setShowAddRule(true)} className="mt-3 flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800">
              <Plus size={16} /> Regel hinzufügen
            </button>
          )}

          {firewall.applied_to?.length > 0 && (
            <div className="mt-4 pt-3 border-t">
              <p className="text-xs text-gray-500 mb-2">Angewendet auf:</p>
              <div className="flex gap-2 flex-wrap">
                {firewall.applied_to.map((a: any, i: number) => (
                  <span key={i} className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-xs">
                    <Server size={12} /> {a.server || a.type}
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

export default function FirewallsPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['firewalls'],
    queryFn: firewallsApi.list,
  })

  const createFw = useMutation({
    mutationFn: () => firewallsApi.create({ name: newName }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firewalls'] })
      setNewName('')
      setShowCreate(false)
    },
  })

  if (isLoading) return <div className="text-center py-8 text-gray-500">Laden...</div>

  const firewalls = data?.data?.firewalls || []

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Firewalls</h1>
        <button onClick={() => setShowCreate(!showCreate)} className="btn btn-primary flex items-center gap-2">
          <Plus size={20} /> Neue Firewall
        </button>
      </div>

      {showCreate && (
        <div className="card mb-6">
          <h3 className="font-bold mb-3">Neue Firewall erstellen</h3>
          <form onSubmit={(e) => { e.preventDefault(); createFw.mutate() }} className="flex gap-3">
            <input
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="Firewall-Name"
              className="flex-1 border rounded px-3 py-2"
              required
            />
            <button type="submit" disabled={createFw.isPending} className="btn btn-primary">
              {createFw.isPending ? 'Erstelle...' : 'Erstellen'}
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-gray-600">Abbrechen</button>
          </form>
          {createFw.isError && <p className="text-red-600 text-sm mt-2">Fehler beim Erstellen</p>}
        </div>
      )}

      <div className="grid gap-4">
        {firewalls.map((fw: any) => (
          <FirewallCard key={fw.id} firewall={fw} />
        ))}
        {firewalls.length === 0 && (
          <p className="text-center text-gray-500 py-8">Keine Firewalls vorhanden</p>
        )}
      </div>
    </div>
  )
}
