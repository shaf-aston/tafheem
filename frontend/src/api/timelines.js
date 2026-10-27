// Timelines: the events and why their ayahs came down.
import { api } from './client'

// Every timeline section with its places and sources. About fifty events, fixed
// for the life of the backend, so it is fetched whole once and filtered here.
export const timelinesQuery = {
  queryKey: ['timelines'],
  queryFn: () => api.get('/timelines').then((r) => r.data),
}

// Why the ayahs of one timeline event came down: one line per report. The
// report itself is read from the Qur'an's library like any other book on that
// ayah, so nothing here fetches a megabyte of prose to show a list.
export const asbabQuery = (section, event) => ({
  queryKey: ['timeline-asbab', section, event],
  queryFn: () => api.get(`/timelines/${section}/${event}/asbab`).then((r) => r.data),
})
