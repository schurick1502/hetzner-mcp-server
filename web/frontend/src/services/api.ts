import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8501'
const ACCOUNT_STORAGE_KEY = 'hetzner_active_account'

export function getActiveHetznerAccount(): string | null {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(ACCOUNT_STORAGE_KEY)
}

export function setActiveHetznerAccount(accountId: string | null): void {
  if (typeof window === 'undefined') return
  if (accountId) {
    window.localStorage.setItem(ACCOUNT_STORAGE_KEY, accountId)
  } else {
    window.localStorage.removeItem(ACCOUNT_STORAGE_KEY)
  }
}

export function getHetznerAccountHeaders(): Record<string, string> {
  const accountId = getActiveHetznerAccount()
  return accountId && accountId !== 'all' ? { 'X-Hetzner-Account': accountId } : {}
}

function requireSpecificAccountForWrite(): void {
  if (getActiveHetznerAccount() === 'all') {
    throw new Error('Schreibaktionen sind im Modus "Alle Accounts" deaktiviert. Bitte einen konkreten Account waehlen.')
  }
}

async function getAllAccountIds(): Promise<string[]> {
  const res = await api.get('/accounts')
  const accounts = res?.data?.accounts || []
  return accounts.map((a: any) => a.id).filter(Boolean)
}

async function listAcrossAccounts(path: string, listKey: string, params?: any): Promise<any> {
  const active = getActiveHetznerAccount()
  if (active !== 'all') {
    return api.get(path, params ? { params } : undefined)
  }

  const accountIds = await getAllAccountIds()
  const responses = await Promise.all(
    accountIds.map((accountId) => api.get(path, {
      ...(params ? { params } : {}),
      headers: { 'X-Hetzner-Account': accountId },
    }))
  )

  const mergedItems = responses.flatMap((res, idx) => {
    const items = res?.data?.[listKey]
    if (!Array.isArray(items)) return []
    const accountId = accountIds[idx]
    return items.map((item: any) => ({ ...item, __account: accountId }))
  })

  const mergedData = {
    success: true,
    [listKey]: mergedItems,
    count: mergedItems.length,
  }

  return { ...responses[0], data: mergedData }
}

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const accountId = getActiveHetznerAccount()
  if (accountId && accountId !== 'all') {
    config.headers = config.headers ?? {}
    config.headers['X-Hetzner-Account'] = accountId
  }
  return config
})

// Servers
export const serversApi = {
  list: () => listAcrossAccounts('/servers', 'servers'),
  get: (id: string) => api.get(`/servers/${id}`),
  create: (data: any) => { requireSpecificAccountForWrite(); return api.post('/servers', data) },
  delete: (id: string, force: boolean = false) => { requireSpecificAccountForWrite(); return api.delete(`/servers/${id}?force=${force}`) },
  power: (id: string, action: string) => { requireSpecificAccountForWrite(); return api.post(`/servers/${id}/power`, { action }) },
  enableBackup: (id: string) => { requireSpecificAccountForWrite(); return api.post(`/servers/${id}/backup/enable`) },
  disableBackup: (id: string) => { requireSpecificAccountForWrite(); return api.post(`/servers/${id}/backup/disable`) },
}

// Firewalls
export const firewallsApi = {
  list: () => listAcrossAccounts('/firewalls', 'firewalls'),
  create: (data: any) => { requireSpecificAccountForWrite(); return api.post('/firewalls', data) },
  delete: (id: string, force: boolean = false) => { requireSpecificAccountForWrite(); return api.delete(`/firewalls/${id}?force=${force}`) },
  addRule: (id: string, rule: any) => { requireSpecificAccountForWrite(); return api.post(`/firewalls/${id}/rules`, rule) },
  setRules: (id: string, rules: any[]) => { requireSpecificAccountForWrite(); return api.put(`/firewalls/${id}/rules`, { rules }) },
}

// Volumes
export const volumesApi = {
  list: () => listAcrossAccounts('/volumes', 'volumes'),
  create: (data: any) => { requireSpecificAccountForWrite(); return api.post('/volumes', data) },
  delete: (id: string, force: boolean = false) => { requireSpecificAccountForWrite(); return api.delete(`/volumes/${id}?force=${force}`) },
  attach: (volume: string, server: string) => { requireSpecificAccountForWrite(); return api.post(`/volumes/${volume}/attach/${server}`) },
  detach: (volume: string) => { requireSpecificAccountForWrite(); return api.post(`/volumes/${volume}/detach`) },
}

