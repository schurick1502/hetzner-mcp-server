import { useQuery } from '@tanstack/react-query'
import { Network } from 'lucide-react'
import { networksApi } from '../services/api'

export default function NetworksPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['networks'],
    queryFn: networksApi.list,
  })

  if (isLoading) return <div>Laden...</div>

  const networks = data?.data?.networks || []

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Networks</h1>

      <div className="grid gap-4">
        {networks.map((net: any) => (
          <div key={net.id} className="card">
            <div className="flex items-center gap-3">
              <Network className="w-6 h-6 text-hetzner-red" />
              <div>
                <h3 className="font-bold">{net.name}</h3>
                <p className="text-sm text-gray-600 font-mono">{net.ip_range}</p>
                <p className="text-xs text-gray-500 mt-1">{net.subnets.length} Subnets</p>
              </div>
            </div>
          </div>
        ))}
        {networks.length === 0 && (
          <p className="text-center text-gray-500 py-8">Keine Netzwerke vorhanden</p>
        )}
      </div>
    </div>
  )
}
