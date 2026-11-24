// Render one still per listed frame with a single bundle: `node scripts/stills.mjs [comp] f1 f2 …`.
import { bundle } from '@remotion/bundler'
import { renderStill, selectComposition } from '@remotion/renderer'
import path from 'node:path'
import fs from 'node:fs'

const args = process.argv.slice(2)
const id = Number.isNaN(Number(args[0])) ? args.shift() : 'Launch'
const frames = args.map(Number)
const browserExecutable = process.env.REMOTION_CHROME || null
const serveUrl = await bundle({ entryPoint: path.resolve('src/index.js') })
const composition = await selectComposition({ serveUrl, id, browserExecutable, inputProps: { withAudio: false } })
fs.mkdirSync('out/stills', { recursive: true })
for (const frame of frames) {
  const output = `out/stills/${id}-${String(frame).padStart(4, '0')}.jpg`
  await renderStill({ serveUrl, composition, frame, output, browserExecutable, imageFormat: 'jpeg', scale: 0.5, inputProps: { withAudio: false } })
  console.log(output)
}
