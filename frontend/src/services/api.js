import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const raw = localStorage.getItem('climate-ai-user')
  if (raw) {
    const { token } = JSON.parse(raw)
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api

// ---- typed helper calls (keeps components free of raw endpoint strings) ----
export const getCurrentWeather = () => api.get('/weather').then((r) => r.data)
export const getNationalSummary = () => api.get('/weather/national-summary').then((r) => r.data)
export const getDistricts = () => api.get('/districts').then((r) => r.data)
export const getDistrictHistory = (district, days = 60) =>
  api.get(`/districts/${encodeURIComponent(district)}/history`, { params: { days } }).then((r) => r.data)
export const getRegionSummary = () => api.get('/districts/regions/summary').then((r) => r.data)
export const getPredictions = () => api.get('/prediction').then((r) => r.data)
export const postPrediction = (payload) => api.post('/prediction', payload).then((r) => r.data)
export const getModelMetrics = () => api.get('/prediction/model-metrics').then((r) => r.data)
export const getAlerts = (minLevel = 'Yellow', search = '') =>
  api.get('/alerts', { params: { min_level: minLevel, search: search || undefined } }).then((r) => r.data)
export const getNationalTrend = (days = 90) => api.get('/history', { params: { days } }).then((r) => r.data)
export const uploadWeatherFile = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return api
    .post('/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => onProgress?.(Math.round((evt.loaded * 100) / evt.total)),
    })
    .then((r) => r.data)
}
