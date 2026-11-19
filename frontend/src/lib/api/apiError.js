import offline from '../../config/offline.json'

// A command to start the server helps only on the machine the server would run on.
const OWN_MACHINE = ['localhost', '127.0.0.1'].includes(globalThis.location?.hostname)

/**
 * The words for a request that got no answer at all, or null when it did get one. With no
 * signal that is the reader's connection, not the server, and says so in their words.
 */
function unreached(error) {
  if (error?.response?.status) return null
  if (globalThis.navigator?.onLine === false) return offline.copy['needs-signal']
  if (error?.code === 'ERR_NETWORK' || error?.message?.toLowerCase().includes('network')) {
    return OWN_MACHINE ? "Can't reach the backend. Is it running? Try: python -m uvicorn backend.main:app --reload" : offline.copy.unreached
  }
  return null
}

/** Extract a user-facing message from an axios/fetch error. */
export function errorMessage(error, fallback = 'An unexpected error occurred.') {
  return error?.response?.data?.detail || unreached(error) || error?.message || fallback
}

export function errorStatus(error) {
  return error?.response?.status
}

/**
 * A query's `retry`: a failed request tried again up to `times` times, but never one the
 * server refused (4xx, 429 among them). Asked again it answers the same, and on a model
 * route each refusal still counts against the reader's share of calls.
 */
export const retryServerErrors = (times) => (failures, error) => {
  const status = errorStatus(error)
  return failures < times && !(status >= 400 && status < 500)
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
  if (!status) return unreached(error) || error?.message || fallback

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
  if (status === 504) return 'Request timed out. Try again in a few seconds.'

  return detail || fallback
}
