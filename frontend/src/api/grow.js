// Grow: the worlds the learning paths are served from.
import { api } from './client'

// One Grow world served whole by the backend (routers/grow.py): its levels, paths and units. The Prayer world reads it.
export const getGrowWorld = (id) =>
  api.get(`/grow/worlds/${id}`).then((r) => r.data)
