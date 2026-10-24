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
 * The landing page does not, and is always the base look.
 */
import { readFileSync } from 'node:fs'
import { colorScheme } from '../src/lib/theme/colorScheme.js'

const theme = JSON.parse(readFileSync(new URL('../src/config/theme.json', import.meta.url), 'utf8'))
const { base, 'hint-key': HINT_KEY, device, looks } = theme.themes

const ground = (selector, bg) => `${selector} { background: ${bg}; }`

// The base look's ground is the page's own; every look gets one for its data-theme.
const GROUNDS = [
  ground('html, body', theme.color.bg),
  ...Object.entries(looks).map(([name, look]) =>
    ground(`html[data-theme="${name}"], html[data-theme="${name}"] body`, look.color?.bg ?? theme.color.bg)),
]

// look name -> the colour-scheme it asks the browser for
const SCHEMES = Object.fromEntries(Object.entries(looks).map(([name, look]) => [name, colorScheme(look.scheme)]))

// Opening from the splash: the page fades in and, on a themed page, the ground
// eases from the splash's dark (the base look, as the manifest has it) to the
// chosen look's. Same keyframe as every other arrival (fade-in, styles/motion.css).
// The Animations setting (--motion-scale 0) and reduced motion both make it a cut.
const { 'boot-ms': BOOT_MS, 'boot-from': BOOT_FROM, 'settle-ease': SETTLE } = theme.motion
const BOOT = (themed) => `@media (prefers-reduced-motion: no-preference) {
      #root > * { --fade-from: ${BOOT_FROM}; animation: fade-in calc(${BOOT_MS}ms * var(--motion-scale, 1)) ${SETTLE} backwards; }${themed ? `
      @keyframes boot-ground { from { background: ${theme.color.bg}; } }
      html[data-theme] { animation: boot-ground calc(${BOOT_MS}ms * var(--motion-scale, 1)) ${SETTLE} backwards; }` : ''}
    }`

const STYLE = (themed) =>
  `<style>html, body { margin: 0; }\n    ${(themed ? GROUNDS : GROUNDS.slice(0, 1)).join('\n    ')}\n    ${BOOT(themed)}</style>`

// The same decision as theme.js's resolveTheme, from the same theme.json: a
// look's name, or the device choice, which asks the device; anything else is
// the base look and is left alone. No hint yet is a first visit, which starts
// on the device choice, as Settings does.
const SCRIPT = `<script>
    try {
      var c = localStorage.getItem('${HINT_KEY}') || '${device.choice}';
      if (c === '${device.choice}') c = matchMedia('(prefers-color-scheme: light)').matches ? '${device.light}' : '${device.dark}';
      var scheme = ${JSON.stringify(SCHEMES)}[c];
      if (scheme && c !== '${base}') { document.documentElement.dataset.theme = c; document.documentElement.style.colorScheme = scheme; }
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
