/** A file that does not change while the page is open (public/, a timing sheet): loaded once, one error wording. */
import { queryClient } from './queryClient'

export async function fetchStatic(url, what) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Could not load ${what} (${response.status})`)
  return response.json()
}

export const staticQuery = (url, what) => ({
  queryKey: ['static', url],
  queryFn: () => fetchStatic(url, what),
  staleTime: Infinity,
})

/** The same file for code outside React; the one cache is the app's client. */
export const loadStatic = (url, what) => queryClient.fetchQuery(staticQuery(url, what))
