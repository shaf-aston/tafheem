// Fonts load before frame 0: a fallback serif in a render is a bug, not a look.
import { continueRender, delayRender, staticFile } from 'remotion'

const FACES = [
  ['Inter', 'inter.woff2', '100 900', 'normal'],
  ['Noto Naskh Arabic', 'noto-naskh-arabic-arabic-400-normal.woff2', '400', 'normal'],
  ['Noto Naskh Arabic', 'noto-naskh-arabic-arabic-700-normal.woff2', '700', 'normal'],
  ['QPC Hafs', 'qpc-hafs.woff2', '400', 'normal'],
  ['Code Mono', 'dejavu-sans-mono.ttf', '400', 'normal'],
]

const handle = delayRender('Loading brand fonts')
Promise.all(
  FACES.map(([family, file, weight, style]) =>
    new FontFace(family, `url(${staticFile(`fonts/${file}`)})`, { weight, style })
      .load()
      .then((face) => document.fonts.add(face)),
  ),
)
  .then(() => document.fonts.ready)
  .then(() => continueRender(handle))
  .catch((err) => {
    console.error(err)
    continueRender(handle)
  })
