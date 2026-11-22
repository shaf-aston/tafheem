import { QueryClient } from '@tanstack/react-query'

import { retryServerErrors } from './apiError'

export const queryClient = new QueryClient({
  // The data is fixed for the life of the backend: keep every answer, so a
  // second visit is instant and a fetch-ahead (lib/api/warm) is never repeated.
  // A failed read is tried once more, but not one the server refused or the host could not reach it for.
  defaultOptions: { queries: { retry: retryServerErrors(1), staleTime: Infinity, gcTime: 30 * 60_000 } },
})
