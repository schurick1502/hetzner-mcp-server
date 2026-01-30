import { useQuery } from '@tanstack/react-query'
import { Server, Shield, HardDrive, Network } from 'lucide-react'
import { serversApi, firewallsApi, volumesApi, networksApi } from '../services/api'

export default function DashboardPage() {
  const { data: servers } = useQuery({
    queryKey: ['servers'],
    queryFn: serversApi.list,
  })

  const { data: firewalls } = useQuery({
    queryKey: ['firewalls'],
    queryFn: firewallsApi.list,
  })

  const { data: volumes } = useQuery({
    queryKey: ['volumes'],
    queryFn: volumesApi.list,
  })

  const { data: networks } = useQuery({
    queryKey: ['networks'],
    queryFn: networksApi.list,
  })

  const stats = [
    {
      name: 'Servers',
      count: servers?.data?.count || 0,
      icon: <Server className="w-8 h-8" />,
      color: 'bg-blue-500',
    },
    {
      name: 'Firewalls',
      count: firewalls?.data?.count || 0,
      icon: <Shield className="w-8 h-8" />,
      color: 'bg-green-500',
    },
    {
      name: 'Volumes',
      count: volumes?.data?.count || 0,
      icon: <HardDrive className="w-8 h-8" />,
      color: 'bg-purple-500',
    },
    {
      name: 'Networks',
      count: networks?.data?.count || 0,
      icon: <Network className="w-8 h-8" />,
      color: 'bg-orange-500',
    },
  ]

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{stat.name}</p>
                <p className="text-3xl font-bold mt-1">{stat.count}</p>
              </div>
              <div className={`${stat.color} text-white p-3 rounded-lg`}>
                {stat.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h2 className="text-xl font-bold mb-4">Kürzlich erstellte Server</h2>
        <div className="space-y-2">
          {servers?.data?.servers?.slice(0, 5).map((server: any) => (
            <div key={server.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Server className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="font-medium">{server.name}</p>
                  <p className="text-sm text-gray-600">{server.server_type} • {server.location}</p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm ${
                server.status === 'running' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {server.status}
              </span>
            </div>
          )) || <p className="text-gray-500">Keine Server vorhanden</p>}
        </div>
      </div>
    </div>
  )
}
