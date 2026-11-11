import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('./progress', () => ({
  fetchAccount: vi.fn(),
  logIn: vi.fn(),
  needsCode: (error) => error?.response?.status === 403,
}))
vi.mock('./profile', () => ({ logOutBecause: vi.fn() }))

const { checkAccount } = await import('./accountCheck')
const { fetchAccount, logIn } = await import('./progress')
const { logOutBecause } = await import('./profile')

const refused = (status, detail) => Object.assign(new Error('refused'), { response: { status, data: { detail } } })

describe('checking the kept name on load', () => {
  let onCode
  beforeEach(() => { onCode = vi.fn() })
  afterEach(() => vi.clearAllMocks())

  it('keeps an account this browser is proven to be', async () => {
    fetchAccount.mockResolvedValue({ name: 'amina', proven: true })
    expect(await checkAccount('amina', onCode)).toEqual({ name: 'amina', proven: true })
    expect(logIn).not.toHaveBeenCalled()
    expect(onCode).not.toHaveBeenCalled()
  })

  it('claims an account from before codes, and hands its new code to be shown', async () => {
    fetchAccount.mockResolvedValue({ name: 'amina', proven: false })
    logIn.mockResolvedValue({ name: 'amina', recovery: 'AAAA-BBBB-CCCC-DDDD' })
    expect(await checkAccount('amina', onCode)).toMatchObject({ name: 'amina' })
    expect(logIn).toHaveBeenCalledWith('amina')
    expect(onCode).toHaveBeenCalledWith('AAAA-BBBB-CCCC-DDDD')
  })

  it('a claim lost to another tab of this browser is no reason to log out', async () => {
    fetchAccount.mockResolvedValueOnce({ name: 'amina', proven: false })
      .mockResolvedValueOnce({ name: 'amina', proven: true })
    logIn.mockRejectedValue(refused(403, "Type this account's recovery code"))
    expect(await checkAccount('amina', onCode)).toEqual({ name: 'amina', proven: true })
    expect(logOutBecause).not.toHaveBeenCalled()
  })

  it('a claim lost to someone else logs out, saying the server\'s reason', async () => {
    fetchAccount.mockResolvedValueOnce({ name: 'amina', proven: false })
      .mockRejectedValueOnce(refused(401, 'Log in again on this device'))
    logIn.mockRejectedValue(refused(403, "Type this account's recovery code"))
    expect(await checkAccount('amina', onCode)).toBeNull()
    expect(logOutBecause).toHaveBeenCalledWith('amina: Log in again on this device.')
  })

  it('a name the server will not take from this browser logs out', async () => {
    fetchAccount.mockRejectedValue(refused(401, 'Log in again: no account with that username'))
    expect(await checkAccount('amina', onCode)).toBeNull()
    expect(logOutBecause).toHaveBeenCalledOnce()
  })

  it('a server that is down logs nobody out', async () => {
    fetchAccount.mockRejectedValue(refused(503, 'starting'))
    await expect(checkAccount('amina', onCode)).rejects.toThrow('refused')
    fetchAccount.mockResolvedValue({ name: 'amina', proven: false })
    logIn.mockRejectedValue(refused(429))
    await expect(checkAccount('amina', onCode)).rejects.toThrow('refused')
    expect(logOutBecause).not.toHaveBeenCalled()
  })
})
