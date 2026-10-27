// The app itself: whether the backend is up, and what it is built on.
import { api } from './client'

export const healthCheck = () =>
  api.get('/health').then((r) => r.data)

// Everything the app is built on. Fixed for the life of the backend, so it is
// asked for once and kept, the footer on every tab reads the same answer.
export const getSources = () =>
  api.get('/sources').then((r) => r.data.sources)
