import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Server, Play, Square, RotateCw, Trash2, Plus } from 'lucide-react'
import { serversApi } from '../services/api'

export default function ServersPage() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['servers'],
    queryFn: serversApi.list,
  })

  const powerMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: string }) =>
      serversApi.power(id, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => serversApi.delete(id, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] })
    },
  })

  if (isLoading) {
    return <div className="text-center py-12">Laden...</div>
  }

  const servers = data?.data?.servers || []

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Servers</h1>
        <button
          onClick={() => alert('Server-Erstellung kommt bald!')}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={20} />
          Neuer Server
        </button>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4">Name</th>
                <th className="text-left py-3 px-4">Status</th>
                <th className="text-left py-3 px-4">Typ</th>
                <th className="text-left py-3 px-4">Location</th>
                <th className="text-left py-3 px-4">IPv4</th>
                <th className="text-right py-3 px-4">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {servers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    Keine Server vorhanden
                  </td>
                </tr>
              ) : (
                servers.map((server: any) => (
                  <tr key={server.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <Server size={18} className="text-gray-400" />
                        <span className="font-medium">{server.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 rounded-full text-xs ${
                          server.status === 'running'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {server.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">{server.server_type}</td>
                    <td className="py-3 px-4">{server.location}</td>
                    <td className="py-3 px-4 font-mono text-sm">{server.public_ipv4}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-2">
                        {server.status === 'running' ? (
                          <button
                            onClick={() => powerMutation.mutate({ id: server.name, action: 'shutdown' })}
                            className="p-2 hover:bg-gray-200 rounded"
                            title="Stop"
                          >
                            <Square size={16} />
                          </button>
                        ) : (
                          <button
                            onClick={() => powerMutation.mutate({ id: server.name, action: 'start' })}
                            className="p-2 hover:bg-gray-200 rounded"
                            title="Start"
                          >
                            <Play size={16} />
                          </button>
                        )}
                        <button
                          onClick={() => powerMutation.mutate({ id: server.name, action: 'reboot' })}
                          className="p-2 hover:bg-gray-200 rounded"
                          title="Reboot"
                        >
                          <RotateCw size={16} />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm(`Server "${server.name}" wirklich löschen?`)) {
                              deleteMutation.mutate(server.name)
                            }
                          }}
                          className="p-2 hover:bg-red-100 text-red-600 rounded"
                          title="Löschen"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
