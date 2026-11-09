/**
 * What search engines and AI assistants read about the site, from one file: src/config/seo.json.
 *
 * The landing page is drawn by script, so a crawler that runs none (most AI ones) saw an empty
 * page. This puts the title, social card, structured data (JSON-LD) and a plain summary in the
 * front door's HTML, and writes robots.txt, sitemap.xml and llms.txt beside it at build.
 */
import { readFileSync } from 'node:fs'

const SEO = JSON.parse(readFileSync(new URL('../src/config/seo.json', import.meta.url), 'utf8'))

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const url = (seo, path) => seo.site + path

/** The <head> tags for the front door. */
export function headTags(seo = SEO) {
  const image = url(seo, seo.image.path)
  const meta = [
    ['name', 'description', seo.description],
    ['name', 'keywords', seo.keywords.join(', ')],
    ['property', 'og:type', 'website'],
    ['property', 'og:site_name', seo.name],
    ['property', 'og:url', url(seo, '/')],
    ['property', 'og:title', seo.title],
    ['property', 'og:description', seo.description],
    ['property', 'og:image', image],
    ['property', 'og:image:width', '1200'],
    ['property', 'og:image:height', '630'],
    ['property', 'og:image:alt', seo.image.alt],
    ['name', 'twitter:card', 'summary_large_image'],
  ].map(([key, name, content]) => `<meta ${key}="${name}" content="${esc(content)}" />`)
  return [`<title>${esc(seo.title)}</title>`, `<link rel="canonical" href="${url(seo, '/')}" />`, ...meta,
    `<script type="application/ld+json">${JSON.stringify(jsonLd(seo)).replace(/</g, '\\u003c')}</script>`].join('\n    ')
}

/** Structured data: the app itself, and the questions people ask about it. */
export function jsonLd(seo = SEO) {
  return [
    {
      '@context': 'https://schema.org', '@type': 'WebApplication', name: seo.name, url: url(seo, '/app'),
      description: seo.description, applicationCategory: 'EducationalApplication', operatingSystem: 'Any (web browser)',
      inLanguage: ['en', 'ar'], isAccessibleForFree: true, offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
      featureList: seo.features, image: url(seo, seo.image.path),
    },
    {
      '@context': 'https://schema.org', '@type': 'FAQPage',
      mainEntity: seo.faq.map(({ q, a }) => ({ '@type': 'Question', name: q, acceptedAnswer: { '@type': 'Answer', text: a } })),
    },
  ]
}

/** What a reader that runs no script sees (most AI crawlers); browsers that run the landing never show it. */
export function summary(seo = SEO) {
  const list = (items) => items.map((i) => `<li>${esc(i)}</li>`).join('')
  return `<main><h1>${esc(seo.title)}</h1><p>${esc(seo.description)}</p><ul>${list(seo.features)}</ul>`
    + seo.faq.map(({ q, a }) => `<h2>${esc(q)}</h2><p>${esc(a)}</p>`).join('')
    + `<p><a href="/app">Open Tafheem</a></p></main>`
}

export function robots(seo = SEO) {
  const blocked = seo.noindex.map((p) => `Disallow: ${p}`).join('\n')
  // Named outright so a host's default never shuts the AI assistants out.
  const bots = seo.ai_bots.map((b) => `User-agent: ${b}`).join('\n')
  return `User-agent: *\nAllow: /\n${blocked}\n\n${bots}\nAllow: /\n${blocked}\n\nSitemap: ${url(seo, '/sitemap.xml')}\n`
}

export function sitemap(seo = SEO, today = new Date().toISOString().slice(0, 10)) {
  const rows = seo.pages.map((p) => `  <url><loc>${url(seo, p.path)}</loc><lastmod>${today}</lastmod><priority>${p.priority.toFixed(1)}</priority></url>`)
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${rows.join('\n')}\n</urlset>\n`
}

/** llms.txt (llmstxt.org): the site in plain markdown for AI assistants. */
export function llms(seo = SEO) {
  return `# ${seo.name}\n\n> ${seo.description}\n\n## Features\n\n${seo.features.map((f) => `- ${f}`).join('\n')}\n\n`
    + `## Questions\n\n${seo.faq.map(({ q, a }) => `### ${q}\n\n${a}`).join('\n\n')}\n\n`
    + `## Links\n\n- [Open the app](${url(seo, '/app')})\n- [Privacy](${url(seo, '/privacy.html')})\n`
}

export const seo = {
  name: 'seo',
  transformIndexHtml(html, { filename }) {
    if (!/[\\/]index\.html$/.test(filename)) return html
    return html.replace(/<title>[^<]*<\/title>/, headTags()).replace('<div id="root"></div>', `<div id="root"></div>
    <noscript>${summary()}</noscript>`)
  },
  generateBundle() {
    for (const [fileName, source] of [['robots.txt', robots()], ['sitemap.xml', sitemap()], ['llms.txt', llms()]]) {
      this.emitFile({ type: 'asset', fileName, source })
    }
  },
}
