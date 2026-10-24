/**
 * Where a place sits on the small country maps (components/colloquial/CountryMap).
 *
 * One flat projection for the whole Arab world, shared with the script that
 * drew the outlines (scripts/countryShapes.mjs), so a city's dot lands where its
 * country's outline says. Plain equirectangular, squeezed east-west by the
 * cosine of the region's middle latitude: at these latitudes the shapes read
 * true, and it is two lines anyone can check.
 */
const LON0 = -20
const LAT0 = 42
const K = 14
const SQUEEZE = Math.cos((25 * Math.PI) / 180)

/** [lon, lat] in degrees → [x, y] in map units, y down. */
export const project = ([lon, lat]) => [(lon - LON0) * K * SQUEEZE, (LAT0 - lat) * K]

/**
 * The box, aspect wide to 1 high, that shows these countries and cities with
 * room round them: [x, y, w, h] for an SVG viewBox. A small country is padded
 * out to a least width, so Bahrain or Lebanon shows its neighbours rather than
 * filling the frame like a blob.
 */
export function viewOf(boxes, points = [], { pad = 0.18, least = 60, aspect = 1 } = {}) {
  const xs = [...boxes.flatMap((b) => [b[0], b[2]]), ...points.map((p) => p[0])]
  const ys = [...boxes.flatMap((b) => [b[1], b[3]]), ...points.map((p) => p[1])]
  if (!xs.length) return null
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)]
  const w = Math.max(x1 - x0, (y1 - y0) * aspect, least) * (1 + pad * 2)
  const h = w / aspect
  const round = (n) => Math.round(n * 10) / 10
  return [round((x0 + x1 - w) / 2), round((y0 + y1 - h) / 2), round(w), round(h)]
}

/** Whether two [x0, y0, x1, y1] boxes overlap; a view is [x, y, w, h]. */
export const touches = (box, [x, y, w, h]) => box[0] < x + w && box[2] > x && box[1] < y + h && box[3] > y
