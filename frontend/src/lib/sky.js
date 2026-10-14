/**
 * Where a surah's stars sit in its constellation. Pure: ayah count and a seed (the surah number) in,
 * points out, in a 0..100 by 0..60 box (stars keep to y 16..44; Sky.jsx shows 10..50). Drawn by components/grow/scenes/Sky.jsx.
 * Reads right to left (the first ayah on the right), zig-zagging; made for up to 11 stars (8 apart at least).
 */
import { makeRandom } from './quiz'

const WIDTH = 100
const MARGIN = 8
const MID = 30

export function starsOf(count, seed) {
  const random = makeRandom(seed)
  const step = count > 1 ? (WIDTH - 2 * MARGIN) / (count - 1) : 0
  return Array.from({ length: count }, (_, i) => {
    const x = count > 1 ? WIDTH - MARGIN - i * step : WIDTH / 2
    const dy = count > 1 ? (i % 2 ? 1 : -1) * (8 + 6 * random()) : 0
    return { x: +(x + (random() - 0.5) * 3).toFixed(1), y: +(MID + dy).toFixed(1) }
  })
}
