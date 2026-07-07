import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Save, Eye, EyeOff, CheckCircle, AlertCircle, Cloud, Bot, Container } from 'lucide-react'
import { settingsApi } from '../services/api'

interface SettingMeta {
  label: string
  value: string
  is_secret: boolean
  has_value: boolean
}

interface SettingGroup {
  label: string
  settings: Record<string, SettingMeta>
}

const GROUP_ICONS: Record<string, React.ReactNode> = {
  hetzner: <Cloud className="w-5 h-5 text-red-500" />,
  ai: <Bot className="w-5 h-5 text-purple-500" />,
  docker: <Container className="w-5 h-5 text-blue-500" />,
}

function SettingsGroup({ groupKey, group, onSave }: {
  groupKey: string
  group: SettingGroup
  onSave: (settings: Record<string, string>) => void
}) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({})
  const [saved, setSaved] = useState(false)

  const handleChange = (key: string, value: string) => {
    setValues(prev => ({ ...prev, [key]: value }))
    setSaved(false)
  }

  const toggleShow = (key: string) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const handleSave = () => {
    onSave(values)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const hasChanges = Object.keys(values).length > 0

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        {GROUP_ICONS[groupKey] || <Settings className="w-5 h-5" />}
        <h2 className="text-lg font-bold">{group.label}</h2>
      </div>

      <div className="space-y-4">
        {Object.entries(group.settings).map(([key, meta]) => (
          <div key={key}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {meta.label}
              {meta.has_value && (
                <span className="ml-2 text-xs text-green-600 font-normal">Konfiguriert</span>
              )}
              {!meta.has_value && (
                <span className="ml-2 text-xs text-gray-400 font-normal">Nicht gesetzt</span>
              )}
            </label>
            <div className="flex gap-2">
              <div className="flex-1 relative">
                {key === 'DOCKER_MONITOR_SERVERS' ? (
                  <textarea
                    value={values[key] ?? meta.value ?? ''}
                    onChange={e => handleChange(key, e.target.value)}
                    placeholder='[{"name":"Server 1","host":"1.2.3.4","user":"root","port":22}]'
                    className="w-full border rounded px-3 py-2 text-sm font-mono"
                    rows={4}
                  />
                ) : (
                  <input
                    type={meta.is_secret && !showSecrets[key] ? 'password' : 'text'}
                    value={values[key] ?? ''}
                    onChange={e => handleChange(key, e.target.value)}
                    placeholder={meta.is_secret ? (meta.has_value ? 'Neuen Wert eingeben zum Ändern' : 'Wert eingeben') : meta.value || 'Wert eingeben'}
                    className="w-full border rounded px-3 py-2 text-sm font-mono pr-10"
                  />
                )}
                {meta.is_secret && (
                  <button
                    type="button"
                    onClick={() => toggleShow(key)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showSecrets[key] ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                )}
              </div>
            </div>
            {key === 'DOCKER_MONITOR_SERVERS' && (
              <p className="text-xs text-gray-500 mt-1">
                Mehrere Hosts als JSON-Array, z.B. <code className="bg-gray-100 px-1 rounded">{`[{"name":"Main","host":"46.225.53.7","user":"root","port":22},{"name":"Backup","host":"1.2.3.4","user":"root","port":22}]`}</code>
              </p>
            )}
            {meta.is_secret && meta.has_value && (
              <p className="text-xs text-gray-400 mt-1 font-mono">{meta.value}</p>
            )}
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3 mt-4 pt-4 border-t">
        <button
          onClick={handleSave}
          disabled={!hasChanges}
          className="btn btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save size={16} /> Speichern
        </button>
        {saved && (
          <span className="flex items-center gap-1 text-green-600 text-sm">
            <CheckCircle size={16} /> Gespeichert
          </span>
        )}
      </div>
    </div>
  )
}

export default function SettingsPage() {
  const queryClient = useQueryClient()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.get,
  })

  const updateSettings = useMutation({
    mutationFn: (settings: Record<string, string>) => settingsApi.update({ settings }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
  })

  if (isLoading) return <div className="text-center py-8 text-gray-500">Laden...</div>

  if (isError) return (
    <div className="text-center py-8">
      <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
      <p className="text-red-600">Fehler beim Laden der Einstellungen</p>
    </div>
  )

  const groups = data?.data?.data as Record<string, SettingGroup> || {}

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Einstellungen</h1>
          <p className="text-gray-500 mt-1">API-Keys und Konfiguration verwalten</p>
        </div>
      </div>

      {updateSettings.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-700 text-sm">Fehler beim Speichern der Einstellungen</p>
        </div>
      )}

      <div className="grid gap-6">
        {Object.entries(groups).map(([groupKey, group]) => (
          <SettingsGroup
            key={groupKey}
            groupKey={groupKey}
            group={group}
            onSave={(settings) => updateSettings.mutate(settings)}
          />
        ))}
      </div>

      <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-amber-800 text-sm">
          Hinweis: Einige Einstellungen erfordern einen Neustart des Backends, um wirksam zu werden.
          Bei Docker-Umgebungen: <code className="bg-amber-100 px-1 rounded">docker-compose restart backend</code>
        </p>
      </div>
    </div>
  )
}
