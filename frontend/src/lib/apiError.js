/** Extract a user-facing message from an axios/fetch error. */
export function errorMessage(error, fallback = 'An unexpected error occurred.') {
  return error?.response?.data?.detail || error?.message || fallback
}

export function errorStatus(error) {
  return error?.response?.status
}

/**
 * Returns a specific, actionable error message based on HTTP status code.
 * Falls back to the server's `detail` field, then the provided fallback string.
 *
 * Use this in place of errorMessage() for better H9 (error recovery) compliance.
 */
export function smartError(error, fallback = 'Request failed.') {
  const status = error?.response?.status
  const detail = error?.response?.data?.detail

  // Network-level failure, no HTTP response at all
  if (!status) {
    if (error?.code === 'ERR_NETWORK' || error?.message?.toLowerCase().includes('network')) {
      return "Can't reach the backend. Is it running? Try: python -m uvicorn backend.main:app --reload"
    }
    return error?.message || fallback
  }

  if (status === 404) return detail || 'Not found. Check the reference numbers and try again.'
  if (status === 422) return detail || "The server couldn't process that input. Check your Arabic text."
  if (status === 429) return 'Too many requests. Wait a moment, then try again.'
  // Not an API-key message: a dead backend behind the dev proxy also lands here,
  // and blaming a key sends the reader to fix the wrong thing.
  if (status === 500) return detail || 'The server hit an error. If it was just restarted, wait a moment and try again.'
  // detail first, like every line above it: 503 also means "a part of the app is
  // switched off", no AI reachable, a book not loaded; and the server says
  // which. Telling the reader to wait for a startup that already finished sends
  // them to watch the wrong thing.
  if (status === 503) return detail || 'Backend is starting up. Wait a moment, then try again.'
  if (status === 504) return 'Request timed out. The AI model is busy. Try again in a few seconds.'

  return detail || fallback
}
