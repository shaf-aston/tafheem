// Colloquial: the spoken dialects, their units, lessons and pictures.
import { api } from './client'

// The spoken dialects with their unit and lesson titles, and nothing else: the
// Colloquial tab opens on this list and a unit is sixty kilobytes on its own.
export const colloquialQuery = {
  queryKey: ['colloquial'],
  queryFn: () => api.get('/colloquial').then((r) => r.data),
}

// One whole unit, every lesson in it. Sent whole because a learner moves between
// a unit's lessons freely, so paging would only add a wait mid-lesson.
export const colloquialUnitQuery = (dialect, unit) => ({
  queryKey: ['colloquial-unit', dialect, unit],
  queryFn: () => api.get(`/colloquial/${encodeURIComponent(dialect)}/${encodeURIComponent(unit)}`).then((r) => r.data),
})

// One lesson's phrases as every dialect says them, matched by slot.
export const colloquialCompareQuery = (unit, lesson) => ({
  queryKey: ['colloquial-compare', unit, lesson],
  queryFn: () => api.get(`/colloquial/compare/${encodeURIComponent(unit)}/${encodeURIComponent(lesson)}`).then((r) => r.data),
})

// A phrase picture: `file` is the path the lesson names, like "unit-01/greeting.jpg".
export const colloquialImageUrl = (file) =>
  `${api.defaults.baseURL}/colloquial/image/${file.split('/').map(encodeURIComponent).join('/')}`
