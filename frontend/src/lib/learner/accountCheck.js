/**
 * The header's check, on each load, that the name kept in this browser is still this browser's to use
 * (components/profile/ProfileButton.jsx). Apart from the component so it can be tested without one.
 */
import { errorMessage } from '../api/apiError'
import { logOutBecause } from './profile'
import { pullShelf } from '../store/shelf'
import { fetchAccount, logIn, needsCode, newRecoveryCode } from './progress'

/**
 * The account, once this browser is proven to be its; `onCode` gets a recovery code made on the way.
 * Resolves null after logging out (a 401: the server's reason is kept for the log-in box). Throws
 * anything else, so a server that is down logs nobody out.
 */
export async function checkAccount(name, onCode) {
  try {
    const account = await fetchAccount()
    if (account.proven !== false) {
      // Signed up from a page that never showed a code: this browser holds the account, and makes its first
      // code now. A failure is no reason to log out: the next load asks again.
      if (account.has_code === false) await newRecoveryCode().then(onCode, () => {})
      return account
    }
    // An account from before codes that nobody has claimed: this browser claims it.
    try {
      const signed = await logIn(name)
      if (signed.recovery) onCode(signed.recovery)
      // The shelf is the account's own, so reading it needs the cookie this claim just set; the pull at start
      // was refused. (Pushes waited the same way, so this device's copy is still the one to keep in step.)
      await pullShelf(name)
      // What is returned is react-query's to keep for half an hour: not with the code in it.
      return { ...signed, recovery: undefined }
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
