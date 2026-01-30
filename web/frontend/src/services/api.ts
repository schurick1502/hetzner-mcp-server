import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
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
}

// Misc
export const miscApi = {
  sshKeys: () => api.get('/ssh-keys'),
  images: () => api.get('/images'),
  serverTypes: () => api.get('/server-types'),
  locations: () => api.get('/locations'),
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

export default api
