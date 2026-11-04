import axios from 'axios'

import { profileHeaders } from '../lib/learner/profile'

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Whose record a request is about goes on every request, read at send time so
// a name switched a moment ago is the one sent. A route that does not care
// ignores it; one that does can no longer be called without it by mistake and
// file a learner's answers under the guest. A call that names someone else
// (sign-up, log-in) keeps its own.
api.interceptors.request.use((config) => {
  for (const [key, value] of Object.entries(profileHeaders())) {
    if (!config.headers.has(key)) config.headers.set(key, value)
  }
  return config
})
