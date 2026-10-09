/**
 * The app's Arabic face asked for with the page, not after it.
 *
 * A face named in CSS is only fetched once the browser has the CSS, has laid
 * out text that uses it, and found it missing: three steps late, so the
 * Arabic drew in a fallback face and then jumped when Noto Naskh landed. One
 * preload link for the one file every tab reads in (400 weight, Arabic
 * letters) starts it with the page. Only that one: preloading every weight
 * and face would hold back the page's own code for files most visits never use.
 */
const FACE = /^assets\/noto-naskh-arabic-arabic-400-normal-[\w-]+\.woff2$/

/** The link for the face's built file in `bundle`, or '' if it is not there. */
export function fontPreloadTag(bundle) {
  const file = Object.keys(bundle ?? {}).find((name) => FACE.test(name))
  return file ? `<link rel="preload" as="font" type="font/woff2" href="/${file}" crossorigin>` : ''
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