// Networks
export const networksApi = {
  list: () => listAcrossAccounts('/networks', 'networks'),
  create: (data: any) => { requireSpecificAccountForWrite(); return api.post('/networks', data) },
  delete: (id: string, force: boolean = false) => { requireSpecificAccountForWrite(); return api.delete(`/networks/${id}?force=${force}`) },
  addSubnet: (id: string, data: any) => { requireSpecificAccountForWrite(); return api.post(`/networks/${id}/subnets`, data) },
  deleteSubnet: (id: string, ip_range: string) => { requireSpecificAccountForWrite(); return api.delete(`/networks/${id}/subnets`, { data: { ip_range } }) },
  addRoute: (id: string, data: any) => { requireSpecificAccountForWrite(); return api.post(`/networks/${id}/routes`, data) },
  deleteRoute: (id: string, data: any) => { requireSpecificAccountForWrite(); return api.delete(`/networks/${id}/routes`, { data }) },
}

// Settings
export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data: any) => api.put('/settings', data),
}

// Misc
export const miscApi = {
  accounts: () => api.get('/accounts'),
  sshKeys: () => listAcrossAccounts('/ssh-keys', 'ssh_keys'),
  images: () => listAcrossAccounts('/images', 'images'),
  serverTypes: () => listAcrossAccounts('/server-types', 'server_types'),
  locations: () => listAcrossAccounts('/locations', 'locations'),
}

// Storage (Images by type)
export const storageApi = {
  snapshots: () => listAcrossAccounts('/images', 'images', { image_type: 'snapshot' }),
  backups: () => listAcrossAccounts('/images', 'images', { image_type: 'backup' }),
  systemImages: () => listAcrossAccounts('/images', 'images', { image_type: 'system' }),
}

// Docker Monitoring
export const dockerApi = {
  servers: () => api.get('/docker/servers'),
  containers: (server: string) => api.get('/docker/containers', { params: { server } }),
  systemMetrics: (server: string) => api.get('/docker/system-metrics', { params: { server } }),
}

// Metrics
export const metricsApi = {
  getServerMetrics: (id: string, type: string, start: string, end: string, accountId?: string) =>
    (() => {
      if (getActiveHetznerAccount() === 'all' && !accountId) {
        throw new Error('Metriken im Modus "Alle Accounts" nicht verfuegbar. Bitte einen Account waehlen.')
      }
      return api.get(`/servers/${id}/metrics`, {
        params: { type, start, end },
        ...(accountId ? { headers: { 'X-Hetzner-Account': accountId } } : {}),
      })
    })(),
}

// CLI
export const cliApi = {
  execute: (command: string, args: Record<string, any>) =>
    api.post('/cli/execute', { command, args }),
  listTools: () => api.get('/cli/tools'),
}

// AI
export const aiApi = {
  listProviders: () => api.get('/ai/providers'),
  // Chat verwendet fetch direkt wegen SSE
}

// Security
export const securityApi = {
  audit: () => api.get('/security/audit'),
}

// Costs
export const costsApi = {
  getCosts: async () => {
    if (getActiveHetznerAccount() !== 'all') return api.get('/costs')

    const accountIds = await getAllAccountIds()
    const responses = await Promise.all(
      accountIds.map((accountId) => api.get('/costs', { headers: { 'X-Hetzner-Account': accountId } }))
    )

    const merged = {
      total_monthly: 0,
      breakdown: {
        servers: { total: 0, items: [] as any[] },
        volumes: { total: 0, items: [] as any[] },
        snapshots: { total: 0, items: [] as any[] },
        floating_ips: { total: 0, items: [] as any[] },
        primary_ips: { total: 0, items: [] as any[] },
        load_balancers: { total: 0, items: [] as any[] },
      },
      server_types: [] as any[],
    }

    responses.forEach((res, idx) => {
      const accountId = accountIds[idx]
      const data = res?.data?.data
      if (!data) return
      merged.total_monthly += Number(data.total_monthly || 0)
      Object.keys(merged.breakdown).forEach((key) => {
        const src = data.breakdown?.[key]
        if (!src) return
        merged.breakdown[key as keyof typeof merged.breakdown].total += Number(src.total || 0)
        merged.breakdown[key as keyof typeof merged.breakdown].items.push(
          ...(src.items || []).map((item: any) => ({ ...item, __account: accountId }))
        )
      })
      if (Array.isArray(data.server_types) && merged.server_types.length === 0) {
        merged.server_types = data.server_types
      }
    })

    return { ...responses[0], data: { success: true, data: merged } }
  },
}

