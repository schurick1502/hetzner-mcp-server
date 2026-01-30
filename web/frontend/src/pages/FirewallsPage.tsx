import { useQuery } from '@tanstack/react-query'
import { Shield } from 'lucide-react'
import { firewallsApi } from '../services/api'

export default function FirewallsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['firewalls'],
    queryFn: firewallsApi.list,
  })

  if (isLoading) return <div>Laden...</div>

  const firewalls = data?.data?.firewalls || []

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Firewalls</h1>

      <div className="grid gap-4">
        {firewalls.map((fw: any) => (
          <div key={fw.id} className="card">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="w-6 h-6 text-hetzner-red" />
                <div>
                  <h3 className="font-bold">{fw.name}</h3>
                  <p className="text-sm text-gray-600">{fw.rules_count} Regeln</p>
                </div>
              </div>
            </div>
          </div>
        ))}
        {firewalls.length === 0 && (
          <p className="text-center text-gray-500 py-8">Keine Firewalls vorhanden</p>
        )}
      </div>
    </div>
  )
}
