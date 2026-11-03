// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'

import { reloadOnUpdate } from './offline'

/** A stand-in service worker container that can say a new worker took over. */
function worker(controller) {
  const target = new EventTarget()
  Object.defineProperty(navigator, 'serviceWorker', { configurable: true, value: Object.assign(target, { controller }) })
  return () => target.dispatchEvent(new Event('controllerchange'))
}

const reload = vi.fn()
Object.defineProperty(window, 'location', { configurable: true, value: { reload } })
const visibility = (state) => {
  Object.defineProperty(document, 'visibilityState', { configurable: true, value: state })
  document.dispatchEvent(new Event('visibilitychange'))
}

afterEach(() => { reload.mockReset(); visibility('visible') })

describe('reloadOnUpdate', () => {
  it('loads the new version at once when the page has not been touched', () => {
    const takeOver = worker({})
    reloadOnUpdate()
    takeOver()
    expect(reload).toHaveBeenCalledOnce()
  })

  it('waits for the reader to switch away once they are using the page', () => {
    const takeOver = worker({})
    reloadOnUpdate()
    window.dispatchEvent(new Event('pointerdown'))
    takeOver()
    expect(reload).not.toHaveBeenCalled()
    visibility('hidden')
    expect(reload).toHaveBeenCalledOnce()
  })

  it('does nothing on the very first visit, when no version was running before', () => {
    const takeOver = worker(null)
    reloadOnUpdate()
    takeOver()
    expect(reload).not.toHaveBeenCalled()
  })
})
