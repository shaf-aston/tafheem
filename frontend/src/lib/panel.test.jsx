import { Suspense } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { panel } from './panel'

const Stub = ({ x }) => <p>stub {x}</p>

describe('panel', () => {
  it('waits on the code until it has come', () => {
    const P = panel(() => new Promise(() => {}))
    expect(renderToStaticMarkup(<Suspense fallback="wait"><P x={1} /></Suspense>)).toBe('wait')
  })

  it('renders at once once preloaded', async () => {
    const P = panel(async () => ({ default: Stub }))
    await P.preload()
    expect(renderToStaticMarkup(<Suspense fallback="wait"><P x={1} /></Suspense>)).toBe('<p>stub 1</p>')
  })
})
