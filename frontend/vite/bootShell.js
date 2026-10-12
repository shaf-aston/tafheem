/**
 * What every page shows before its script runs: one place, both pages.
 *
 * Until the script lands (and, in the app, until the account's shelf has been
 * asked for) the page was blank, white on a laptop and on a phone alike, and
 * then everything jumped in. The dark ground and a spinner now come with the
 * HTML itself. The ground is theme.json's own `bg`, read here so there is no
 * second copy of the colour to drift; the spinner sits inside #root, so React
 * replaces it on mount. It stays invisible for 250ms: a fast load shows nothing.
 */
import { readFileSync } from 'node:fs'

const { color } = JSON.parse(readFileSync(new URL('../src/theme.json', import.meta.url), 'utf8'))

const STYLE = `<style>
      html, body { background: ${color.bg}; margin: 0; }
      .boot { min-height: 100vh; display: grid; place-items: center; }
      .boot i { width: 28px; height: 28px; border-radius: 50%; border: 3px solid #ffffff22;
        border-top-color: #ffffff88; opacity: 0; animation: boot-spin 0.9s linear 0.25s infinite; }
      @keyframes boot-spin { from { transform: rotate(0); opacity: 1 } to { transform: rotate(360deg); opacity: 1 } }
    </style>`
const SPINNER = '<div class="boot" aria-hidden="true"><i></i></div>'

export const bootShellPlugin = {
  name: 'boot-shell',
  transformIndexHtml: {
    order: 'pre',
    handler: (html) =>
      html.replace('</head>', `${STYLE}\n  </head>`).replace('<div id="root"></div>', `<div id="root">${SPINNER}</div>`),
  },
}
