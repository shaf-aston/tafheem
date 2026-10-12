import { describe, expect, it } from 'vitest'

import { bootShellPlugin } from './bootShell'

describe('bootShellPlugin', () => {
  it('paints the theme ground before any CSS, on any page', () => {
    const out = bootShellPlugin.transformIndexHtml.handler('<head></head><body><div id="root"></div></body>')
    expect(out).toContain('background: #0c1018')
  })
})
