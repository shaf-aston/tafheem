import { describe, expect, it } from 'vitest'

import { bootShellPlugin } from './bootShell'

describe('bootShell', () => {
  it('paints the theme ground and puts the spinner in #root, on any page', () => {
    const html = '<head></head><body><div id="root"></div></body>'
    const out = bootShellPlugin.transformIndexHtml.handler(html)
    expect(out).toContain('background: #0c1018')
    expect(out).toContain('<div id="root"><div class="boot"')
  })
})
