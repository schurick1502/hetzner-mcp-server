import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { HardDrive, Camera, Archive, Disc } from 'lucide-react'
import { volumesApi, storageApi } from '../services/api'

type Tab = 'volumes' | 'snapshots' | 'backups' | 'images'

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

export default function StoragePage() {
  const [activeTab, setActiveTab] = useState<Tab>('volumes')

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'volumes', label: 'Volumes', icon: <HardDrive size={20} /> },
    { key: 'snapshots', label: 'Snapshots', icon: <Camera size={20} /> },
    { key: 'backups', label: 'Backups', icon: <Archive size={20} /> },
    { key: 'images', label: 'System Images', icon: <Disc size={20} /> },
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
    </div>
  )
}
