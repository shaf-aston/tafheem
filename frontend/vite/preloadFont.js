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

/** The links for the faces' built files in `bundle`; '' for any that is not there. */
export function fontPreloadTag(bundle) {
  const names = Object.keys(bundle ?? {})
  return FACES.map((face) => names.find((name) => face.test(name)))
    .filter(Boolean)
    .map((file) => `<link rel="preload" as="font" type="font/woff2" href="/${file}" crossorigin>`)
    .join('\n    ')
}

/** For app.html only: the landing page has its own, lighter, type. */
export const preloadFont = {
  name: 'preload-font',
  transformIndexHtml: {
    order: 'post',
    handler(html, { filename, bundle }) {
      if (!filename.endsWith('app.html')) return html
      const tag = fontPreloadTag(bundle)
      return tag ? html.replace('</title>', `</title>\n    ${tag}`) : html
    },
  },
}