// Load Balancers
export const loadBalancersApi = {
  list: () => listAcrossAccounts('/load-balancers', 'load_balancers'),
  create: (data: any) => { requireSpecificAccountForWrite(); return api.post('/load-balancers', data) },
  delete: (id: string, force: boolean = false) => { requireSpecificAccountForWrite(); return api.delete(`/load-balancers/${id}?force=${force}`) },
  addService: (id: string, data: any) => { requireSpecificAccountForWrite(); return api.post(`/load-balancers/${id}/services`, data) },
  deleteService: (id: string, listenPort: number) => { requireSpecificAccountForWrite(); return api.delete(`/load-balancers/${id}/services/${listenPort}`) },
  addTarget: (id: string, data: any) => { requireSpecificAccountForWrite(); return api.post(`/load-balancers/${id}/targets`, data) },
  removeTarget: (id: string, data: any) => { requireSpecificAccountForWrite(); return api.delete(`/load-balancers/${id}/targets`, { data }) },
  changeAlgorithm: (id: string, data: any) => { requireSpecificAccountForWrite(); return api.put(`/load-balancers/${id}/algorithm`, data) },
}

// Topology
export const topologyApi = {
  get: async () => {
    if (getActiveHetznerAccount() !== 'all') return api.get('/topology')

    const accountIds = await getAllAccountIds()
    const responses = await Promise.all(
      accountIds.map((accountId) => api.get('/topology', { headers: { 'X-Hetzner-Account': accountId } }))
    )

    const mergedNodes: any[] = []
    const mergedEdges: any[] = []
    const counts = {
      servers: 0,
      firewalls: 0,
      volumes: 0,
      networks: 0,
      load_balancers: 0,
    }

    responses.forEach((res, idx) => {
      const accountId = accountIds[idx]
      const data = res?.data?.data
      if (!data) return
      const idMap = new Map<string, string>()
      ;(data.nodes || []).forEach((n: any) => {
        const newId = `${accountId}:${n.id}`
        idMap.set(n.id, newId)
        mergedNodes.push({ ...n, id: newId, metadata: { ...n.metadata, __account: accountId } })
      })
      ;(data.edges || []).forEach((e: any) => {
        mergedEdges.push({
          ...e,
          from: idMap.get(e.from) || `${accountId}:${e.from}`,
          to: idMap.get(e.to) || `${accountId}:${e.to}`,
        })
      })
      Object.keys(counts).forEach((k) => {
        counts[k as keyof typeof counts] += Number(data.counts?.[k] || 0)
      })
    })

    return { ...responses[0], data: { success: true, data: { nodes: mergedNodes, edges: mergedEdges, counts } } }
  },
}

// Bulk Operations
export const bulkApi = {
  execute: (action: string, serverNames: string[]) =>
    (() => {
      requireSpecificAccountForWrite()
      return api.post('/servers/bulk', { action, server_names: serverNames })
    })(),
}

// Snapshot Scheduler
export const snapshotSchedulerApi = {
  list: () => api.get('/snapshots/schedules'),
  create: (data: any) => api.post('/snapshots/schedules', data),
  update: (id: string, data: any) => api.put(`/snapshots/schedules/${id}`, data),
  delete: (id: string) => api.delete(`/snapshots/schedules/${id}`),
  runNow: (id: string) => api.post(`/snapshots/schedules/${id}/run`),
}

// Alerting
export const alertingApi = {
  getConfig: () => api.get('/alerting/config'),
  updateConfig: (data: any) => api.put('/alerting/config', data),
  getStatus: () => api.get('/alerting/status'),
}

// DNS
export const dnsApi = {
  list: () => listAcrossAccounts('/dns', 'data'),
  updatePtr: (data: any) => { requireSpecificAccountForWrite(); return api.patch('/dns', data) },
}

// Health Checks
export const healthApi = {
  check: () => api.get('/health-checks'),
}

export default api
