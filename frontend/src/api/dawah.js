// Dawah: the topics and questions.
import { api } from './client'

// Every dawah topic and question, fetched whole once like timelinesQuery.
export const dawahQuery = {
  queryKey: ['dawah'],
  queryFn: () => api.get('/dawah').then((r) => r.data),
}
