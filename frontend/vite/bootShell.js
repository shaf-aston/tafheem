/**
 * Every page's ground before its CSS lands: one place, both pages.
 *
 * The theme's colours reach :root from script (theme.js), so until then a page
 * painted the browser's own white, on a laptop and a phone alike. theme.json's
 * `bg` is read here, so there is no second copy of the colour to drift.
 */
import { readFileSync } from 'node:fs'

const { color } = JSON.parse(readFileSync(new URL('../src/theme.json', import.meta.url), 'utf8'))

const STYLE = `<style>html, body { background: ${color.bg}; margin: 0; }</style>`

export const bootShellPlugin = {
  name: 'boot-shell',
  transformIndexHtml: {
    order: 'pre',
    handler: (html) => html.replace('</head>', `  ${STYLE}\n  </head>`),
  },
}
