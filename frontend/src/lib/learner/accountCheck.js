/**
 * The header's check, on each load, that the name kept in this browser is still this browser's to use
 * (components/profile/ProfileButton.jsx). Apart from the component so it can be tested without one.
 */
import { errorMessage } from '../api/apiError'
import { logOutBecause } from './profile'
import { fetchAccount, logIn, needsCode } from './progress'

/**
 * The account, once this browser is proven to be its; `onCode` gets a recovery code made on the way.
 * Resolves null after logging out (a 401: the server's reason is kept for the log-in box). Throws
 * anything else, so a server that is down logs nobody out.
 */
export async function checkAccount(name, onCode) {
  try {
    const account = await fetchAccount()
    if (account.proven !== false) return account
    // An account from before codes that nobody has claimed: this browser claims it.
    try {
      const signed = await logIn(name)
      if (signed.recovery) onCode(signed.recovery)
      return signed
    } catch (error) {
      if (!needsCode(error)) throw error
      // Claimed a moment ago: by another tab of this browser (then the cookie is here now), or by someone
      // else (then this asks for the code with a 401, logging out below).
      const again = await fetchAccount()
      if (again.proven !== false) return again
      throw error
    }
  } catch (error) {
    if (error.response?.status !== 401 && !needsCode(error)) throw error
    logOutBecause(`${name}: ${errorMessage(error, 'Log in again')}.`)
    return null
  }
}
