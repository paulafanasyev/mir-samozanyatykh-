import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

// The Frankfurt API is the current production backend. Keep an explicit
// fallback so the static Render frontend never silently sends /api/* to itself
// when VITE_API_URL is missing. Also migrate the old Oregon hostname.
const configuredApiUrl = String(import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '')
const currentApiUrl = 'https://mir-samozanyatykh-api-frankfurt.onrender.com'
const isOldOregonApi = /mirsamozanyatykh-api\.onrender\.com/i.test(configuredApiUrl)
const rawApiBaseUrl = configuredApiUrl && !isOldOregonApi ? configuredApiUrl : currentApiUrl

// Accept both host URLs and legacy URLs ending in /api; request paths are normalized below.
export const API_BASE_URL = rawApiBaseUrl.replace(/\/api$/, '')
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

const csrfToken = () => document.cookie.split('; ').find((x) => x.startsWith('csrf_token='))?.split('=')[1] || ''

apiClient.interceptors.request.use((config) => {
  if (typeof config.url === 'string' && config.url.startsWith('/') && !config.url.startsWith('/api/')) {
    config.url = `/api${config.url}`
  }
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (['post', 'put', 'patch', 'delete'].includes((config.method || '').toLowerCase())) {
    const csrf = csrfToken()
    if (csrf) config.headers['X-CSRF-Token'] = decodeURIComponent(csrf)
  }
  return config
})

let refreshing: Promise<string | null> | null = null
apiClient.interceptors.response.use(undefined, async (error) => {
  const original = error.config
  const shouldRefresh = error.response?.status === 401 && original && !original._retry && !String(original.url || '').includes('/api/auth/refresh')
  if (!shouldRefresh) return Promise.reject(error)
  original._retry = true
  refreshing ||= apiClient.post('/api/auth/refresh').then((response) => {
    const token = response.data.access_token as string
    useAuthStore.getState().setToken(token)
    return token
  }).catch(() => null).finally(() => { refreshing = null })
  const token = await refreshing
  if (token) {
    original.headers.Authorization = `Bearer ${token}`
    return apiClient(original)
  }
  useAuthStore.getState().logout()
  window.location.href = '/login'
  return Promise.reject(error)
})

export const api = apiClient
export default apiClient
