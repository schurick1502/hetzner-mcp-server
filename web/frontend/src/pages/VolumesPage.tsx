import { useQuery } from '@tanstack/react-query'
import { HardDrive } from 'lucide-react'
import { volumesApi } from '../services/api'

export default function VolumesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['volumes'],
    queryFn: volumesApi.list,
  })

  if (isLoading) return <div>Laden...</div>

  const volumes = data?.data?.volumes || []

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Volumes</h1>

      <div className="card">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left py-3">Name</th>
              <th className="text-left py-3">Größe</th>
              <th className="text-left py-3">Location</th>
              <th className="text-left py-3">Server</th>
              <th className="text-left py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {volumes.map((vol: any) => (
              <tr key={vol.id} className="border-b">
                <td className="py-3 flex items-center gap-2">
                  <HardDrive size={18} className="text-gray-400" />
                  {vol.name}
                </td>
                <td className="py-3">{vol.size} GB</td>
                <td className="py-3">{vol.location}</td>
                <td className="py-3">{vol.server || '-'}</td>
                <td className="py-3">
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                    {vol.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {volumes.length === 0 && (
          <p className="text-center text-gray-500 py-8">Keine Volumes vorhanden</p>
        )}
      </div>
    </div>
  )
}
