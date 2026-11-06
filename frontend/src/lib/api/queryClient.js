import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  // The data is fixed for the life of the backend: keep every answer, so a
  // second visit is instant and a fetch-ahead (lib/api/warm) is never repeated.
  defaultOptions: { queries: { retry: 1, staleTime: Infinity, gcTime: 30 * 60_000 } },
})
