/**
 * The app's Arabic face asked for with the page, not after it.
 *
 * A face named in CSS is only fetched once the browser has the CSS, has laid
 * out text that uses it, and found it missing: three steps late, so the
 * Arabic drew in a fallback face and then jumped when Noto Naskh landed. Two
 * preload links, for the Arabic (400 weight) and the interface's Latin
 * face, start them with the page. Only those: preloading every weight
 * and face would hold back the page's own code for files most visits never use.
 */
const FACES = [
  /^assets\/noto-naskh-arabic-arabic-400-normal-[\w-]+\.woff2$/,
  // The interface face (Latin): its late swap reflowed every label and button.
  /^assets\/inter-latin-wght-normal-[\w-]+\.woff2$/,
]

// The tabs that draw the Qur'an in its script (the app's own addresses, vercel.json), and its face.
const QURAN_TABS = /^\/(mem|memorise|quran)(\/|$)/
const QURAN_FACE = /^assets\/scheherazade-new-arabic-400-normal-[\w-]+\.woff2$/

const link = (file) => `<link rel="preload" as="font" type="font/woff2" href="/${file}" crossorigin>`
const builtIn = (bundle, face) => Object.keys(bundle ?? {}).find((name) => face.test(name))

/** The links for the faces' built files in `bundle`; '' for any that is not there. */
export function fontPreloadTag(bundle) {
  return FACES.map((face) => builtIn(bundle, face))
    .filter(Boolean)
    .map(link)
    .join('\n    ')
}

/** The line that adds the Qur'an face's link on the tabs that draw it; '' when the face is not built. */
export function quranPreloadScript(bundle) {
  const file = builtIn(bundle, QURAN_FACE)
  return file ? `<script>if (${QURAN_TABS}.test(location.pathname)) document.head.insertAdjacentHTML('beforeend', '${link(file)}')</script>` : ''
}

/** For app.html only: the landing page has its own, lighter, type. */
export const preloadFont = {
  name: 'preload-font',
  transformIndexHtml: {
    order: 'post',
    handler(html, { filename, bundle }) {
      if (!filename.endsWith('app.html')) return html
      const tags = [fontPreloadTag(bundle), quranPreloadScript(bundle)].filter(Boolean).join('\n    ')
      return tags ? html.replace('</title>', `</title>\n    ${tags}`) : html
    },
  },
}
