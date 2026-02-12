import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Server, Shield, HardDrive, Network, Scale, RefreshCw } from 'lucide-react'
import { topologyApi } from '../services/api'

const TYPE_CONFIG: Record<string, { color: string; bg: string; border: string; icon: any; label: string }> = {
  server: { color: 'text-blue-700', bg: 'bg-blue-50', border: 'border-blue-300', icon: Server, label: 'Server' },
  firewall: { color: 'text-green-700', bg: 'bg-green-50', border: 'border-green-300', icon: Shield, label: 'Firewall' },
  volume: { color: 'text-purple-700', bg: 'bg-purple-50', border: 'border-purple-300', icon: HardDrive, label: 'Volume' },
  network: { color: 'text-orange-700', bg: 'bg-orange-50', border: 'border-orange-300', icon: Network, label: 'Netzwerk' },
  load_balancer: { color: 'text-pink-700', bg: 'bg-pink-50', border: 'border-pink-300', icon: Scale, label: 'Load Balancer' },
}

const EDGE_COLORS: Record<string, string> = {
  firewall: '#22c55e',
  volume: '#a855f7',
  network: '#f97316',
  lb_target: '#ec4899',
}

interface TopoNode {
  id: string
  type: string
  name: string
  metadata: Record<string, any>
}

interface TopoEdge {
  from: string
  to: string
  type: string
}

function TopologyGraph({ nodes, edges }: { nodes: TopoNode[]; edges: TopoEdge[] }) {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)

  // Layout: Server in der Mitte, andere Ressourcen gruppiert drumherum
  const servers = nodes.filter(n => n.type === 'server')
  const firewalls = nodes.filter(n => n.type === 'firewall')
  const volumes = nodes.filter(n => n.type === 'volume')
  const networks = nodes.filter(n => n.type === 'network')
  const lbs = nodes.filter(n => n.type === 'load_balancer')

  // Positionen berechnen
  const positions: Record<string, { x: number; y: number }> = {}
  const centerX = 500
  const centerY = 300

  // Server in der Mitte vertikal
  servers.forEach((s, i) => {
    positions[s.id] = {
      x: centerX,
      y: 80 + i * (Math.min(120, 500 / Math.max(servers.length, 1))),
    }
  })

  // Firewalls links oben
  firewalls.forEach((f, i) => {
    positions[f.id] = { x: 150, y: 60 + i * 100 }
  })

  // Volumes rechts oben
  volumes.forEach((v, i) => {
    positions[v.id] = { x: 850, y: 60 + i * 100 }
  })

  // Networks links unten
  networks.forEach((n, i) => {
    positions[n.id] = { x: 150, y: 350 + i * 100 }
  })

  // Load Balancers rechts unten
  lbs.forEach((l, i) => {
    positions[l.id] = { x: 850, y: 350 + i * 100 }
  })

  const maxY = Math.max(...Object.values(positions).map(p => p.y), 400) + 80
  const highlightedEdges = hoveredNode
    ? edges.filter(e => e.from === hoveredNode || e.to === hoveredNode)
    : edges
  const highlightedNodeIds = hoveredNode
    ? new Set([hoveredNode, ...highlightedEdges.map(e => e.from), ...highlightedEdges.map(e => e.to)])
    : null

  return (
    <svg width="100%" viewBox={`0 0 1000 ${maxY}`} className="border rounded-xl bg-white">
      {/* Edges */}
      {edges.map((edge, i) => {
        const from = positions[edge.from]
        const to = positions[edge.to]
        if (!from || !to) return null
        const isHighlighted = !highlightedNodeIds || (highlightedNodeIds.has(edge.from) && highlightedNodeIds.has(edge.to))
        return (
          <line
            key={i}
            x1={from.x}
            y1={from.y}
            x2={to.x}
            y2={to.y}
            stroke={EDGE_COLORS[edge.type] || '#9ca3af'}
            strokeWidth={isHighlighted ? 2.5 : 1}
            strokeOpacity={isHighlighted ? 0.8 : 0.15}
            strokeDasharray={edge.type === 'network' ? '6 3' : undefined}
          />
        )
      })}

      {/* Nodes */}
      {nodes.map(node => {
        const pos = positions[node.id]
        if (!pos) return null
        const config = TYPE_CONFIG[node.type]
        if (!config) return null
        const isHighlighted = !highlightedNodeIds || highlightedNodeIds.has(node.id)
        const isHovered = hoveredNode === node.id

        return (
          <g
            key={node.id}
            transform={`translate(${pos.x}, ${pos.y})`}
            onMouseEnter={() => setHoveredNode(node.id)}
            onMouseLeave={() => setHoveredNode(null)}
            className="cursor-pointer"
            opacity={isHighlighted ? 1 : 0.25}
          >
            {/* Background circle */}
            <circle
              r={isHovered ? 34 : 30}
              fill={isHovered ? 'white' : '#f8fafc'}
              stroke={isHovered ? EDGE_COLORS[node.type === 'server' ? 'network' : node.type === 'firewall' ? 'firewall' : node.type === 'volume' ? 'volume' : node.type === 'load_balancer' ? 'lb_target' : 'network'] || '#d1d5db' : '#e5e7eb'}
              strokeWidth={isHovered ? 3 : 1.5}
              className="transition-all"
            />
            {/* Icon placeholder - text-based */}
            <text
              textAnchor="middle"
              dominantBaseline="central"
              fontSize="11"
              fontWeight="bold"
              fill={isHovered ? '#1e293b' : '#64748b'}
            >
              {node.type === 'server' ? 'SRV' :
               node.type === 'firewall' ? 'FW' :
               node.type === 'volume' ? 'VOL' :
               node.type === 'network' ? 'NET' : 'LB'}
            </text>
            {/* Name label */}
            <text
              y={44}
              textAnchor="middle"
              fontSize="11"
              fill="#334155"
              fontWeight={isHovered ? 'bold' : 'normal'}
            >
              {node.name}
            </text>
            {/* Metadata on hover */}
            {isHovered && node.metadata && (
              <text y={58} textAnchor="middle" fontSize="9" fill="#94a3b8">
                {node.type === 'server' && `${node.metadata.server_type} - ${node.metadata.location}`}
                {node.type === 'firewall' && `${node.metadata.rules_count} Regeln`}
                {node.type === 'volume' && `${node.metadata.size} GB`}
                {node.type === 'network' && node.metadata.ip_range}
                {node.type === 'load_balancer' && `${node.metadata.type} - ${node.metadata.algorithm}`}
              </text>
            )}
          </g>
        )
      })}

      {/* Legende */}
      {Object.entries(TYPE_CONFIG).map(([type, config], i) => (
        <g key={type} transform={`translate(${20 + i * 170}, ${maxY - 30})`}>
          <circle r={6} fill={EDGE_COLORS[type === 'server' ? 'network' : type === 'firewall' ? 'firewall' : type === 'volume' ? 'volume' : type === 'load_balancer' ? 'lb_target' : 'network'] || '#9ca3af'} />
          <text x={14} dominantBaseline="central" fontSize="11" fill="#64748b">{config.label}</text>
        </g>
      ))}
    </svg>
  )
}

