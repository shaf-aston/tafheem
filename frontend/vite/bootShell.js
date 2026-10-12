/**
 * Every page's ground before its CSS lands: one place, both pages.
 *
 * The theme's colours reach :root from script (theme.js), so until then a page
 * painted the browser's own white, on a laptop and a phone alike. theme.json's
 * `bg` is read here, so there is no second copy of the colour to drift.
 *
 * A page that wears more than one look says so with `data-themed` on <html>.
 * It also gets each look's ground and a short script that reads the hint
 * theme.js left behind, so a reader who chose light is not shown dark first.
 * The landing page does not, and is always dark.
 */
import { readFileSync } from 'node:fs'

const theme = JSON.parse(readFileSync(new URL('../src/theme.json', import.meta.url), 'utf8'))
const { 'hint-key': HINT_KEY, 'base-scheme': BASE_SCHEME, ...looks } = theme.themes

const ground = (selector, bg) => `${selector} { background: ${bg}; }`

const LOOKS = Object.entries(looks).filter(([name, values]) => !name.startsWith('_') && typeof values === 'object')
// look name -> the colour-scheme it asks the browser for
const SCHEMES = Object.fromEntries(LOOKS.map(([name, values]) => [name, values.scheme]))

const GROUNDS = [
  ground('html, body', theme.color.bg),
  ...LOOKS.map(([name, values]) => ground(`html[data-theme="${name}"], html[data-theme="${name}"] body`, values.color.bg)),
]

const STYLE = (themed) =>
  `<style>html, body { margin: 0; }\n    ${(themed ? GROUNDS : GROUNDS.slice(0, 1)).join('\n    ')}</style>`

// The choice is one of the look names or `system` (the device's light look is
// the one named `light`, as in theme.js); anything else is the base look.
const SCRIPT = `<script>
    try {
      var c = localStorage.getItem('${HINT_KEY}');
      if (c === 'system') c = matchMedia('(prefers-color-scheme: light)').matches ? 'light' : '${BASE_SCHEME}';
      var scheme = ${JSON.stringify(SCHEMES)}[c];
      if (scheme) { document.documentElement.dataset.theme = c; document.documentElement.style.colorScheme = scheme; }
    } catch (e) {}
  </script>`

export const bootShellPlugin = {
  name: 'boot-shell',
  transformIndexHtml: {
    order: 'pre',
    handler: (html) => {
      const themed = /<html[^>]*\sdata-themed/.test(html)
      return html.replace('</head>', `  ${STYLE(themed)}${themed ? `\n  ${SCRIPT}` : ''}\n  </head>`)
    },
  },
}
