import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { HardDrive, Camera, Archive, Disc, Clock, Plus, Trash2, Play } from 'lucide-react'
import { volumesApi, storageApi, snapshotSchedulerApi, serversApi } from '../services/api'

type Tab = 'volumes' | 'snapshots' | 'backups' | 'images' | 'scheduler'

function VolumesTab() {
  const { data, isLoading } = useQuery({
    queryKey: ['volumes'],
    queryFn: volumesApi.list,
  })

  if (isLoading) return <div className="text-center py-8 text-gray-500">Laden...</div>

  const volumes = data?.data?.volumes || []

  return (
    <div className="card">
      <table className="w-full">
        <thead>
          <tr className="border-b">
            <th className="text-left py-3">Name</th>
            <th className="text-left py-3">Größe</th>
            <th className="text-left py-3">Location</th>
            <th className="text-left py-3">Server</th>
            <th className="text-left py-3">Format</th>
            <th className="text-left py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {volumes.map((vol: any) => (
            <tr key={vol.id} className="border-b hover:bg-gray-50">
              <td className="py-3 flex items-center gap-2">
                <HardDrive size={18} className="text-gray-400" />
                {vol.name}
              </td>
              <td className="py-3">{vol.size} GB</td>
              <td className="py-3">{vol.location}</td>
              <td className="py-3">{vol.server || '-'}</td>
              <td className="py-3">{vol.format || '-'}</td>
              <td className="py-3">
                <span className={`px-2 py-1 rounded-full text-xs ${
                  vol.status === 'available'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
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
  )
}

function SnapshotsTab() {
  const { data, isLoading } = useQuery({
    queryKey: ['snapshots'],
    queryFn: storageApi.snapshots,
  })

  if (isLoading) return <div className="text-center py-8 text-gray-500">Laden...</div>

  const snapshots = data?.data?.images || []

  return (
    <div className="card">
      <table className="w-full">
        <thead>
          <tr className="border-b">
            <th className="text-left py-3">Name</th>
            <th className="text-left py-3">Beschreibung</th>
            <th className="text-left py-3">OS</th>
            <th className="text-left py-3">Architektur</th>
            <th className="text-left py-3">Disk-Größe</th>
            <th className="text-left py-3">Erstellt am</th>
          </tr>
        </thead>
        <tbody>
          {snapshots.map((img: any) => (
            <tr key={img.id} className="border-b hover:bg-gray-50">
              <td className="py-3 flex items-center gap-2">
                <Camera size={18} className="text-gray-400" />
                {img.name || `Snapshot #${img.id}`}
              </td>
              <td className="py-3">{img.description || '-'}</td>
              <td className="py-3">{img.os_flavor} {img.os_version}</td>
              <td className="py-3">{img.architecture || '-'}</td>
              <td className="py-3">{img.disk_size ? `${img.disk_size} GB` : '-'}</td>
              <td className="py-3">{img.created ? new Date(img.created).toLocaleDateString('de-DE') : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {snapshots.length === 0 && (
        <p className="text-center text-gray-500 py-8">Keine Snapshots vorhanden</p>
      )}
    </div>
  )
}

function BackupsTab() {
  const { data, isLoading } = useQuery({
    queryKey: ['backups'],
    queryFn: storageApi.backups,
  })

  if (isLoading) return <div className="text-center py-8 text-gray-500">Laden...</div>

  const backups = data?.data?.images || []

  return (
    <div className="card">
      <table className="w-full">
        <thead>
          <tr className="border-b">
            <th className="text-left py-3">Name</th>
            <th className="text-left py-3">Beschreibung</th>
            <th className="text-left py-3">OS</th>
            <th className="text-left py-3">Architektur</th>
            <th className="text-left py-3">Disk-Größe</th>
            <th className="text-left py-3">Erstellt am</th>
          </tr>
        </thead>
        <tbody>
          {backups.map((img: any) => (
            <tr key={img.id} className="border-b hover:bg-gray-50">
              <td className="py-3 flex items-center gap-2">
                <Archive size={18} className="text-gray-400" />
                {img.name || `Backup #${img.id}`}
              </td>
              <td className="py-3">{img.description || '-'}</td>
              <td className="py-3">{img.os_flavor} {img.os_version}</td>
              <td className="py-3">{img.architecture || '-'}</td>
              <td className="py-3">{img.disk_size ? `${img.disk_size} GB` : '-'}</td>
              <td className="py-3">{img.created ? new Date(img.created).toLocaleDateString('de-DE') : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {backups.length === 0 && (
        <p className="text-center text-gray-500 py-8">Keine Backups vorhanden</p>
      )}
    </div>
  )
}

function ImagesTab() {
  const { data, isLoading } = useQuery({
    queryKey: ['systemImages'],
    queryFn: storageApi.systemImages,
  })

  if (isLoading) return <div className="text-center py-8 text-gray-500">Laden...</div>

  const images = data?.data?.images || []

  return (
    <div className="card">
      <table className="w-full">
        <thead>
          <tr className="border-b">
            <th className="text-left py-3">Name</th>
            <th className="text-left py-3">Beschreibung</th>
            <th className="text-left py-3">OS</th>
            <th className="text-left py-3">Architektur</th>
            <th className="text-left py-3">Disk-Größe</th>
            <th className="text-left py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {images.map((img: any) => (
            <tr key={img.id} className="border-b hover:bg-gray-50">
              <td className="py-3 flex items-center gap-2">
                <Disc size={18} className="text-gray-400" />
                {img.name}
              </td>
              <td className="py-3">{img.description || '-'}</td>
              <td className="py-3">{img.os_flavor} {img.os_version}</td>
              <td className="py-3">{img.architecture || '-'}</td>
              <td className="py-3">{img.disk_size ? `${img.disk_size} GB` : '-'}</td>
              <td className="py-3">
                <span className={`px-2 py-1 rounded-full text-xs ${
                  img.deprecated
                    ? 'bg-red-100 text-red-800'
                    : 'bg-green-100 text-green-800'
                }`}>
                  {img.deprecated ? 'Veraltet' : 'Aktiv'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {images.length === 0 && (
        <p className="text-center text-gray-500 py-8">Keine System-Images vorhanden</p>
      )}
    </div>
  )
}

function SchedulerTab() {
  const [showCreate, setShowCreate] = useState(false)
  const [server, setServer] = useState('')
  const [interval, setInterval_] = useState('daily')
  const [time, setTime] = useState('03:00')
  const [retention, setRetention] = useState('5')
  const queryClient = useQueryClient()

  const { data: schedulesData, isLoading } = useQuery({
    queryKey: ['snapshotSchedules'],
    queryFn: snapshotSchedulerApi.list,
  })

  const { data: serversData } = useQuery({
    queryKey: ['servers'],
    queryFn: serversApi.list,
  })

  const createSchedule = useMutation({
    mutationFn: (data: any) => snapshotSchedulerApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshotSchedules'] })
      setShowCreate(false)
      setServer('')
    },
  })

  const deleteSchedule = useMutation({
    mutationFn: (id: string) => snapshotSchedulerApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['snapshotSchedules'] }),
  })

  const runNow = useMutation({
    mutationFn: (id: string) => snapshotSchedulerApi.runNow(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['snapshotSchedules'] }),
  })

  if (isLoading) return <div className="text-center py-8 text-gray-500">Laden...</div>

  const schedules = schedulesData?.data?.data || []
  const serverList = serversData?.data?.servers || []

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button onClick={() => setShowCreate(!showCreate)} className="btn btn-primary flex items-center gap-2 text-sm">
          <Plus size={16} /> Neuer Zeitplan
        </button>
      </div>

      {showCreate && (
        <div className="card mb-4">
          <h3 className="font-bold mb-3">Neuen Snapshot-Zeitplan erstellen</h3>
          <form onSubmit={(e) => {
            e.preventDefault()
            createSchedule.mutate({ server, interval: interval, time, retention: parseInt(retention) })
          }} className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Server</label>
              <select value={server} onChange={e => setServer(e.target.value)} className="w-full border rounded px-3 py-2 text-sm" required>
                <option value="">Auswählen...</option>
                {serverList.map((s: any) => (
                  <option key={s.id} value={s.name}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Intervall</label>
              <select value={interval} onChange={e => setInterval_(e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                <option value="daily">Täglich</option>
                <option value="weekly">Wöchentlich</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Uhrzeit</label>
              <input type="time" value={time} onChange={e => setTime(e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Aufbewahrung</label>
              <input type="number" value={retention} onChange={e => setRetention(e.target.value)} min="1" max="50" className="w-full border rounded px-3 py-2 text-sm" />
            </div>
            <div className="flex items-end gap-2">
              <button type="submit" disabled={createSchedule.isPending} className="btn btn-primary text-sm py-2">
                {createSchedule.isPending ? 'Erstelle...' : 'Erstellen'}
              </button>
              <button type="button" onClick={() => setShowCreate(false)} className="text-sm py-2 px-3 text-gray-600">Abbrechen</button>
            </div>
          </form>
          {createSchedule.isError && <p className="text-red-600 text-sm mt-2">Fehler beim Erstellen</p>}
        </div>
      )}

      <div className="card">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2 px-2">Server</th>
              <th className="py-2 px-2">Intervall</th>
              <th className="py-2 px-2">Uhrzeit</th>
              <th className="py-2 px-2">Aufbewahrung</th>
              <th className="py-2 px-2">Letzter Lauf</th>
              <th className="py-2 px-2">Status</th>
              <th className="py-2 px-2 w-24"></th>
            </tr>
          </thead>
          <tbody>
            {schedules.map((s: any) => (
              <tr key={s.id} className="border-b hover:bg-gray-50">
                <td className="py-2 px-2 font-medium">{s.server}</td>
                <td className="py-2 px-2">
                  <span className="px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-700">
                    {s.interval === 'daily' ? 'Täglich' : 'Wöchentlich'}
                  </span>
                </td>
                <td className="py-2 px-2 font-mono">{s.time}</td>
                <td className="py-2 px-2">{s.retention} Snapshots</td>
                <td className="py-2 px-2 text-gray-500">
                  {s.last_run ? new Date(s.last_run).toLocaleString('de-DE') : 'Nie'}
                </td>
                <td className="py-2 px-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${s.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {s.enabled ? 'Aktiv' : 'Inaktiv'}
                  </span>
                </td>
                <td className="py-2 px-2">
                  <div className="flex gap-1">
                    <button
                      onClick={() => runNow.mutate(s.id)}
                      disabled={runNow.isPending}
                      className="p-1 hover:bg-blue-100 text-blue-600 rounded"
                      title="Jetzt ausführen"
                    >
                      <Play size={14} />
                    </button>
                    <button
                      onClick={() => { if (confirm('Zeitplan löschen?')) deleteSchedule.mutate(s.id) }}
                      disabled={deleteSchedule.isPending}
                      className="p-1 hover:bg-red-100 text-red-500 rounded"
                      title="Löschen"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {schedules.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p>Keine Zeitpläne konfiguriert</p>
            <p className="text-sm mt-1">Erstelle einen Zeitplan für automatische Snapshots.</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default function StoragePage() {
  const [activeTab, setActiveTab] = useState<Tab>('volumes')

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'volumes', label: 'Volumes', icon: <HardDrive size={20} /> },
    { key: 'snapshots', label: 'Snapshots', icon: <Camera size={20} /> },
    { key: 'backups', label: 'Backups', icon: <Archive size={20} /> },
    { key: 'images', label: 'System Images', icon: <Disc size={20} /> },
    { key: 'scheduler', label: 'Scheduler', icon: <Clock size={20} /> },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Storage</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-hetzner-blue text-hetzner-blue'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'volumes' && <VolumesTab />}
      {activeTab === 'snapshots' && <SnapshotsTab />}
      {activeTab === 'backups' && <BackupsTab />}
      {activeTab === 'images' && <ImagesTab />}
      {activeTab === 'scheduler' && <SchedulerTab />}
    </div>
  )
}
