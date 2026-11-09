import { describe, expect, it } from 'vitest'

import { headTags, robots, seo, sitemap } from './seo'

const page = '<head><title>x</title></head><body><div id="root"></div></body>'

describe('seo', () => {
  it('gives the front door its title, canonical, structured data and a no-script summary', () => {
    const html = seo.transformIndexHtml(page, { filename: '/repo/frontend/index.html' })
    expect(html).toContain('<link rel="canonical" href="https://tafheem-app.vercel.app/" />')
    expect(html).toContain('"@type":"FAQPage"')
    expect(html).toMatch(/<noscript><main><h1>Tafheem: /)
    expect(html).not.toContain('<title>x</title>')
  })

  it('leaves the app and record pages alone', () => {
    expect(seo.transformIndexHtml(page, { filename: '/repo/frontend/app.html' })).toBe(page)
  })

  it('escapes quotes in meta content and keeps </script> out of the JSON-LD', () => {
    const tags = headTags({ site: 'https://a.b', name: 'N', title: 'T', description: 'say "hi" </script>', keywords: [],
      image: { path: '/i.jpg', alt: 'a' }, features: [], faq: [] })
    expect(tags).toContain('content="say &quot;hi&quot; &lt;/script&gt;"')
    expect(tags.match(/<\/script>/g)).toHaveLength(1)
  })

  it('robots lets the AI assistants in, keeps the recorder out, points at the sitemap', () => {
    const txt = robots()
    expect(txt).toContain('User-agent: GPTBot')
    expect(txt).toContain('Disallow: /record')
    expect(txt).toContain('Sitemap: https://tafheem-app.vercel.app/sitemap.xml')
  })

  it('sitemap lists every page', () => {
    expect(sitemap(undefined, '2026-11-09')).toContain('<loc>https://tafheem-app.vercel.app/app</loc><lastmod>2026-11-09</lastmod>')
  })
})
