import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8501'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Servers
export const serversApi = {
  list: () => api.get('/servers'),
  get: (id: string) => api.get(`/servers/${id}`),
  create: (data: any) => api.post('/servers', data),
  delete: (id: string, force: boolean = false) => api.delete(`/servers/${id}?force=${force}`),
  power: (id: string, action: string) => api.post(`/servers/${id}/power`, { action }),
  enableBackup: (id: string) => api.post(`/servers/${id}/backup/enable`),
  disableBackup: (id: string) => api.post(`/servers/${id}/backup/disable`),
}

// Firewalls
export const firewallsApi = {
  list: () => api.get('/firewalls'),
  create: (data: any) => api.post('/firewalls', data),
  delete: (id: string, force: boolean = false) => api.delete(`/firewalls/${id}?force=${force}`),
  addRule: (id: string, rule: any) => api.post(`/firewalls/${id}/rules`, rule),
  setRules: (id: string, rules: any[]) => api.put(`/firewalls/${id}/rules`, { rules }),
}

// Volumes
export const volumesApi = {
  list: () => api.get('/volumes'),
  create: (data: any) => api.post('/volumes', data),
  delete: (id: string, force: boolean = false) => api.delete(`/volumes/${id}?force=${force}`),
  attach: (volume: string, server: string) => api.post(`/volumes/${volume}/attach/${server}`),
  detach: (volume: string) => api.post(`/volumes/${volume}/detach`),
}

// Networks
export const networksApi = {
  list: () => api.get('/networks'),
  create: (data: any) => api.post('/networks', data),
  delete: (id: string, force: boolean = false) => api.delete(`/networks/${id}?force=${force}`),
  addSubnet: (id: string, data: any) => api.post(`/networks/${id}/subnets`, data),
  deleteSubnet: (id: string, ip_range: string) => api.delete(`/networks/${id}/subnets`, { data: { ip_range } }),
  addRoute: (id: string, data: any) => api.post(`/networks/${id}/routes`, data),
  deleteRoute: (id: string, data: any) => api.delete(`/networks/${id}/routes`, { data }),
}

// Settings
export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data: any) => api.put('/settings', data),
}

// Misc
export const miscApi = {
  sshKeys: () => api.get('/ssh-keys'),
  images: () => api.get('/images'),
  serverTypes: () => api.get('/server-types'),
  locations: () => api.get('/locations'),
}

// Storage (Images by type)
export const storageApi = {
  snapshots: () => api.get('/images', { params: { image_type: 'snapshot' } }),
  backups: () => api.get('/images', { params: { image_type: 'backup' } }),
  systemImages: () => api.get('/images', { params: { image_type: 'system' } }),
}

// Docker Monitoring
export const dockerApi = {
  servers: () => api.get('/docker/servers'),
  containers: (server: string) => api.get('/docker/containers', { params: { server } }),
  systemMetrics: (server: string) => api.get('/docker/system-metrics', { params: { server } }),
}

// Metrics
export const metricsApi = {
  getServerMetrics: (id: string, type: string, start: string, end: string) =>
    api.get(`/servers/${id}/metrics`, { params: { type, start, end } }),
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
  getCosts: () => api.get('/costs'),
}

// Load Balancers
export const loadBalancersApi = {
  list: () => api.get('/load-balancers'),
  create: (data: any) => api.post('/load-balancers', data),
  delete: (id: string, force: boolean = false) => api.delete(`/load-balancers/${id}?force=${force}`),
  addService: (id: string, data: any) => api.post(`/load-balancers/${id}/services`, data),
  deleteService: (id: string, listenPort: number) => api.delete(`/load-balancers/${id}/services/${listenPort}`),
  addTarget: (id: string, data: any) => api.post(`/load-balancers/${id}/targets`, data),
  removeTarget: (id: string, data: any) => api.delete(`/load-balancers/${id}/targets`, { data }),
  changeAlgorithm: (id: string, data: any) => api.put(`/load-balancers/${id}/algorithm`, data),
}

// Topology
export const topologyApi = {
  get: () => api.get('/topology'),
}

// Bulk Operations
export const bulkApi = {
  execute: (action: string, serverNames: string[]) =>
    api.post('/servers/bulk', { action, server_names: serverNames }),
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
  list: () => api.get('/dns'),
  updatePtr: (data: any) => api.patch('/dns', data),
}

// Health Checks
export const healthApi = {
  check: () => api.get('/health-checks'),
}

export default api
