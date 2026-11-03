// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'

import * as motion from './motion'
import { flyTo } from './flyTo'

afterEach(() => vi.restoreAllMocks())

describe('flyTo', () => {
  it('flies nothing and leaves nothing behind with Animations off', async () => {
    vi.spyOn(motion, 'motionOff').mockReturnValue(true)
    const from = document.createElement('span')
    const to = document.createElement('span')
    document.body.append(from, to)
    await flyTo(from, to)
    expect(document.body.children).toHaveLength(2)
  })

  it('resolves at once with nothing to fly from or to', async () => {
    await expect(flyTo(null, document.body)).resolves.toBeUndefined()
  })
})
