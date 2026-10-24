// Rendered to static markup: with no IntersectionObserver (as in tests and old
// browsers) useInView counts an element as seen, so a .reveal is never left hidden.
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import Reveal from './Reveal'

describe('Reveal', () => {
  it('renders its children as a visible .reveal.in, wearing the class it was given', () => {
    const html = renderToStaticMarkup(<Reveal as="h2" className="strip" style={{ '--i': 2 }}>Hello</Reveal>)
    expect(html).toMatch(/^<h2 class="reveal in strip"/)
    expect(html).toContain('Hello')
  })
})