export default function TopologyPage() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['topology'],
    queryFn: topologyApi.get,
  })

  const topology = data?.data?.data

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Infrastruktur-Topologie</h1>
          <p className="text-gray-500 mt-1">Visuelle Darstellung aller Ressourcen und Verbindungen</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="btn btn-primary flex items-center gap-2"
        >
          <RefreshCw size={16} className={isFetching ? 'animate-spin' : ''} />
          Aktualisieren
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-8 text-gray-500">Lade Topologie...</div>
      ) : topology ? (
        <>
          {/* Zusammenfassung */}
          <div className="grid grid-cols-5 gap-4 mb-6">
            {Object.entries(TYPE_CONFIG).map(([type, config]) => {
              const Icon = config.icon
              const count = topology.counts[type === 'load_balancer' ? 'load_balancers' : `${type}s`] || 0
              return (
                <div key={type} className={`card !p-4 ${config.bg} border ${config.border}`}>
                  <div className="flex items-center gap-2">
                    <Icon size={20} className={config.color} />
                    <span className={`text-2xl font-bold ${config.color}`}>{count}</span>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{config.label}</p>
                </div>
              )
            })}
          </div>

          {/* Graph */}
          {topology.nodes.length > 0 ? (
            <div className="card !p-2">
              <TopologyGraph nodes={topology.nodes} edges={topology.edges} />
            </div>
          ) : (
            <div className="card text-center py-12 text-gray-500">
              <Network className="w-16 h-16 mx-auto mb-3 text-gray-300" />
              <p className="text-lg">Keine Ressourcen gefunden</p>
            </div>
          )}

          {/* Verbindungs-Detail */}
          {topology.edges.length > 0 && (
            <div className="card mt-4">
              <h3 className="font-bold mb-3">Verbindungen ({topology.edges.length})</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {topology.edges.map((edge: TopoEdge, i: number) => {
                  const fromNode = topology.nodes.find((n: TopoNode) => n.id === edge.from)
                  const toNode = topology.nodes.find((n: TopoNode) => n.id === edge.to)
                  return (
                    <div key={i} className="flex items-center gap-2 text-sm p-2 bg-gray-50 rounded">
                      <span className="font-medium">{fromNode?.name}</span>
                      <span className="text-gray-400">&rarr;</span>
                      <span className="font-medium">{toNode?.name}</span>
                      <span
                        className="ml-auto text-xs px-1.5 py-0.5 rounded"
                        style={{ backgroundColor: `${EDGE_COLORS[edge.type]}20`, color: EDGE_COLORS[edge.type] }}
                      >
                        {edge.type}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-8 text-red-500">Fehler beim Laden der Topologie</div>
      )}
    </div>
  )
}
